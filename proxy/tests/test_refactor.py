
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from proxy.llm_proxy import llm_proxy
from proxy.protocols import LLMRequest

async def test_llm_proxy_tracking():
    print("Testing llm_proxy tracking with aiohttp...")
    
    # Mock dependencies
    with patch("aiohttp.ClientSession") as MockSession, \
         patch("proxy.llm_proxy.langfuse") as mock_langfuse:
        
        # Setup session mock
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        # Setup response mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            },
            "id": "123",
            "created": 111,
            "object": "chat.completion",
            "model": "gpt-4"
        }
        # post context manager
        mock_post = MagicMock()
        mock_post.__aenter__.return_value = mock_response
        mock_post.__aexit__.return_value = None
        mock_session.post.return_value = mock_post

        # Setup Langfuse mock
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        
        mock_generation = MagicMock()
        mock_trace.generation.return_value = mock_generation

        # Call function
        request = LLMRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            user_id="user123",
            app_title="my-app",
            tags=["t1"]
        )
        
        response = await llm_proxy(
            endpoint="http://test",
            api_key="key",
            request=request
        )
        
        # Verify tracking
        # 1. trace called
        mock_langfuse.trace.assert_called_once()
        call_kwargs = mock_langfuse.trace.call_args[1]
        assert call_kwargs['name'] == "process-request"
        assert call_kwargs['user_id'] == "user123"
        assert call_kwargs['tags'] == ["t1"]
        assert call_kwargs['metadata']['application'] == "my-app"
        
        # 2. generation created
        mock_trace.generation.assert_called_once()
        gen_kwargs = mock_trace.generation.call_args[1]
        assert gen_kwargs['name'] == "llm-response"
        assert gen_kwargs['model'] == "gpt-4"
        
        # 3. generation updated
        mock_generation.update.assert_called()
        mock_generation.end.assert_called_once()
        
        print(f"Response: {response}")
        print("PASS: Tracking works")

async def test_llm_proxy_opt_out():
    print("Testing llm_proxy opt_out...")
    
    with patch("aiohttp.ClientSession") as MockSession, \
         patch("proxy.llm_proxy.langfuse") as mock_langfuse:
        
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": "Hello"}],
            "id": "1", "created": 2, "object": "chat.completion", "model": "gpt-4"
        }
        
        # For opt out, I used `async with session.post(...) as resp:`
        mock_post = MagicMock()
        mock_post.__aenter__.return_value = mock_response
        mock_post.__aexit__.return_value = None
        mock_session.post.return_value = mock_post
        
        request = LLMRequest(
            model="gpt-4",
            opt_out=True
        )
        
        await llm_proxy(
            endpoint="http://test",
            api_key="key",
            request=request
        )
        
        # Verify NO tracking
        mock_langfuse.trace.assert_not_called()
        print("PASS: Opt-out works")

async def main():
    await test_llm_proxy_tracking()
    await test_llm_proxy_opt_out()

if __name__ == "__main__":
    asyncio.run(main())
