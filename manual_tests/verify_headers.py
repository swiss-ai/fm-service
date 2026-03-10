import openai
from openai import OpenAI

# Initialize client pointing to local proxy
client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8080/v1"
)

def test_non_streaming():
    print("Testing Non-Streaming...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Model name doesn't matter much for proxy logic test if using mock/upstream
            messages=[{"role": "user", "content": "Hello"}],
            stream=False
        )
        # In the proxy implementation for non-streaming, we attached headers to the ModelResponse object.
        # However, the OpenAI client SDK might not expose extra fields directly on the response object 
        # unless they are standard. 
        # But wait, the proxy returns a ModelResponse which is Pydantic. 
        # FastAPI returns this as JSON. 
        # So the JSON body will contain 'headers' field if we added it to ModelResponse model and populate it.
        # Let's inspect the raw response if possible or check if 'headers' key exists in the dict representation.
        
        # The openai client parses the response into a ChatCompletion object. 
        # Extra fields might be in model_extra or similar, or just valid if the client is lenient.
        # Actually, standard OpenAI client might ignore unknown fields.
        # To verify this properly, we might need to use `requests` or `httpx` directly to see the raw JSON body,
        # OR check if the client puts it in `extra_fields`.
        
        print("Response received.")
        if hasattr(response, 'headers'):
             print(f"Headers found in response object: {response.headers}")
        else:
             # It might be in the model dump if pydantic v2
             try:
                 print(f"Response dict: {response.model_dump()}")
             except:
                 print(f"Response dict: {response.dict()}")
                 
    except Exception as e:
        print(f"Non-streaming test failed: {e}")

def test_streaming():
    print("\nTesting Streaming...")
    try:
        # For streaming, we modify the HTTP headers of the response.
        # The OpenAI client exposes the raw HTTP response object if access is needed, 
        # but usually `with_raw_response` is used.
        response = client.chat.completions.with_raw_response.create(
             model="gpt-3.5-turbo",
             messages=[{"role": "user", "content": "Hello"}],
             stream=True
        )
        
        print("Streaming response received.")
        headers = response.headers
        print(f"Headers keys: {headers.keys()}")
        # Check for a specific header we expect from upstream or just that it's populated
        # We can just print them all.
        print("Headers:")
        for k, v in headers.items():
            print(f"{k}: {v}")
            
    except Exception as e:
        print(f"Streaming test failed: {e}")

def test_non_streaming_raw():
    print("\nTesting Non-Streaming Raw to see JSON body...")
    import requests
    url = "http://localhost:8080/v1/chat/completions"
    headers = {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        json_resp = response.json()
        if "headers" in json_resp:
            print("SUCCESS: 'headers' field found in JSON response.")
            print(f"Headers: {json_resp['headers']}")
        else:
            print("FAILURE: 'headers' field NOT found in JSON response.")
            print(f"Keys found: {json_resp.keys()}")
    except Exception as e:
        print(f"Raw test failed: {e}")

if __name__ == "__main__":
    test_non_streaming_raw()
    test_streaming()
