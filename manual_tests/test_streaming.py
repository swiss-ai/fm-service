import openai

client = openai.Client(api_key="sk-rc-", base_url="http://localhost:8080/v1")
res = client.chat.completions.create(
    model="-",
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
