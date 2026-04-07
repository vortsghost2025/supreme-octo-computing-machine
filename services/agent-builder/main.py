import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-builder")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

artifacts_store = {}

class ArtifactRequest(BaseModel):
    artifact_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class CodeRequest(BaseModel):
    language: str
    prompt: str
    context: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME}

@app.post("/create")
async def create_artifact(req: ArtifactRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "artifact_type": req.artifact_type,
                "content": req.content,
                "metadata": req.metadata or {}
            }
            async with session.post(f"{BACKEND_URL}/agents/builder/create", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    artifact_id = result.get("artifact_id")
                    if artifact_id:
                        artifacts_store[artifact_id] = result
                    return result
                raise HTTPException(status_code=resp.status, detail="Artifact creation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artifact/{artifact_id}")
async def get_artifact(artifact_id: str):
    if artifact_id in artifacts_store:
        return artifacts_store[artifact_id]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/agents/builder/artifact/{artifact_id}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=404, detail="Artifact not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-code")
async def generate_code(req: CodeRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "language": req.language,
                "prompt": req.prompt,
                "context": req.context or {}
            }
            async with session.post(f"{BACKEND_URL}/agents/builder/generate", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Code generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artifacts")
async def list_artifacts():
    return {"artifacts": list(artifacts_store.values())}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["create", "generate-code", "artifacts"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "create_artifact":
                            result = await create_artifact(ArtifactRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "artifact_created",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "generate_code":
                            result = await generate_code(CodeRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "code_generated",
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
