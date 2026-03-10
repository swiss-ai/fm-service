import openai
client = openai.OpenAI(
    api_key="sk-rc-",
    # base_url="http://localhost:8080/v1",
    # base_url="http://148.187.108.173:8092/v1/service/llm/v1/",
    base_url="https://api.swissai.cscs.ch/v1",
)
res = client.completions.create(
    model="Qwen/Qwen3-Next-80B-A3B-Instruct",
    prompt="Hello, how are you?",
    max_tokens=256,
    stream=False,
)
print(res)