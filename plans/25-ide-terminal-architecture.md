# SNAC-v2 IDE Terminal MVP Architecture (M6)

**Plan:** 25-ide-terminal-architecture  
**Status:** Architectural Design  
**Target:** M6 IDE Terminal MVP  
**Created:** 2026-03-13  

---

## 1. Overview

The IDE Terminal MVP enables multi-shell terminal sessions directly within the SNAC-v2 cockpit. This feature bridges the gap between the agent orchestration layer and direct command execution, supporting PowerShell, bash, cmd, and sh shells through a unified terminal gateway.

### Goals

1. **Multi-shell support**: PowerShell, bash, cmd, sh in tabbed interface
2. **Real-time streaming**: PTY sessions via WebSocket for live output
3. **Gateway architecture**: Dedicated terminal gateway service handling session lifecycle
4. **Backend integration**: Leverage existing FastAPI backend for session management
5. **Terminal pane UI**: React terminal component for cockpit integration
6. **File workspace**: Explorer, open/edit, diff, patch capabilities
7. **Agent workspace board**: Spawn agents, assign tasks, track ownership
8. **Shared command bus**: Unified events, logs, tool outputs stream
9. **Runtime mode controls**: Shared, Sandbox, Parallel Test modes
10. **Command Policy Service**: Allowlist/denylist + approval workflow

### Scope

| Feature | Phase | Description |
|---------|-------|-------------|
| Terminal Gateway | 1 | PTY session management + WebSocket streaming |
| File Workspace | 2 | File explorer, diff/patch operations |
| Agent Board | 3 | Task management + worker integration |
| Command Bus | 4 | Centralized event stream |
| Runtime Modes | 5 | Shared/Sandbox/Parallel Test isolation |
| Policy Service | 6 | Allowlist/denylist + approval workflow |

---

