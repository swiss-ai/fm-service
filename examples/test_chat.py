import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key='test',
    base_url="http://localhost:8080/v1",
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-1M",
    messages=[
        {"role": "system", "content": "Talk like an expert historian."},
        {
            "role": "user",
            "content": "Who is Alan turing?",
        },
    ],
)



print(response)