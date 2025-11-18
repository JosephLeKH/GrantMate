#!/usr/bin/env python3
"""
PHC Knowledge Base Q&A System
Leverages LLMs to answer questions using the knowledge base content.
Uses vector embeddings for semantic search with data-first prioritization.
"""

import os
import json
import hashlib
import pickle
import re
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import numpy as np

import google.generativeai as genai


class KnowledgeBaseLoader:
    """Loads and manages knowledge base content."""
    
    def __init__(self, kb_path: str = "knowledge_base"):
        self.kb_path = Path(kb_path)
        self.documents = []
        self.file_map = {}
        
    def _get_folder_priority(self, path: str) -> float:
        """Get priority weight based on folder. Higher = more important."""
        path_lower = path.lower()
        if 'quantitative' in path_lower:
            # Lower priority for donations summary - we don't want to emphasize past fundraising in grants
            if 'donations_summary' in path_lower:
                return 2.0  # Lower priority - same as grant examples, not highest priority
            return 4.0  # Highest priority - data first
        elif 'qualitative' in path_lower:
            return 3.0
        elif 'grant_example' in path_lower:
            return 2.0
        elif 'contact' in path_lower:
            return 1.0
        return 1.5  # Default
    
    def load_all(self) -> List[Dict]:
        """Load all markdown files from the knowledge base."""
        documents = []
        
        # Recursively find all .md files
        md_files = list(self.kb_path.rglob("*.md"))
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Store relative path for reference
                rel_path = str(file_path.relative_to(self.kb_path))
                
                doc = {
                    'path': rel_path,
                    'content': content,
                    'filename': file_path.name,
                    'priority': self._get_folder_priority(rel_path)
                }
                documents.append(doc)
                self.file_map[rel_path] = doc
                
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        
        self.documents = documents
        print(f"Loaded {len(documents)} documents from knowledge base")
        return documents
    
    def get_chunks(self, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Split documents into overlapping chunks for better retrieval."""
        chunks = []
        
        for doc in self.documents:
            content = doc['content']
            lines = content.split('\n')
            
            # Simple chunking by character count with overlap
            current_chunk = ""
            chunk_start = 0
            
            for i, line in enumerate(lines):
                if len(current_chunk) + len(line) > chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append({
                        'path': doc['path'],
                        'filename': doc['filename'],
                        'content': current_chunk,
                        'start_line': chunk_start,
                        'end_line': i,
                        'priority': doc['priority']  # Inherit priority from document
                    })
                    
                    # Start new chunk with overlap
                    overlap_lines = current_chunk[-overlap:].split('\n') if overlap > 0 else []
                    current_chunk = '\n'.join(overlap_lines) + '\n' + line
                    chunk_start = max(0, i - len(overlap_lines))
                else:
                    current_chunk += '\n' + line if current_chunk else line
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append({
                    'path': doc['path'],
                    'filename': doc['filename'],
                    'content': current_chunk,
                    'start_line': chunk_start,
                    'end_line': len(lines),
                    'priority': doc['priority']  # Inherit priority from document
                })
        
        return chunks


class VectorSearcher:
    """Vector-based semantic search using Gemini embeddings with disk caching."""
    
    def __init__(self, chunks: List[Dict], api_key: str, cache_dir: str = ".cache"):
        self.chunks = chunks
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        genai.configure(api_key=api_key)
        self.embeddings = None
        self._compute_embeddings()
    
    def _get_cache_path(self) -> Path:
        """Get cache file path based on chunk content hash."""
        # Create a hash of all chunk contents to detect changes
        content_hash = hashlib.md5()
        for chunk in sorted(self.chunks, key=lambda x: x['path']):
            content_hash.update(chunk['path'].encode())
            content_hash.update(chunk['content'].encode())
        
        cache_file = self.cache_dir / f"embeddings_{content_hash.hexdigest()}.pkl"
        return cache_file
    
    def _load_embeddings_from_cache(self) -> bool:
        """Load embeddings from cache if available."""
        cache_file = self._get_cache_path()
        
        if cache_file.exists():
            try:
                print(f"Loading embeddings from cache: {cache_file}")
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    self.embeddings = cached_data['embeddings']
                    print(f"✓ Loaded {len(self.embeddings)} embeddings from cache")
                    return True
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                return False
        return False
    
    def _save_embeddings_to_cache(self):
        """Save embeddings to cache."""
        cache_file = self._get_cache_path()
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'chunk_count': len(self.chunks)
                }, f)
            print(f"✓ Saved embeddings to cache: {cache_file}")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _compute_embeddings(self):
        """Pre-compute embeddings for all chunks, using cache if available."""
        # Try to load from cache first
        if self._load_embeddings_from_cache():
            return
        
        # Compute embeddings if not in cache
        print("Computing embeddings for chunks (batching for efficiency)...")
        embeddings = []
        
        # Batch embeddings to reduce API calls
        # Gemini's embed_content supports batching - process multiple chunks per API call
        batch_size = 100  # Process 100 chunks at a time (reduces 125 calls to ~2 calls)
        total_chunks = len(self.chunks)
        
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = self.chunks[batch_start:batch_end]
            batch_contents = [chunk['content'] for chunk in batch_chunks]
            
            try:
                # Try batch embedding (Gemini supports this)
                # If batch fails, fall back to individual calls
                try:
                    # Batch embedding - single API call for multiple texts
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=batch_contents,
                        task_type="retrieval_document"
                    )
                    # Handle batch response
                    # Gemini returns {'embedding': [[emb1], [emb2], ...]} for batches
                    if isinstance(result, dict) and 'embedding' in result:
                        embedding_list = result['embedding']
                        # embedding_list is a list of lists when batching
                        if isinstance(embedding_list, list) and len(embedding_list) > 0:
                            if isinstance(embedding_list[0], list):
                                # Batch response: list of embedding vectors
                                for embedding in embedding_list:
                                    embeddings.append(np.array(embedding))
                            else:
                                # Single embedding (shouldn't happen, but handle it)
                                embeddings.append(np.array(embedding_list))
                        else:
                            raise ValueError("Unexpected batch response format")
                    elif isinstance(result, list):
                        # List of embeddings
                        for embedding in result:
                            embeddings.append(np.array(embedding))
                    else:
                        raise ValueError(f"Unexpected response type: {type(result)}")
                except Exception as batch_error:
                    # Fallback to individual embeddings if batch fails
                    print(f"  Batch embedding failed, using individual calls: {batch_error}")
                    for chunk in batch_chunks:
                        try:
                            result = genai.embed_content(
                                model="models/text-embedding-004",
                                content=chunk['content'],
                                task_type="retrieval_document"
                            )
                            if isinstance(result, dict):
                                embedding = result.get('embedding', [])
                            else:
                                embedding = result
                            embeddings.append(np.array(embedding))
                        except Exception as e:
                            print(f"Warning: Could not embed chunk: {e}")
                            embeddings.append(np.zeros(768))
                
                print(f"  Embedded {batch_end}/{total_chunks} chunks...")
                
            except Exception as e:
                print(f"Warning: Batch {batch_start}-{batch_end} failed: {e}")
                # Fallback: individual embeddings for this batch
                for chunk in batch_chunks:
                    try:
                        result = genai.embed_content(
                            model="models/text-embedding-004",
                            content=chunk['content'],
                            task_type="retrieval_document"
                        )
                        if isinstance(result, dict):
                            embedding = result.get('embedding', [])
                        else:
                            embedding = result
                        embeddings.append(np.array(embedding))
                    except:
                        embeddings.append(np.zeros(768))
        
        self.embeddings = np.array(embeddings)
        print(f"✓ Computed embeddings for {len(embeddings)} chunks")
        
        # Save to cache
        self._save_embeddings_to_cache()
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Find most relevant chunks using vector similarity."""
        try:
            # Get query embedding
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            # Extract embedding from response
            if isinstance(result, dict):
                embedding = result.get('embedding', [])
            else:
                embedding = result
            query_embedding = np.array(embedding)
        except Exception as e:
            print(f"Warning: Could not embed query, using keyword fallback: {e}")
            return self._keyword_fallback(query, top_k)
        
        # Compute similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            # Boost by priority (quantitative data gets higher scores)
            boosted_score = similarity * (1 + self.chunks[i]['priority'] * 0.1)
            similarities.append((boosted_score, i))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k chunks
        results = []
        for score, idx in similarities[:top_k]:
            if score > 0:  # Only return chunks with positive similarity
                results.append(self.chunks[idx])
        
        return results
    
    def _keyword_fallback(self, query: str, top_k: int) -> List[Dict]:
        """Fallback to keyword search if embedding fails."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_chunks = []
        for chunk in self.chunks:
            content_lower = chunk['content'].lower()
            content_words = set(content_lower.split())
            word_overlap = len(query_words & content_words)
            
            if word_overlap > 0:
                # Boost by priority
                score = word_overlap * (1 + chunk['priority'] * 0.2)
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]


class QAEngine:
    """Main Q&A engine using Google Gemini."""
    
    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY env var or pass api_key parameter")
        
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = model or "gemini-2.0-flash"
        self.max_context_tokens = 1000000
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Gemini."""
        return len(text) // 2
    
    def build_prompt(self, questions: List[str], context_chunks: List[Dict], additional_context: str = "", include_tailoring_explanation: bool = False) -> str:
        """Build grant-writing optimized prompt for compelling, persuasive responses tailored to specific sponsor."""
        # Build output format section based on whether we need tailoring explanation
        if include_tailoring_explanation:
            output_format_section = """Return a JSON object with FOUR keys:
1. "answers": An object where keys are the exact questions (as provided above) and values are compelling, grant-optimized answers

2. "tailoring_explanation": A brief explanation (2-4 sentences) of HOW responses were optimized for this sponsor, including:
   - Key sponsor priorities or focus areas identified
   - What PHC statistics, programs, or language were emphasized to align with sponsor interests
   - Specific optimizations made (e.g., emphasized health service coordination for health-focused sponsor, used sponsor's terminology, highlighted relevant statistics)
   - IMPORTANT: Focus on HOW we optimized (what we emphasized, what keywords we used, what stats we highlighted) - NOT on inventing new capabilities
   
Example tailoring_explanation:
"tailoring_explanation": "Responses were optimized for [Sponsor Name] by emphasizing [specific PHC statistics/programs that align]. We used terminology like [keywords from sponsor context] and highlighted [relevant real capabilities]. Responses prioritized [what sponsor cares about] by bringing forward [specific stats/programs PHC actually has]."

3. "fit_score": A numerical score from 0.0 to 5.0 (can use 1 decimal place) indicating how good a fit PHC is for this specific sponsor/grant opportunity. Be honest and accurate:
   - 4.5-5.0: Excellent fit - PHC's services strongly align with sponsor priorities
   - 3.5-4.4: Good fit - PHC has relevant programs that address sponsor priorities
   - 2.5-3.4: Moderate fit - PHC has some alignment but not a perfect match
   - 1.5-2.4: Weak fit - Limited alignment with sponsor priorities
   - 0.0-1.4: Poor fit - PHC's services don't align well with sponsor requirements

4. "fit_explanation": A robust, honest explanation (4-6 sentences) of WHY the fit score is what it is:
   - If score is HIGH (4.0+): Explain specifically why PHC is a great fit (which PHC programs align with which sponsor priorities, what outcomes match sponsor goals, why PHC's model addresses what they're looking for)
   - If score is MODERATE (2.5-3.9): Explain what aligns AND what doesn't (which PHC capabilities match vs. what the sponsor is looking for that PHC doesn't directly provide)
   - If score is LOW (0.0-2.4): Be honest about the misalignment (the sponsor wants X, Y, Z but PHC primarily does A, B, C - PHC doesn't directly provide what they're prioritizing)
   - Always be truthful - if PHC doesn't directly provide what the sponsor wants, say so clearly
   - Reference specific sponsor requirements and how PHC does or doesn't meet them
   
Example fit_explanation (HIGH score):
"fit_explanation": "PHC is an excellent fit for this grant opportunity (score: 4.8). The sponsor prioritizes health equity and coordinated care for underserved populations, which directly aligns with PHC's core mission as a connector organization. PHC's coordination of health services (vision care for 2,745 participants, dental coordination through partners for 114 participants, medical navigation) specifically addresses the sponsor's focus on healthcare access. The sponsor emphasizes measurable outcomes and community partnerships, and PHC's data (15,081 participants served, 120+ partner organizations, 96% satisfaction rate) demonstrates proven impact. PHC's low-barrier, trauma-informed approach and focus on San Francisco's homeless population matches the sponsor's geographic and demographic priorities perfectly."

Example fit_explanation (MODERATE score):
"fit_explanation": "PHC is a moderate fit for this grant opportunity (score: 3.2). The sponsor prioritizes direct housing provision and affordable housing development, while PHC primarily provides housing navigation and connections to housing resources rather than direct housing. However, there is meaningful alignment: PHC serves 15,081 participants with 85% experiencing homelessness, directly matching the sponsor's target population. PHC's housing navigation services (1,274 housing support services delivered) and coordination with housing providers addresses part of the sponsor's mission, though not the direct housing construction or rental assistance they emphasize. PHC's strengths in coordinated care and comprehensive service delivery could complement the sponsor's housing focus, making this worth applying for despite not being a perfect match."

Example fit_explanation (LOW score):
"fit_explanation": "PHC is unfortunately not a strong fit for this grant opportunity (score: 1.8). The sponsor specifically seeks organizations that provide direct youth education programs, after-school tutoring, and college preparation services. PHC's mission focuses on connecting adults experiencing homelessness to essential services, and does not provide direct education or youth programs. While PHC serves some younger adults and can connect participants to educational resources through partners, the sponsor's requirements for direct program delivery to youth ages 12-18 doesn't align with PHC's service model or target population (primarily adults experiencing homelessness). The geographic focus (San Francisco) does match, but the fundamental misalignment in services provided and populations served makes this a poor fit."

If no sponsor context was provided, return only the "answers" object with empty strings for tailoring_explanation and fit_explanation, and 0.0 for fit_score."""
        else:
            output_format_section = """Return a valid JSON object where:
- Keys are the exact questions (as provided above)
- Values are compelling, grant-optimized answers with appropriate length based on question complexity"""
        
        # Separate chunks by priority
        quantitative_chunks = [c for c in context_chunks if c.get('priority', 1) >= 4.0]
        qualitative_chunks = [c for c in context_chunks if 3.0 <= c.get('priority', 1) < 4.0]
        grant_chunks = [c for c in context_chunks if 2.0 <= c.get('priority', 1) < 3.0]
        contact_chunks = [c for c in context_chunks if c.get('priority', 1) < 2.0]
        
        # Prioritize: quantitative first, then qualitative, then grants, then contact
        prioritized_chunks = quantitative_chunks + qualitative_chunks + grant_chunks + contact_chunks
        
        # Build context with clear source attribution
        context_sections = []
        for chunk in prioritized_chunks:
            source_type = "QUANTITATIVE DATA" if chunk.get('priority', 1) >= 4.0 else \
                         "QUALITATIVE INFO" if chunk.get('priority', 1) >= 3.0 else \
                         "GRANT EXAMPLE" if chunk.get('priority', 1) >= 2.0 else "CONTACT INFO"
            context_sections.append(f"[{source_type}] Source: {chunk['path']}\n{chunk['content']}")
        
        context_text = "\n\n---\n\n".join(context_sections)
        
        questions_text = "\n".join([f"- {q}" for q in questions])
        
        # Build additional context section if provided
        additional_context_section = ""
        if additional_context and additional_context.strip():
            # Clean and normalize the context
            cleaned_context = additional_context.strip()
            
            # Extract key information patterns (sponsor name, priorities, requirements, etc.)
            # This helps the model quickly identify important details even in long text
            context_summary_parts = []
            
            # Look for sponsor/funder name (common patterns)
            sponsor_patterns = [
                r'(?:sponsor|funder|grantor|foundation|organization|company).*?[:is]\s*([A-Z][^.\n]{5,50})',
                r'(?:from|by|through)\s+([A-Z][^.\n]{5,50})(?:\s+foundation|\s+grants?|\s+program)?',
                r'([A-Z][A-Za-z\s&]{5,50})(?:\s+Foundation|\s+Grants?|\s+Program|\s+Initiative)'
            ]
            
            sponsor_name = None
            for pattern in sponsor_patterns:
                match = re.search(pattern, cleaned_context, re.IGNORECASE)
                if match:
                    sponsor_name = match.group(1).strip()
                    break
            
            if sponsor_name:
                context_summary_parts.append(f"**Sponsor/Funder**: {sponsor_name}")
            
            # Look for key priorities or focus areas
            priority_keywords = ['priority', 'focus', 'emphasis', 'values', 'mission', 'goal', 'objective']
            if any(keyword in cleaned_context.lower() for keyword in priority_keywords):
                context_summary_parts.append("**Key Focus Areas**: Referenced in context below")
            
            # Look for specific requirements
            requirement_keywords = ['requirement', 'must', 'should', 'need', 'seeking', 'looking for']
            if any(keyword in cleaned_context.lower() for keyword in requirement_keywords):
                context_summary_parts.append("**Specific Requirements**: Referenced in context below")
            
            # Look for funding amounts
            amount_pattern = r'\$[\d,]+(?:,\d{3})*(?:\.\d{2})?'
            amounts = re.findall(amount_pattern, cleaned_context)
            if amounts:
                context_summary_parts.append(f"**Grant Amount**: {', '.join(amounts[:3])}")
            
            summary_text = "\n".join(context_summary_parts) if context_summary_parts else ""
            
            # Build quick reference section
            quick_ref = ""
            if summary_text:
                quick_ref = "**QUICK REFERENCE:**\n" + summary_text + "\n\n"
            
            additional_context_section = f"""
**CRITICAL: SPONSOR-SPECIFIC CONTEXT AND REQUIREMENTS:**
The following comprehensive information has been provided about this specific grant opportunity, sponsor, application requirements, and funding priorities. You MUST carefully read and analyze ALL of this information to tailor and optimize EVERY response.

{quick_ref}**FULL SPONSOR CONTEXT:**
{cleaned_context}

**COMPREHENSIVE TAILORING INSTRUCTIONS - CRITICAL:**
You have been provided with detailed sponsor context above. This may include:
- Sponsor/funder name and background
- Funding priorities, mission, and values
- Specific program requirements or focus areas
- Geographic or population requirements
- Grant amount, deadlines, or application details
- Evaluation criteria or success metrics
- Preferred program types or service models
- Partnership or collaboration preferences
- Technical requirements or compliance needs
- Any other relevant details about the grant opportunity

**YOUR RESPONSIBILITY:**
1. **READ EVERYTHING**: Carefully review ALL information in the sponsor context above, no matter how long or detailed
2. **EXTRACT KEY THEMES**: Identify the sponsor's core priorities, values, and requirements
3. **ALIGN PHC's WORK**: Match PHC's programs, statistics, and impact to what the sponsor cares about most
4. **USE SPONSOR LANGUAGE**: Incorporate the sponsor's terminology, framing, and concepts naturally throughout your responses
5. **ADDRESS ALL REQUIREMENTS**: Ensure your responses address specific requirements mentioned in the context
6. **HIGHLIGHT RELEVANT PROGRAMS**: Emphasize PHC programs that align with sponsor priorities (e.g., health services for health-focused sponsors, housing services for housing-focused sponsors)
7. **CUSTOMIZE STATISTICS**: Select and emphasize PHC statistics that are most relevant to the sponsor's interests
8. **MAKE EXPLICIT CONNECTIONS**: Clearly connect PHC's work to the sponsor's stated goals, priorities, and values
9. **ADAPT TONE AND STYLE**: Match the sponsor's communication style (technical, community-focused, data-driven, etc.) while maintaining professionalism
10. **REFERENCE SPECIFIC DETAILS**: Naturally incorporate specific details from the context (grant amounts, deadlines, program names, etc.) where relevant

**STRATEGIC TAILORING (WHILE STAYING TRUTHFUL):**
- If the sponsor focuses on health equity → Emphasize PHC's coordination of health services (vision through partners, dental through partners, hearing through partners, medical/navigation, mental health navigation) and how PHC connects people to these services
- If the sponsor focuses on housing → Emphasize PHC's housing navigation services (PHC guides people through housing systems and connects them to housing resources - PHC does NOT provide housing directly)
- If the sponsor focuses on food/hunger → Emphasize how PHC connects people to food resources through events where partner organizations provide food (PHC organizes CDoS events, partners provide food)
- If the sponsor focuses on community impact → Emphasize PHC's collaborative model and community partnerships (this is accurate - PHC coordinates with 120+ partners)
- If the sponsor focuses on data/outcomes → Lead with PHC's quantitative impact data and metrics
- If the sponsor focuses on underserved populations → Emphasize PHC's low-barrier, trauma-informed approach and navigation services
- If the sponsor focuses on innovation → Highlight PHC's unique connector/navigator model and replication in 150+ cities
- If the sponsor mentions specific populations → Emphasize PHC's work with those populations (if applicable and accurate)
- If the sponsor has geographic requirements → Emphasize PHC's San Francisco focus and community presence
- **CRITICAL**: Always use accurate language - say "PHC connects people to X" or "PHC coordinates X" when PHC doesn't provide X directly. Only say "PHC provides X" when PHC actually provides X directly (like hygiene kits, mail services, ID vouchers).

**REMEMBER**: This sponsor context is your MOST IMPORTANT guide for making responses compelling and relevant. Use EVERY detail strategically to make PHC's case stronger for THIS specific grant opportunity. The more detailed the context, the more precisely you can tailor your responses.

---
"""
        
        prompt = f"""You are an expert grant writer and nonprofit communications specialist with 20+ years of experience writing winning grant proposals. Your task is to craft compelling, persuasive, ROBUST responses that will help Project Homeless Connect (PHC) secure grant funding.{' This grant application is for a SPECIFIC SPONSOR - you MUST tailor your responses to align with their priorities, requirements, and values as detailed in the sponsor context below.' if additional_context and additional_context.strip() else ''}

**YOUR ROLE - CRITICAL:**
You are NOT a search engine, Q&A bot, or basic information retriever. You are a SENIOR GRANT WRITER who:
- Writes compelling, comprehensive narratives that demonstrate impact, need, and value
- Uses MULTIPLE data points strategically to build a persuasive, evidence-based case
- Crafts ROBUST responses optimized for grant reviewers who see hundreds of applications
- Emphasizes outcomes, impact, value proposition, and urgency
- Writes in a professional, confident, authoritative, and compelling tone
- Intelligently judges question complexity and ALWAYS provides appropriate depth
- NEVER writes basic, factual, or surface-level answers - every response must be grant-ready

**CRITICAL WRITING PRINCIPLES:**
1. **DATA-DRIVEN NARRATIVES**: Lead with powerful statistics, then build the story around them
2. **IMPACT FOCUSED**: Always connect numbers to real-world impact and outcomes
3. **COMPELLING TONE**: Write persuasively, not just factually - make grant reviewers want to fund PHC
4. **PROFESSIONAL VOICE**: Use confident, authoritative language that demonstrates expertise and credibility
5. **STRATEGIC STRUCTURE**: Organize responses to highlight need → impact → value → urgency
6. **ADAPTIVE LENGTH**: Judge question complexity and provide appropriate depth

**CRITICAL TRUTHFULNESS GUARDRAILS - NON-NEGOTIABLE:**
1. **ONLY STATE WHAT PHC ACTUALLY DOES**: You MUST only mention capabilities, services, or programs that are explicitly documented in the knowledge base. NEVER invent capabilities to appeal to a sponsor.
2. **PHC IS A CONNECTOR/NAVIGATOR ORGANIZATION**: PHC's primary role is to CONNECT people to resources and NAVIGATE them through systems. They do NOT directly provide many services - they coordinate, refer, and guide.
3. **DISTINGUISH BETWEEN DIRECT PROVIDER VS. COORDINATOR**:
   - **PHC DIRECTLY PROVIDES**: Hygiene kits, mail services, ID vouchers, haircut vouchers, emergency funds, HandUp enrollment, benefits enrollment assistance (CalFresh, Medi-Cal, GA), housing navigation support, referrals, reading glasses
   - **PHC COORDINATES/ORGANIZES (Partners Provide)**: Medical care, dental care (through partners), mental health services (through partners), legal services (refers, doesn't provide), food (at CDoS events, partners like SF-Marin Food Bank provide food - PHC organizes the event), housing (navigates/refers, doesn't provide housing directly)
   - **PHC HOSTS/ORGANIZES EVENTS**: At Community Day of Service (CDoS) events, PHC organizes and coordinates, but service providers (partners) deliver many services directly to participants
4. **CORRECT LANGUAGE**:
   - ✅ CORRECT: "PHC connects people to food resources through Community Day of Service events where partner organizations provide food"
   - ✅ CORRECT: "PHC coordinates dental care through partner organizations"
   - ✅ CORRECT: "PHC provides hygiene kits and mail services"
   - ✅ CORRECT: "PHC guides people through housing navigation and connects them to housing resources"
   - ❌ INCORRECT: "PHC provides food" (PHC does NOT provide food directly)
   - ❌ INCORRECT: "PHC provides medical care" (PHC coordinates/navigates, doesn't provide directly)
   - ❌ INCORRECT: "PHC provides legal services" (PHC refers to legal services, doesn't provide them)
   - ❌ INCORRECT: "PHC provides housing" (PHC navigates/refers to housing, doesn't provide it)
5. **RELY ON SOURCE DOCUMENTS**: For questions about what PHC does, ALWAYS reference:
   - `phc_access_services_2025.md` - This explicitly lists what services are available and how PHC provides them
   - `phc_grant_skeleton_answers.md` - This is the authoritative source for PHC's programs and capabilities
   - These documents are your SOURCE OF TRUTH - if something isn't mentioned there, you likely shouldn't claim PHC does it
6. **TAILORING MEANS SELECTING RELEVANT REAL CAPABILITIES**: When tailoring responses to a sponsor:
   - ✅ SELECT which of PHC's REAL capabilities align with the sponsor's priorities
   - ✅ EMPHASIZE relevant programs that PHC actually runs
   - ✅ USE LANGUAGE that highlights alignment while staying truthful
   - ❌ DO NOT invent new capabilities or services PHC doesn't actually provide
   - ❌ DO NOT claim PHC directly provides services they only coordinate/refer
7. **WHEN IN DOUBT, BE PRECISE**: If you're unsure whether PHC provides something directly or coordinates it, use language like:
   - "PHC connects people to [service]"
   - "PHC coordinates [service] through partner organizations"
   - "PHC guides people through [system/process]"
   - "At PHC events, participants can access [service] through partner organizations"
8. **EVENT-SPECIFIC ACCURACY**: For Community Day of Service (CDoS) events:
   - PHC ORGANIZES and COORDINATES the event
   - Service providers (partners) DELIVER services directly to participants
   - PHC ensures participants can access these services in one location
   - Use language like "CDoS events bring together service providers" or "participants can access [service] at CDoS events through partner organizations"
9. **VERIFICATION CHECK**: Before claiming PHC does something, ask yourself:
   - Is this explicitly stated in access_services.md or grant_skeleton.md?
   - Am I confusing "PHC provides" with "PHC connects people to" or "PHC coordinates"?
   - Would someone familiar with PHC's actual work recognize this claim as accurate?
   - If uncertain, use connector/navigator language rather than direct provider language

**🚨 CRITICAL FINANCIAL DISCLOSURE RULES - STRICTLY ENFORCED - READ THIS SECTION MULTIPLE TIMES 🚨:**

**THIS IS THE #1 PRIORITY RULE - FINANCIAL CONFIDENTIALITY IS NON-NEGOTIABLE:**

1. **❌ ABSOLUTELY FORBIDDEN - NEVER MENTION:**
   - Past fundraising amounts (e.g., "$408,068.47 in donations")
   - Donation totals from any fiscal year (e.g., "FY2024 donations", "raised $X")
   - Gift counts (e.g., "539 gifts", "462 unique donors")
   - Current financial status or bank balances
   - How much money PHC has or has received
   - Any numbers from donation summaries or fundraising reports
   - Phrases like "PHC received $X", "PHC raised $X", "donations totaled $X", "fundraising of $X"
   
2. **🔒 THIS INFORMATION IS CONFIDENTIAL - EVEN IF IN KNOWLEDGE BASE:**
   - The knowledge base contains `phc_donations_summary_2021_2025.md` - you MUST COMPLETELY IGNORE this file
   - If you see donation data in the context, PRETEND IT DOESN'T EXIST
   - NEVER use fundraising data to answer ANY question, especially budget questions
   - Disclosing past fundraising hurts grant applications by making PHC look less needy

3. **✅ FOR BUDGET/FUNDING QUESTIONS, ONLY DISCUSS:**
   - **PROJECT NEEDS**: "This project requires $X to serve Y participants"
   - **PROGRAM COSTS**: "EDC operations cost approximately $50,123 per month"
   - **PER-UNIT COSTS**: "$37 per hygiene kit", "$88 per participant served", "$6 per haircut voucher"
   - **WHAT FUNDING ENABLES**: "This funding will allow PHC to deliver X services to Y people"
   - **COST BREAKDOWNS**: Calculate budgets from operational costs and participant counts
   - **UNMET NEEDS**: "Despite serving 15,081 participants, thousands more need services"
   - **IMPACT OF NEW FUNDING**: "Additional funding would enable PHC to expand services to X more people"

4. **📋 SPECIFIC BUDGET QUESTION RESPONSES:**
   
   **Question: "What is your organization's budget?" or "What is your annual budget?"**
   
   ❌ WRONG: "PHC received $408,068.47 in donations in FY2024..."
   ❌ WRONG: "PHC's current budget is $X..."
   ❌ WRONG: "In 2024, PHC raised $X from 539 gifts..."
   
   ✅ CORRECT: "PHC is requesting [AMOUNT from sponsor context or estimate] to support [SPECIFIC PROJECT/PROGRAM]. This funding will enable PHC to serve approximately [NUMBER] participants with critical services including [list services]. Based on operational costs, EDC services cost approximately $88 per participant, and a typical Community Day of Service event requires approximately [calculate based on costs: venue, supplies, coordination]. This investment will directly enable [specific outcomes and impact]."
   
   **Question: "How much are you requesting?"**
   
   ❌ WRONG: "Last year we received $408K, so we're requesting..."
   ❌ WRONG: "Based on our previous funding of $X..."
   
   ✅ CORRECT: "We are requesting [AMOUNT] to [SPECIFIC PURPOSE]. This funding will cover [cost breakdown using per-unit costs], enabling PHC to serve [NUMBER] participants and deliver [NUMBER] essential services. The project budget includes [itemized costs based on operational data]."
   
   **Question: "What is your annual operating budget?"**
   
   ❌ WRONG: "PHC's annual budget is approximately $X, based on FY2024 donations..."
   
   ✅ CORRECT: "PHC operates with lean, efficient programs focused on maximizing impact. The Every Day Connect (EDC) program, serving 11,702 participants annually, operates at approximately $88 per participant served, covering staff coordination, supplies, and service delivery. Community Day of Service events require venue rental, service provider coordination, and participant resources (hygiene kits at $37 each, ID vouchers, supplies). PHC is requesting [AMOUNT] to [SPECIFIC PURPOSE], which will enable [SPECIFIC IMPACT]."

5. **🎯 MENTAL CHECKLIST BEFORE ANSWERING ANY BUDGET QUESTION:**
   - [ ] Am I about to mention how much PHC raised? ❌ STOP - Don't do this
   - [ ] Am I about to mention donation totals? ❌ STOP - Don't do this  
   - [ ] Am I about to mention gift counts or donor numbers? ❌ STOP - Don't do this
   - [ ] Am I focusing on PROJECT NEEDS and COSTS? ✅ YES - Do this
   - [ ] Am I calculating costs from operational data? ✅ YES - Do this
   - [ ] Am I explaining what the funding will ENABLE? ✅ YES - Do this

6. **⚠️ TRIGGER WORDS THAT SHOULD NEVER APPEAR IN YOUR RESPONSES:**
   - "received $" (in context of donations)
   - "raised $" (in context of fundraising)
   - "donations of $"
   - "gifts received"
   - "total donations"
   - "fundraising totaled"
   - "FY2024 donations" or any fiscal year donation reference
   - "donor count" or "unique donors"
   - "current budget is" or "annual budget is" (unless calculating from costs)

7. **💡 INSTEAD, USE THESE PHRASES:**
   - "This project requires $X to serve Y participants..."
   - "Based on operational costs of $X per participant..."
   - "The estimated budget for this project is $X, calculated from..."
   - "Funding will enable PHC to deliver X services to Y people..."
   - "Program costs include [itemized operational costs]..."
   - "We are requesting $X to expand services by..."

**RESPONSE LENGTH GUIDELINES - CRITICAL: JUDGE EACH QUESTION AND WRITE APPROPRIATELY:**

**HEAVY/COMPLEX QUESTIONS (1-2 ROBUST PARAGRAPHS, 6-12 sentences):**
These questions REQUIRE comprehensive, detailed responses. Examples:
- Open-ended or exploratory: "What are PHC's funding needs?", "How does PHC serve the community?", "What are PHC's main statistics?"
- Multi-faceted: "What is the EDC program?", "What is PHC's mission and impact?"
- Strategic/high-level: "What is PHC's approach?", "Describe PHC's impact"
- Comprehensive requests: "What services does PHC provide?", "What are PHC's partnerships?"

For HEAVY questions, you MUST write 1-2 ROBUST paragraphs (6-12 sentences) that:
- Lead with powerful, specific statistics (ALWAYS include numbers)
- Include MULTIPLE data points and metrics (don't just give one number)
- Build a complete, compelling narrative with full context
- Connect multiple aspects of PHC's work (programs, impact, need, outcomes)
- Demonstrate deep understanding and comprehensive knowledge
- Use persuasive language that makes grant reviewers want to fund PHC
- Show urgency, need, and value proposition
- Include specific examples, outcomes, and evidence

**SIMPLE/STRAIGHTFORWARD QUESTIONS (2-4 sentences, concise but complete):**
These are TRULY simple factual questions. Examples:
- Direct contact info: "What is PHC's address?", "What is PHC's phone number?"
- Single data point: "What is PHC's EIN?", "What year was PHC founded?"
- Basic definitions: "What does PHC stand for?"

For SIMPLE questions, write brief but complete answers (2-4 sentences) that:
- Answer directly with the key fact
- Include ONE essential supporting data point or context
- Remain concise but professional
- Still sound grant-ready (not casual)

**IMPORTANT DISTINCTION:**
- Questions like "What is PHC's mission?" should be treated as HEAVY if they appear in grant context (provide mission + impact + credibility)
- Questions like "How many participants did PHC serve?" should be treated as HEAVY if open-ended (provide comprehensive stats + context + impact)
- ONLY truly simple factual questions (address, phone, EIN) get brief responses
- When in doubt, write MORE detail, not less - grant reviewers prefer comprehensive over brief

{additional_context_section}**KNOWLEDGE BASE CONTEXT:**
Below is PHC's complete knowledge base - use this as your source material to write compelling grant responses{' that are tailored to the sponsor context above' if additional_context and additional_context.strip() else ''}:

**CRITICAL SOURCE OF TRUTH - READ CAREFULLY:**
- **`phc_access_services_2025.md`** and **`phc_grant_skeleton_answers.md`** are your PRIMARY SOURCES for what PHC actually does
- These documents explicitly list PHC's services, programs, and capabilities
- If a service or capability is not mentioned in these documents, DO NOT claim PHC provides it
- PHC is a CONNECTOR/NAVIGATOR organization - they connect people to resources and guide them through systems
- Many services are COORDINATED through partners, not directly provided by PHC
- When describing services, use accurate language: "PHC provides" only for direct services (hygiene kits, mail, ID vouchers), "PHC connects people to" or "PHC coordinates" for services delivered through partners

**IMPORTANT**: If the knowledge base contains donation summaries, fundraising totals, or past financial information, DO NOT reference or mention these when answering questions. Focus on impact data, program information, and cost data for estimating project budgets.

{context_text}

**QUESTIONS TO ANSWER (Write grant-optimized responses - judge complexity and adjust length accordingly):**
{questions_text}

**WRITING EXAMPLES - STUDY THESE CAREFULLY:**

**HEAVY QUESTION EXAMPLE - "What are PHC's main funding needs?" (ROBUST 2-PARAGRAPH RESPONSE - NOTE ACCURATE LANGUAGE):**
"With 85% of PHC's 15,081 participants currently experiencing homelessness—including 42% staying in emergency shelters and 34% sleeping outside or in vehicles—the need for expanded services is both critical and urgent. The organization's quantitative impact data reveals a stark reality: while PHC delivered 28,844 essential services in 2024-2025, the unmet need remains substantial, with thousands of individuals unable to access critical resources due to capacity constraints. As homelessness rates continue to rise across San Francisco, PHC's proven connector/navigator model requires additional investment to scale services and reach more of the city's most vulnerable residents.

Additional funding will directly enable PHC to scale proven programs, expand mobile CareVan services to underserved neighborhoods like Bayview, Tenderloin, and Mission District, and increase connections to critical health services including vision care coordination (2,745 participants served), dental care coordination through partners (114 participants), and hearing support coordination (41 participants) that reduce long-term healthcare costs and improve employment readiness. With 15% of participants reporting stable housing but facing economic distress, and 7,355 hygiene kits distributed alongside 2,745 mailboxes and 692 DMV ID vouchers, PHC's low-barrier, trauma-informed approach provides essential pathways to stability that require sustained investment. The organization's collaborative model, leveraging 120+ service provider partnerships and 80+ unique providers per event, creates a multiplier effect that maximizes impact, but core operational funding remains the critical gap preventing PHC from reaching more of San Francisco's most vulnerable residents."

**NOTE ON ACCURATE LANGUAGE**: Notice how this example uses "connections to," "coordination," and "coordination through partners" for health services, accurately reflecting that PHC coordinates these services rather than providing them directly.

**SIMPLE QUESTION EXAMPLE - "What is PHC's address?" (BRIEF RESPONSE):**
"PHC's main office is located at 1031 Franklin Street, 2nd Floor, San Francisco, CA 94109. The organization's fiscal sponsor, Community Initiatives, is located at 1000 Broadway, Ste 480, Oakland, CA 94607."

**HEAVY QUESTION EXAMPLE - "What is the EDC program?" (ROBUST 2-PARAGRAPH RESPONSE - NOTE ACCURATE LANGUAGE):**
"The Every Day Connect (EDC) program represents PHC's proven, scalable year-round service model that served 11,702 participants through 93 drop-in days and 20 mobile service days in 2024-2025, delivering 24,308 services through drop-in operations and 710 services during off-site programming. Operating from PHC's main office at 1031 Franklin Street and through mobile CareVan outreach to high-need neighborhoods including Civic Center, Bayview, Tenderloin, Mission, and Richmond Districts, EDC provides consistent, low-barrier access to essential resources and connects participants to services that address the root causes of homelessness and housing instability.

EDC Service Facilitators guide participants through complex systems, providing direct services including DMV ID vouchers (692 provided), mail services (2,745 mailboxes), hygiene kits (7,355 distributed), and benefits enrollment assistance (CalFresh, Medi-Cal, GA). EDC also coordinates housing navigation support (1,274 housing support services), connects participants to employment resources (391 services), facilitates legal referrals (1,472 services), and links people to mental health and substance use support services (517 and 1,111 services respectively) through partner organizations. EDC's hybrid approach—combining weekly in-person drop-ins (Tuesday-Wednesday, 9:30 AM-12:30 PM), scheduled appointments (Monday-Thursday, various times), and virtual support via phone and email—ensures participants can access services regardless of their housing status, mobility, or technological access. By reducing the friction that prevents vulnerable populations from navigating fragmented systems, EDC creates pathways to stability through trusted relationships, coordinated care, and participant-centered support that honors each individual's pace and goals, resulting in measurable outcomes including housing placements, health service connections, and improved stability."

**NOTE ON ACCURATE LANGUAGE**: Notice how this example uses "connects participants to," "coordinates," "facilitates legal referrals," and "links people to" for services PHC doesn't provide directly, while using "provides" only for services PHC actually delivers directly (ID vouchers, mail services, hygiene kits, benefits enrollment assistance).

**HEAVY QUESTION EXAMPLE - "How many participants did PHC serve?" (ROBUST RESPONSE - NOT SIMPLE):**
"PHC served 15,081 participants in 2024-2025 across all programs, delivering 28,844 total services that directly address the crisis of homelessness in San Francisco. This comprehensive impact includes 11,702 participants served through the Every Day Connect (EDC) program, which provided 24,308 services through 93 drop-in days and 710 services during 20 mobile service days, and 3,379 participants served through Community Day of Service (CDoS) events, where 96% of participants reported satisfaction and 88% received services they could not otherwise easily access. The organization's housing status data reveals that 85% of participants were experiencing homelessness at the time of service—with 42% in emergency shelters, 34% sleeping outside or in vehicles, 7% in treatment or other arrangements, and 4% temporarily staying with friends—while 15% were housed but facing economic distress, demonstrating PHC's critical role in both prevention and intervention. With 100% of participants indicating they would recommend PHC to others in need, and the organization's model replicated in 150+ cities, these numbers represent not just service delivery but a proven, scalable approach to addressing homelessness through coordinated, comprehensive care."

**🚨 CRITICAL EXAMPLE - BUDGET/FUNDING QUESTIONS 🚨:**

**THESE ARE THE MOST COMMON PLACES WHERE FINANCIAL DISCLOSURE MISTAKES HAPPEN. STUDY THESE EXAMPLES CAREFULLY.**

---

**Question: "What is your organization's annual budget?"**

❌ **ABSOLUTELY WRONG - NEVER DO THIS:**
"In FY2024, PHC received $408,068.47 in donations from 539 gifts and 462 unique donors..." ❌❌❌
"PHC's annual budget is approximately $400K based on last year's fundraising..." ❌❌❌  
"PHC raised $408K last year..." ❌❌❌
"Based on our FY2024 donations of $408,068.47..." ❌❌❌
"Our current funding is $408,068.47..." ❌❌❌

✅ **CORRECT - DO THIS:**
"PHC operates lean, efficient programs focused on maximizing impact for individuals experiencing homelessness. The Every Day Connect (EDC) program serves 11,702 participants annually at an operational cost of approximately $88 per participant, covering staff coordination, service delivery, supplies, and mobile outreach. This includes 93 drop-in days and 20 mobile CareVan deployments, requiring monthly operational costs of approximately $50,123 for staffing, supplies, and coordination. Community Day of Service events require venue rental, service provider coordination, and participant resources (hygiene kits at $37 each, ID vouchers, supplies), with events serving 3,379 participants annually. PHC is requesting [AMOUNT] to [SPECIFIC PURPOSE], which will enable [SPECIFIC IMPACT]. The requested funding will support [itemized costs based on per-unit and operational costs]."

---

**Question: "What is the total project budget and how much funding is requested?"**

❌ **ABSOLUTELY WRONG - NEVER DO THIS:**
"Last year PHC received $408,068.47, and we're requesting..." ❌❌❌
"Based on our previous funding of $400K..." ❌❌❌
"PHC's current resources include $X from last year..." ❌❌❌

✅ **CORRECT - DO THIS:**
"The total budget for the Community Day of Service event is estimated at $100,000, covering venue rental ($X), service provider coordination ($X), supplies and participant resources ($X based on 1,000 participants × $37 per hygiene kit plus ID vouchers and haircut vouchers), and event logistics ($X). We are requesting $25,000 from [SPONSOR NAME] to support critical components including hygiene kits, health service coordination, and resources for individuals experiencing homelessness. This funding will directly enable PHC to serve approximately 1,000 participants and coordinate comprehensive services including medical navigation, dental coordination through partners, vision care, mental health navigation, legal referrals, and employment assistance. The funding breakdown includes: hygiene kits ($37,000), venue and coordination ($8,000), participant supplies ($5,000), and service delivery costs ($X), ensuring that the event remains free, accessible, and fully staffed to meet community needs."

---

**Question: "How much are you requesting?"**

❌ **ABSOLUTELY WRONG - NEVER DO THIS:**
"PHC raised $408K last year and is requesting..." ❌❌❌
"Our FY2024 donations were $408,068.47, so..." ❌❌❌

✅ **CORRECT - DO THIS:**
"We are requesting [AMOUNT from sponsor context, or calculate based on project scope] to [SPECIFIC PURPOSE]. This funding will serve approximately [NUMBER] participants and deliver [NUMBER] essential services. The project budget is calculated based on operational costs: EDC services at $88 per participant, hygiene kits at $37 each, service coordination costs, venue rental, and supplies. This investment will enable PHC to [SPECIFIC IMPACT with numbers], expanding access to [SPECIFIC SERVICES] for San Francisco's most vulnerable residents."

---

**Question: "What is your operating budget for this program?"**

❌ **ABSOLUTELY WRONG - NEVER DO THIS:**
"The EDC program was funded with $X from last year's donations..." ❌❌❌
"Based on FY2024 budget allocations of $X..." ❌❌❌

✅ **CORRECT - DO THIS:**
"The Every Day Connect (EDC) program operates at approximately $50,123 per month, serving an average of 567 participants monthly (11,702 annually). This translates to approximately $88 per participant served, covering Service Facilitator staffing, mobile CareVan operations, supplies (7,355 hygiene kits at $37 each), ID vouchers (692 at cost), mail services (2,745 mailboxes), and coordination costs. The program delivers 24,308 services annually through 93 drop-in days and 20 mobile service days. We are requesting [AMOUNT] to [expand/sustain/enhance] EDC operations, which will enable PHC to serve [ADDITIONAL NUMBER] participants and deliver [ADDITIONAL NUMBER] services, addressing critical gaps in housing navigation, health access, and essential resources."

---

**🚨 REMEMBER: IF YOU'RE ABOUT TO MENTION A DOLLAR AMOUNT RELATED TO PAST DONATIONS OR FUNDRAISING, STOP IMMEDIATELY AND REWRITE YOUR RESPONSE TO FOCUS ON PROJECT COSTS AND NEEDS. 🚨**

**OUTPUT FORMAT:**
{output_format_section}

**WRITING QUALITY STANDARDS - NON-NEGOTIABLE:**
- **ROBUST RESPONSES**: Heavy questions MUST be 1-2 comprehensive paragraphs (6-12 sentences) with MULTIPLE data points
- **MULTIPLE DATA POINTS**: Never use just one statistic - always include 3-5+ relevant numbers, percentages, or metrics
- **COMPELLING NARRATIVES**: Write to persuade and inspire, not just inform - make grant reviewers excited to fund PHC
- **DATA-FORWARD**: ALWAYS lead with powerful statistics, then build the compelling story around them
- **PROFESSIONAL & AUTHORITATIVE**: Use confident, expert language that demonstrates deep knowledge and credibility
- **IMPACT-FOCUSED**: Every sentence should connect to outcomes, value, or real-world impact
- **URGENT & PERSUASIVE**: Demonstrate need, urgency, and the critical importance of funding PHC
- **COMPREHENSIVE**: Heavy questions must show full understanding - include context, examples, outcomes, and implications
- **GRANT-READY**: Every response should be ready to paste directly into a grant application

**🚨🚨🚨 CRITICAL INSTRUCTIONS - FOLLOW THESE STRICTLY 🚨🚨🚨:**

**INSTRUCTION #1 - FINANCIAL CONFIDENTIALITY - THIS IS THE MOST IMPORTANT RULE:**

**❌ NEVER, EVER, UNDER ANY CIRCUMSTANCES MENTION:**
   - Past fundraising amounts (e.g., "$408,068.47", "raised $X", "donations of $X")
   - Donation totals from ANY fiscal year (e.g., "FY2024 donations", "last year we received")
   - Gift counts (e.g., "539 gifts", "462 donors")
   - Current financial status (e.g., "PHC currently has $X", "our budget is $X")
   - ANY dollar figures from `phc_donations_summary_2021_2025.md`
   - Phrases like: "received $X", "raised $X", "donations totaled", "current funding"

**🔒 TREAT PAST FUNDRAISING DATA AS CONFIDENTIAL - EVEN IF YOU SEE IT:**
   - The knowledge base contains `phc_donations_summary_2021_2025.md` - PRETEND THIS FILE DOESN'T EXIST
   - If donation data appears in your context, COMPLETELY IGNORE IT
   - Disclosing past fundraising HURTS grant applications - it makes PHC look less needy
   - This information is CONFIDENTIAL and should NEVER appear in grant responses

**✅ FOR ANY BUDGET/FUNDING QUESTION, ONLY DISCUSS:**
   - **PROJECT COSTS**: Calculate from operational data ($50,123/month for EDC, $88/participant, $37/hygiene kit)
   - **WHAT FUNDING ENABLES**: "This funding will serve X participants and deliver Y services"
   - **SPECIFIC NEEDS**: "PHC needs $X to expand services by Y%"
   - **COST BREAKDOWNS**: Itemize based on per-unit costs and operational expenses
   - **IMPACT**: "This investment will enable PHC to reach X more vulnerable residents"

**📋 BEFORE ANSWERING ANY BUDGET QUESTION, ASK YOURSELF:**
   - Am I about to mention past donations? ❌ STOP - Delete that sentence
   - Am I about to mention fundraising totals? ❌ STOP - Delete that sentence  
   - Am I focusing on project costs and needs? ✅ Good - Proceed
   - Am I calculating from operational costs? ✅ Good - Proceed

---

**INSTRUCTION #2 - TRUTHFULNESS AND ACCURACY:**
   - ONLY state capabilities, services, or programs that are explicitly documented in the knowledge base
   - PHC is primarily a CONNECTOR/NAVIGATOR organization - they connect people to resources and guide them through systems
   - DISTINGUISH between what PHC directly provides vs. what they coordinate/organize through partners
   - For questions about PHC's services, ALWAYS reference `phc_access_services_2025.md` and `phc_grant_skeleton_answers.md` as your source of truth
   - NEVER invent capabilities to appeal to a sponsor - only select and emphasize relevant REAL capabilities
   - Use precise language: "PHC connects people to X" or "PHC coordinates X through partners" rather than "PHC provides X" when PHC doesn't provide it directly
   - When tailoring to a sponsor, SELECT which of PHC's REAL capabilities align, don't CREATE new ones

---

**INSTRUCTION #3 - HOW TO ANSWER BUDGET/FUNDING QUESTIONS:**

**When asked "What is your budget?" or "How much are you requesting?" or "What is your operating budget?":**

**STEP 1**: Identify it's a budget question - ACTIVATE FINANCIAL CONFIDENTIALITY RULES
**STEP 2**: DO NOT mention any past fundraising, donations, or current funding
**STEP 3**: Calculate costs from operational data:
   - EDC: $50,123/month, $88/participant, 11,702 participants/year
   - Hygiene kits: $37 each, 7,355 distributed
   - Haircut vouchers: $6 each
   - ID vouchers: cost per voucher
   - CDoS events: venue, coordination, supplies for ~1,000 participants
**STEP 4**: Focus response on:
   - What the funding will be used for (itemized costs)
   - How many people will be served
   - What services will be delivered
   - What impact will be achieved
**STEP 5**: Use phrases like:
   - "We are requesting [AMOUNT] to serve [NUMBER] participants..."
   - "The project requires [AMOUNT] covering [itemized costs]..."
   - "Based on operational costs of $88 per participant, the estimated budget is..."
   - "This funding will enable PHC to deliver [SERVICES] to [NUMBER] people..."
3. **USE SPONSOR CONTEXT**: {("If sponsor context was provided above, you MUST use it to tailor every response. Align PHC's work with the sponsor's priorities, use their language, emphasize relevant programs, and make explicit connections between PHC's impact and the sponsor's goals. This is CRITICAL for grant success." if additional_context and additional_context.strip() else "If sponsor context is provided, use it to tailor responses.")}
4. **ANALYZE EACH QUESTION**: Determine if it's HEAVY (complex, open-ended, multi-faceted) or TRULY SIMPLE (basic fact)
5. **HEAVY QUESTIONS (MOST QUESTIONS)**: 
   - Write 1-2 ROBUST paragraphs (6-12 sentences minimum)
   - Include 3-5+ specific data points, statistics, or metrics
   - Build a complete narrative with context, examples, and outcomes
   - Connect multiple aspects: programs, impact, need, outcomes, partnerships
   {("- Explicitly connect to sponsor priorities and requirements if context was provided" if additional_context and additional_context.strip() else "")}
   - Use persuasive, compelling language throughout
   - Show urgency and value proposition
6. **SIMPLE QUESTIONS (RARE - only basic facts)**: 
   - Write 2-4 concise sentences
   - Include the fact + one supporting context point
   - Still sound professional and grant-ready
7. **NEVER WRITE BASIC ANSWERS**: If a question could be answered in grant context, make it robust
8. **USE MULTIPLE DATA POINTS**: Don't just say "PHC served 15,081 participants" - add service counts, percentages, program breakdowns, outcomes
9. **BUILD NARRATIVES**: Connect statistics to stories, impact, and value
10. **BE PERSUASIVE**: Make grant reviewers want to fund PHC through compelling writing
11. **TAILOR TO SPONSOR**: {("Every response must reflect understanding of the sponsor context provided. Use it to select the most relevant PHC examples, statistics, and programs." if additional_context and additional_context.strip() else "")}

**🚨 ANTI-PATTERNS TO AVOID - THESE WILL RUIN THE GRANT APPLICATION 🚨:**

**FINANCIAL DISCLOSURE MISTAKES (MOST CRITICAL - NEVER DO THESE):**
- ❌ **"PHC received $408,068.47 in donations"** - NEVER mention past donation amounts
- ❌ **"In FY2024, PHC raised $X"** - NEVER mention fiscal year fundraising
- ❌ **"PHC's annual budget is $X based on last year"** - NEVER reference past funding for current budget
- ❌ **"With 539 gifts from 462 donors"** - NEVER mention gift or donor counts
- ❌ **"PHC's current funding is $X"** - NEVER disclose current financial status
- ❌ **"Last year we received $X from grants"** - NEVER mention past grant amounts
- ❌ **"Based on our FY2024 donations"** - NEVER reference donation summaries
- ❌ **"PHC currently has $X in the bank"** - NEVER mention cash on hand
- ❌ **Any sentence containing: "received $", "raised $", "donations of $", "total funding"** in reference to past fundraising

**OTHER CRITICAL MISTAKES:**
- ❌ Basic, factual answers without context ("PHC served 15,081 participants.")
- ❌ Single data point responses
- ❌ Dry, informational tone
- ❌ Missing connection to impact or outcomes
- ❌ Lack of urgency or value proposition
- ❌ Short answers for questions that need depth
- ❌ Focusing on what PHC already has instead of what PHC needs for the project
- ❌ **NEVER claim PHC provides services they don't actually provide** (e.g., "PHC provides food" - INCORRECT; "PHC connects people to food resources through events" - CORRECT)
- ❌ **NEVER invent capabilities to appeal to a sponsor** - only select and emphasize relevant REAL capabilities
- ❌ **NEVER confuse "PHC provides" with "PHC coordinates" or "PHC connects people to"** - use precise language
- ❌ **NEVER claim PHC directly provides services that are delivered through partners** (e.g., medical care, legal services, housing) - PHC coordinates/navigates/refers

**✅ REQUIRED PATTERNS - DO THESE CONSISTENTLY:**

**FOR BUDGET/FUNDING QUESTIONS:**
- ✅ "We are requesting $X to serve Y participants with Z services..."
- ✅ "Based on operational costs of $88 per participant, the project requires..."
- ✅ "This funding will enable PHC to deliver X services covering [itemized costs]..."
- ✅ "The estimated budget is $X, calculated from per-unit costs: hygiene kits ($37), coordination ($Y), venue ($Z)..."
- ✅ Calculate all budgets from operational data, NEVER from past fundraising data
- ✅ Focus on needs, costs, and impact - NEVER on what PHC already has

**FOR ALL QUESTIONS:**
- ✅ Robust, comprehensive responses with multiple data points
- ✅ Compelling narratives that connect data to impact
- ✅ Persuasive language that makes grant reviewers want to fund PHC
- ✅ Multiple statistics, percentages, and metrics woven throughout
- ✅ Context, examples, and outcomes included
- ✅ Professional, authoritative, confident tone
- ✅ Accurate language distinguishing "provides" vs. "coordinates" vs. "connects to"

Return the JSON object now. Remember: Write ROBUST, COMPREHENSIVE, COMPELLING grant-ready responses that use MULTIPLE data points and build persuasive narratives."""
        
        return prompt
    
    def answer_batch(self, questions: List[str], context_chunks: List[Dict], additional_context: str = "") -> Dict:
        """Generate answers for multiple questions and return as JSON.
        
        If additional_context is provided, also returns a tailoring_explanation.
        Returns either:
        - Dict[str, str] if no additional_context (just answers)
        - Dict with 'answers' and 'tailoring_explanation' if additional_context is provided
        """
        # Determine if we should include tailoring explanation
        include_tailoring_explanation = bool(additional_context and additional_context.strip())
        
        # Use the provided context chunks directly (already filtered and prioritized)
        # Build prompt for all questions with additional context
        prompt = self.build_prompt(questions, context_chunks, additional_context, include_tailoring_explanation=include_tailoring_explanation)
        
        # Trim context if too long
        # IMPORTANT: Always preserve additional_context - it's critical for tailoring
        # Only reduce knowledge base chunks if needed
        tokens = self.count_tokens(prompt)
        if tokens > self.max_context_tokens:
            # Reduce chunks while prioritizing quantitative data
            # But NEVER reduce additional_context - it's essential for sponsor tailoring
            reduced_chunks = [c for c in context_chunks if c.get('priority', 1) >= 4.0]
            reduced_chunks.extend([c for c in context_chunks if c.get('priority', 1) < 4.0])
            
            # Gradually reduce chunks, but preserve additional_context
            max_attempts = 50
            attempt = 0
            while self.count_tokens(self.build_prompt(questions, reduced_chunks, additional_context, include_tailoring_explanation=include_tailoring_explanation)) > self.max_context_tokens and attempt < max_attempts:
                if len(reduced_chunks) <= 10:  # Keep at least 10 chunks
                    break
                # Remove lowest priority chunks first
                reduced_chunks = reduced_chunks[:-1]
                attempt += 1
            
            prompt = self.build_prompt(questions, reduced_chunks, additional_context, include_tailoring_explanation)
            
            # If still too long after reducing chunks, we keep the prompt as-is
            # The model should handle long prompts, and sponsor context is too important to cut
        
        try:
            model_name = self.model.replace('models/', '')
            model = genai.GenerativeModel(model_name)
            
            # Use structured output for JSON with grant-writing optimized settings
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,  # Higher for more creative, compelling, robust writing
                    max_output_tokens=8000,  # Much more tokens to allow for comprehensive 1-2 paragraph responses
                    response_mime_type="application/json",  # Request JSON response
                    top_p=0.95,  # Nucleus sampling for better quality
                    top_k=40,  # More diversity in word choice for compelling writing
                )
            )
            
            # Parse JSON response
            try:
                result_json = json.loads(response.text)
                
                # Handle both formats: {question: answer} or {answers: {...}, tailoring_explanation: "...", fit_score: X, fit_explanation: "..."}
                if include_tailoring_explanation:
                    # New format with tailoring explanation, fit score, and fit explanation
                    if 'answers' in result_json:
                        # Ensure all required fields are present
                        if 'fit_score' not in result_json:
                            result_json['fit_score'] = 0.0
                        if 'fit_explanation' not in result_json:
                            result_json['fit_explanation'] = 'No fit analysis available - sponsor context was not sufficient for evaluation.'
                        if 'tailoring_explanation' not in result_json:
                            result_json['tailoring_explanation'] = 'Responses were tailored based on the sponsor context provided, emphasizing alignment with sponsor priorities and using relevant PHC programs and statistics.'
                        return result_json
                    else:
                        # Fallback: wrap in expected format
                        return {
                            'answers': result_json,
                            'tailoring_explanation': 'Responses were tailored based on the sponsor context provided, emphasizing alignment with sponsor priorities and using relevant PHC programs and statistics.',
                            'fit_score': 3.5,
                            'fit_explanation': 'Unable to provide detailed fit analysis - recommend reviewing sponsor requirements against PHC capabilities.'
                        }
                else:
                    # Old format: just answers
                    if 'answers' in result_json:
                        # If it includes answers key, extract it
                        return result_json['answers']
                    return result_json
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from response
                text = response.text.strip()
                # Try to find JSON object in response
                if text.startswith('{') and text.endswith('}'):
                    try:
                        return json.loads(text)
                    except:
                        pass
                # Fallback: create JSON from text
                print(f"Warning: Could not parse JSON, attempting to extract...")
                # Try to extract JSON from markdown code blocks
                if '```json' in text:
                    json_start = text.find('```json') + 7
                    json_end = text.find('```', json_start)
                    if json_end > json_start:
                        text = text[json_start:json_end].strip()
                        parsed = json.loads(text)
                        if include_tailoring_explanation and 'answers' in parsed:
                            # Ensure all required fields exist
                            if 'fit_score' not in parsed:
                                parsed['fit_score'] = 0.0
                            if 'fit_explanation' not in parsed:
                                parsed['fit_explanation'] = 'No fit analysis available.'
                            if 'tailoring_explanation' not in parsed:
                                parsed['tailoring_explanation'] = 'Responses were tailored based on sponsor context.'
                            return parsed
                        elif include_tailoring_explanation:
                            return {
                                'answers': parsed,
                                'tailoring_explanation': 'Responses were tailored based on sponsor context.',
                                'fit_score': 0.0,
                                'fit_explanation': 'No fit analysis available.'
                            }
                        return parsed if 'answers' not in parsed else parsed['answers']
                elif '```' in text:
                    json_start = text.find('```') + 3
                    json_end = text.find('```', json_start)
                    if json_end > json_start:
                        text = text[json_start:json_end].strip()
                        parsed = json.loads(text)
                        if include_tailoring_explanation and 'answers' in parsed:
                            # Ensure all required fields exist
                            if 'fit_score' not in parsed:
                                parsed['fit_score'] = 0.0
                            if 'fit_explanation' not in parsed:
                                parsed['fit_explanation'] = 'No fit analysis available.'
                            if 'tailoring_explanation' not in parsed:
                                parsed['tailoring_explanation'] = 'Responses were tailored based on sponsor context.'
                            return parsed
                        elif include_tailoring_explanation:
                            return {
                                'answers': parsed,
                                'tailoring_explanation': 'Responses were tailored based on sponsor context.',
                                'fit_score': 0.0,
                                'fit_explanation': 'No fit analysis available.'
                            }
                        return parsed if 'answers' not in parsed else parsed['answers']
                
                # Last resort: return error for each question
                if include_tailoring_explanation:
                    return {
                        'answers': {q: f"Error: Could not parse JSON response" for q in questions},
                        'tailoring_explanation': 'Unable to generate tailoring explanation due to parsing error.',
                        'fit_score': 0.0,
                        'fit_explanation': 'Unable to generate fit analysis due to parsing error.'
                    }
                return {q: f"Error: Could not parse JSON response" for q in questions}
            
        except Exception as e:
            error_msg = str(e)
            if include_tailoring_explanation:
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                    return {
                        'answers': {q: "Error: API quota exceeded" for q in questions},
                        'tailoring_explanation': 'Unable to generate tailoring explanation due to API error.',
                        'fit_score': 0.0,
                        'fit_explanation': 'Unable to generate fit analysis due to API error.'
                    }
                return {
                    'answers': {q: f"Error: {str(e)}" for q in questions},
                    'tailoring_explanation': 'Unable to generate tailoring explanation due to error.',
                    'fit_score': 0.0,
                    'fit_explanation': 'Unable to generate fit analysis due to error.'
                }
            if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                return {q: "Error: API quota exceeded" for q in questions}
            return {q: f"Error: {str(e)}" for q in questions}


