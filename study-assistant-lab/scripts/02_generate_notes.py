#!/usr/bin/env python3
"""
Generate structured exam notes from study materials
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import openai
from pydantic import BaseModel, Field, ValidationError

# Load environment variables
load_dotenv()

class Note(BaseModel):
    """Individual study note schema"""
    id: int = Field(..., ge=1, le=10, description="Note ID from 1 to 10")
    heading: str = Field(..., min_length=1, max_length=100, description="Concise note title")
    summary: str = Field(..., min_length=10, max_length=150, description="Brief summary of the concept")
    page_ref: Optional[int] = Field(None, description="Page number in source PDF if available")

class NotesResponse(BaseModel):
    """Response containing all 10 notes"""
    notes: List[Note] = Field(..., min_items=10, max_items=10, description="Exactly 10 study notes")

def initialize_client():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return openai.OpenAI(api_key=api_key)

def read_pdf_content(data_dir="data"):
    """Read content from PDF files in data directory"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return "No study materials found."
    
    pdf_files = list(data_path.glob("*.pdf"))
    if not pdf_files:
        return "No PDF files found in data directory."
    
    # For this implementation, we'll use the file names as context
    # In a real scenario, you'd extract text from PDFs
    file_info = []
    for pdf_file in pdf_files:
        file_info.append(f"Study material: {pdf_file.name}")
    
    return f"Available study materials: {', '.join([f.stem for f in pdf_files])}"

def create_system_prompt():
    """Create system prompt for note generation"""
    return """You are a study summarizer. Your task is to generate exactly 10 unique, high-quality study notes that will help students prepare for an exam.

Requirements:
- Generate EXACTLY 10 notes, no more, no less
- Each note should cover a different key concept
- Summaries must be concise but informative (10-150 characters)
- Include page references when possible
- Focus on the most important concepts for exam preparation
- Make notes distinct and non-overlapping

Respond with valid JSON matching this exact schema:
{
    "notes": [
        {
            "id": 1,
            "heading": "Example Concept",
            "summary": "Brief explanation of the concept that students need to know for the exam.",
            "page_ref": 42
        }
    ]
}"""

def generate_notes_with_context(client, context=""):
    """Generate notes using chat completion with structured output"""
    
    system_prompt = create_system_prompt()
    
    user_prompt = f"""Based on the study materials about calculus and mathematical concepts, generate exactly 10 exam preparation notes.

Study materials context: {context}

Focus on key concepts that students typically need to know for calculus exams, such as:
- Derivatives and their applications
- Integrals (definite and indefinite)
- Fundamental theorems
- Key mathematical principles
- Problem-solving techniques

Generate exactly 10 unique notes in the required JSON format."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating notes: {e}")
        raise

def validate_and_parse_notes(json_content):
    """Validate JSON response and parse into Pydantic models"""
    try:
        # Parse JSON
        data = json.loads(json_content)
        
        # Validate with Pydantic
        notes_response = NotesResponse(**data)
        
        return notes_response.notes
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        raise
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        raise

def print_notes(notes):
    """Pretty print the generated notes"""
    print("\n" + "="*70)
    print("📚 GENERATED EXAM NOTES")
    print("="*70)
    
    for note in notes:
        print(f"\n📝 {note.id:2d}. {note.heading}")
        print("-" * 50)
        print(f"Summary: {note.summary}")
        if note.page_ref:
            print(f"Page: {note.page_ref}")
        print()

def save_notes_to_file(notes, filename="exam_notes.json"):
    """Save notes to JSON file"""
    notes_data = {
        "notes": [note.model_dump() for note in notes],
        "generated_at": "2024-06-04",
        "total_notes": len(notes)
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Notes saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error saving notes: {e}")

def load_assistant_context(client):
    """Load context from assistant's knowledge base"""
    try:
        # Try to get some context from uploaded files
        with open("assistant_id.json", 'r') as f:
            data = json.load(f)
            assistant_id = data.get('assistant_id')
        
        if assistant_id:
            assistant = client.beta.assistants.retrieve(assistant_id)
            return f"Using knowledge from assistant: {assistant.name}"
    except:
        pass
    
    return "General calculus and mathematics study materials"

def main():
    """Main function"""
    print("📚 Starting Exam Notes Generation...")
    
    try:
        # Initialize client
        client = initialize_client()
        print("✅ OpenAI client initialized")
        
        # Get context
        pdf_context = read_pdf_content()
        assistant_context = load_assistant_context(client)
        context = f"{pdf_context}. {assistant_context}"
        
        print(f"📖 Context: {context}")
        
        # Generate notes
        print("🤖 Generating notes...")
        json_response = generate_notes_with_context(client, context)
        
        # Parse and validate
        print("✅ Validating response...")
        notes = validate_and_parse_notes(json_response)
        
        print(f"✅ Generated and validated {len(notes)} notes")
        
        # Display notes
        print_notes(notes)
        
        # Save to file
        save_notes_to_file(notes)
        
        # Summary
        print("\n" + "="*70)
        print("✅ NOTES GENERATION COMPLETED SUCCESSFULLY!")
        print(f"   - Generated: {len(notes)} notes")
        print(f"   - Saved to: exam_notes.json")
        print(f"   - All notes validated against schema")
        print("="*70)
        
        return 0
        
    except Exception as e:
        print(f"❌ Notes generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())