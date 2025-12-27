import json
import backoff
import os
import aiohttp
from typing import Dict, Any, Optional, Union, Callable
from langfuse import Langfuse, propagate_attributes
from proxy.protocols import (
    ModelResponse, 
    RetryConstantError, 
    RetryExpoError, 
    UnknownLLMError,
    LLMRequest,
    LLMRequest,
    LLMCompletionsRequest,
)
from proxy.metrics import metrics_collector
import time
import asyncio
from proxy.utils import get_hardware_spec

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

active_requests = 0

async def response_generator(response, generation, trace=None, metrics_ctx=None):
    accumulated_content = []
    has_started_content = False
    first_token_time = None
    token_count = 0
    
    # Unpack metrics context
    start_time = None
    model = None
    node_id = None
    dnt_endpoint = None
    concurrency = 0
    
    if not trace and hasattr(response, "trace_span"):
        trace = response.trace_span
    
    if metrics_ctx:
        start_time = metrics_ctx.get('start_time')
        model = metrics_ctx.get('model')
        node_id = metrics_ctx.get('node_id')
        dnt_endpoint = metrics_ctx.get('dnt_endpoint')
        concurrency = metrics_ctx.get('concurrency')

    try:
        # response is now an aiohttp Stream or similar
        async for line in response:
            line = line.strip()
            if not line:
                continue
            if line.startswith(b"data: "):
                data_str = line[6:].decode('utf-8')
                if data_str == "[DONE]":
                    continue
                try:
                    data = json.loads(data_str)
                    # Accumulate content
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        # Handle Chat Completion (delta)
                        if "delta" in choice and "content" in choice["delta"]:
                            original_content = choice["delta"]["content"]
                            if original_content:
                                processed_content = original_content
                                if not has_started_content:
                                    processed_content = original_content.lstrip()
                                    if processed_content:
                                        if not first_token_time:
                                            first_token_time = time.time()
                                        has_started_content = True
                                choice["delta"]["content"] = processed_content
                                if processed_content:
                                    accumulated_content.append(processed_content)
                                    
                        # Handle Legacy Completion (text)
                        elif "text" in choice:
                            original_content = choice["text"]
                            if original_content:
                                processed_content = original_content
                                if not has_started_content:
                                    processed_content = original_content.lstrip()
                                    if processed_content:
                                        if not first_token_time:
                                            first_token_time = time.time()
                                        has_started_content = True
                                choice["text"] = processed_content
                                if processed_content:
                                    accumulated_content.append(processed_content)

                    if data.get("usage", None) is not None:
                        if generation:
                            usage_data = {}
                            if "prompt_tokens" in data["usage"]:
                                usage_data["promptTokens"] = data["usage"]["prompt_tokens"]
                            if "completion_tokens" in data["usage"]:
                                usage_data["completionTokens"] = data["usage"]["completion_tokens"]
                            if "total_tokens" in data["usage"]:
                                usage_data["totalTokens"] = data["usage"]["total_tokens"]

                            if "completion_tokens" in data["usage"]:
                                token_count = data["usage"]["completion_tokens"]

                            generation.update(usage=usage_data)
                    yield f"data: {json.dumps(data)}\n\n"
                except json.JSONDecodeError:
                    continue
    finally:
        full_content = "".join(accumulated_content)
        if trace:
            trace.update(output=full_content)

        if generation:
            generation.update(output=full_content)
             
        # Record Metrics
        if metrics_ctx and start_time and node_id:
             end_time = time.time()
             latency = end_time - start_time
             ttft = (first_token_time - start_time) if first_token_time else latency
             
             # If we didn't get usage data, estimate from content length
             if token_count == 0 and full_content:
                 token_count = len(full_content) / 4.0 # Crude approximation
             
             throughput = token_count / latency if latency > 0 else 0
             
             metrics_collector.record(
                 model=model,
                 node_id=node_id,
                 dnt_endpoint=dnt_endpoint,
                 concurrency=concurrency,
                 ttft=ttft,
                 latency=latency,
                 throughput=throughput
             )
        
        global active_requests
        active_requests -= 1

def handle_llm_exception(e: Exception):
    if isinstance(e, aiohttp.ClientResponseError):
        if e.status in [408, 429, 500, 502, 503, 504]:
             raise RetryExpoError(f"HTTP {e.status}: {e.message}") from e
        else:
             raise RetryConstantError(f"HTTP {e.status}: {e.message}") from e
    elif isinstance(e, (aiohttp.ClientError, aiohttp.ServerTimeoutError)):
         raise RetryConstantError(str(e)) from e
    else:
        raise UnknownLLMError from e

class StreamWrapper:
    def __init__(self, gen, generation=None, headers=None):
        self.gen = gen
        self.generation = generation
        self.headers = headers
    def __aiter__(self):
        return self.gen

