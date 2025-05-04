import os

import logfire
from contextlib import asynccontextmanager
from sqlmodel import create_engine
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from proxy.llm_proxy import llm_proxy
from proxy.config import get_settings
from proxy.auth import get_profile_from_accesstoken, get_or_create_apikey
from proxy.provider import get_all_models

engine = None
settings = get_settings()
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
    yield
    engine = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("LOGFIRE_TOKEN", None):
    logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
    logfire.instrument_fastapi(app, capture_headers=True)

@app.get("/v1/models_detailed")
async def list_models_detailed():
    models = get_all_models(settings.ocf_head_addr+"/v1/dnt/table", with_details=True)
    return models

@app.get("/v1/models")
async def list_models():
    models = get_all_models(settings.ocf_head_addr+"/v1/dnt/table", with_details=False)
    return models

@app.get("/v1/profile")
async def get_profile(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None):
    try:
        user_profile = get_profile_from_accesstoken(credentials.credentials)
        if user_profile:
            api_key = get_or_create_apikey(engine, user_profile['email'])
        user_profile['api_key'] = api_key.key
        return user_profile
    except Exception as e:
        return HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)