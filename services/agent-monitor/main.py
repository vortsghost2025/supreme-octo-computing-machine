import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI
from typing import Dict, Any
import psutil

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-monitor")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME}

@app.get("/metrics")
async def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
        "agents_registered": 6,
        "agent": AGENT_NAME
    }

@app.get("/system")
async def get_system_info():
    return {
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "platform": os.name,
        "agent": AGENT_NAME
    }

@app.get("/swarm")
async def get_swarm_status():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/swarm/status", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"status": "unknown"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/backend-health")
async def check_backend():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return {
                    "backend": "healthy" if resp.status == 200 else "unhealthy",
                    "status_code": resp.status
                }
    except Exception as e:
        return {"backend": "error", "error": str(e)}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["metrics", "system", "swarm", "health-check"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "get_metrics":
                            result = await get_metrics()
                            await ws.send(json.dumps({
                                "type": "metrics_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "health_check":
                            result = await check_backend()
                            await ws.send(json.dumps({
                                "type": "health_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                    except websockets.exceptions.ConnectionClosed:
                        break
                    except Exception as e:
                        print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Registration error: {e}, retrying in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    import uvicorn
    loop = asyncio.get_event_loop()
    loop.create_task(register())
    uvicorn.run(app, host="0.0.0.0", port=8000)
