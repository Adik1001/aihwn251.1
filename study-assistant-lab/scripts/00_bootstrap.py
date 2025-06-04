

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()

def initialize_client():
    """Initialize and return OpenAI client (using openai module directly)"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    openai.api_key = api_key
    try:
        openai.models.list()
        print("✅ OpenAI client initialized successfully")
        return openai
    except Exception as e:
        print(f"❌ Failed to connect to OpenAI: {e}")
        raise

def create_assistant(client):
    """Create or retrieve existing assistant"""
    assistant_file = "assistant_id.json"
    
    if os.path.exists(assistant_file):
        try:
            with open(assistant_file, 'r') as f:
                data = json.load(f)
                assistant_id = data.get('assistant_id')
            
            assistant = client.beta.assistants.retrieve(assistant_id)
            print(f"✅ Retrieved existing assistant: {assistant.name} (ID: {assistant.id})")
            return assistant
        except Exception as e:
            print(f"⚠️  Could not retrieve existing assistant: {e}")
            print("Creating new assistant...")

    try:
        assistant = client.beta.assistants.create(
            name="Study Q&A Assistant",
            instructions=(
                "You are a helpful tutor. "
                "Use the knowledge in the attached files to answer questions. "
                "Cite sources where possible. "
                "Provide clear, concise explanations suitable for studying."
            ),
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}]
        )
        
        with open(assistant_file, 'w') as f:
            json.dump({'assistant_id': assistant.id}, f)
        
        print(f"✅ Created new assistant: {assistant.name} (ID: {assistant.id})")
        return assistant
        
    except Exception as e:
        print(f"❌ Failed to create assistant: {e}")
        raise


def upload_pdf_files(client, data_dir="data"):
    """Upload PDF files from data directory"""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"⚠️  Data directory '{data_dir}' not found.")
        return []
    
    pdf_files = list(data_path.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️  No PDF files found in '{data_dir}'.")
        return []

    uploaded_files = []
    
    for pdf_file in pdf_files:
        try:
            print(f"📄 Uploading {pdf_file.name}...")
            with open(pdf_file, "rb") as f:
                file = client.files.create(file=f, purpose="assistants")
            uploaded_files.append(file)
            print(f"✅ Uploaded {pdf_file.name} (ID: {file.id})")
        except Exception as e:
            print(f"❌ Failed to upload {pdf_file.name}: {e}")
    
    return uploaded_files

def attach_files_to_assistant(client, assistant, uploaded_files):
    """Attach uploaded files to the assistant"""
    if not uploaded_files:
        print("⚠️  No files to add to assistant.")
        return None

    try:
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            file_ids=[f.id for f in uploaded_files]
        )
        print(f"✅ Updated assistant with {len(uploaded_files)} files")
        return assistant
    except Exception as e:
        print(f"❌ Failed to attach files to assistant: {e}")
        raise

def main():
    """Main bootstrap function"""
    print("🚀 Starting AI Tutor Bootstrap Process...")

    try:
        client = initialize_client()
        uploaded_files = upload_pdf_files(client)

        if uploaded_files:
            assistant = client.beta.assistants.create(
                name="Study Q&A Assistant",
                instructions=(
                    "You are a helpful tutor. "
                    "Use the knowledge in the attached files to answer questions. "
                    "Cite sources where possible. "
                    "Provide clear, concise explanations suitable for studying."
                ),
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}]
            )
            with open("assistant_id.json", 'w') as f:
                json.dump({'assistant_id': assistant.id}, f)
            print(f"✅ Created new assistant: {assistant.name} (ID: {assistant.id})")
            print("✅ Bootstrap completed successfully!")
            print(f"   - Assistant ID: {assistant.id}")
            print(f"   - Files uploaded: {len(uploaded_files)}")
        else:
            assistant = create_assistant(client)
            print("✅ Assistant created, but no files were uploaded.")
            print("   Add PDF files to the 'data' directory and run this script again.")

        print("\n🎓 Ready to use the Q&A assistant!")

    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
