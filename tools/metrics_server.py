
import os
import json
import base64
import urllib.parse
import hashlib
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Body
import aiohttp
import redis
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Metrics Server")

# --- Redis Cache Implementation (Simplified adaptation from proxy/redis_cache.py) ---
class RedisCache:
    def __init__(self, host: str = None, port: int = 6379, db: int = 0, password: str = None):
        self.host = host or os.environ.get("REDIS_HOST", "localhost")
        self.port = port
        self.db = db
        self.password = password or os.environ.get("REDIS_PASSWORD")
        self.redis_client: Optional[redis.Redis] = None
        
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def get(self, key: str) -> Optional[str]:
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        return None

    def set(self, key: str, value: str, ttl: int = 300) -> bool:
        if self.redis_client:
            try:
                return self.redis_client.setex(key, ttl, value)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        return False

# Global cache instance
cache = RedisCache()

# --- Config ---
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")

if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    logger.warning("LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set. Metrics queries will fail unless cached.")


class MetricsQuery(BaseModel):
    view: str = "observations"
    metrics: list[dict]
    dimensions: list[dict] = []
    fromTimestamp: Optional[str] = None
    toTimestamp: Optional[str] = None
    # Allow extra fields to pass through if needed
    class Config:
        extra = "allow"

async def fetch_langfuse_metrics(query_json: Dict[str, Any]) -> Dict[str, Any]:
    encoded_query = urllib.parse.quote(json.dumps(query_json))
    url = f"https://cloud.langfuse.com/api/public/v2/metrics?query={encoded_query}"
    
    auth_s = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
    auth_b64 = base64.b64encode(auth_s.encode()).decode()
    headers = {"Authorization": f"Basic {auth_b64}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise HTTPException(status_code=resp.status, detail=f"Langfuse API error: {text}")
            return await resp.json()

def generate_cache_key(query_json: Dict[str, Any]) -> str:
    # Sort keys to ensure consistent hashing
    serialized = json.dumps(query_json, sort_keys=True)
    return f"metrics:{hashlib.md5(serialized.encode()).hexdigest()}"

@app.post("/metrics")
async def get_metrics(query: Dict[str, Any] = Body(...)):
    """
    Get metrics from Langfuse with Redis caching.
    Accepts arbitrary JSON query that matches Langfuse API requirements.
    """
    cache_key = generate_cache_key(query)
    
    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for key: {cache_key}")
        try:
            return json.loads(cached_result)
        except json.JSONDecodeError:
            logger.warning("Failed to decode cached result")
    
    logger.info(f"Cache miss for key: {cache_key}, fetching from Langfuse")
    
    # Fetch from API
    try:
        result = await fetch_langfuse_metrics(query)
    except Exception as e:
        # If API fails and we don't have cache, we have to error out
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Cache result
    cache.set(cache_key, json.dumps(result), ttl=300) # 5 minutes cache
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
