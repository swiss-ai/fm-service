import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("RC_API_KEY", "test_user_id"),
    base_url="http://localhost:8080/v1",
)

models = client.models.list()

print(models)