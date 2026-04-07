import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

app = FastAPI()

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://we.taile9966e.ts.net:9001")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-nvidia")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

class InferenceRequest(BaseModel):
    model: str
    prompt: str
    options: Optional[Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    options: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME, "ollama": OLLAMA_BASE}

@app.get("/ready")
async def ready():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return {"ready": True, "ollama": OLLAMA_BASE}
                return {"ready": False}
    except Exception as e:
        return {"ready": False, "error": str(e)}

@app.post("/inference")
async def inference(req: InferenceRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": req.model,
                "prompt": req.prompt,
                "options": req.options or {},
                "stream": False
            }
            async with session.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "model": req.model,
                        "response": data.get("response", ""),
                        "done": data.get("done", True),
                        "context": data.get("context", [])
                    }
                raise HTTPException(status_code=resp.status, detail="Ollama inference failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": req.model,
                "messages": req.messages,
                "options": req.options or {},
                "stream": False
            }
            async with session.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "model": req.model,
                        "message": data.get("message", {}),
                        "done": data.get("done", True)
                    }
                raise HTTPException(status_code=resp.status, detail="Ollama chat failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"models": data.get("models", [])}
                return {"models": [], "error": "failed to fetch"}
    except Exception as e:
        return {"models": [], "error": str(e)}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["inference", "chat", "models", "gpu"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "inference":
                            result = await inference(InferenceRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "inference_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "chat":
                            result = await chat(ChatRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "chat_result",
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
