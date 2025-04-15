import os
import json
import logfire
from typing import Annotated
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from sqlmodel import create_engine, Session
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException, Depends

from proxy.llm import proxy
from proxy.entities import ProviderKey
from proxy.config import get_endpoint_by_model_name, get_all_available_models
from proxy.utils import construct_profile

token_auth_scheme = HTTPBearer()
engine = None

known_profiles = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # Load the ML model
    engine = create_engine(
        os.environ.get(
            "DATABASE_URL", 
            "sqlite:///./test.db"
        ), 
        connect_args={}
    )
    yield
    # Clean up the ML models and release the resources
    engine = None

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
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

def data_generator(response, generation):
    for chunk in response:
        data = chunk.to_dict()
        if data.get("usage", None) is not None:
            generation.update(usage={
                "promptTokens": data["usage"]["prompt_tokens"],
                "completionTokens": data["usage"]["completion_tokens"],
            })
        yield f"data: {json.dumps(data)}\n\n"

@app.post("/v1/chat/completions")
async def completion(
        request: Request, 
        session: SessionDep,
        token: str = Depends(token_auth_scheme),
    ):
    if token.credentials not in known_profiles:
        profile = construct_profile(
            session,
            token.credentials
        )
        known_profiles[token.credentials] = profile
    else:
        profile = known_profiles[token.credentials]
    data = await request.json()
    try:
        target = await get_endpoint_by_model_name(data['model'])
    except Exception as e:
        raise HTTPException(status_code=404, detail="model provider not found")
    
    api_key = "sk-rc-test"
    if target['type'] == "ocf":
        target_url = f"{target['url']}/v1/service/llm/v1"
    elif target['type'] == "openai":
        target_url = f"{target['url']}"
        api_key = profile[target['prefix']]
        data['model'] = data['model'].replace(f"{target['prefix']}/", "")
    response = proxy(target_url, api_key, **data)
    if 'stream' in data and data['stream'] == True:
        return StreamingResponse(
            data_generator(response, response.generation), 
            media_type='text/event-stream'
        )
    return response

@app.get("/v1/models")
async def list_models(
        session: SessionDep,
        token: str = Depends(token_auth_scheme),
    ):
    """List all available models in OpenAI format."""
    if token.credentials not in known_profiles:
        profile = construct_profile(
            session,
            token.credentials
        )
        known_profiles[token.credentials] = profile
    else:
        profile = known_profiles[token.credentials]
    models = await get_all_available_models(profile)
    model_objects = []
    for model in models:
        model_objects.append({
            "id": model.get("id", "unknown"),
            "object": "model",
            "created": model.get("created", 0),
            "owned_by": model.get("owned_by", "unknown")
        })
    return {
        "object": "list",
        "data": model_objects
    }

@app.get("/v1/models_detailed")
async def list_models():
    models = await get_all_available_models(extended=True)
    model_objects = []
    for model in models:
        model_objects.append({
            "id": model.get("id", "unknown"),
            "object": "model",
            "created": model.get("created", 0),
            "owned_by": model.get("owned_by", "0x"),
            "device": model.get("device", "unknown")
        })
    return {
        "object": "list",
        "data": model_objects
    }

@app.post("/api/provider_key")
async def submit_key(
    provider_key: ProviderKey,
    session: SessionDep,
    token: str = Depends(token_auth_scheme),
):
    session.add(provider_key)
    session.commit()
    session.refresh(provider_key)
    return {
        "status": "created",
        "data": provider_key
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)