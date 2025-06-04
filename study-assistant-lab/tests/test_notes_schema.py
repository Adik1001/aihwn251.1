import openai
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use the assistant ID and create a new thread
thread = client.beta.threads.create()

# Add a message to the thread
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What is the derivative of sin(x)?"
)

# Run the assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id="asst_dh0svaxmUwXkbGbybEsjalap"
)

# Poll until the run is completed
import time

while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status in ['completed', 'failed']:
        break
    time.sleep(1)

# Get the assistant’s reply
messages = client.beta.threads.messages.list(thread_id=thread.id)
for message in messages.data:
    if message.role == "assistant":
        print("Assistant:", message.content[0].text.value)
