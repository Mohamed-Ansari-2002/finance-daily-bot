import os
from groq import Groq

# Paste your key directly here for testing
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Say hello and tell me today's date."
        }
    ],
    max_tokens=100
)

print(response.choices[0].message.content)