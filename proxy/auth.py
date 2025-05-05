import os
import secrets
import traceback
import requests
from datetime import datetime
from sqlmodel import SQLModel, Field, Session, create_engine, select

known_tokens = set()

class APIKey(SQLModel, table=True):
    key: str = Field(primary_key=True)
    budget: int = Field(default=1000)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    owner_email: str = Field(default="")

def get_or_create_apikey(engine, owner_email: str) -> APIKey:
    with Session(engine) as session:
        api_key = session.exec(
            select(APIKey).where(APIKey.owner_email == owner_email)
        ).first()
        if api_key is None:
            key = f"sk-rc-{secrets.token_urlsafe(16)}"
            api_key = APIKey(key=key, owner_email=owner_email)
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
        return api_key

def rotate_key(engine, key: str) -> APIKey:
    with Session(engine) as session:
        api_key = session.exec(
            select(APIKey).where(APIKey.key == key)
        ).first()
        if api_key is None:
            raise ValueError("Invalid key")
        api_key.key = f"sk-rc-{secrets.token_urlsafe(16)}"
        session.add(api_key)
        session.commit()
        session.refresh(api_key)
        return api_key

def verify_token(engine, token: str) -> APIKey:
    if token in known_tokens:
        return True
    with Session(engine) as session:
        api_key = session.exec(
            select(APIKey).where(APIKey.key == token)
        ).first()
        if api_key is None:
            return None
        known_tokens.add(token)
        return True

def get_profile_from_accesstoken(access_token: str):
    res = requests.get(
        "https://researchcomputer.eu.auth0.com/userinfo",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    if res.status_code != 200:
        print(f"Invalid access token: {res.status_code} {res.text}")
        raise Exception(f"Invalid access token: {res.status_code} {res.text}")
    user = res.json()
    return user

if __name__ =="__main__":
    pg_host = os.environ.get("PG_HOST", "localhost")
    engine = create_engine(pg_host, echo=True)
    SQLModel.metadata.create_all(engine)