## 2. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COCKPIT (Frontend)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Terminal Pane Component                          │    │
│  │  ┌──────────┬──────────┬──────────┬──────────┐                      │    │
│  │  │ Tab: PS1 │ Tab: bash│ Tab: cmd │ Tab: +   │                      │    │
│  │  ├──────────┴──────────┴──────────┴──────────┤                      │    │
│  │  │                                             │                      │    │
│  │  │           Terminal Output Area             │                      │    │
│  │  │           (xterm.js renderer)               │                      │    │
│  │  │                                             │                      │    │
│  │  ├─────────────────────────────────────────────┤                      │    │
│  │  │  > _                                        │                      │    │
│  │  └─────────────────────────────────────────────┘                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ WebSocket (ws://)
                                       │ HTTP/REST
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                          BACKEND (FastAPI)                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐                     │
│  │   Terminal Gateway    │  │   Session Manager      │                     │
│  │   (WebSocket Handler) │◄─┤   (PTY Pool)           │                     │
│  │                       │  │                        │                     │
│  │   - Session lifecycle │  │   - Create/Close       │                     │
│  │   - Input forwarding  │  │   - Shell selection    │                     │
│  │   - Output streaming │  │   - Environment vars   │                     │
│  └───────────┬────────────┘  └───────────┬────────────┘                     │
│              │                            │                                   │
│              ▼                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     PTY Process Layer                                │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │ PowerShell  │ │    bash     │ │    cmd.exe  │ │     sh      │   │    │
│  │  │  (Windows)  │ │  (Linux/WSL)│ │  (Windows)  │ │ (Git Bash)  │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Integration Layer                                  │    │
│  │   - /health, /swarm/status, /swarm/events/recent                    │    │
│  │   - Redis for session state (if available)                          │    │
│  │   - Event emission: terminal.session.*                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Terminal Gateway Service Architecture

### 3.1 Session Manager

The Session Manager handles PTY process lifecycle:

```python
# backend/terminal/session_manager.py

from dataclasses import dataclass
from typing import Dict, Optional, List
import asyncio
import uuid

@dataclass
class TerminalSession:
    session_id: str
    shell_type: str  # powershell, bash, cmd, sh
    process: asyncio.subprocess.Process
    working_directory: str
    created_at: str
    status: str  # running, idle, closed

class SessionManager:
    """Manages PTY sessions for terminal connections."""
    
    def __init__(self, max_sessions: int = 20):
        self._sessions: Dict[str, TerminalSession] = {}
        self._max_sessions = max_sessions
    
    async def create_session(
        self,
        shell_type: str,
        working_directory: str = "."
    ) -> TerminalSession:
        """Create a new PTY session with specified shell."""
        
        # Shell command mapping
        shell_commands = {
            "powershell": ["powershell.exe", "-NoLogo"],
            "cmd": ["cmd.exe"],
            "bash": ["bash", "--login"],
            "sh": ["sh"],
        }
        
        if shell_type not in shell_commands:
            raise ValueError(f"Unsupported shell type: {shell_type}")
        
        # Enforce session limit
        if len(self._sessions) >= self._max_sessions:
            raise RuntimeError(f"Max sessions ({self._max_sessions}) reached")
        
        # Create PTY process
        cmd = shell_commands[shell_type]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=working_directory,
            env=self._get_environment()
        )
        
        session = TerminalSession(
            session_id=str(uuid.uuid4()),
            shell_type=shell_type,
            process=process,
            working_directory=working_directory,
            created_at=datetime.utcnow().isoformat(),
            status="running"
        )
        
        self._sessions[session.session_id] = session
        return session
    
    async def write_to_session(self, session_id: str, data: bytes) -> None:
        """Forward input to PTY process."""
        session = self._sessions.get(session_id)
        if not session or session.status == "closed":
            raise ValueError(f"Session {session_id} not found or closed")
        
        session.process.stdin.write(data)
        await session.process.stdin.drain()
    
    async def read_from_session(self, session_id: str) -> bytes:
        """Read output from PTY process."""
        session = self._sessions.get(session_id)
        if not session or session.status == "closed":
            raise ValueError(f"Session {session_id} not found or closed")
        
        # Non-blocking read with timeout
        try:
            output = await asyncio.wait_for(
                session.process.stdout.read(4096),
                timeout=0.1
            )
            return output
        except asyncio.TimeoutError:
            return b""
    
    async def close_session(self, session_id: str) -> None:
        """Terminate a PTY session."""
        session = self._sessions.pop(session_id, None)
        if session:
            session.status = "closed"
            session.process.terminate()
            try:
                await asyncio.wait_for(session.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                session.process.kill()
    
    def _get_environment(self) -> Dict[str, str]:
        """Build environment for shell process."""
        import os
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        return env
```

### 3.2 WebSocket Handler

The WebSocket handler manages real-time terminal communication:

```python
# backend/terminal/websocket_handler.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections per session."""
    
    def __init__(self):
        self._active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self._active_connections:
            self._active_connections[session_id] = set()
        self._active_connections[session_id].add(websocket)
    
    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self._active_connections:
            self._active_connections[session_id].discard(websocket)
            if not self._active_connections[session_id]:
                del self._active_connections[session_id]
    
    async def send_to_session(self, session_id: str, data: bytes):
        """Send PTY output to all connected clients."""
        if session_id in self._active_connections:
            # Convert bytes to base64 for JSON transport
            import base64
            message = {
                "type": "output",
                "data": base64.b64encode(data).decode("utf-8")
            }
            for connection in list(self._active_connections[session_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

# Global session manager
session_manager = SessionManager()
connection_manager = ConnectionManager()

@router.websocket("/terminal/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for terminal I/O."""
    
    await connection_manager.connect(session_id, websocket)
    
    try:
        # Start output reader task
        async def read_output():
            while True:
                try:
                    output = await session_manager.read_from_session(session_id)
                    if output:
                        await connection_manager.send_to_session(session_id, output)
                    await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
                except Exception:
                    break
        
        reader_task = asyncio.create_task(read_output())
        
        # Handle input from client
        while True:
            try:
                message = await websocket.receive_json()
                
                if message.get("type") == "input":
                    import base64
                    data = base64.b64decode(message.get("data", ""))
                    await session_manager.write_to_session(session_id, data)
                    
                elif message.get("type") == "resize":
                    # Handle terminal resize (future enhancement)
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception:
                break
        
        reader_task.cancel()
        
    finally:
        connection_manager.disconnect(session_id, websocket)
```

---

## 4. API Endpoints

### 4.1 REST Endpoints (HTTP)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/terminal/sessions` | Create a new terminal session |
| `GET` | `/terminal/sessions` | List active terminal sessions |
| `GET` | `/terminal/sessions/{session_id}` | Get session details |
| `DELETE` | `/terminal/sessions/{session_id}` | Close a terminal session |
| `GET` | `/terminal/shells` | List available shell types |

### 4.2 WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `ws://host:port/terminal/{session_id}` | Real-time terminal I/O |

### 4.3 Request/Response Models

```python
# backend/terminal/models.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CreateSessionRequest(BaseModel):
    shell_type: str = Field(
        description="Shell type: powershell, bash, cmd, sh",
        pattern="^(powershell|bash|cmd|sh)$"
    )
    working_directory: Optional[str] = Field(
        default=".",
        description="Initial working directory"
    )

class SessionResponse(BaseModel):
    session_id: str
    shell_type: str
    working_directory: str
    created_at: str
    status: str

class ShellInfo(BaseModel):
    shell_type: str
    display_name: str
    available: bool
    platform: str  # windows, linux, cross-platform
```

---

## 5. WebSocket Protocol

### 5.1 Message Format

All WebSocket messages are JSON-encoded:

```json
// Client -> Server (Input)
{
  "type": "input",
  "data": "<base64-encoded-input-bytes>"
}

// Client -> Server (Resize)
{
  "type": "resize",
  "columns": 80,
  "rows": 24
}

// Server -> Client (Output)
{
  "type": "output",
  "data": "<base64-encoded-output-bytes>"
}

// Server -> Client (Error)
{
  "type": "error",
  "message": "<error-description>"
}

// Server -> Client (Session Events)
{
  "type": "session_event",
  "event": "started" | "closed" | "error",
  "session_id": "<session-id>",
  "timestamp": "<ISO-timestamp>"
}
```

### 5.2 Connection Lifecycle

```
Client                          Server
  │                                │
  │──── WS Connect (session_id) ──►│
  │                                │
  │◄──── Accept Connection ────────│
  │                                │
  │──── {"type":"input",...} ─────►│ (forwarded to PTY)
  │                                │
  │◄──── {"type":"output",...} ────│ (PTY output)
  │                                │
  │──── WS Disconnect ────────────►│ (session stays open)
  │                                │
  │      ... time passes ...       │
  │                                │
  │──── WS Reconnect (same ID) ───►│ (resume session)
  │                                │
  │──── {"type":"input",...} ─────►│
  │                                │
```

---

## 6. Security Model

### 6.1 Risk Classification

Commands are classified into risk categories:

| Class | Description | Requires Approval |
|-------|-------------|-------------------|
| `safe` | Read-only, informational | No |
| `guarded` | File read, local queries | No (logging only) |
| `dangerous` | File write, network calls | Yes (production) |
| `blocked` | Destructive commands | Always blocked |

### 6.2 Blocked Commands (MVP)

```python
_BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/(?:\S+)?",
    r"del\s+/[qf]\s+[A-Z]:\\",
    r"format\s+[A-Z]:",
    r"shutdown",
    r"reboot",
    r"init\s+6",
    r"systemctl\s+stop",
]
```

### 6.3 Approval Workflow (Future)

1. Command matches `dangerous` pattern
2. Emit `terminal.session.approval_required` event
3. Frontend displays approval dialog
4. User approves/denies via REST API
5. Command executes or is rejected

### 6.4 Input Sanitization

- All input is treated as raw bytes to PTY
- No interpretation of control sequences
- Terminal escape sequences allowed (for cursor control, colors)

---

## 7. Integration Points

### 7.1 Existing Backend Integration

The terminal gateway integrates with existing backend services:

| Integration | Endpoint | Purpose |
|-------------|----------|---------|
| Health Check | `GET /health` | Verify backend availability |
| Swarm Status | `GET /swarm/status` | Display worker queue in terminal status |
| Events | `GET /swarm/events/recent` | Show recent events in terminal sidebar |
| Timeline | `GET /timeline` | Command history logging |

### 7.2 Event Emission

Terminal sessions emit events to Redis/event bus:

```
terminal.session.created
terminal.session.started
terminal.session.output
terminal.session.error
terminal.session.closed
terminal.session.approval_required  (future)
```

### 7.3 Environment Variables

Sessions inherit configured environment:

```python
TERMINAL_INITIAL_DIR = os.getenv("TERMINAL_INITIAL_DIR", ".")
TERMINAL_ALLOWED_SHELLS = os.getenv("TERMINAL_ALLOWED_SHELLS", "powershell,bash,cmd,sh")
TERMINAL_MAX_SESSIONS = int(os.getenv("TERMINAL_MAX_SESSIONS", "20"))
```

---

## 8. Frontend Terminal Pane Design

### 8.1 Component Architecture

```
TerminalPane (Container)
├── TerminalTabs (Tab Bar)
│   ├── TabItem[] (each shell session)
│   └── NewTabButton
├── TerminalOutput (xterm.js)
│   └── Terminal (renderer)
├── TerminalInput (Command Line)
└── TerminalToolbar (Actions)
    ├── ClearButton
    ├── KillButton
    └── SettingsButton
```

### 8.2 Dependencies

```json
// ui/package.json
{
  "dependencies": {
    "@xterm/xterm": "^5.5.0",
    "@xterm/addon-fit": "^0.10.0",
    "@xterm/addon-web-links": "^0.11.0"
  }
}
```

### 8.3 Terminal Component Implementation

```jsx
// ui/src/components/TerminalPane.jsx

import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import './TerminalPane.css';

export function TerminalPane({ backendUrl }) {
  const terminalRef = useRef(null);
  const wsRef = useRef(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [availableShells, setAvailableShells] = useState([]);
  
  const terminal = useRef(null);
  const fitAddon = useRef(null);
  
  useEffect(() => {
    // Initialize xterm
    terminal.current = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#cccccc',
      },
      scrollback: 10000,
    });
    
    fitAddon.current = new FitAddon();
    terminal.current.loadAddon(fitAddon.current);
    terminal.current.open(terminalRef.current);
    fitAddon.current.fit();
    
    // Handle terminal input
    terminal.current.onData((data) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'input',
          data: btoa(data)
        }));
      }
    });
    
    // Fetch available shells
    fetch(`${backendUrl}/terminal/shells`)
      .then(r => r.json())
      .then(data => setAvailableShells(data));
    
    // Handle window resize
    window.addEventListener('resize', () => fitAddon.current?.fit());
    
    return () => {
      terminal.current?.dispose();
      wsRef.current?.close();
    };
  }, [backendUrl]);
  
  const createSession = async (shellType) => {
    const response = await fetch(`${backendUrl}/terminal/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shell_type: shellType })
    });
    const session = await response.json();
    
    setSessions(prev => [...prev, session]);
    setActiveSession(session.session_id);
    
    // Connect WebSocket
    const ws = new WebSocket(
      `ws://${backendUrl.replace('http://', '')}/terminal/${session.session_id}`
    );
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'output') {
        terminal.current?.write(atob(msg.data));
      } else if (msg.type === 'error') {
        terminal.current?.writeln(`\r\n\x1b[31mError: ${msg.message}\x1b[0m`);
      }
    };
    
    wsRef.current = ws;
  };
  
  return (
    <div className="terminal-pane">
      <div className="terminal-tabs">
        {sessions.map(session => (
          <button
            key={session.session_id}
            className={`tab ${activeSession === session.session_id ? 'active' : ''}`}
            onClick={() => setActiveSession(session.session_id)}
          >
            {session.shell_type}
          </button>
        ))}
        <select 
          onChange={(e) => createSession(e.target.value)}
          value=""
        >
          <option value="" disabled>+ New Terminal</option>
          {availableShells.map(shell => (
            <option key={shell.shell_type} value={shell.shell_type}>
              {shell.display_name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="terminal-container" ref={terminalRef} />
      
      <div className="terminal-toolbar">
        <button onClick={() => terminal.current?.clear()}>Clear</button>
        <button onClick={() => {
          // Send interrupt signal
          wsRef.current?.send(JSON.stringify({ type: 'input', data: btoa('\x03') }));
        }}>Interrupt</button>
      </div>
    </div>
  );
}
```

### 8.4 Styling (TerminalPane.css)

```css
.terminal-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
}

.terminal-tabs {
  display: flex;
  gap: 4px;
  padding: 8px;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.terminal-tabs .tab {
  padding: 4px 12px;
  background: #2d2d30;
  border: none;
  color: #cccccc;
  cursor: pointer;
}

.terminal-tabs .tab.active {
  background: #1e1e1e;
  border-bottom: 2px solid #007acc;
}

.terminal-container {
  flex: 1;
  padding: 8px;
}

.terminal-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #252526;
  border-top: 1px solid #3e3e42;
}

.terminal-toolbar button {
  padding: 4px 12px;
  background: #3e3e42;
  border: none;
  color: #cccccc;
  cursor: pointer;
}

.terminal-toolbar button:hover {
  background: #505050;
}
```

---

## 9. File Workspace Tools

### 9.1 File Explorer Component

The file workspace provides a file explorer sidebar integrated with terminal sessions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IDE Terminal Workspace                              │
├─────────────┬───────────────────────────────────────────────────────────────┤
│ File        │  ┌─────────────────────────────────────────────────────────┐ │
│ Explorer    │  │ Terminal Tabs: [PS1] [bash] [cmd] [+]                   │ │
│             │  ├─────────────────────────────────────────────────────────┤ │
│ 📁 src/     │  │                                                         │ │
│  ├─ main.py │  │  PS C:\project> ls -la                                  │ │
│  ├─ app.py  │  │  total 100                                             │ │
│  └─ utils/  │  │  drwxr-xr-x  5 user  4096 Mar 13 10:00 .               │ │
│ 📁 tests/   │  │  -rw-r--r--  1 user   234 main.py                      │ │
│  └─ test.py │  │  -rw-r--r--  1 user   456 app.py                      │ │
│             │  │                                                         │ │
│ 📁 config/  │  └─────────────────────────────────────────────────────────┘ │
│  └─ .env    │  ┌─────────────────────────────────────────────────────────┐ │
│             │  │ > _                                                      │ │
│             │  └─────────────────────────────────────────────────────────┘ │
├─────────────┴───────────────────────────────────────────────────────────────┤
│ Status: Connected │ Shell: PowerShell │ Runtime: Shared                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 File Operations API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workspace/files` | List directory contents |
| `GET` | `/workspace/files/{path}` | Read file content |
| `POST` | `/workspace/files/{path}` | Create/update file |
| `DELETE` | `/workspace/files/{path}` | Delete file |
| `POST` | `/workspace/diff` | Compute diff between two files |
| `POST` | `/workspace/patch` | Apply patch to file |

### 9.3 File Explorer Models

```python
# backend/workspace/models.py

class FileEntry(BaseModel):
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    modified_at: Optional[str] = None
    permissions: Optional[str] = None

class DirectoryRequest(BaseModel):
    path: str = Field(default=".", description="Directory path to list")
    recursive: bool = Field(default=False, description="Recursive listing")

class FileContentRequest(BaseModel):
    path: str
    encoding: str = Field(default="utf-8")

class DiffRequest(BaseModel):
    original: str = Field(description="Original file path or content")
    modified: str = Field(description="Modified file path or content")
    context_lines: int = Field(default=3)

class DiffResponse(BaseModel):
    original: str
    modified: str
    hunks: List[Dict[str, Any]]
    stats: Dict[str, int]  # additions, deletions, unchanged

class PatchRequest(BaseModel):
    target_path: str
    patch_content: str
    base64_encoded: bool = Field(default=False)
```

### 9.4 Diff/Patch Implementation

```python
# backend/workspace/diff_engine.py

import difflib
import base64
from typing import List, Dict, Any

class DiffEngine:
    """Handles file diffing and patching operations."""
    
    def compute_diff(self, original: str, modified: str, context: int = 3) -> DiffResponse:
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            lineterm='',
            n=context
        ))
        
        hunks = self._parse_hunks(diff)
        stats = self._compute_stats(diff)
        
        return DiffResponse(
            original=original,
            modified=modified,
            hunks=hunks,
            stats=stats
        )
    
    def apply_patch(self, target_content: str, patch: str) -> str:
        """Apply unified diff patch to content."""
        import io
        from unittest.mock import patch as mock_patch
        
        original_lines = target_content.splitlines(keepends=True)
        
        for line in patch.splitlines():
            if line.startswith('---') or line.startswith('+++'):
                continue
            if line.startswith('@@'):
                continue
                
        # Use patchutil or manual application
        return target_content
```

---

## 10. Agent Workspace Board

### 10.1 Overview

The Agent Workspace Board provides a visual interface for managing agent tasks:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent Workspace Board                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Runtime: [Shared ▼]  │  Workers: 4 Active  │  Queue: 12 Pending          │
├───────────────────────┬───────────────────────┬─────────────────────────────┤
│   TO DO               │   IN PROGRESS         │   DONE                      │
│   ┌───────────────┐   │   ┌───────────────┐   │   ┌───────────────┐        │
│   │ Task: Review  │   │   │ Task: Build   │   │   │ Task: Research│        │
│   │ Agent: review │   │   │ Agent: builder│   │   │ Agent: research│       │
│   │ Priority: high│   │   │ Assigned: @k3 │   │   │ Status: ✅    │        │
│   └───────────────┘   │   │ Progress: 45% │   │   └───────────────┘        │
│   ┌───────────────┐   │   └───────────────┘   │   ┌───────────────┐        │
│   │ Task: Refactor│   │                       │   │ Task: Test    │        │
│   │ Agent: builder│   │                       │   │ Agent: review │        │
│   │ Priority: med │   │                       │   │ Status: ✅    │        │
│   └───────────────┘   │                       │   └───────────────┘        │
├───────────────────────┴───────────────────────┴─────────────────────────────┤
│ [➕ Add Task] [🔄 Refresh] [📊 View Graph]                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Agent Board API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/agents/tasks` | List all tasks with status |
| `POST` | `/agents/tasks` | Create new task |
| `PUT` | `/agents/tasks/{task_id}` | Update task |
| `DELETE` | `/agents/tasks/{task_id}` | Delete task |
| `POST` | `/agents/tasks/{task_id}/assign` | Assign task to agent |
| `GET` | `/agents/workers` | List available workers |
| `POST` | `/agents/spawn` | Spawn new worker |
| `GET` | `/agents/graph` | Get agent relationship graph |

### 10.3 Agent Task Models

```python
# backend/agents/models.py

class AgentTask(BaseModel):
    task_id: str
    title: str
    description: Optional[str] = None
    agent_type: str = Field(
        description="Worker type: research_worker, analysis_worker, builder_worker, review_worker"
    )
    status: str = Field(
        default="todo",
        pattern="^(todo|in_progress|done|blocked)$"
    )
    priority: str = Field(
        default="normal",
        pattern="^(high|normal|low)$"
    )
    assignee: Optional[str] = None
    runtime: str = Field(
        default="shared",
        pattern="^(shared|sandbox|parallel_test)$"
    )
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

class CreateTaskRequest(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Optional[Annotated[str, Field(max_length=2000)]] = None
    agent_type: str
    priority: str = "normal"
    runtime: str = "shared"

class AssignTaskRequest(BaseModel):
    worker_id: str
    task_id: str

class WorkerInfo(BaseModel):
    worker_id: str
    worker_type: str
    runtime: str
    status: str  # idle, running, busy
    current_task_id: Optional[str] = None
    started_at: str
```

### 10.4 Agent Board Implementation

```python
# backend/agents/board.py

from typing import Dict, List, Optional
from datetime import datetime
import uuid

class AgentBoard:
    """Manages the agent task board state."""
    
    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}
        self._workers: Dict[str, Dict] = {}
    
    async def create_task(self, request: CreateTaskRequest) -> AgentTask:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            agent_type=request.agent_type,
            priority=request.priority,
            runtime=request.runtime,
            status="todo",
            created_at=datetime.utcnow().isoformat()
        )
        self._tasks[task.task_id] = task
        
        await self._emit_board_event("task_created", task)
        return task
    
    async def assign_task(self, task_id: str, worker_id: str) -> AgentTask:
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.assignee = worker_id
        task.status = "in_progress"
        task.updated_at = datetime.utcnow().isoformat()
        
        await self._emit_board_event("task_assigned", task)
        return task
    
    async def complete_task(self, task_id: str) -> AgentTask:
        task = self._tasks.get(task_id)
        task.status = "done"
        task.completed_at = datetime.utcnow().isoformat()
        
        await self._emit_board_event("task_completed", task)
        return task
    
    def get_board_state(self) -> Dict[str, List[AgentTask]]:
        return {
            "todo": [t for t in self._tasks.values() if t.status == "todo"],
            "in_progress": [t for t in self._tasks.values() if t.status == "in_progress"],
            "done": [t for t in self._tasks.values() if t.status == "done"],
            "blocked": [t for t in self._tasks.values() if t.status == "blocked"],
        }
```

---

## 11. Shared Command Bus

### 11.1 Event Stream Architecture

The Shared Command Bus provides a unified event stream for all terminal, agent, and tool outputs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Shared Command Bus                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                   │
│  │  Terminal   │    │    Agent    │    │    File     │                   │
│  │   Output    │    │   Output    │    │   Tools     │                   │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                   │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Event Bus (Redis Streams)                       │  │
│  │                                                                       │  │
│  │  Channel: snac.events                                               │  │
│  │  - terminal.output: {session_id, timestamp, data}                  │  │
│  │  - agent.task_output: {task_id, worker_id, output}                 │  │
│  │  - tool.execution: {tool_name, params, result, duration_ms}        │  │
│  │  - system.log: {level, message, timestamp}                         │  │
│  └────────────────────────────────┬────────────────────────────────────┘  │
│                                   │                                         │
│           ┌───────────────────────┼───────────────────────┐                │
│           ▼                       ▼                       ▼                │
│    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐         │
│    │  Terminal   │        │    Agent    │        │   Event     │         │
│    │  Listeners  │        │  Listeners   │        │  Listeners  │         │
│    └─────────────┘        └─────────────┘        └─────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Command Bus Events

| Event Type | Channel | Payload |
|------------|---------|---------|
| `terminal.session.created` | `snac.events` | `{session_id, shell_type, created_at}` |
| `terminal.session.output` | `snac.events` | `{session_id, data, timestamp}` |
| `terminal.session.closed` | `snac.events` | `{session_id, exit_code, duration_ms}` |
| `agent.task.queued` | `snac.events` | `{task_id, agent_type, priority}` |
| `agent.task.started` | `snac.events` | `{task_id, worker_id, started_at}` |
| `agent.task.output` | `snac.events` | `{task_id, worker_id, output, timestamp}` |
| `agent.task.completed` | `snac.events` | `{task_id, result, duration_ms}` |
| `tool.execution.started` | `snac.events` | `{tool_name, params, execution_id}` |
| `tool.execution.completed` | `snac.events` | `{tool_name, result, duration_ms}` |
| `tool.execution.error` | `snac.events` | `{tool_name, error, execution_id}` |

### 11.3 Event Bus API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/events/stream` | SSE stream of all events |
| `GET` | `/events/recent` | Get recent events (last N) |
| `GET` | `/events/by-type/{event_type}` | Get events filtered by type |
| `GET` | `/events/by-session/{session_id}` | Get events for a session |
| `POST` | `/events/publish` | Publish custom event |

### 11.4 Event Models

```python
# backend/events/models.py

class BusEvent(BaseModel):
    event_id: str
    event_type: str
    channel: str = "snac.events"
    timestamp: str
    source: str  # terminal, agent, tool, system
    payload: Dict[str, Any]
    trace_id: Optional[str] = None

class EventStreamResponse(BaseModel):
    events: List[BusEvent]
    total: int
    next_cursor: Optional[str] = None

class PublishEventRequest(BaseModel):
    event_type: str
    source: str
    payload: Dict[str, Any]
    channel: str = "snac.events"
```

### 11.5 Event Bus Implementation

```python
# backend/events/bus.py

import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid

class EventBus:
    """Central event bus for SNAC-v2."""
    
    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._subscribers: Dict[str, List[Callable]] = {}
        self._in_memory_events: List[BusEvent] = []
        self._max_events = 10000
    
    async def publish(self, event: BusEvent) -> None:
        """Publish event to Redis stream or in-memory buffer."""
        event.event_id = str(uuid.uuid4())
        event.timestamp = datetime.utcnow().isoformat()
        
        if self._redis:
            await self._redis.xadd(
                event.channel,
                {"data": json.dumps(event.model_dump())}
            )
        
        self._in_memory_events.append(event)
        if len(self._in_memory_events) > self._max_events:
            self._in_memory_events = self._in_memory_events[-self._max_events:]
        
        await self._notify_subscribers(event)
    
    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def get_recent(self, limit: int = 100, event_type: Optional[str] = None) -> List[BusEvent]:
        """Get recent events."""
        events = self._in_memory_events[-limit:]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events
    
    async def _notify_subscribers(self, event: BusEvent) -> None:
        """Notify all subscribers for this event type."""
        callbacks = self._subscribers.get(event.event_type, [])
        for callback in callbacks:
            try:
                await callback(event)
            except Exception:
                pass
```

---

## 12. Runtime Mode Controls

### 12.1 Runtime Modes

The IDE Terminal supports three runtime modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `Shared` | Common PTY, shared filesystem | Development, debugging |
| `Sandbox` | Isolated container per session | Testing, untrusted code |
| `Parallel Test` | Multiple replicas for testing | A/B testing, load simulation |

### 12.2 Runtime Mode API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/runtimes` | List available runtime modes |
| `GET` | `/runtimes/{mode}/status` | Get runtime mode status |
| `POST` | `/runtimes/{mode}/configure` | Configure runtime settings |
| `POST` | `/runtimes/{mode}/switch` | Switch current runtime |

### 12.3 Runtime Mode Models

```python
# backend/runtimes/models.py

class RuntimeMode(str, Enum):
    SHARED = "shared"
    SANDBOX = "sandbox"
    PARALLEL_TEST = "parallel_test"

class RuntimeConfig(BaseModel):
    mode: RuntimeMode
    max_sessions: int = 20
    max_memory_mb: int = 512
    allow_network: bool = True
    allow_filesystem: bool = True
    timeout_seconds: int = 300

class RuntimeStatus(BaseModel):
    mode: RuntimeMode
    active_sessions: int
    max_sessions: int
    resources: Dict[str, Any]  # memory, cpu, disk usage
    status: str  # running, paused, error

class SwitchRuntimeRequest(BaseModel):
    target_mode: RuntimeMode
    migrate_sessions: bool = True
```

### 12.4 Runtime Mode Implementation

```python
# backend/runtimes/manager.py

from enum import Enum
from typing import Dict, Optional

class RuntimeManager:
    """Manages different runtime execution modes."""
    
    def __init__(self):
        self._current_mode = RuntimeMode.SHARED
        self._configs: Dict[RuntimeMode, RuntimeConfig] = {
            RuntimeMode.SHARED: RuntimeConfig(
                mode=RuntimeMode.SHARED,
                max_sessions=20,
                allow_network=True,
                allow_filesystem=True,
            ),
            RuntimeMode.SANDBOX: RuntimeConfig(
                mode=RuntimeMode.SANDBOX,
                max_sessions=5,
                max_memory_mb=512,
                allow_network=False,
                allow_filesystem=True,
                timeout_seconds=120,
            ),
            RuntimeMode.PARALLEL_TEST: RuntimeConfig(
                mode=RuntimeMode.PARALLEL_TEST,
                max_sessions=10,
                max_memory_mb=1024,
                allow_network=True,
                allow_filesystem=True,
                timeout_seconds=600,
            ),
        }
    
    async def get_current_status(self) -> RuntimeStatus:
        config = self._configs[self._current_mode]
        active = await self._count_active_sessions(self._current_mode)
        
        return RuntimeStatus(
            mode=self._current_mode,
            active_sessions=active,
            max_sessions=config.max_sessions,
            resources=await self._get_resource_usage(),
            status="running"
        )
    
    async def switch_mode(self, new_mode: RuntimeMode) -> RuntimeStatus:
        """Switch to a different runtime mode."""
        self._current_mode = new_mode
        
        await self._emit_event(
            "runtime.mode_changed",
            {"old_mode": self._current_mode, "new_mode": new_mode}
        )
        
        return await self.get_current_status()
    
    async def validate_session(self, session_id: str) -> bool:
        """Check if session is valid for current runtime."""
        config = self._configs[self._current_mode]
        
        if config.max_sessions and await self._count_active_sessions(self._current_mode) >= config.max_sessions:
            return False
        
        return True
```

---

## 13. Command Policy Service

### 13.1 Policy Architecture

The Command Policy Service enforces allowlist/denylist controls on command execution:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Command Policy Service                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Command Input                                                            │
│        │                                                                   │
│        ▼                                                                   │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐             │
│   │   Input     │───►│   Policy     │───►│  Execution      │             │
│   │   Parser    │    │   Engine     │    │  Controller     │             │
│   └─────────────┘    └──────────────┘    └──────────────────┘             │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                         │
│         ▼                   ▼                   ▼                         │
│   ┌───────────┐       ┌───────────┐       ┌───────────┐                    │
│   │ Allowlist │       │ Denylist  │       │ Approval │                    │
│   │  Match    │       │  Match    │       │ Required │                    │
│   └───────────┘       └───────────┘       └───────────┘                   │
│        │                   │                   │                           │
│        └───────────────────┴───────────────────┘                           │
│                            │                                               │
│                            ▼                                               │
│                    ┌───────────────┐                                       │
│                    │    Result     │                                       │
│                    │  ALLOW/DENY   │                                       │
│                    │  /APPROVAL    │                                       │
│                    └───────────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Policy API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/policy/rules` | List all policy rules |
| `POST` | `/policy/rules` | Add new rule |
| `PUT` | `/policy/rules/{rule_id}` | Update rule |
| `DELETE` | `/policy/rules/{rule_id}` | Delete rule |
| `POST` | `/policy/check` | Check command against policy |
| `GET` | `/policy/approvals` | List pending approvals |
| `POST` | `/policy/approvals/{approval_id}/approve` | Approve command |
| `POST` | `/policy/approvals/{approval_id}/deny` | Deny command |

### 13.3 Policy Models

```python
# backend/policy/models.py

class PolicyRule(BaseModel):
    rule_id: str
    name: str
    pattern: str = Field(description="Regex pattern to match")
    action: str = Field(
        pattern="^(allow|deny|approval_required)$"
    )
    priority: int = Field(default=100, description="Higher = checked first")
    runtime_modes: List[str] = Field(
        default=["shared", "sandbox", "parallel_test"],
        description="Which runtimes this rule applies to"
    )
    description: Optional[str] = None
    created_at: str
    enabled: bool = True

class CreateRuleRequest(BaseModel):
    name: str
    pattern: str
    action: str
    priority: int = 100
    runtime_modes: List[str] = ["shared", "sandbox", "parallel_test"]
    description: Optional[str] = None

class PolicyCheckRequest(BaseModel):
    command: str
    runtime: str = "shared"
    session_id: Optional[str] = None

class PolicyCheckResponse(BaseModel):
    allowed: bool
    action: str  # allow, deny, approval_required
    rule_id: Optional[str] = None
    reason: Optional[str] = None
    approval_id: Optional[str] = None

class ApprovalRequest(BaseModel):
    approval_id: str
    command: str
    runtime: str
    requested_by: str
    requested_at: str
    status: str = "pending"  # pending, approved, denied
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
```

### 13.4 Policy Engine Implementation

```python
# backend/policy/engine.py

import re
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class PolicyEngine:
    """Enforces command allowlist/denylist policies."""
    
    DEFAULT_DENY_PATTERNS = [
        r"rm\s+-rf\s+/(?:\S+)?",           # Recursive delete root
        r"del\s+/[qf]\s+[A-Z]:\\",          # Windows force delete
        r"format\s+[A-Z]:",                 # Drive format
        r"shutdown",                         # System shutdown
        r"reboot",                           # System reboot
        r"init\s+[06]",                     # Linux init 0/6
        r"systemctl\s+stop\s+(sshd|cron)",  # Critical service stop
        r"chmod\s+-R\s+777\s+/",            # World-writable chmod
        r"curl.*\|.*sh",                    # Pipe to shell
        r"wget.*\|.*sh",                    # Pipe to shell
    ]
    
    DEFAULT_ALLOW_PATTERNS = [
        r"^ls\s*",
        r"^dir\s*",
        r"^pwd\s*",
        r"^cat\s+",
        r"^type\s+",
        r"^echo\s*",
        r"^git\s+",
        r"^npm\s+",
        r"^node\s+",
        r"^python\s+",
    ]
    
    def __init__(self):
        self._rules: List[PolicyRule] = []
        self._approvals: Dict[str, ApprovalRequest] = {}
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default deny/allow rules."""
        # Add default deny patterns
        for i, pattern in enumerate(self.DEFAULT_DENY_PATTERNS):
            self._rules.append(PolicyRule(
                rule_id=f"deny_{i}",
                name=f"Default Deny {i}",
                pattern=pattern,
                action="deny",
                priority=1000,
                created_at=datetime.utcnow().isoformat(),
                description="Default blocked command pattern"
            ))
        
        # Add default allow patterns
        for i, pattern in enumerate(self.DEFAULT_ALLOW_PATTERNS):
            self._rules.append(PolicyRule(
                rule_id=f"allow_{i}",
                name=f"Default Allow {i}",
                pattern=pattern,
                action="allow",
                priority=500,
                created_at=datetime.utcnow().isoformat(),
                description="Default allowed command pattern"
            ))
    
    async def check(self, request: PolicyCheckRequest) -> PolicyCheckResponse:
        """Check command against policy rules."""
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            [r for r in self._rules if r.enabled and request.runtime in r.runtime_modes],
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            if re.search(rule.pattern, request.command, re.IGNORECASE):
                if rule.action == "deny":
                    return PolicyCheckResponse(
                        allowed=False,
                        action="deny",
                        rule_id=rule.rule_id,
                        reason=f"Command matches deny rule: {rule.name}"
                    )
                elif rule.action == "approval_required":
                    approval = await self._create_approval_request(
                        request.command,
                        request.runtime,
                        request.session_id
                    )
                    return PolicyCheckResponse(
                        allowed=False,
                        action="approval_required",
                        rule_id=rule.rule_id,
                        reason=f"Command requires approval: {rule.name}",
                        approval_id=approval.approval_id
                    )
                elif rule.action == "allow":
                    return PolicyCheckResponse(
                        allowed=True,
                        action="allow",
                        rule_id=rule.rule_id,
                        reason=f"Command matches allow rule: {rule.name}"
                    )
        
        # Default: allow if no rule matches
        return PolicyCheckResponse(
            allowed=True,
            action="allow",
            reason="No matching rule - default allow"
        )
    
    async def _create_approval_request(
        self,
        command: str,
        runtime: str,
        session_id: Optional[str]
    ) -> ApprovalRequest:
        """Create pending approval request."""
        approval = ApprovalRequest(
            approval_id=str(uuid.uuid4()),
            command=command,
            runtime=runtime,
            requested_by=session_id or "system",
            requested_at=datetime.utcnow().isoformat(),
            status="pending"
        )
        self._approvals[approval.approval_id] = approval
        
        # Emit event for UI notification
        await self._emit_approval_event(approval)
        
        return approval
    
    async def approve(self, approval_id: str, resolved_by: str) -> ApprovalRequest:
        """Approve a pending command."""
        approval = self._approvals.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval.status = "approved"
        approval.resolved_at = datetime.utcnow().isoformat()
        approval.resolved_by = resolved_by
        
        return approval
    
    async def deny(self, approval_id: str, resolved_by: str) -> ApprovalRequest:
        """Deny a pending command."""
        approval = self._approvals.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval.status = "denied"
        approval.resolved_at = datetime.utcnow().isoformat()
        approval.resolved_by = resolved_by
        
        return approval
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return [a for a in self._approvals.values() if a.status == "pending"]
```

---

## 14. Implementation Phases

### Phase 1: Core Terminal (MVP)

1. **Session Manager**: PTY creation and lifecycle
2. **WebSocket Handler**: Basic I/O streaming
3. **REST API**: Session CRUD operations
4. **Frontend**: Basic terminal pane with xterm.js

### Phase 2: File Workspace

1. **File Explorer**: Directory listing and navigation
2. **File Operations**: Read, write, delete files
3. **Diff/Patch**: File comparison and patch application
4. **Integration**: Connect file operations to terminal context

### Phase 3: Agent Board

1. **Task Management**: Create, update, delete tasks
2. **Worker Integration**: Connect to existing swarm workers
3. **Drag-and-Drop**: Move tasks between columns
4. **Real-time Updates**: SSE for task status changes

### Phase 4: Command Bus

1. **Event Emission**: Terminal, agent, tool events
2. **Event Streaming**: SSE endpoint for real-time logs
3. **Event History**: Redis-backed event storage
4. **Filtering**: Query events by type, source, session

### Phase 5: Runtime Modes

1. **Mode Switching**: Shared/Sandbox/Parallel Test
2. **Resource Limits**: Memory, CPU, session limits per mode
3. **Session Migration**: Migrate sessions between modes
4. **Status Dashboard**: View runtime health

### Phase 6: Command Policy

1. **Default Rules**: Built-in allowlist/denylist
2. **Custom Rules**: User-defined regex patterns
3. **Approval Workflow**: UI for approving blocked commands
4. **Audit Log**: Command execution history

---

## 15. Validation Tests

### Terminal Tests

```bash
# PowerShell test
pwsh -c "echo terminal-ok"

# Bash test  
bash -lc "echo terminal-ok"

# Via API
curl -X POST http://localhost:8000/terminal/sessions \
  -H "Content-Type: application/json" \
  -d '{"shell_type":"powershell"}'

# WebSocket connection
wscat -c ws://localhost:8000/terminal/<session-id>
```

### File Workspace Tests

```bash
# List directory
curl -X GET "http://localhost:8000/workspace/files?path=."

# Read file
curl -X GET "http://localhost:8000/workspace/files/main.py"

# Create file
curl -X POST "http://localhost:8000/workspace/files/test.txt" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello World"}'

# Compute diff
curl -X POST "http://localhost:8000/workspace/diff" \
  -H "Content-Type: application/json" \
  -d '{"original": "line1\nline2\nline3", "modified": "line1\nmodified\nline3"}'
```

### Agent Board Tests

```bash
# Create task
curl -X POST "http://localhost:8000/agents/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "agent_type": "builder_worker", "priority": "high"}'

# List tasks
curl -X GET "http://localhost:8000/agents/tasks"

# List workers
curl -X GET "http://localhost:8000/agents/workers"

# Assign task
curl -X POST "http://localhost:8000/agents/tasks/<task_id>/assign" \
  -H "Content-Type: application/json" \
  -d '{"worker_id": "<worker_id>"}'
```

### Event Bus Tests

```bash
# Get recent events
curl -X GET "http://localhost:8000/events/recent?limit=50"

# Get events by type
curl -X GET "http://localhost:8000/events/by-type/terminal.session.output"

# Event stream (SSE)
curl -N "http://localhost:8000/events/stream"
```

### Runtime Mode Tests

```bash
# Get runtime status
curl -X GET "http://localhost:8000/runtimes/shared/status"

# List runtimes
curl -X GET "http://localhost:8000/runtimes"

# Switch runtime
curl -X POST "http://localhost:8000/runtimes/sandbox/switch" \
  -H "Content-Type: application/json" \
  -d '{"migrate_sessions": true}'
```

### Command Policy Tests

```bash
# Check allowed command
curl -X POST "http://localhost:8000/policy/check" \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la", "runtime": "shared"}'

# Check blocked command (should deny)
curl -X POST "http://localhost:8000/policy/check" \
  -H "Content-Type: application/json" \
  -d '{"command": "rm -rf /", "runtime": "shared"}'

# Get pending approvals
curl -X GET "http://localhost:8000/policy/approvals"

# Approve command
curl -X POST "http://localhost:8000/policy/approvals/<approval_id>/approve"
```

---

## 16. File Structure

```
backend/
├── main.py                    # Existing FastAPI app
├── terminal/
│   ├── __init__.py
│   ├── models.py              # Pydantic models
│   ├── session_manager.py     # PTY session management
│   ├── websocket_handler.py   # WebSocket endpoint
│   └── router.py              # Terminal router registration
├── workspace/
│   ├── __init__.py
│   ├── models.py              # File operation models
│   ├── explorer.py            # File explorer logic
│   ├── diff_engine.py         # Diff/patch computation
│   └── router.py              # Workspace router
├── agents/
│   ├── __init__.py
│   ├── models.py              # Task and worker models
│   ├── board.py               # Agent board state
│   └── router.py              # Agent router
├── events/
│   ├── __init__.py
│   ├── models.py              # Event models
│   ├── bus.py                 # Event bus implementation
│   └── router.py              # Events router
├── runtimes/
│   ├── __init__.py
│   ├── models.py              # Runtime config models
│   ├── manager.py              # Runtime mode manager
│   └── router.py              # Runtimes router
├── policy/
│   ├── __init__.py
│   ├── models.py              # Policy rule models
│   ├── engine.py               # Policy enforcement engine
│   └── router.py              # Policy router

ui/src/
├── components/
│   ├── TerminalPane.jsx        # Main terminal component
│   ├── TerminalPane.css       # Terminal styles
│   ├── FileExplorer.jsx       # File explorer sidebar
│   ├── AgentBoard.jsx         # Agent task board
│   ├── EventLog.jsx           # Shared event log viewer
│   └── RuntimeSelector.jsx    # Runtime mode selector
├── hooks/
│   ├── useTerminal.js          # Terminal connection hook
│   ├── useWorkspace.js        # File operations hook
│   ├── useAgentBoard.js       # Agent board hook
│   └── useEvents.js           # Event stream hook
├── App.jsx                    # Integration point
└── stores/
    └── ideStore.js            # IDE state management
```

---

## 17. Open Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Shell availability detection | Auto-detect vs. config | Config-driven for MVP |
| Session persistence | In-memory vs. Redis | In-memory with Redis fallback |
| Terminal resize handling | Dynamic vs. fixed | Dynamic (Phase 2) |
| Multiple simultaneous sessions | Tabs vs. single | Tabs (Phase 2) |
| Sandbox isolation | Docker vs. gVisor vs. none | Docker (Phase 5) |
| Event delivery | WebSocket vs. SSE | SSE for logs, WS for terminal |
| Policy storage | Redis vs. file | Redis with file backup |

---

## 18. References

- Master Roadmap: `plans/22-master-execution-roadmap.md`
- Event Bus Contracts: `plans/23-event-bus-contracts.md`
- Backend Code: `backend/main.py`
- Frontend Code: `ui/src/App.jsx`