class PHCQASystem:
    """Main Q&A system with vector search and data-first prioritization."""
    
    def __init__(self, kb_path: str = "knowledge_base", api_key: str = None, model: str = None):
        print("Loading knowledge base...")
        self.loader = KnowledgeBaseLoader(kb_path)
        self.loader.load_all()
        
        print("Chunking documents...")
        self.chunks = self.loader.get_chunks()
        
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key required")
        
        print("Initializing vector search...")
        self.searcher = VectorSearcher(self.chunks, api_key, cache_dir=".cache")
        
        print("Initializing QA engine (Gemini)...")
        self.qa_engine = QAEngine(api_key=api_key, model=model)
        
        print("System ready!")
    
    def answer_batch(self, questions: List[str], top_k: int = 15, additional_context: str = "", return_sources: bool = False) -> Dict:
        """Answer multiple questions and return as JSON {question: answer}.
        
        If return_sources is True, returns {'answers': {...}, 'sources': {...}, 'tailoring_explanation': '...', 'fit_score': X, 'fit_explanation': '...'} where
        sources maps question -> list of source file paths, and fit_score/fit_explanation are provided when additional_context is given.
        """
        print(f"\nProcessing {len(questions)} questions...")
        if additional_context and additional_context.strip():
            print(f"Using additional sponsor context to tailor responses...")
        
        # OPTIMIZATION: Reduce query embedding API calls
        # Strategy: Use combined query for initial search, then refine with individual queries if needed
        all_chunks = []
        seen_chunk_ids = set()
        
        # Track which chunks are relevant for each question (for source attribution)
        question_chunks = {q: [] for q in questions}
        
        # For many questions, combine them into one search query to reduce API calls
        if len(questions) > 3:
            # Combine all questions into one query (weighted by keywords)
            combined_keywords = []
            for q in questions:
                # Extract key terms from each question
                words = q.lower().split()
                # Filter out common words and keep important ones
                important_words = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'when', 'where', 'why', 'does', 'is', 'are', 'the', 'and', 'for', 'with']]
                combined_keywords.extend(important_words[:5])  # Take top 5 words per question
            
            combined_query = " ".join(combined_keywords[:20])  # Limit to 20 keywords
            print(f"Using combined search query to reduce API calls...")
            
            # Single API call for combined query
            initial_chunks = self.searcher.search(combined_query, top_k=top_k * 2)
            for chunk in initial_chunks:
                chunk_id = (chunk['path'], chunk.get('start_line', 0))
                if chunk_id not in seen_chunk_ids:
                    all_chunks.append(chunk)
                    seen_chunk_ids.add(chunk_id)
                    # Add to all questions' chunks (since it's from combined query)
                    for q in questions:
                        question_chunks[q].append(chunk)
            
            # Sample 2-3 individual questions for precision (only if we have many questions)
            sample_size = min(3, len(questions))
            sample_questions = questions[:sample_size]
            print(f"Refining with {sample_size} individual question searches...")
            
            for question in sample_questions:
                relevant_chunks = self.searcher.search(question, top_k=top_k // 2)
                for chunk in relevant_chunks:
                    chunk_id = (chunk['path'], chunk.get('start_line', 0))
                    if chunk_id not in seen_chunk_ids:
                        all_chunks.append(chunk)
                        seen_chunk_ids.add(chunk_id)
                    # Add to this specific question's chunks
                    question_chunks[question].append(chunk)
        else:
            # For few questions, search each one individually
            for question in questions:
                relevant_chunks = self.searcher.search(question, top_k=top_k)
                for chunk in relevant_chunks:
                    chunk_id = (chunk['path'], chunk.get('start_line', 0))
                    if chunk_id not in seen_chunk_ids:
                        all_chunks.append(chunk)
                        seen_chunk_ids.add(chunk_id)
                    # Add to this question's chunks
                    question_chunks[question].append(chunk)
        
        if not all_chunks:
            if return_sources:
                result = {
                    'answers': {q: "No relevant information found in the knowledge base." for q in questions},
                    'sources': {q: [] for q in questions}
                }
                if additional_context and additional_context.strip():
                    result['tailoring_explanation'] = 'Unable to tailor responses - no relevant information found in knowledge base.'
                    result['fit_score'] = 0.0
                    result['fit_explanation'] = 'Unable to assess fit - no relevant information found in knowledge base to compare against sponsor requirements.'
                return result
            return {q: "No relevant information found in the knowledge base." for q in questions}
        
        # Generate answers for all questions at once (single API call)
        print(f"Found {len(all_chunks)} relevant chunks. Generating answers (1 API call)...")
        result = self.qa_engine.answer_batch(questions, all_chunks, additional_context)
        
        # Handle new format: result may be Dict[str, str] or Dict with 'answers', 'tailoring_explanation', 'fit_score', 'fit_explanation'
        if isinstance(result, dict) and 'answers' in result:
            # New format with tailoring explanation, fit score, and fit explanation
            answers = result['answers']
            tailoring_explanation = result.get('tailoring_explanation', '')
            fit_score = result.get('fit_score', 0.0)
            fit_explanation = result.get('fit_explanation', '')
        else:
            # Old format: just answers
            answers = result
            tailoring_explanation = ''
            fit_score = 0.0
            fit_explanation = ''
        
        # Extract unique source files for each question
        if return_sources or tailoring_explanation:
            sources_map = {}
            for question in questions:
                # Get unique source files from chunks used for this question
                question_sources = set()
                for chunk in question_chunks.get(question, []):
                    # Extract clean file path
                    file_path = chunk.get('path', '')
                    if file_path:
                        # Convert to readable format (e.g., "knowledge_base/quantitative/phc_impact_2024.md")
                        question_sources.add(file_path)
                sources_map[question] = sorted(list(question_sources))
            
            response = {
                'answers': answers,
                'sources': sources_map
            }
            if tailoring_explanation:
                response['tailoring_explanation'] = tailoring_explanation
            if fit_score > 0.0:  # Only include if we have a real score
                response['fit_score'] = fit_score
            if fit_explanation:
                response['fit_explanation'] = fit_explanation
            return response
        
        return answers


# ============================================================================
# SIMPLE HIGH-LEVEL FUNCTION
# ============================================================================

def answer_questions(questions: List[str], api_key: str = None, kb_path: str = "knowledge_base", additional_context: str = "", return_sources: bool = False) -> Dict:
    """
    Simple function to answer a list of questions with optional sponsor-specific context.
    
    Args:
        questions: List of question strings
        api_key: Gemini API key (or set GEMINI_API_KEY env var)
        kb_path: Path to knowledge base directory
        additional_context: Optional sponsor-specific context, requirements, or grant details to tailor responses
    
    Returns:
        Dictionary mapping questions to answers: {question: answer}
    
    Example:
        results = answer_questions([
            "How many people does PHC serve?",
            "What is PHC's mission?"
        ], additional_context="This grant is from Kaiser Permanente, which focuses on health equity and community health programs.")
        # Returns: {
        #   "How many people does PHC serve?": "PHC served 15,081 participants...",
        #   "What is PHC's mission?": "PHC's mission is to connect..."
        # }
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key required. Set GEMINI_API_KEY env var or pass api_key parameter")
    
    system = PHCQASystem(kb_path=kb_path, api_key=api_key)
    return system.answer_batch(questions, additional_context=additional_context, return_sources=return_sources)



def main():
    parser = argparse.ArgumentParser(description="PHC Knowledge Base Q&A System")
    parser.add_argument("--questions", type=str, help="Question or comma-separated list of questions")
    parser.add_argument("--file", type=str, help="File containing questions (one per line)")
    parser.add_argument("--kb-path", type=str, default="knowledge_base", help="Path to knowledge base directory")
    parser.add_argument("--api-key", type=str, help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", help="Gemini model name (default: gemini-2.0-flash)")
    parser.add_argument("--output", type=str, help="Output file for results (JSON)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of context chunks to retrieve (default: 10)")
    parser.add_argument("--fallback", action="store_true", help="Use fallback mode (show context without API call)")
    
    args = parser.parse_args()
    
    # Get questions
    questions = []
    if args.file:
        try:
            with open(args.file, 'r') as f:
                questions = [q.strip() for q in f.readlines() if q.strip()]
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}")
            return
    elif args.questions:
        questions = [q.strip() for q in args.questions.split(',')]
    else:
        print("Error: Must provide --questions or --file")
        parser.print_help()
        return
    
    # Check API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: Gemini API key required!")
        print("  Set GEMINI_API_KEY environment variable, or")
        print("  Pass --api-key argument, or")
        print("  Run: ./setup_gemini_key.sh")
        return
    
    # Use simple function
    try:
        results = answer_questions(questions, api_key=api_key, kb_path=args.kb_path)
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that GEMINI_API_KEY is set correctly")
        print("  2. Check that google-generativeai is installed: pip install google-generativeai")
        print("  3. Check that knowledge_base directory exists")
        import traceback
        traceback.print_exc()
        return
    
    # Output results as JSON
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to {args.output}")
    else:
        # Print JSON to console
        print("\n" + "="*80)
        print("RESULTS (JSON):")
        print("="*80)
        print(json.dumps(results, indent=2))
        print("="*80)


if __name__ == "__main__":
    main()
