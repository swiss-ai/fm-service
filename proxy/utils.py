from sqlmodel import select, Session
from proxy.entities import ProviderKey

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
    print(f"profile: {profile}")
    return profile