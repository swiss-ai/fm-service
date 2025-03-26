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
                                            models.append({
                                                'name': model_name, 
                                                'device': parse_hardware_info(node_info.get("hardware"))
                                            })
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
    return random.choice(candidates)

async def get_all_available_models(extended=False):
    models = []
    for endpoint in available_endpoints:
        if endpoint['type'] == 'ocf':
            models += await get_ocf_models(endpoint['url'])
    if extended:
        return [{'id': model['name'], 'created_by': '0x', 'owned_by': '0x', 'device': model['device']} for model in models]
    return [{'id': model['name'], 'created_by': '0x', 'owned_by': '0x'} for model in models]