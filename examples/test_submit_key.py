import requests
from openai import OpenAI

# Configuration - Update these values as needed
BASE_URL = "http://localhost:8080/api"
USER_API_KEY = "test_user_id"  # This becomes the user ID in the proxy server
PROVIDER = "swissai.org"  # The provider type you want to submit a key for
PROVIDER_API_KEY = "your_api_key_here"  # The API key for the provider
MODEL = "google/gemma-3-27b-it"  # Model to test after key submission

# Create OpenAI client with the user API key
client = OpenAI(
    api_key=USER_API_KEY,
    base_url=BASE_URL,
)

# First, test submitting a provider key
def test_submit_key():
    print("\n=== Testing Provider Key Submission ===")
    
    headers = {
        "Authorization": f"Bearer {USER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "provider_id": PROVIDER,
        "key": PROVIDER_API_KEY,
        "owner_key": USER_API_KEY,
    }
    
    response = requests.post(
        f"{BASE_URL}/provider_key",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

test_submit_key()