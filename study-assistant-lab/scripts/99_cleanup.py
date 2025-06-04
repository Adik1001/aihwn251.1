#!/usr/bin/env python3
"""
Cleanup script to delete OpenAI resources and avoid unnecessary charges
"""

import os
import json
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

def initialize_client():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return openai.OpenAI(api_key=api_key)

def cleanup_assistant(client):
    """Delete the assistant"""
    try:
        with open("assistant_id.json", 'r') as f:
            data = json.load(f)
            assistant_id = data.get('assistant_id')
        
        if assistant_id:
            # Delete assistant
            client.beta.assistants.delete(assistant_id)
            print(f"✅ Deleted assistant: {assistant_id}")
            
            # Remove assistant ID file
            os.remove("assistant_id.json")
            print("✅ Removed assistant_id.json")
        else:
            print("⚠️  No assistant ID found")
            
    except FileNotFoundError:
        print("⚠️  assistant_id.json not found")
    except Exception as e:
        print(f"❌ Error deleting assistant: {e}")

def cleanup_vector_store(client):
    """Delete the vector store"""
    try:
        with open("vector_store_id.json", 'r') as f:
            data = json.load(f)
            vector_store_id = data.get('vector_store_id')
        
        if vector_store_id:
            # Delete vector store
            client.beta.vector_stores.delete(vector_store_id)
            print(f"✅ Deleted vector store: {vector_store_id}")
            
            # Remove vector store ID file
            os.remove("vector_store_id.json")
            print("✅ Removed vector_store_id.json")
        else:
            print("⚠️  No vector store ID found")
            
    except FileNotFoundError:
        print("⚠️  vector_store_id.json not found")
    except Exception as e:
        print(f"❌ Error deleting vector store: {e}")

def cleanup_files(client):
    """Delete uploaded files"""
    try:
        # List all files
        files = client.files.list()
        deleted_count = 0
        
        for file in files:
            if file.purpose == "assistants":
                try:
                    client.files.delete(file.id)
                    print(f"✅ Deleted file: {file.filename} ({file.id})")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Error deleting file {file.id}: {e}")
        
        if deleted_count == 0:
            print("⚠️  No assistant files found to delete")
        else:
            print(f"✅ Deleted {deleted_count} files")
            
    except Exception as e:
        print(f"❌ Error listing/deleting files: {e}")

def cleanup_local_files():
    """Clean up local generated files"""
    local_files = [
        "exam_notes.json",
        "assistant_id.json",
        "vector_store_id.json"
    ]
    
    for filename in local_files:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"✅ Removed local file: {filename}")
        except Exception as e:
            print(f"❌ Error removing {filename}: {e}")

def confirm_cleanup():
    """Ask user to confirm cleanup"""
    print("⚠️  This will delete all OpenAI resources created by this project:")
    print("   - Assistant")
    print("   - Vector store")
    print("   - Uploaded files")
    print("   - Local generated files")
    print()
    
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    return response in ['yes', 'y']

def main():
    """Main cleanup function"""
    print("🧹 OpenAI Resources Cleanup Script")
    print("="*50)
    
    if not confirm_cleanup():
        print("❌ Cleanup cancelled by user")
        return 0
    
    try:
        # Initialize client
        client = initialize_client()
        print("✅ OpenAI client initialized")
        
        # Cleanup in order
        print("\n🗑️  Starting cleanup process...")
        
        # 1. Delete assistant (this should also clean up associated resources)
        cleanup_assistant(client)
        
        # 2. Delete vector store
        cleanup_vector_store(client)
        
        # 3. Delete uploaded files
        cleanup_files(client)
        
        # 4. Clean up local files
        cleanup_local_files()
        
        print("\n" + "="*50)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
        print("   All OpenAI resources have been deleted.")
        print("   No ongoing charges should occur.")
        print("="*50)
        
        return 0
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())