import jwt
from typing import Optional
from fastapi import Depends
from sqlmodel import select, Session
from proxy.entities import ProviderKey
from proxy.config import get_settings
from proxy.exceptions import UnauthenticatedException, UnauthorizedException
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer

def construct_profile(session:Session, user_key: str):
    """
    Fetch all ProviderKey records associated with a user and construct a dictionary mapping
    provider IDs to their respective keys.
    
    Args:
        session: SQLModel database session
        user_key: The user's API key/identifier
        
    Returns:
        dict: A dictionary with provider_id as keys and provider keys as values
    """
    # Create a query to select all active provider keys for this user
    query = select(ProviderKey).where(
        ProviderKey.owner_key == user_key,
        ProviderKey.is_active == True
    )
    # Execute the query and fetch all results
    results = session.exec(query).all()
    # Build the provider_id -> key mapping
    profile = {provider_key.provider_id: provider_key.key for provider_key in results}
    return profile

class VerifyToken:
    """Does all the token verification using PyJWT"""

    def __init__(self):
        self.config = get_settings()
        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f'https://{self.config.auth0_domain}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
    ): 
        if token is None:
            raise UnauthenticatedException

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.config.auth0_algorithms,
                audience=self.config.auth0_api_audience,
                issuer=self.config.auth0_issuer,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))
    
        return payload
