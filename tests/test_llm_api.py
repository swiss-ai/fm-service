import openai
client = openai.OpenAI(
    api_key="sk-rc-",
    base_url="http://localhost:8080/v1",
)
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"},
    ]
)
print(response)