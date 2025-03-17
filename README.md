# AI Proxy

A versatile proxy server that can forward API requests to multiple AI model providers, supporting both OpenAI-compatible APIs and OCF (Open Compute Foundation) API formats.

## Features

- Proxies requests to multiple configured endpoints
- Supports both OpenAI API format and OCF API format
- Auto-discovers available models from each endpoint
- Load-balances requests across endpoints that support the requested model
- Support for streaming responses
- Configurable via `config.py` or environment variables

## Setup

1. Clone this repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your endpoints in `config.py` (see Configuration section)
4. Run the server:
   ```bash
   python main.py
   ```

The server will start on port 8000 by default. You can change this by setting the `PORT` environment variable.

## Configuration

### Using config.py (Recommended)

Edit the `config.py` file to configure your endpoints:

```python
endpoints = [
    {
        'url': 'http://example-ocf-endpoint.com',
        'type': 'ocf',  # OCF format API
        'api_key': 'your-api-key'
    },
    {
        'url': 'https://example-openai-endpoint.com',
        'type': 'openai',  # Standard OpenAI API
        'api_key': 'your-api-key'
    }
]
```

Each endpoint needs:
- `url`: The base URL of the API endpoint (no trailing slash)
- `type`: Either 'ocf' or 'openai'
- `api_key`: Your API key for that endpoint

### Using Environment Variables (Legacy)

You can also configure the proxy using environment variables:

```bash
# Set a default OpenAI API URL
export TARGET_OPENAI_URL=https://api.openai.com

# Set a default API key
export API_KEY=your-api-key-here

# Configure multiple endpoints (JSON format)
export ENDPOINTS='{"https://api.openai.com":"your-api-key","https://another-endpoint.com":"another-api-key"}'

# Or as a comma-separated list
export ENDPOINTS=https://api.openai.com,https://another-endpoint.com
```

When using environment variables, all endpoints are treated as OpenAI-compatible.

## API Endpoints

### Main Proxy Endpoint

All OpenAI API paths are proxied transparently:

```
POST /v1/chat/completions
POST /v1/completions
GET /v1/models
...etc
```

The proxy will automatically route your request to an appropriate endpoint based on the requested model.

### Proxy Management Endpoints

- `GET /v1/models` - List all available models from all configured endpoints in OpenAI-compatible format
- `GET /v1/endpoints` - List all configured endpoints and their available models

## Environment Variables

- `PORT`: Port to run the server on (default: 8000)
- `TARGET_OPENAI_URL`: Default OpenAI API URL (default: https://api.openai.com)
- `API_KEY`: Default API key
- `TIMEOUT`: Request timeout in seconds (default: 60)
- `ENDPOINTS`: JSON string or comma-separated list of endpoints (see Configuration)

## Endpoint Types

### OpenAI Type

Standard OpenAI-compatible API endpoints that implement the OpenAI API specification. Models are discovered by calling the `/v1/models` endpoint.

### OCF Type

Open Compute Foundation API format endpoints follow the OCF specification. The proxy discovers available models by calling the `/v1/dnt/table` endpoint, which provides information about available nodes and their services.

For OCF endpoints, the proxy extracts model information exclusively from service identity groups with entries like `model=ModelName`. Only the portion after the "model=" prefix is used as the model identifier.

When using OCF endpoints, you reference models by the model name that appears after the "model=" prefix in the identity group (e.g., `Qwen/Qwen2.5-7B-Instruct-1M`).

The proxy automatically routes requests to the appropriate OCF endpoint based on the model specified in your request.

## License

MIT 