import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-azure-coordinator")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

deployments_store = {}

class DeployRequest(BaseModel):
    service_type: str
    config: Dict[str, Any]
    environment: Optional[str] = "development"

class ScaleRequest(BaseModel):
    deployment_id: str
    replicas: int

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME}

@app.post("/deploy")
async def deploy(req: DeployRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "service_type": req.service_type,
                "config": req.config,
                "environment": req.environment
            }
            async with session.post(f"{BACKEND_URL}/agents/operator/deploy", json=payload, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    deployment_id = result.get("deployment_id")
                    if deployment_id:
                        deployments_store[deployment_id] = result
                    return result
                raise HTTPException(status_code=resp.status, detail="Deployment failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scale")
async def scale(req: ScaleRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"replicas": req.replicas}
            async with session.post(f"{BACKEND_URL}/agents/operator/scale/{req.deployment_id}", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Scale failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    if deployment_id in deployments_store:
        return deployments_store[deployment_id]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/agents/operator/status/{deployment_id}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=404, detail="Deployment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/deployment/{deployment_id}")
async def delete_deployment(deployment_id: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{BACKEND_URL}/agents/operator/deployment/{deployment_id}", timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    if deployment_id in deployments_store:
                        del deployments_store[deployment_id]
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Delete failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deployments")
async def list_deployments():
    return {"deployments": list(deployments_store.values())}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["deploy", "scale", "status", "azure"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "deploy":
                            result = await deploy(DeployRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "deploy_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "scale":
                            result = await scale(ScaleRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "scale_result",
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