async def _execute_http_request(
    session: aiohttp.ClientSession,
    url: str,
    headers: Dict,
    payload: Dict,
    stream: bool,
    generation: Any = None
) -> Union[ModelResponse, StreamWrapper]:
    req_cm = session.post(url, json=payload, headers=headers)
    try:
        resp = await req_cm.__aenter__()
    except Exception as e:
        await session.close()
        raise e

    if resp.status >= 400:
        try:
            text = await resp.text()
        except:
            text = str(resp.status)
        await req_cm.__aexit__(None, None, None)
        await session.close()
        
        if resp.status in [429, 500, 502, 503, 504]:
             raise RetryExpoError(f"HTTP {resp.status}: {text}")
        else:
             raise RetryConstantError(f"HTTP {resp.status}: {text}")
             
    # Capture headers
    response_headers = dict(resp.headers)
    if stream:
        if generation:
            resp.generation = generation
        async def wrapped_content():
            try:
                async for chunk in resp.content:
                    yield chunk
            finally:
                await req_cm.__aexit__(None, None, None)
                await session.close()
        return StreamWrapper(wrapped_content(), generation, headers=response_headers)
    else:
        try:
            data = await resp.json()
        finally:
            await req_cm.__aexit__(None, None, None)
            await session.close()
        
        model_response = ModelResponse(**data)
        model_response.headers = response_headers
        return model_response

