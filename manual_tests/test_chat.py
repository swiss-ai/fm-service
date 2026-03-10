import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("RC_API_KEY", "test_user_id"),
    base_url="http://localhost:8080/v1",
)

response = client.chat.completions.create(
    model="swissai.org/meta-llama/Llama-3.3-70B-Instruct",
    messages=[
        {"role": "system", "content": "Talk like an expert historian."},
        {
            "role": "user",
            "content": "Who is Alan turing?",
        },
    ],
)

print(response)