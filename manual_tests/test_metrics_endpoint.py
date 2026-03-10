
import asyncio
import aiohttp
import json
import subprocess
import time
import os
import signal

SERVER_PORT = 8000
SERVER_URL = f"http://localhost:{SERVER_PORT}/metrics"

QUERY_JSON = {
    "view": "observations",
    "metrics": [{"measure": "count", "aggregation": "count"}, {"measure": "latency", "aggregation": "p50"}],
    "dimensions": [{"field": "providedModelName"}],
    "fromTimestamp": "2024-01-01T00:00:00Z",
    "toTimestamp": "2024-12-23T00:00:00Z"
}

async def run_test():
    server_process = subprocess.Popen(
        ["uvicorn", "tools.metrics_server:app", "--port", str(SERVER_PORT)],
        env=os.environ.copy()
    )
    
    print(f"Started server with PID {server_process.pid}")
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        for _ in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{SERVER_PORT}/docs") as resp:
                        if resp.status == 200:
                            print("Server is up!")
                            break
            except:
                time.sleep(1)
        else:
            print("Server failed to start in time.")
            return

        async with aiohttp.ClientSession() as session:
            # First request - should be a miss (or hit if run before)
            print("\nSending Request 1...")
            start_time = time.time()
            async with session.post(SERVER_URL, json=QUERY_JSON) as resp:
                print(f"Response Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print("Received data (truncated):", str(data)[:100])
                else:
                    text = await resp.text()
                    print(f"Error: {text}")
            duration1 = time.time() - start_time
            print(f"Request 1 took {duration1:.4f} seconds")

            # Second request - should be a hit (faster)
            print("\nSending Request 2 (Cache Test)...")
            start_time = time.time()
            async with session.post(SERVER_URL, json=QUERY_JSON) as resp:
                print(f"Response Status: {resp.status}")
            duration2 = time.time() - start_time
            print(f"Request 2 took {duration2:.4f} seconds")
            
            if duration2 < duration1:
                print("\nSUCCESS: Second request was faster, indicating caching is likely working.")
            else:
                print("\nWARNING: Second request was not significantly faster. Caching might not be effective or API is very fast.")

    finally:
        print("\nStopping server...")
        server_process.send_signal(signal.SIGTERM)
        server_process.wait()
        print("Server stopped.")

if __name__ == "__main__":
    asyncio.run(run_test())
