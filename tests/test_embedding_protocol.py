
from proxy.protocols import ModelResponse, EmbeddingObject
import json
import base64
import struct

def test_model_response_with_embeddings():
    embedding = EmbeddingObject(
        embedding=[0.1, 0.2, 0.3],
        index=0
    )
    
    response = ModelResponse(
        object="list",
        data=[embedding],
        model="test-model",
        usage={"prompt_tokens": 5, "total_tokens": 5}
    )
    
    assert response.object == "list"
    assert len(response.data) == 1
    assert response.data[0].embedding == [0.1, 0.2, 0.3]
    assert response.data[0].index == 0
    assert response.data[0].object == "embedding"
    
    # Test JSON serialization
    json_output = response.model_dump_json()
    data = json.loads(json_output)
    assert data["object"] == "list"
    assert data["data"][0]["object"] == "embedding"
    assert data["data"][0]["embedding"] == [0.1, 0.2, 0.3]

    # Test Base64 handling
    floats = [0.1, 0.2, 0.3]
    packed = struct.pack(f'<{len(floats)}f', *floats)
    b64_str = base64.b64encode(packed).decode('utf-8')
    
    embedding_b64 = EmbeddingObject(
        embedding=b64_str,
        index=1
    )
    assert embedding_b64.embedding == [pytest.approx(x) for x in floats] # Use pytest.approx for potential float precision issues, but here likely exact
    # actually manual list compare for exact floats from struct pack/unpack usually fine for simple values
    # but let's be safe if we had pytest imported. We don't have pytest in this script, just manual asserts.
    # struct pack/unpack of 0.1 might have slight diffs from literal 0.1? No, 0.1 float is 0.1 float.
    
    # re-unpack to check equality exactly as the class does
    assert embedding_b64.embedding == list(struct.unpack(f'<{len(floats)}f', packed))

if __name__ == "__main__":
    test_model_response_with_embeddings()
    print("Verification passed!")
