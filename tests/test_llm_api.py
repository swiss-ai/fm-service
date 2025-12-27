import openai
client = openai.OpenAI(
    api_key="sk-rc-XJqaLep36bF2VddH6srz1w",
    base_url="http://localhost:8080/v1",
    # base_url="http://148.187.108.173:8092/v1/service/llm/v1/",
)
response = client.chat.completions.create(
    model="Qwen/Qwen3-0.6B",
    messages=[
        {"role": "user", "content": "Write an essay about alan turing?"},
    ],
    stream=False,
)
print(f"response: {response}")
# for chunk in response:
#     if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
#         print(chunk.choices[0].delta.content, end="", flush=True)
