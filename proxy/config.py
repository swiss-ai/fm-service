import random
import aiohttp
from async_lru import alru_cache
from typing import Dict
from pydantic_settings import BaseSettings
from functools import lru_cache

@lru_cache()
def get_settings():
    return Settings()

# Dictionary to store user-submitted provider keys
provider_keys: Dict[str, Dict[str, str]] = {}

class Settings(BaseSettings):
    auth0_domain: str
    auth0_api_audience: str
    auth0_issuer: str
    auth0_algorithms: str
    auth0_client_id: str
    auth0_client_secret: str
    logfire_token: str
    database_url: str
    auth_secret: str
    auth_trust_host: bool = False
    class Config:
        env_file = ".env"

available_endpoints = [
    {
        'url': 'http://140.238.223.116:8092',
        'type': 'ocf',
        'api_key': 'test',
    }
]

def parse_hardware_info(hardware_info):
    """
    Parse hardware information and return a string representation.
    
    Args:
        hardware_info (dict): Dictionary containing hardware information
        
    Returns:
        str: String representation of the hardware in the format "Nx[Spec]"
    """
    if not hardware_info or "gpus" not in hardware_info or not hardware_info["gpus"]:
        return "Unknown"
    # Group GPUs by name
    gpu_counts = {}
    for gpu in hardware_info["gpus"]:
        name = gpu.get("name", "Unknown GPU")
        gpu_counts[name] = gpu_counts.get(name, 0) + 1
    # Format the output
    result = []
    for gpu_name, count in gpu_counts.items():
        result.append(f"{count}x {gpu_name}")
    return ", ".join(result)

@alru_cache(maxsize=32)
async def get_nonocf_models(prefix, endpoint):
    target_url = f"{endpoint}/models"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data['data']:
                        models.append({
                            'name': f"{prefix}/{model['id']}",
                            'device': 'API'
                        })
                    return models
                else:
                    print(f"Error fetching models: HTTP {response.status}")
                    return []
    except Exception as e:
        print(f"Error fetching models from {target_url}: {e}")
        return []
    
async def get_ocf_models(endpoint):
    target_url = f"{endpoint}/v1/dnt/table"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for node_info in data.values():
                        if not node_info.get('service'):
                            continue
                        device_info = parse_hardware_info(node_info.get("hardware"))
                        for service in node_info['service']:
                            if not service.get('identity_group'):
                                continue
                            # Extract model names from identity_group
                            model_names = [identity[len('model='):] for identity in service['identity_group'] 
                                          if identity.startswith('model=')]
                            # Add each model to the list
                            models.extend({'name': model_name, 'device': device_info} 
                                         for model_name in model_names)
                    
                    return models
                else:
                    print(f"Error fetching models: HTTP {response.status}")
                    return []
    except Exception as e:
        print(f"Error fetching models from {target_url}: {e}")
        return []

@alru_cache(maxsize=32)
async def get_endpoint_by_model_name(model_name):
    candidates = []
    for endpoint in available_endpoints:
        if endpoint['type'] == 'ocf':
            models = await get_ocf_models(endpoint['url'])
            if model_name in [x['name'] for x in models]:
                candidates.append(endpoint)
        else:
            models = await get_nonocf_models(
                endpoint['prefix'],
                endpoint['url']
            )
            if model_name in [f"{x['name']}" for x in models]:
                candidates.append(endpoint)
    return random.choice(candidates)

async def get_all_available_models(extended=False):
    models = []
    for endpoint in available_endpoints:
        if endpoint['type'] == 'ocf':
            models += await get_ocf_models(endpoint['url'])
        else:
            models += await get_nonocf_models(
                endpoint['prefix'], 
                endpoint['url']
            )
    if extended:
        return [{'id': model['name'], 'created_by': '0x', 'owned_by': '0x', 'device': model['device']} for model in models]
    return [{'id': model['name'], 'created_by': '0x', 'owned_by': '0x'} for model in models]