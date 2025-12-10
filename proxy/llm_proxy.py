import json
import backoff
import os
from langfuse import Langfuse
from langfuse.openai import openai
from proxy.protocols import ModelResponse, RetryConstantError, RetryExpoError, UnknownLLMError

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

async def response_generator(response, generation):
    async for chunk in response:
        data = chunk.to_dict()
        # In streaming mode, usage information comes in the final chunk
        if data.get("usage", None) is not None:
            generation.update(usage={
                "promptTokens": data["usage"]["prompt_tokens"],
                "completionTokens": data["usage"]["completion_tokens"],
            })
        yield f"data: {json.dumps(data)}\n\n"

def handle_llm_exception(e: Exception):
    if isinstance(
        e,
        (
            openai.APIError,
            openai.Timeout,
        ),
    ):
        raise RetryConstantError from e
    elif isinstance(e, openai.RateLimitError):
        raise RetryExpoError from e
    elif isinstance(
        e,
        (
            openai.APIConnectionError,
            openai.AuthenticationError,
        ),
    ):
        raise e
    else:
        raise UnknownLLMError from e

@backoff.on_exception(
    wait_gen=backoff.constant,
    exception=RetryConstantError,
    max_tries=3,
    interval=3,
)
@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=RetryExpoError,
    jitter=backoff.full_jitter,
    max_value=100,
    factor=1.5,
)
async def llm_proxy(endpoint, api_key, **kwargs) -> ModelResponse:
    async def _completion():
        try:
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=endpoint,
            )
            user_id = kwargs.get('user_id', '')
            del kwargs['user_id']
            response = await client.chat.completions.create(
                model=kwargs.get('model'),
                messages=kwargs.get('messages', []),
                stream=kwargs.get('stream', False),
                stream_options=kwargs.get('stream_options'),
                logprobs=kwargs.get('logprobs', False),
                top_logprobs=kwargs.get('top_logprobs', None),
                max_tokens=kwargs.get('max_tokens', None),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                seed=kwargs.get('seed', 42),
                presence_penalty=kwargs.get('presence_penalty', 0.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                extra_body=kwargs.get('extra_body', {}),
                name='chat-generation',
                metadata={
                    'langfuse_user_id': user_id,
                    'application': kwargs.get('application', 'fmservice')
                }
            )
            return response
        except Exception as e:
            print(f"Error in llm_proxy: {e}")
            handle_llm_exception(e)
    try:
        return await _completion()
    except Exception as e:
        raise e

def handle_llm_exception(e: Exception):
    if isinstance(
        e,
        (
            openai.APIError,
            openai.Timeout,
        ),
    ):
        raise RetryConstantError from e
    elif isinstance(e, openai.RateLimitError):
        raise RetryExpoError from e
    elif isinstance(
        e,
        (
            openai.APIConnectionError,
            openai.AuthenticationError,
        ),
    ):
        raise e
    else:
        raise UnknownLLMError from e

@backoff.on_exception(
    wait_gen=backoff.constant,
    exception=RetryConstantError,
    max_tries=3,
    interval=3,
)
@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=RetryExpoError,
    jitter=backoff.full_jitter,
    max_value=100,
    factor=1.5,
)
async def llm_proxy_completions(endpoint, api_key, **kwargs) -> ModelResponse:
    async def _completion():
        try:
            client = openai.AsyncClient(
                api_key=api_key,
                base_url=endpoint,
            )
            user_id = kwargs.get('user_id', '')
            del kwargs['user_id']
            response = await client.completions.create(
                model=kwargs.get('model'),
                prompt=kwargs.get('prompt', ''),
                stream=kwargs.get('stream', False),
                stream_options=kwargs.get('stream_options'),
                max_tokens=kwargs.get('max_tokens', None),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                seed=kwargs.get('seed', 42),
                presence_penalty=kwargs.get('presence_penalty', 0.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                extra_body=kwargs.get('extra_body', {}),
                name='completions-generation',
                metadata={
                    'langfuse_user_id': user_id,
                    'application': kwargs.get('application', 'fmservice')
                }
            )
            return response
        except Exception as e:
            print(f"Error in llm_proxy: {e}")
            handle_llm_exception(e)
    try:
        return await _completion()
    except Exception as e:
        raise e
    
@backoff.on_exception(
    wait_gen=backoff.constant,
    exception=RetryConstantError,
    max_tries=3,
    interval=3,
)
@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=RetryExpoError,
    jitter=backoff.full_jitter,
    max_value=100,
    factor=1.5,
)
async def llm_proxy_embeddings(endpoint, api_key, **kwargs) -> ModelResponse:
    async def _embedding():
        try:
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=endpoint,
            )
            user_id = kwargs.get('user_id', '')
            del kwargs['user_id']
            
            embedding_params = {
                'model': kwargs.get('model'),
                'input': kwargs.get('input', []),
                'encoding_format': kwargs.get('encoding_format', 'float'),
                'name': 'embeddings-generation',
                'metadata': {
                    'langfuse_user_id': user_id,
                    'application': kwargs.get('application', 'fmservice')
                }
            }
            
            # Only supported in text-embedding-3 and later models
            if kwargs.get('dimensions') is not None:
                embedding_params['dimensions'] = kwargs.get('dimensions')
            
            response = await client.embeddings.create(**embedding_params)
            return response
        except Exception as e:
            print(f"Error in llm_proxy_embeddings: {e}")
            handle_llm_exception(e)
    try:
        return await _embedding()
    except Exception as e:
        raise e