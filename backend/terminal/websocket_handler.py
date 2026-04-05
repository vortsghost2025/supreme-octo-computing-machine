"""
WebSocket handler for IDE terminal sessions.
Provides a single endpoint /terminal/ws/{session_id} that streams PTY output
and accepts input from the client.
"""

import json
import datetime
import asyncio
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi import Depends

# Import the existing terminal session storage utilities
from backend.main import terminal_sessions, _timeline_append

router = APIRouter()

class ConnectionManager:
    """Track active WebSocket connections per terminal session."""
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(session_id, []).append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_message(self, websocket: WebSocket, message: str) -> None:
        await websocket.send_text(message)

    async def broadcast(self, session_id: str, message: str) -> None:
        for ws in self.active_connections.get(session_id, []):
            await ws.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def terminal_ws(session_id: str, websocket: WebSocket):
    """WebSocket endpoint for a terminal session.
    Clients should first create a session via POST /terminal/sessions and then
    connect here using the returned session_id.
    """
    # Verify session exists
    session = terminal_sessions.get(session_id)
    if not session:
        await websocket.close(code=1008)
        raise HTTPException(status_code=404, detail="Terminal session not found")

    await manager.connect(session_id, websocket)
    proc = session.get("process")
    if not proc:
        await manager.disconnect(session_id, websocket)
        await websocket.close()
        raise HTTPException(status_code=400, detail="No process attached to session")

    # Helper coroutine to read stdout/stderr and forward to client
    async def read_output():
        try:
            while True:
                if proc.poll() is not None:
                    # Process ended – flush remaining output then break
                    remaining = await proc.stdout.read()
                    if remaining:
                        await manager.broadcast(session_id, json.dumps({"session_id": session_id, "type": "stdout", "data": remaining.decode(errors='replace')}))
                    break

                # Read a line from stdout with timeout to allow periodic stderr checks
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=0.5)
                except asyncio.TimeoutError:
                    line = b""
                if line:
                    await manager.broadcast(session_id, json.dumps({"session_id": session_id, "type": "stdout", "data": line.decode(errors='replace')}))

                # Read any available stderr data
                if proc.stderr.at_eof():
                    stderr_data = await proc.stderr.read()
                    if stderr_data:
                        await manager.broadcast(session_id, json.dumps({"session_id": session_id, "type": "stderr", "data": stderr_data.decode(errors='replace')}))
                else:
                    # Try non‑blocking read of a small chunk
                    try:
                        stderr_chunk = proc.stderr.read_nowait()
                    except Exception:
                        stderr_chunk = b""
                    if stderr_chunk:
                        await manager.broadcast(session_id, json.dumps({"session_id": session_id, "type": "stderr", "data": stderr_chunk.decode(errors='replace')}))
                await asyncio.sleep(0.01)
        finally:
            # Mark session ended and emit timeline event
            session["status"] = "ended"
            session["ended_at"] = datetime.datetime.utcnow().isoformat()
            await _timeline_append({
                "type": "terminal_session_ended",
                "session_id": session_id,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            })
            # Close all websockets for this session
            for ws in manager.active_connections.get(session_id, []):
                await ws.close()
            manager.active_connections.pop(session_id, None)

    # Start background task for reading output
    output_task = asyncio.create_task(read_output())

    try:
        while True:
            data = await websocket.receive_text()
            # Expect JSON messages with an "input" field
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            input_text = payload.get("input")
            if input_text is None:
                continue
            # Write to PTY stdin
            if proc.stdin:
                proc.stdin.write(input_text.encode())
                await proc.stdin.drain()
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    finally:
        output_task.cancel()
        try:
            await output_task
        except asyncio.CancelledError:
            pass
