import os
import json
import base64
import urllib.parse
import aiohttp
import asyncio

query_json = {
    "view": "observations",
    "metrics": [{"measure": "count", "aggregation": "count"}, {"measure": "latency", "aggregation": "p50"}],
    "dimensions": [{"field": "providedModelName"}],
    "fromTimestamp": "2024-01-01T00:00:00Z",
    "toTimestamp": "2024-12-23T00:00:00Z"
}
query_str = json.dumps(query_json, sort_keys=True)
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
encoded_query = urllib.parse.quote(query_str)
url = f"https://cloud.langfuse.com/api/public/v2/metrics?query={encoded_query}"
# Basic Auth Header
auth_s = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
auth_b64 = base64.b64encode(auth_s.encode()).decode()
headers = {"Authorization": f"Basic {auth_b64}"}


async def main():
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                print(data)

if __name__ == "__main__":
    
    asyncio.run(main())