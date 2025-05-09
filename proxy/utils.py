import os
import requests
from typing import Optional

base_endpoint = "https://cloud.langfuse.com/api/public/metrics/daily"

def get_statistics(api_key: Optional[str] = None):
    # Parse request body for api_key
    lf_endpoint = base_endpoint
    if api_key is not None:
        lf_endpoint += f"?userId={api_key}"
    # Basic authentication credentials
    username = os.getenv("LANGFUSE_PUBLIC_KEY")
    password = os.getenv("LANGFUSE_SECRET_KEY")
    try:
        # Make API request with basic authentication
        response = requests.get(lf_endpoint, auth=(username, password))
        # Check if request was successful
        response.raise_for_status()
        # Parse and print the JSON response
        data = response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
    return data