

import os
import json
import time
from dotenv import load_dotenv
import openai

load_dotenv()

def initialize_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return openai.OpenAI(api_key=api_key)

def load_assistant_id():
    try:
        with open("assistant_id.json", 'r') as f:
            data = json.load(f)
            return data.get('assistant_id')
    except FileNotFoundError:
        print("❌ Assistant ID not found. Please run 00_bootstrap.py first.")
        return None

def create_thread(client):
    thread = client.beta.threads.create()
    return thread

def add_message(client, thread_id, content):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    return message

def run_assistant(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        for message in messages:
            if message.role == "assistant":
                return message
    
    elif run.status == 'failed':
        print(f"❌ Run failed: {run.last_error}")
        return None
    
    return None

def format_message_content(message):
    content_parts = []
    citations = []
    
    for content in message.content:
        if content.type == 'text':
            text = content.text.value
            
            if content.text.annotations:
                for annotation in content.text.annotations:
                    if annotation.type == 'file_citation':
                        citation = {
                            'file_id': annotation.file_citation.file_id,
                            'quote': annotation.file_citation.quote
                        }
                        citations.append(citation)
                        
                        text = text.replace(annotation.text, f" [Citation {len(citations)}]")
            
            content_parts.append(text)
    
    return '\n'.join(content_parts), citations

def print_response(message):
    if not message:
        print("❌ No response received.")
        return
    
    content, citations = format_message_content(message)
    
    print("\n" + "="*60)
    print("🤖 ASSISTANT RESPONSE:")
    print("="*60)
    print(content)
    
    if citations:
        print("\n" + "-"*40)
        print("📚 CITATIONS:")
        print("-"*40)
        for i, citation in enumerate(citations, 1):
            print(f"[{i}] File ID: {citation['file_id']}")
            if citation.get('quote'):
                print(f"    Quote: \"{citation['quote'][:100]}...\"")
        print("-"*40)

def interactive_qa(client, assistant_id):
    print("\n🎓 Welcome to AI Study Assistant!")
    print("Ask questions about your study materials. Type 'quit' to exit.")
    print("="*60)
    
    thread = create_thread(client)
    print(f"📝 Created conversation thread: {thread.id}")
    
    test_prompts = [
        "Explain the difference between a definite and an indefinite integral in one paragraph.",
        "Give me the statement of the Mean Value Theorem."
    ]
    
    print("\n💡 Suggested test questions:")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"   {i}. {prompt}")
    
    while True:
        print("\n" + "="*60)
        question = input("❓ Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye! Happy studying!")
            break
        
        if not question:
            continue
        
        try:
            print("🤔 Thinking...")
            
            add_message(client, thread.id, question)
            
            response = run_assistant(client, thread.id, assistant_id)
            
            print_response(response)
            
        except Exception as e:
            print(f"❌ Error: {e}")

def test_assistant(client, assistant_id):
    print("\n🧪 Testing Assistant with Sample Questions...")
    
    test_questions = [
        "Explain the difference between a definite and an indefinite integral in one paragraph.",
        "Give me the statement of the Mean Value Theorem.",
        "What is the fundamental theorem of calculus?"
    ]
    
    thread = create_thread(client)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test Question {i}: {question}")
        print("-" * 50)
        
        try:
            add_message(client, thread.id, question)
            response = run_assistant(client, thread.id, assistant_id)
            print_response(response)
            
        except Exception as e:
            print(f"❌ Error with question {i}: {e}")

def main():
    try:
        client = initialize_client()
        
        assistant_id = load_assistant_id()
        if not assistant_id:
            return 1
        
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
            print(f"✅ Connected to assistant: {assistant.name}")
        except Exception as e:
            print(f"❌ Could not connect to assistant: {e}")
            return 1
        
        print("\nChoose an option:")
        print("1. Interactive Q&A session")
        print("2. Run test questions")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            interactive_qa(client, assistant_id)
        elif choice == "2":
            test_assistant(client, assistant_id)
        else:
            print("Invalid choice. Running interactive session...")
            interactive_qa(client, assistant_id)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())