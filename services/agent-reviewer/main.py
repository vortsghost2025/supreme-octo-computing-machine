import os, asyncio, json, websockets, aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.getenv("AGENT_NAME", "agent-reviewer")
KILO_GATEWAY = os.getenv("KILO_GATEWAY", "ws://kilo-gateway:3002")

reviews_store = {}

class ReviewRequest(BaseModel):
    content: str
    review_type: str
    criteria: Optional[Dict[str, Any]] = {}

class ValidationRequest(BaseModel):
    code: str
    language: str
    rules: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_NAME}

@app.post("/validate")
async def validate(req: ValidationRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "code": req.code,
                "language": req.language,
                "rules": req.rules or {}
            }
            async with session.post(f"{BACKEND_URL}/agents/reviewer/validate", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    review_id = result.get("review_id")
                    if review_id:
                        reviews_store[review_id] = result
                    return result
                raise HTTPException(status_code=resp.status, detail="Validation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review")
async def review(req: ReviewRequest):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": req.content,
                "review_type": req.review_type,
                "criteria": req.criteria or {}
            }
            async with session.post(f"{BACKEND_URL}/agents/reviewer/review", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    review_id = result.get("review_id")
                    if review_id:
                        reviews_store[review_id] = result
                    return result
                raise HTTPException(status_code=resp.status, detail="Review failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result/{review_id}")
async def get_review_result(review_id: str):
    if review_id in reviews_store:
        return reviews_store[review_id]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/agents/reviewer/result/{review_id}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=404, detail="Review not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reviews")
async def list_reviews():
    return {"reviews": list(reviews_store.values())}

async def register():
    while True:
        try:
            async with websockets.connect(KILO_GATEWAY) as ws:
                await ws.send(json.dumps({
                    "type": "register",
                    "name": AGENT_NAME,
                    "capabilities": ["validate", "review", "quality-gate"]
                }))
                print(f"{AGENT_NAME} registered to kilo-gateway")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "name": AGENT_NAME}))
                        elif data.get("type") == "validate":
                            result = await validate(ValidationRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "validation_result",
                                "request_id": data.get("request_id"),
                                "result": result
                            }))
                        elif data.get("type") == "review":
                            result = await review(ReviewRequest(**data.get("payload", {})))
                            await ws.send(json.dumps({
                                "type": "review_result",
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
