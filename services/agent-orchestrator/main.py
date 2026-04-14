import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-orchestrator")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = {}
    agents: Optional[List[str]] = []

class PlanRequest(BaseModel):
    goal: str
    constraints: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME}

@app.post("/delegate")
async def delegate_task(req: TaskRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "task": req.task,
                "context": req.context or {},
                "agents": req.agents or []
            }
            async with session.post(f"{BACKEND_URL}/agent/run", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Backend task failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan")
async def create_plan(req: PlanRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "goal": req.goal,
                "constraints": req.constraints or {}
            }
            async with session.post(f"{BACKEND_URL}/agents/planner/plan", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Planning failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/swarm/status", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"status": "unknown"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["delegate", "plan", "orchestrate"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "delegate":
                            result = await delegate_task(TaskRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "delegate_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "plan":
                            result = await create_plan(PlanRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "plan_result",
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
