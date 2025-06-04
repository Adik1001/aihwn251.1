import os
import json
from dotenv import load_dotenv
import openai
import time

load_dotenv()

def ask_question(question, assistant_id, file_ids):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai

    thread = client.beta.threads.create()
    print(f"Thread created: {thread.id}")

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
        file_ids=file_ids  
    )
    print(f"Message sent: {message.id}")

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    print(f"Run started: {run.id}")

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status in ["completed", "failed", "cancelled"]:
            break
        time.sleep(1)

    if run_status.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                print("\nAssistant's answer:")
                print(msg.content[0].text.value)
                break
    else:
        print(f"Run did not complete successfully: {run_status.status}")

def main():
    try:
        with open("assistant_id.json", "r") as f:
            assistant_id = json.load(f)["assistant_id"]
    except Exception as e:
        print(f"Could not load assistant_id.json: {e}")
        return

    file_ids_input = input("Enter file ID(s) to use (comma-separated, e.g. file-xxxx): ").strip()
    file_ids = [fid.strip() for fid in file_ids_input.split(",") if fid.strip()]
    if not file_ids:
        print("No file IDs provided. Exiting.")
        return

    question = input("Enter your question: ").strip()
    if not question:
        print("No question provided. Exiting.")
        return

    ask_question(question, assistant_id, file_ids)

if __name__ == "__main__":
    main() 