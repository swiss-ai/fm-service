
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add proxy parent dir to path so we can import proxy modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm_proxy import llm_proxy, llm_proxy_completions, llm_proxy_embeddings
from backend.protocols import ModelResponse, Choices, Message, Usage

async def test_llm_proxy_tracking():
    print("Testing llm_proxy tracking...")
    
    # Mock dependencies
    with patch("backend.llm_proxy._execute_http_request", new_callable=AsyncMock) as mock_execute, \
         patch("backend.llm_proxy.langfuse") as mock_langfuse:
        
        # Setup _execute_http_request mock
        mock_response = ModelResponse(
            choices=[Choices(message=Message(role="assistant", content="Hello"))],
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )
        mock_execute.return_value = mock_response
        
        # Setup Langfuse mock
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_span
        mock_langfuse.trace.return_value = mock_span # trace() returns a client/span object
        
        mock_generation = MagicMock()
        mock_span.generation.return_value = mock_generation

        # Call function
        await llm_proxy(
            endpoint="http://test",
            api_key="key",
            request=MagicMock(
                model="gpt-4",
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                opt_out=False,
                user_id="user123",
                app_title="my-app",
                tags=["t1"],
                temperature=0.7,
                max_tokens=100,
                to_payload=lambda: {"model": "gpt-4", "messages": []}
            )
        )
        
        # Verify tracking
        # 1. langfuse.trace called
        mock_langfuse.trace.assert_called_once()
        call_kwargs = mock_langfuse.trace.call_args[1]
        assert call_kwargs['name'] == "process-request"
        assert call_kwargs['user_id'] == "user123"
        assert call_kwargs['tags'] == ["t1"]
        assert call_kwargs['metadata']['application'] == "my-app"
        
        # 2. generation created
        mock_span.generation.assert_called_once()
        gen_kwargs = mock_span.generation.call_args[1]
        assert gen_kwargs['name'] == "llm-response"
        assert gen_kwargs['model'] == "gpt-4"
        
        # 3. generation updated
        mock_generation.update.assert_called()
        mock_generation.end.assert_called_once()
        
        print("PASS: Tracking works")

async def test_llm_proxy_opt_out():
    print("Testing llm_proxy opt_out...")
    
    with patch("backend.llm_proxy._execute_http_request", new_callable=AsyncMock) as mock_execute, \
         patch("backend.llm_proxy.langfuse") as mock_langfuse:
        
        mock_response = ModelResponse(choices=[])
        mock_execute.return_value = mock_response
        
        await llm_proxy(
            endpoint="http://test",
            api_key="key",
             request=MagicMock(
                model="gpt-4",
                messages=[],
                stream=False,
                opt_out=True,
                to_payload=lambda: {"model": "gpt-4"}
            )
        )
        
        # Verify NO tracking
        mock_langfuse.trace.assert_not_called()
        print("PASS: Opt-out works")

async def main():
    await test_llm_proxy_tracking()
    await test_llm_proxy_opt_out()

if __name__ == "__main__":
    asyncio.run(main())
