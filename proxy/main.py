import os

import logfire
from contextlib import asynccontextmanager
from sqlmodel import create_engine
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from proxy.llm_proxy import llm_proxy, response_generator
from proxy.config import get_settings
from proxy.auth import get_profile_from_accesstoken, get_or_create_apikey, verify_token
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

@app.post("/v1/chat/completions")
async def completion(
        request: Request, 
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    ):
    token = credentials.credentials
    
    if not verify_token(engine, token):
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )
    
    data = await request.json()
    if 'stream' not in data:
        data['stream'] = False
    if type(data['stream']) == str:
        if data['stream'].lower() == "true":
            data['stream'] = True # convert to boolean
    if data['stream']:
        data['stream_options'] = {"include_usage": True}
    response = llm_proxy(
        endpoint=settings.ocf_head_addr+"/v1/service/llm/v1/",
        api_key=token,
        **data,
    )
    if 'stream' in data and data['stream'] == True:
        return StreamingResponse(response_generator(response, response.generation), media_type='text/event-stream')
    return response

@app.get("/v1/models_detailed")
async def list_models_detailed():
    models = get_all_models(settings.ocf_head_addr+"/v1/dnt/table", with_details=True)
    return dict(
        object="list",
        data=models,
    )

@app.get("/v1/models")
async def list_models():
    models = get_all_models(settings.ocf_head_addr+"/v1/dnt/table", with_details=False)
    return dict(
        object="list",
        data=models,
    )

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