async def _shared_proxy_handler(
    endpoint: str,
    api_key: str,
    payload: Dict,
    headers_extra: Dict,
    stream: bool,
    opt_out: bool,
    full_url: str,
    # Langfuse specific args
    trace_name: str,
    trace_user_id: str,
    trace_tags: list,
    trace_metadata: Dict,
    generation_name: str,
    generation_model: str,
    generation_params: Dict,
    generation_input: Any,
    # Output extraction callback for non-streaming generation update
    output_extractor: Callable[[ModelResponse], Dict] = None
) -> Union[ModelResponse, StreamWrapper]:
    global active_requests
    active_requests += 1
    start_time = time.time()
    snapshot_concurrency = active_requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    headers.update(headers_extra)
    
    if opt_out:
        session = aiohttp.ClientSession()
        try:
            resp = await _execute_http_request(
                session=session,
                url=full_url,
                headers=headers,
                payload=payload,
                generation=None
            )
            node_id = resp.headers.get("X-Computing-Node", "unknown") if hasattr(resp, "headers") else "unknown"
            dnt_endpoint = endpoint.split("/service")[0] + "/dnt/table"
            if stream and isinstance(resp, StreamWrapper):
                 resp.metrics_ctx = {
                     "start_time": start_time,
                     "model": generation_model, 
                     "node_id": node_id,
                     "dnt_endpoint": dnt_endpoint,
                     "concurrency": snapshot_concurrency
                 }
                 pass
                 
            else:
                 # Non-streaming
                 end_time = time.time()
                 latency = end_time - start_time
                 
                 token_count = 0
                 if isinstance(resp, ModelResponse) and resp.usage:
                     token_count = resp.usage.completion_tokens
                 
                 throughput = token_count / latency if latency > 0 else 0
                 
                 metrics_collector.record(
                     model=generation_model,
                     node_id=node_id,
                     dnt_endpoint=dnt_endpoint,
                     concurrency=snapshot_concurrency,
                     ttft=latency, # TTFT = Latency for non-stream
                     latency=latency,
                     throughput=throughput
                 )
                 active_requests -= 1
            
            return resp

        except Exception as e:
            active_requests -= 1
            if not session.closed:
                await session.close()
            handle_llm_exception(e)

    # Trace creation using start_span (manual lifecycle to support streaming)
    # Replaces start_as_current_observation context manager to avoid ContextVar token issues across async boundaries.
    
    trace = langfuse.start_span(
        name=trace_name,
        metadata=trace_metadata
    )
    
    trace.update(tags=trace_tags)
    trace.update_trace(
        user_id=trace_user_id, tags=trace_tags, metadata=trace_metadata)
    
    try:
        generation_meta = trace_metadata.copy()
        generation_meta["user_id"] = trace_user_id
        with propagate_attributes(user_id=trace_user_id):
             generation = trace.start_generation(
                 name=generation_name,
                 model=generation_model,
                 model_parameters=generation_params,
                 input=generation_input,
                 metadata=generation_meta
             )
             session = aiohttp.ClientSession()
             try:
                 response = await _execute_http_request(
                     session=session,
                     url=full_url,
                     headers=headers,
                     payload=payload,
                     stream=stream,
                     generation=generation
                 )
             except Exception as inner_e:
                 # If request fails, end generation and re-raise
                 generation.update(status_message=str(inner_e), level="ERROR")
                 raise inner_e

        # Outside propagate_attributes, response is ready.
        
        node_id = response.headers.get("X-Computing-Node", "unknown") if hasattr(response, "headers") else "unknown"
        dnt_endpoint = endpoint.split("/service")[0] + "/dnt/table"

        # Update trace tags with hardware spec and X-Title
        current_metadata = trace_metadata.copy()
        hardware_spec = get_hardware_spec(node_id, dnt_endpoint)
        current_metadata["hardware_spec"] = hardware_spec
        trace.update(metadata=current_metadata)
        generation.update(metadata=current_metadata)
        if stream and isinstance(response, StreamWrapper):
                response.trace_span = trace
                def cleanup_and_end(**kwargs):
                    if kwargs:
                        generation.update(**kwargs)
                    try:
                        pass
                    except:
                        pass
                        
                    generation.update(level="DEFAULT")
                response.metrics_ctx = {
                    "start_time": start_time,
                    "model": generation_model,
                    "node_id": node_id,
                    "dnt_endpoint": dnt_endpoint,
                    "concurrency": snapshot_concurrency
                }
                
                return response

        elif not stream and isinstance(response, ModelResponse):
                end_time = time.time()
                latency = end_time - start_time
                token_count = 0
                if response.usage:
                    token_count = response.usage.completion_tokens
                
                throughput = token_count / latency if latency > 0 else 0
                
                metrics_collector.record(
                    model=generation_model,
                    node_id=node_id,
                    dnt_endpoint=dnt_endpoint,
                    concurrency=snapshot_concurrency,
                    ttft=latency,
                    latency=latency,
                    throughput=throughput
                )
                active_requests -= 1

                update_kwargs = {}
                if response.usage:
                    update_kwargs["usage"] = {
                        "promptTokens": response.usage.prompt_tokens,
                        "completionTokens": response.usage.completion_tokens,
                        "totalTokens": response.usage.total_tokens
                    }
                if output_extractor:
                    update_kwargs.update(output_extractor(response))
                    
                generation.update(**update_kwargs)
                if "output" in update_kwargs:
                     trace.update(output=update_kwargs["output"])
                
                return response

    except Exception as e:
        if 'session' in locals() and not session.closed:
            await session.close()
        try:
            generation.update(status_message=str(e), level="ERROR")
        except:
            pass
        active_requests -= 1
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
async def llm_proxy(endpoint, api_key, request: LLMRequest) -> ModelResponse:
    def chat_output_extractor(resp: ModelResponse):
        if resp.choices and resp.choices[0].message:
            return {"output": resp.choices[0].message}
        return {}
    return await _shared_proxy_handler(
        endpoint=endpoint,
        api_key=api_key,
        payload=request.to_payload(),
        headers_extra={},
        stream=request.stream,
        opt_out=request.opt_out,
        full_url=endpoint.rstrip('/') + "/chat/completions",
        trace_name="chat-generation",
        trace_user_id=request.user_id,
        trace_tags=request.tags,
        trace_metadata={"application": request.app_title},
        generation_name="llm-response",
        generation_model=request.model,
        generation_params={
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        },
        generation_input=request.messages,
        output_extractor=chat_output_extractor
    )

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
async def llm_proxy_completions(endpoint, api_key, request: LLMCompletionsRequest) -> ModelResponse:
    def completion_output_extractor(resp: ModelResponse):
         if resp.choices:
             choice = resp.choices[0]
             if hasattr(choice, 'text'):
                 return {"output": choice.text}
             pass
         return {}

    return await _shared_proxy_handler(
        endpoint=endpoint,
        api_key=api_key,
        payload=request.to_payload(),
        headers_extra={},
        stream=request.stream,
        opt_out=request.opt_out,
        full_url=endpoint.rstrip('/') + "/completions",
        trace_name="generation",
        trace_user_id=request.user_id,
        trace_tags=request.tags,
        trace_metadata={"application": request.app_title},
        generation_name="llm-completions",
        generation_model=request.model,
        generation_params={
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        },
        generation_input=request.prompt,
        output_extractor=completion_output_extractor
    )

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
    # Construct payload manually from kwargs as before
    embedding_params = {
        'model': kwargs.get('model'),
        'input': kwargs.get('input', []),
        'encoding_format': kwargs.get('encoding_format', 'float'),
    }
    if kwargs.get('dimensions') is not None:
        embedding_params['dimensions'] = kwargs.get('dimensions')
    if kwargs.get('user') is not None:
        embedding_params['user'] = kwargs.get('user')
        
    user_id = kwargs.get('user_id', '')
    app_title = kwargs.get('app_title', '')
    
    return await _shared_proxy_handler(
        endpoint=endpoint,
        api_key=api_key,
        payload=embedding_params,
        headers_extra={},
        stream=False,
        opt_out=kwargs.get('opt_out', False),
        full_url=endpoint, 
        trace_name="embeddings-generation",
        trace_user_id=user_id,
        trace_tags=kwargs.get('tags', []),
        trace_metadata={"application": app_title},
        generation_name="embeddings-generation",
        generation_model=kwargs.get('model'),
        generation_params={},
        generation_input=embedding_params["input"],
        output_extractor=None # No output text to extract
    )