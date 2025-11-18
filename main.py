"""
FastAPI service that powers the grant demo front-end.

⚠️ SHOWCASE VERSION - For production deployment:
1. Set GEMINI_API_KEY environment variable
2. Update CORS origins with your production domains
3. Configure proper rate limiting and authentication
4. Review all security settings

See SHOWCASE_NOTICE.md for more information.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qa_system import answer_questions

app = FastAPI(title="PHC Grant Assistant API", version="1.0.0")

# Get root directory
ROOT_DIR = Path(__file__).parent

# CORS middleware - Configure for your deployment
# For production, update this list with your actual frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",                # Local development
        "http://localhost:5173",                # Vite default port
        "http://localhost:3000",                # Next.js/React default port
        # Add your production domains here:
        # "https://your-domain.com",
        # "https://your-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],  # Allows Content-Type, Authorization, etc.
)


class GenerateRequest(BaseModel):
    grantQuestions: str = Field(..., min_length=1, description="Raw grant prompts/questions")
    grantContext: str = Field("", description="Supporting context about the grant and organisation")


class AnswerPayload(BaseModel):
    question: str
    answer: str
    sources: List[str]


class GenerateResponse(BaseModel):
    results: List[AnswerPayload]
    tailoring_explanation: str = Field("", description="Explanation of how responses were tailored for the sponsor")
    fit_score: float = Field(0.0, description="Score out of 5.0 indicating how good a fit PHC is for this sponsor/grant")
    fit_explanation: str = Field("", description="Detailed explanation of the fit score and alignment with sponsor priorities")


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY environment variable not set"
        )
    return api_key


def parse_questions(raw: str) -> List[str]:
    """Split raw question input into discrete prompts with robust cleaning.
    
    Handles multiple formats:
    - One question per line (most common)
    - Blank line separated
    - Bullet points (-, •, *, →)
    - Numbered lists (1., 1), I., a., etc.)
    - Questions without question marks
    - Questions with extra whitespace or formatting
    - Questions with Q: or Question: prefixes
    - Mixed formats
    
    Returns a list of cleaned, normalized questions.
    """
    if not raw or not raw.strip():
        return []
    
    # Normalize line endings and remove excessive whitespace
    normalized = re.sub(r'\r\n', '\n', raw.strip())
    normalized = re.sub(r'\r', '\n', normalized)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)  # Max 2 consecutive newlines
    normalized = re.sub(r'[ \t]+', ' ', normalized)  # Normalize spaces
    
    questions = []
    seen = set()  # Deduplicate
    
    # Strategy 1: Split by newlines and process each line
    lines = normalized.split('\n')
    current_question = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines (they separate questions)
        if not line:
            if current_question:
                # Join accumulated lines into one question
                question = ' '.join(current_question).strip()
                question = clean_question(question)
                if question and question not in seen and is_valid_question(question):
                    questions.append(question)
                    seen.add(question.lower().strip())
                current_question = []
            continue
        
        # Remove common prefixes
        line = re.sub(r'^(Q:|Question:|q:|question:)\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove numbered lists
        line = re.sub(r'^[a-zA-Z][\.\)]\s*', '', line)  # Remove lettered lists (a., b., etc.)
        line = re.sub(r'^[-•*→▶▪▫]\s*', '', line)  # Remove bullet points
        line = re.sub(r'^[IVX]+[\.\)]\s*', '', line)  # Remove Roman numerals
        line = re.sub(r'^\([a-z0-9]+\)\s*', '', line, flags=re.IGNORECASE)  # Remove (a), (1), etc.
        
        # Remove trailing colons that might be from formatting
        line = re.sub(r':\s*$', '', line)
        
        line = line.strip()
        
        if not line:
            continue
        
        # Check if this looks like the start of a new question
        # (ends with ?, or is capitalized and short, or has question words)
        is_new_question = (
            line.endswith('?') or
            (line and line[0].isupper() and len(line.split()) <= 15) or
            re.search(r'^(what|who|when|where|why|how|which|can|could|would|should|is|are|do|does|did|will|has|have)', line, re.IGNORECASE)
        )
        
        if is_new_question and current_question:
            # Finish current question and start new one
            question = ' '.join(current_question).strip()
            question = clean_question(question)
            if question and question not in seen and is_valid_question(question):
                questions.append(question)
                seen.add(question.lower().strip())
            current_question = [line]
        else:
            # Continue building current question
            current_question.append(line)
    
    # Handle last question
    if current_question:
        question = ' '.join(current_question).strip()
        question = clean_question(question)
        if question and question not in seen and is_valid_question(question):
            questions.append(question)
            seen.add(question.lower().strip())
    
    # Strategy 2: If we got very few questions, try splitting by double newlines
    if len(questions) <= 1 and '\n\n' in normalized:
        segments = re.split(r'\n{2,}', normalized)
        for segment in segments:
            cleaned = clean_question(segment.strip())
            if cleaned and cleaned not in seen and is_valid_question(cleaned):
                questions.append(cleaned)
                seen.add(cleaned.lower().strip())
    
    # Strategy 3: If still no questions, try splitting by sentence boundaries
    if not questions:
        # Split by periods, question marks, but keep questions together
        sentences = re.split(r'([.!?]+(?:\s+|$))', normalized)
        current_q = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            current_q.append(sentence)
            if sentence.endswith('?') or (sentence.endswith('.') and len(current_q) >= 2):
                question = ' '.join(current_q).strip()
                question = clean_question(question)
                if question and question not in seen and is_valid_question(question):
                    questions.append(question)
                    seen.add(question.lower().strip())
                current_q = []
        if current_q:
            question = ' '.join(current_q).strip()
            question = clean_question(question)
            if question and question not in seen and is_valid_question(question):
                questions.append(question)
    
    # Final fallback: if still no questions, treat as one question
    if not questions:
        cleaned = clean_question(normalized)
        if cleaned and is_valid_question(cleaned):
            questions.append(cleaned)
    
    # Final cleanup: ensure questions end properly
    cleaned_questions = []
    for q in questions:
        q = clean_question(q)
        # Ensure question ends with proper punctuation if it's long enough
        if len(q) > 20 and not q.rstrip().endswith(('.', '!', '?')):
            # If it looks like a question, add ?
            if any(word in q.lower() for word in ['what', 'who', 'when', 'where', 'why', 'how', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did', 'will', 'has', 'have']):
                q = q.rstrip() + '?'
            else:
                q = q.rstrip() + '.'
        cleaned_questions.append(q)
    
    return cleaned_questions


def clean_question(text: str) -> str:
    """Clean and normalize a single question string."""
    if not text:
        return ""
    
    # Remove common markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code blocks
    text = re.sub(r'#{1,6}\s+', '', text)  # Remove headers
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove leading/trailing punctuation that's not part of the question
    text = re.sub(r'^[:\-–—]\s+', '', text)
    text = re.sub(r'\s+[:\-–—]$', '', text)
    
    # Capitalize first letter if needed
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    
    return text


def is_valid_question(text: str) -> bool:
    """Check if text is a valid question."""
    if not text or len(text) < 10:
        return False
    
    # Must have at least 3 words or be a question
    word_count = len(text.split())
    if word_count < 3 and not text.endswith('?'):
        return False
    
    # Reject very short fragments
    if len(text) < 10:
        return False
    
    # Reject lines that are just formatting
    if text.lower() in ['question', 'answer', 'q:', 'a:', 'note:', 'see:']:
        return False
    
    # Reject lines that are mostly punctuation or numbers
    if len(re.sub(r'[^\w\s]', '', text)) < len(text) * 0.5:
        return False
    
    return True


@app.get("/healthz")
async def healthcheck() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "phc-grant-assistant"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest) -> GenerateResponse:
    """Generate answers for grant questions using the PHC QA system."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Parse questions from input
    questions = parse_questions(payload.grantQuestions)
    if not questions:
        raise HTTPException(status_code=400, detail="No valid grant questions found in input.")

    # Get API key from environment
    api_key = get_api_key()

    # Use answer_questions function
    try:
        # Get additional context if provided
        additional_context = payload.grantContext.strip() if payload.grantContext else ""
        
        # Call the QA system
        result = answer_questions(
            questions, 
            api_key=api_key, 
            kb_path=str(ROOT_DIR / "knowledge_base"),
            additional_context=additional_context,
            return_sources=True
        )
        
        # Handle both old format (Dict[str, str]) and new format (Dict with 'answers', 'sources', 'tailoring_explanation', 'fit_score', 'fit_explanation')
        if isinstance(result, dict) and 'answers' in result:
            answers = result['answers']
            sources_map = result.get('sources', {})
            tailoring_explanation = result.get('tailoring_explanation', '')
            fit_score = result.get('fit_score', 0.0)
            fit_explanation = result.get('fit_explanation', '')
        else:
            # Fallback to old format
            answers = result
            sources_map = {}
            tailoring_explanation = ''
            fit_score = 0.0
            fit_explanation = ''
        
        # Debug: Check what we got back
        if not answers:
            raise HTTPException(
                status_code=500, 
                detail="No answers were generated. The QA system returned an empty result."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating answers: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating answers: {str(e)}"
        )
    
    # Convert to expected API response format
    results = []
    
    # Create a mapping of normalized questions to answers for easier lookup
    answer_map = {}
    sources_map_normalized = {}
    for key, value in answers.items():
        # Store by exact key
        answer_map[key] = value
        # Also store by normalized key (trimmed, lowercased) as fallback
        normalized_key = key.strip().lower()
        if normalized_key not in answer_map:
            answer_map[normalized_key] = value
        # Store sources
        if key in sources_map:
            sources_map_normalized[key] = sources_map[key]
            sources_map_normalized[normalized_key] = sources_map[key]
    
    for question in questions:
        # Try exact match first (most reliable)
        answer = answers.get(question)
        
        # If not found, try normalized match
        if not answer:
            answer = answer_map.get(question.strip().lower())
        
        # Get sources for this question
        question_sources = sources_map.get(question, [])
        if not question_sources:
            question_sources = sources_map_normalized.get(question.strip().lower(), [])
        
        # Clean up source paths for display
        cleaned_sources = []
        for source in question_sources:
            # Convert "knowledge_base/quantitative/phc_impact_2024.md" to readable format
            if 'knowledge_base/' in source:
                # Extract relative path
                rel_path = source.split('knowledge_base/')[-1]
                # Split into parts
                parts = rel_path.replace('.md', '').split('/')
                # Format: "Category → File Name"
                if len(parts) == 2:
                    category = parts[0].replace('_', ' ').title()
                    filename = parts[1].replace('_', ' ').replace('phc ', 'PHC ').title()
                    cleaned_sources.append(f"{category} → {filename}")
                else:
                    # Fallback: just format the filename
                    filename = parts[-1].replace('_', ' ').replace('phc ', 'PHC ').title()
                    cleaned_sources.append(filename)
            else:
                cleaned_sources.append(source)
        
        # If still not found, it means the answer_questions function didn't return
        # an answer for this question (shouldn't happen, but handle it gracefully)
        if not answer:
            logger.warning(f"No answer found for question: '{question}'")
            answer = "Error: Could not generate an answer for this question. Please try rephrasing or check if the question is relevant to PHC's work."
        
        # Always add the result
        results.append(AnswerPayload(
            question=question,
            answer=answer,
            sources=cleaned_sources
        ))

    return GenerateResponse(
        results=results,
        tailoring_explanation=tailoring_explanation,
        fit_score=fit_score,
        fit_explanation=fit_explanation
    )
