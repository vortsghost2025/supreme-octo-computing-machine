import asyncio
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional

# Attempt to import pywinpty for Windows PTY support; fallback to asyncio subprocess
try:
    import pywinpty
    _HAS_PYWINPTY = True
except Exception:
    _HAS_PYWINPTY = False

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

    async def _spawn_process(self, shell_type: str, cwd: str) -> asyncio.subprocess.Process:
        """Create the underlying process. Uses pywinpty on Windows when available."""
        if _HAS_PYWINPTY and shell_type in ("powershell", "cmd"):
            # pywinpty returns a PTY object; we wrap it to mimic asyncio Process API
            pty = pywinpty.Popen(["powershell.exe", "-NoLogo"] if shell_type == "powershell" else ["cmd.exe"], cwd=cwd)
            # Create dummy asyncio Process with needed attributes (stdin, stdout, stderr, pid, terminate, wait)
            class _DummyProcess:
                def __init__(self, pty):
                    self.pty = pty
                    self.stdin = pty
                    self.stdout = pty
                    self.stderr = pty
                    self.pid = pty.pid
                async def wait(self):
                    return await asyncio.get_event_loop().run_in_executor(None, self.pty.wait)
                def terminate(self):
                    self.pty.terminate()
                def kill(self):
                    self.pty.kill()
            return _DummyProcess(pty)
        else:
            shell_commands = {
                "powershell": ["powershell.exe", "-NoLogo"],
                "cmd": ["cmd.exe"],
                "bash": ["bash", "--login"],
                "sh": ["sh"],
            }
            cmd = shell_commands.get(shell_type)
            if not cmd:
                raise ValueError(f"Unsupported shell type: {shell_type}")
            return await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=self._get_environment(),
            )

    def _get_environment(self) -> Dict[str, str]:
        import os
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        return env

    async def create_session(self, shell_type: str, working_directory: str = ".") -> TerminalSession:
        if len(self._sessions) >= self._max_sessions:
            raise RuntimeError(f"Max sessions ({self._max_sessions}) reached")
        process = await self._spawn_process(shell_type, working_directory)
        session = TerminalSession(
            session_id=str(uuid.uuid4()),
            shell_type=shell_type,
            process=process,
            working_directory=working_directory,
            created_at=datetime.utcnow().isoformat(),
            status="running",
        )
        self._sessions[session.session_id] = session
        return session

    async def write_to_session(self, session_id: str, data: bytes) -> None:
        session = self._sessions.get(session_id)
        if not session or session.status == "closed":
            raise ValueError(f"Session {session_id} not found or closed")
        session.process.stdin.write(data)
        await session.process.stdin.drain()

    async def read_from_session(self, session_id: str) -> bytes:
        session = self._sessions.get(session_id)
        if not session or session.status == "closed":
            raise ValueError(f"Session {session_id} not found or closed")
        try:
            output = await asyncio.wait_for(session.process.stdout.read(4096), timeout=0.1)
            return output
        except asyncio.TimeoutError:
            return b""

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            session.status = "closed"
            session.process.terminate()
            try:
                await asyncio.wait_for(session.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                session.process.kill()
