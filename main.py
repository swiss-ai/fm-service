import json
from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse
from config import get_endpoint_by_model_name, get_all_available_models
from llm import proxy
app = FastAPI()

def data_generator(response, generation):
    for chunk in response:
        data = chunk.to_dict()
        if data.get("usage", None) is not None:
            generation.update(usage={
                "promptTokens": data["usage"]["prompt_tokens"],
                "completionTokens": data["usage"]["completion_tokens"],
            })
        yield f"data: {json.dumps(data)}\n\n"

@app.post("/v1/chat/completions", dependencies=[])
async def completion(request: Request):
    data = await request.json()
    target = await get_endpoint_by_model_name(data['model'])
    target = f"{target['url']}/v1/service/llm/v1"
    response = proxy(target, **data)
    if 'stream' in data and data['stream'] == True:
        return StreamingResponse(data_generator(response, response.generation), media_type='text/event-stream')
    return response

@app.get("/v1/models")
async def list_models():
    """List all available models in OpenAI format."""
    models = await get_all_available_models()
    model_objects = []
    
    for model in models:
        model_objects.append({
            "id": model.get("id", "unknown"),
            "object": "model",
            "created": model.get("created", 0),
            "owned_by": model.get("owned_by", "unknown")
        })
    
    return {
        "object": "list",
        "data": model_objects
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)