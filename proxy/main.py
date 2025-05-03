import os
import json
import traceback
import logfire
from typing import Annotated, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from sqlmodel import create_engine, Session, Field, SQLModel, select
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException, Depends, status
from proxy.llm import proxy
from proxy.config import get_endpoint_by_model_name, get_all_available_models, get_settings
from pydantic import BaseModel
import secrets
import string
from datetime import datetime
from auth0.authentication import Users

engine = None
settings = get_settings()
users = Users(settings.auth0_domain)

# User profile model for storing API keys
class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    api_key: str = Field(index=True, unique=True)
    name: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
# Dictionary to cache API key lookups
known_profiles = {}

class TokenRequest(BaseModel):
    client_id: str
    client_secret: str

# Define the token auth scheme
token_auth_scheme = HTTPBearer(
    auto_error=True,
    description="API key authentication - Format: 'Bearer your-api-key'"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # Load the ML model
    engine = create_engine(
        os.environ.get(
            "DATABASE_URL", 
            settings.database_url if hasattr(settings, 'database_url') else "sqlite:///./test.db"
        ), 
        connect_args={}
    )
    # Create tables
    SQLModel.metadata.create_all(engine)
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

# Function to generate a new API key
def generate_api_key(length=32):
    """Generate a random API key."""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

@app.post("/v1/chat/completions")
async def completion(
        request: Request, 
        session: SessionDep,
        credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
    ):
    # Verify API key and get user profile
    profile = await verify_api_key(session, credentials)
    
    data = await request.json()
    try:
        target = await get_endpoint_by_model_name(data['model'])
    except Exception as e:
        raise HTTPException(status_code=404, detail="model provider not found")

    api_key = "sk-rc-test"
    if target['type'] == "ocf":
        target_url = f"{target['url']}/v1/service/llm/v1"
    else:
        raise HTTPException(status_code=404, detail="model provider not supported")
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
        credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
    ):
    """List all available models in OpenAI format."""
    # Verify API key and get user profile
    profile = await verify_api_key(session, credentials)
    
    models = await get_all_available_models()
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
async def list_models_detailed(
        session: SessionDep,
        credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
    ):
    """List all available models with detailed information."""
    # Verify API key and get user profile
    profile = await verify_api_key(session, credentials)
    
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

# Implement a real token verification function using jose
async def verify_access_token(access_token: str) -> UserProfile:
    """
    Verify an access token and return the associated user profile.
    """
    try:
        user = users.userinfo(access_token)
        user['api_key'] = 'sk-rc-test'
        return user
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Update the verify_token endpoint to use the new function
@app.post("/api/auth/verify_token")
async def verify_token(
    request: Request,
    session: SessionDep,
):
    """Verify an access token and get or create the user profile."""
    try:
        data = await request.json()
        access_token = data.get("accessToken")
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is required")
        
        # Verify token and get user profile
        return await verify_access_token(access_token)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing token: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)