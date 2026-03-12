
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.main import app, get_perf_data

client = TestClient(app)

@patch("backend.metrics.metrics_collector.db")
def test_get_perf_endpoint(mock_db):
    # Setup mock
    mock_collection = MagicMock()
    mock_db.collection.return_value = mock_collection
    
    # Mock data
    mock_data = {
        "model": "test-model",
        "hardware": "test-gpu",
        "concurrency": "1",
        "avg_ttft": 0.1,
        "avg_latency": 0.5,
        "avg_throughput": 100.0,
        "count": 10
    }
    
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = mock_data
    
    mock_stream = MagicMock()
    mock_stream.__iter__.return_value = iter([mock_doc])
    mock_collection.stream.return_value = mock_stream
    mock_collection.where.return_value.stream.return_value = mock_stream

    # Clear cache
    get_perf_data.cache_clear()

    # Test GET /v1/perf
    response = client.get("/v1/perf")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["model"] == "test-model"
    
    # Verify DB call
    mock_db.collection.assert_called_with("llm_benchmarks")
    mock_collection.stream.assert_called()

    # Test GET /v1/perf?model=test-model
    response = client.get("/v1/perf?model=test-model")
    assert response.status_code == 200
    
    # Verify filter call
    mock_collection.where.assert_called_with("model", "==", "test-model")

if __name__ == "__main__":
    # Manually run test if executed directly
    # But usually run with pytest
    pass
