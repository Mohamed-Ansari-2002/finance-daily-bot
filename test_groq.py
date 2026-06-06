import os
from groq import Groq

# Paste your key directly here for testing
GROQ_API_KEY = "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"

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