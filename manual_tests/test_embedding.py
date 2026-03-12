import os
from openai import OpenAI


KEY = os.environ["RC_API_KEY"]

client = OpenAI(
    api_key=KEY,
    # base_url="http://localhost:8080/v1"
    base_url="https://api.swissai.cscs.ch/v1",
)

resp = client.embeddings.create(
    model="Snowflake/snowflake-arctic-embed-l-v2.0",
    input="Who is Pablo Picasso?"
)


print("Embedding dim:", len(resp.data[0].embedding))
print(resp.data[0].embedding[:10])  # print first 10 vals
