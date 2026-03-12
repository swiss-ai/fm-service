import os
import openai



client = openai.OpenAI(
    api_key=os.environ["RC_API_KEY"],
    base_url="http://localhost:8080/v1",
    # base_url="http://148.187.108.173:8092/v1/service/llm/v1/",
)
response = client.chat.completions.create(
    model="swiss-ai/Apertus-8B-Instruct-2509",
    messages=[
        {"role": "user", "content": "Write an essay about alan turing?"},
    ],
    stream=False,
)
print(f"response: {response}")

# add a streaming example
response_stream = client.chat.completions.create(
    model="swiss-ai/Apertus-8B-Instruct-2509",
    messages=[
        {"role": "user", "content": "Write an essay about alan turing?"},
    ],
    stream=True,
)
for chunk in response_stream:
    if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)