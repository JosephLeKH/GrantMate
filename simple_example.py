#!/usr/bin/env python3
"""
Simple example of using the PHC Q&A system
Tests with questions from Kaiser Permanente Grant Application
Returns JSON: {question: answer}
"""

from qa_system import answer_questions
import os
import json

# Make sure API key is set
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: Set GEMINI_API_KEY environment variable")
    print("Get your API key from: https://makersuite.google.com/app/apikey")
    print("\nUsage:")
    print("  export GEMINI_API_KEY='your-api-key-here'")
    print("  python3 simple_example.py")
    exit(1)

# Questions from Kaiser Permanente Grant Application (PHC 84)
# This tests how Gemini handles a full grant application's questions
questions = [
    "What is your organization's name and mission?",
    "What is the purpose of your request?",
    "Who will this event serve and how many people will be reached?",
    "What are the goals or intended outcomes of this project?",
    "What services will be offered at the event?",
    "Describe your organization's history and relevant experience.",
    "What community health need does this event address?",
    "How will success be measured?",
    "What is the fiscal sponsor's role?",
    "Who are the primary contacts for this event?",
    "What are the organization's policies regarding discrimination, religion, and politics?",
]

print("="*80)
print("TESTING PHC Q&A SYSTEM")
print("Questions from: Kaiser Permanente Grant Application (PHC 84)")
print("="*80)
print(f"\nProcessing {len(questions)} grant application questions...")
print()

results = answer_questions(questions, api_key=api_key)

# Print JSON results
print("\n" + "="*80)
print("GRANT APPLICATION ANSWERS (JSON):")
print("="*80)
print(json.dumps(results, indent=2))
print("="*80)

# Also print in a more readable format
print("\n" + "="*80)
print("GRANT APPLICATION ANSWERS (READABLE FORMAT):")
print("="*80)
for i, (question, answer) in enumerate(results.items(), 1):
    print(f"\n{i}. {question}")
    print("-" * 80)
    print(answer)
print("="*80)
