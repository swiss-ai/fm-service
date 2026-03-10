import os
import openai

client = openai.Client(
    api_key=os.environ.get("RC_API_KEY"), base_url=os.environ.get("RC_API_BASE")
)
res = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[
        {
            "content": "Who is Alan Turing?", 
            "role": "user",
        }
    ],
    stream=False,
    logprobs=True,
    top_logprobs=2,
    max_tokens=10,
    extra_body = {
        "top_k": 50,
        "chat_template_kwargs": {"enable_thinking": False},
    },
)

print(res)