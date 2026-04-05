import React, { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "./IDETerminal.css";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

const IDETerminal = () => {
  const terminalRef = useRef(null);
  const xtermRef = useRef(null);
  const fitAddonRef = useRef(null);
  const [sessionId, setSessionId] = useState(null);
  const wsRef = useRef(null);

  // Helper to create new terminal session via REST endpoint
  const createSession = async () => {
    try {
      const resp = await fetch(`${API_BASE}/terminal/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shell: "/bin/bash" }),
      });
      if (!resp.ok) throw new Error("Failed to create terminal session");
      const data = await resp.json();
      setSessionId(data.session_id);
    } catch (e) {
      console.error(e);
    }
  };

  // Initialize xterm and WebSocket once we have a sessionId
  useEffect(() => {
    if (!sessionId) return;

    // Initialize xterm if not already
    if (!xtermRef.current) {
      const term = new Terminal({
        cursorBlink: true,
        fontFamily: "monospace",
        fontSize: 14,
        theme: { background: "#1e1e1e", foreground: "#d4d4d4" },
      });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.loadAddon(new WebLinksAddon());
      term.open(terminalRef.current);
      fit.fit();
      xtermRef.current = term;
      fitAddonRef.current = fit;
    }

    // Setup WebSocket connection to stream output and send input
    const ws = new WebSocket(
      `${API_BASE.replace(/^http/, "ws")}/terminal/ws/${sessionId}`,
    );
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Terminal WS open");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "stdout" || payload.type === "stderr") {
          xtermRef.current.write(payload.data);
        } else if (payload.type === "exit") {
          xtermRef.current.write(`\r\n[process exited with code ${payload.data}]`);
          ws.close();
        }
      } catch (e) {
        console.error("WS parse error", e);
      }
    };

    ws.onclose = () => {
      console.log("Terminal WS closed");
    };

    // Forward user input to the PTY
    const onData = (data) => {
      const msg = JSON.stringify({ input: data });
      ws.send(msg);
    };
    xtermRef.current.onData(onData);

    // Cleanup on unmount / session change
    return () => {
      ws.close();
      xtermRef.current?.dispose();
      xtermRef.current = null;
    };
  }, [sessionId]);

  // Create session on component mount
  useEffect(() => {
    createSession();
    // Cleanup any lingering session when component unmounts
    return () => {
      if (sessionId) {
        fetch(`${API_BASE}/terminal/sessions/${sessionId}`, { method: "DELETE" }).catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Resize handling
  useEffect(() => {
    const handleResize = () => {
      if (fitAddonRef.current) fitAddonRef.current.fit();
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <div className="terminal-pane" ref={terminalRef} />;
};

export default IDETerminal;
