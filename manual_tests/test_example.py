import openai

client = openai.Client(api_key="sk-rc-n5R1xut2Hi9Ya2BCX_6XCw", base_url="https://api.swissai.cscs.ch/v1")
res = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[
        {
            "content": "Who is Pablo Picasso?", 
            "role": "user",
        }
    ],
    stream=True,
)

for chunk in res:
    if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
