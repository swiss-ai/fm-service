import json
import backoff
from langfuse.openai import openai
from proxy.protocols import ModelResponse, RetryConstantError, RetryExpoError, UnknownLLMError

def response_generator(response, generation):
    for chunk in response:
        data = chunk.to_dict()
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
            kwargs['name']="chat-generation"
            response = await client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            handle_llm_exception(e) # this tries fallback requests
    try:
        return await _completion()
    except Exception as e:
        raise e