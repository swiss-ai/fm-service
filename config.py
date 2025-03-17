import random
import aiohttp
from async_lru import alru_cache

available_endpoints = [
    {
        'url': 'http://140.238.223.116:8092',
        'type': 'ocf',
        'api_key': 'test',
    }
]

@alru_cache(maxsize=32)
async def get_ocf_models(endpoint):
    target_url = f"{endpoint}/v1/dnt/table"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    models = []
                    for node_id, node_info in data.items():
                        if node_info.get('service'):
                            for service in node_info['service']:
                                if service.get('identity_group'):
                                    for identity in service['identity_group']:
                                        if identity.startswith('model='):
                                            model_name = identity[len('model='):]
                                            models.append(model_name)
                    
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
            if model_name in models:
                candidates.append(endpoint)
    return random.choice(candidates)

@alru_cache(maxsize=32)
async def get_all_available_models():
    models = []
    for endpoint in available_endpoints:
        if endpoint['type'] == 'ocf':
            models += await get_ocf_models(endpoint['url'])
    return [{'id': model, 'created_by': 'unknown', 'owned_by': 'unknown'} for model in models]