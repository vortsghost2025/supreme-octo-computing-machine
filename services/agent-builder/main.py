import os, asyncio, websockets
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

async def register():
    uri = "ws://kilo-gateway:3002"
    async with websockets.connect(uri) as ws:
        await ws.send({"type": "register", "name": os.getenv("AGENT_NAME", "agent-builder")})
        while True:
            await asyncio.sleep(30)

if __name__ == "__main__":
    import uvicorn
    loop = asyncio.get_event_loop()
    loop.create_task(register())
    uvicorn.run(app, host="0.0.0.0", port=8000)
