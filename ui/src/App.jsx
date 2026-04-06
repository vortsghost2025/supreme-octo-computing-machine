import { useEffect, useState, useCallback } from "react";
// IDETerminal component will be added later

// API Base URL - relative so it routes through nginx in production; override with VITE_API_URL in dev
// API Base URL – derived from Vite environment variable if present.
// In production the backend is proxied, but during local development we rely on the VITE_API_URL variable defined in `ui/.env`.
// Falling back to the default port 9002 keeps the UI functional even if the env file is missing.
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:9002";

// ============== COMPONENTS ==============

// 1. MEMORY TIMELINE PANEL
function MemoryTimeline({ events = [], isLoading }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📋 Memory Timeline</h2>
        <span className="badge" data-testid="memory-count">{events?.length ?? 0} events</span>
      </div>
      <div className="panel-content timeline memory-timeline">
        {isLoading ? (
          <div className="loading">Loading timeline...</div>
        ) : (events?.length ?? 0) === 0 ? (
          <div className="empty">No events yet. Run an agent task to see activity.</div>
        ) : (
          events.map((event, idx) => (
            <div key={idx} className={`timeline-item thought-entry ${event.type}`}>
              <div className="timeline-time">
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
              <div className="timeline-type">{event.type}</div>
              <div className="timeline-detail">
                {event.type === "ingest" && `Ingested ${event.chunks} chunks`}
                {event.type === "agent_start" && `Started: ${event.task?.substring(0, 50)}...`}
                {event.type === "agent_step" && `${event.step}: ${event.result}`}
                {event.type === "agent_complete" && `Result: ${event.result}`}
                {event.type === "thought_ingest" && `Thought: ${event.category} (${event.linked_count || 0} links)`}
                {event.type === "swarm_task_created" && `Swarm queued ${event.agent_type} (${event.priority})`}
                {event.type === "swarm_scaler_decision" && `Scaler: ${event.active_workers} -> ${event.desired_workers} (q=${event.queue_depth_total})`}
                {event.type === "memory_learn" && `Learning: ${event.topic} (${event.source_model})`}
                {event.type === "memory_workflow_learn" && `Workflow learned: ${event.workflow_id} (${event.confidence || 0})`}
                {event.type === "memory_injection_apply" && `Injected ${event.applied_count || 0} items into ${event.session_id}`}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// 2. NODE VISUALIZER PANEL
function NodeVisualizer({ currentTask, steps = [] }) {
  const nodes = [
    { id: "planner", label: "Planner", status: "idle" },
    { id: "worker1", label: "Worker 1", status: "idle" },
    { id: "worker2", label: "Worker 2", status: "idle" },
    { id: "end", label: "END", status: "idle" },
  ];

  // Update node status based on current state
  if (currentTask) {
    nodes[0].status = "active"; // Planner is planning
    if (steps.length > 0) {
      nodes[1].status = steps[0].step === 1 ? "active" : "completed";
    }
    if (steps.length > 1) {
      nodes[2].status = steps[1].step === 2 ? "active" : "completed";
    }
    if (steps.length >= 2) {
      nodes[3].status = "active";
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🔗 Node Visualizer</h2>
        <span className="badge">{currentTask ? "Running" : "Idle"}</span>
      </div>
      <div className="panel-content visualizer">
        <div className="node-graph">
          {nodes.map((node, idx) => (
            <div key={node.id} className="node-row">
              <div className={`node ${node.status}`}>
                <span className="node-icon">
                  {node.status === "active" ? "⚡" : node.status === "completed" ? "✓" : "○"}
                </span>
                <span className="node-label">{node.label}</span>
              </div>
              {idx < nodes.length - 1 && (
                <div className={`connector ${node.status === "completed" ? "active" : ""}`}>
                  →
                </div>
              )}
            </div>
          ))}
        </div>
        {currentTask && (
          <div className="current-task">
            <strong>Current Task:</strong> {currentTask}
          </div>
        )}
        {steps.length > 0 && (
          <div className="steps-list">
            <strong>Steps:</strong>
            {steps.map((step, idx) => (
              <div key={idx} className="step-item">
                <span className="step-num">{step.step}.</span>
                <span className="step-type">[{step.type}]</span>
                <span className="step-input">{step.input}</span>
                <span className="step-arrow">→</span>
                <span className="step-result">{step.result}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// 3. TOKEN COST MONITOR PANEL
function TokenMonitor({ usage = { total: 0, bySession: {} }, currentCost = 0 }) {
  const budget = 4.50;
  const alertThreshold = 4.00;
  const percentUsed = (usage.total / budget) * 100;
  const isAlert = usage.total >= alertThreshold;
  const isOverBudget = usage.total >= budget;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>💰 Token Cost Monitor</h2>
        <span className={`badge ${isOverBudget ? "danger" : isAlert ? "warning" : "success"}`}>
          {isOverBudget ? "OVER BUDGET" : isAlert ? "NEAR LIMIT" : "OK"}
        </span>
      </div>
      <div className="panel-content">
        <div className="cost-display">
          <div className="cost-total">
            <span className="cost-label">Total Spent</span>
            <span className="cost-value" data-testid="token-total">${usage.total.toFixed(4)}</span>
          </div>
          <div className="cost-current">
            <span className="cost-label">Current Request</span>
            <span className="cost-value">${currentCost.toFixed(4)}</span>
          </div>
        </div>
        
        <div className="budget-bar">
          <div 
            className={`budget-fill ${isOverBudget ? "danger" : isAlert ? "warning" : "success"}`}
            style={{ width: `${Math.min(percentUsed, 100)}%` }}
          />
        </div>
        <div className="budget-labels">
          <span>$0.00</span>
          <span className={isAlert ? "warning" : ""}>${alertThreshold.toFixed(2)} (alert)</span>
          <span>${budget.toFixed(2)} (limit)</span>
        </div>

        {Object.keys(usage.bySession).length > 0 && (
          <div className="session-costs">
            <strong>By Session:</strong>
            {Object.entries(usage.bySession).map(([session, cost]) => (
              <div key={session} className="session-item">
                <span className="session-id">{session.substring(0, 8)}...</span>
                <span className="session-cost">${cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SwarmMonitor({ status = {}, onScalerTick, isTicking }) {
  const queue = status?.queue_depth || { high: 0, normal: 0, low: 0 };
  const guard = status?.guardrails || {};
  const frozen = Boolean(guard.frozen_scale_up);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🐝 Swarm Monitor</h2>
        <span className={`badge ${frozen ? "warning" : "success"}`} data-testid="swarm-status">
          {frozen ? "GUARDRAIL" : "ACTIVE"}
        </span>
      </div>
      <div className="panel-content swarm-monitor">
        <div className="swarm-metric-total">
          <span className="swarm-label">Total Queue</span>
          <strong data-testid="swarm-count">{status?.queue_depth_total ?? 0}</strong>
        </div>
        <div className="swarm-grid">
          <div className="swarm-metric">
            <span className="swarm-label">Queue (High)</span>
            <strong>{queue.high || 0}</strong>
          </div>
          <div className="swarm-metric">
            <span className="swarm-label">Queue (Normal)</span>
            <strong>{queue.normal || 0}</strong>
          </div>
          <div className="swarm-metric">
            <span className="swarm-label">Queue (Low)</span>
            <strong>{queue.low || 0}</strong>
          </div>
          <div className="swarm-metric">
            <span className="swarm-label">Active Workers</span>
            <strong>{status?.active_workers || 0}</strong>
          </div>
          <div className="swarm-metric">
            <span className="swarm-label">Desired Workers</span>
            <strong>{status?.desired_workers || 0}</strong>
          </div>
          <div className="swarm-metric">
            <span className="swarm-label">Queue Total</span>
            <strong>{status?.queue_depth_total || 0}</strong>
          </div>
        </div>

        <div className="swarm-guardrail">
          <span>CPU: {guard.cpu_percent ?? 0}%</span>
          <span>TPM: {guard.tokens_per_min ?? 0}</span>
          <span>{guard.reason ? `Reason: ${guard.reason}` : "No guardrail block"}</span>
        </div>

        <button className="swarm-tick-btn" onClick={onScalerTick} disabled={isTicking}>
          {isTicking ? "Running Scaler..." : "Run Scaler Tick"}
        </button>
      </div>
    </div>
  );
}

function SwarmGraphPanel({ snapshot }) {
  if (!snapshot) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>🕸️ Swarm Topology</h2>
          <span className="badge">Loading...</span>
        </div>
        <div className="panel-content"><div className="empty">Waiting for graph snapshot...</div></div>
      </div>
    );
  }

  const { nodes = [], active_workers, tasks_running, queue_depth, recent_event_types = [], snapshot_at } = snapshot;
  const workers = nodes.filter((n) => n.type === "worker");

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🕸️ Swarm Topology</h2>
        <span className="badge success">{active_workers} workers</span>
      </div>
      <div className="panel-content">
        <div className="swarm-grid">
          <div className="swarm-metric"><span className="swarm-label">Workers</span><strong>{active_workers}</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Running</span><strong>{tasks_running}</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Queued</span><strong>{queue_depth}</strong></div>
        </div>
        {workers.length > 0 && (
          <div className="graph-worker-list">
            {workers.map((w) => (
              <div key={w.id} className={`graph-worker-node status-${w.status}`}>
                <span className="graph-worker-type">{w.worker_type || "worker"}</span>
                <span className="graph-worker-id">{w.id.substring(0, 8)}</span>
                <span className={`graph-worker-status badge ${w.status === "running" ? "success" : ""}`}>{w.status}</span>
                {w.runtime && <span className="graph-worker-runtime">{w.runtime}</span>}
              </div>
            ))}
          </div>
        )}
        {recent_event_types.length > 0 && (
          <div className="graph-events">
            <span className="graph-events-label">Recent events:</span>
            {recent_event_types.slice(0, 5).map((et, i) => (
              <span key={i} className="graph-event-chip">{et}</span>
            ))}
          </div>
        )}
        <div className="graph-snap-time">Snapshot: {snapshot_at ? new Date(snapshot_at).toLocaleTimeString() : "—"}</div>
      </div>
    </div>
  );
}

function SwarmIntelligencePanel({ summary }) {
  if (!summary || summary.total_tasks === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>🧬 Swarm Intelligence</h2>
          <span className="badge">No data</span>
        </div>
        <div className="panel-content"><div className="empty">No task history yet. Queue some swarm tasks to see intelligence metrics.</div></div>
      </div>
    );
  }

  const successPct = ((summary.task_success_rate || 0) * 100).toFixed(1);
  const strategyColors = { scale_out: "success", parallelize: "success", maintain: "", reduce_parallelism: "warning", no_data: "" };
  const strategyColor = strategyColors[summary.recommended_strategy] || "";

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🧬 Swarm Intelligence</h2>
        <span className={`badge ${strategyColor}`}>{summary.recommended_strategy}</span>
      </div>
      <div className="panel-content">
        <div className="swarm-grid">
          <div className="swarm-metric"><span className="swarm-label">Total Tasks</span><strong>{summary.total_tasks}</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Succeeded</span><strong>{summary.succeeded}</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Failed</span><strong>{summary.failed}</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Success Rate</span><strong>{successPct}%</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Avg Duration</span><strong>{summary.avg_duration_ms}ms</strong></div>
          <div className="swarm-metric"><span className="swarm-label">Busiest Runtime</span><strong>{summary.busiest_runtime || "—"}</strong></div>
        </div>
        {summary.best_worker_id && (
          <div className="intel-best-worker">
            <span className="intel-label">Best Worker:</span>
            <span className="intel-value">{summary.best_worker_type} ({summary.best_worker_id.substring(0, 8)})</span>
          </div>
        )}
        {summary.slowest_task_preview && (
          <div className="intel-slowest">
            <span className="intel-label">Slowest task:</span>
            <span className="intel-value">{summary.slowest_task_preview}</span>
          </div>
        )}
        <div className="intel-strategy">
          <span className="intel-label">Recommended strategy:</span>
          <span className={`intel-value ${strategyColor}`}>{summary.recommended_strategy}</span>
        </div>
      </div>
    </div>
  );
}

function GovernorPanel() {
  const [context, setContext] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [operationPath, setOperationPath] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [guidanceProject, setGuidanceProject] = useState("");
  const [guidanceResult, setGuidanceResult] = useState(null);
  const [narration, setNarration] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/governor/context`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setContext(data))
      .catch(() => setContext(null));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${API_BASE}/governor/refresh`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.context) setContext(data.context);
      alert(data.message);
    } catch (e) {
      console.error("Refresh failed:", e);
      alert("Refresh failed: " + e.message);
    } finally {
      setRefreshing(false);
    }
  };

  const handleValidate = async () => {
    if (!operationPath.trim()) return;
    setLoading(true);
    setValidationResult(null);
    try {
      const res = await fetch(`${API_BASE}/governor/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operationPath }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setValidationResult(data);
    } catch (e) {
      console.error("Validation failed:", e);
      setValidationResult({ allowed: false, reason: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/governor/search?q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error("Search failed:", e);
      setSearchResults([]);
    }
  };

  const handleGuidance = async () => {
    if (!guidanceProject.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/governor/guidance?project=${encodeURIComponent(guidanceProject)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGuidanceResult(data);
    } catch (e) {
      console.error("Guidance failed:", e);
      setGuidanceResult(null);
    }
  };

  const handleNarrate = async () => {
    const msg = validationResult
      ? validationResult.ttsNarration || validationResult.reason || "Operation allowed."
      : `Operation path: ${operationPath}`;
    if (!msg.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/governor/narrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setNarration(data.ssml || data.message || msg);
    } catch (e) {
      console.error("Narration failed:", e);
      setNarration(msg);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🛡️ Governor</h2>
        <span className={`badge ${context ? "success" : "warning"}`}>
          {context ? "Active" : "No Context"}
        </span>
      </div>
      <div className="panel-content governor-panel">
        <div className="governor-context">
          <div className="governor-context-header">
            <h3>Project Context</h3>
            <button onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
          {context ? (
            <div className="governor-context-grid">
              <div className="governor-metric">
                <span className="governor-label">Name</span>
                <strong>{context.name}</strong>
              </div>
              <div className="governor-metric">
                <span className="governor-label">Lifecycle</span>
                <strong>{context.lifecycle}</strong>
              </div>
              <div className="governor-metric">
                <span className="governor-label">Danger Zones</span>
                <strong>{(context.dangerZones ?? []).length}</strong>
              </div>
              <div className="governor-metric">
                <span className="governor-label">Allowed Imports</span>
                <strong>{(context.allowedImports ?? []).length}</strong>
              </div>
            </div>
          ) : (
            <div className="empty">No project manifest found. Create project.manifest.json in your project root.</div>
          )}
        </div>

        <div className="governor-validate">
          <h3>Validate Operation</h3>
          <div className="governor-input-row">
            <input
              type="text"
              value={operationPath}
              onChange={(e) => { setOperationPath(e.target.value); setValidationResult(null); }}
              placeholder="Enter operation path (e.g., /backend/secrets.env)"
            />
            <button onClick={handleValidate} disabled={loading}>
              {loading ? "Checking..." : "Validate"}
            </button>
            <button onClick={handleNarrate} disabled={!validationResult && !operationPath.trim()}>
              Narrate
            </button>
          </div>
          {validationResult && (
            <div className={`validation-result ${validationResult.allowed ? "allowed" : "blocked"}`}>
              <span className="validation-status">
                {validationResult.allowed ? "✅ Allowed" : "🚫 Blocked"}
              </span>
              {validationResult.reason && <div className="validation-reason">{validationResult.reason}</div>}
            </div>
          )}
          {narration && (
            <div className="governor-narration">
              <strong>TSS Narration:</strong>
              <p>{narration}</p>
            </div>
          )}
        </div>

        <div className="governor-search">
          <h3>Search Library</h3>
          <div className="governor-input-row">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search library..."
            />
            <button onClick={handleSearch}>Search</button>
          </div>
          {searchResults.length > 0 && (
            <ul className="governor-search-results">
              {searchResults.map((entry, idx) => (
                <li key={idx} className="governor-search-item">
                  <strong>{entry.title}</strong>
                  <p>{entry.snippet}</p>
                  {entry.tags && <span className="governor-search-tags">{entry.tags.join(", ")}</span>}
                </li>
              ))}
            </ul>
          )}
          {searchQuery && searchResults.length === 0 && (
            <div className="empty">No results found for "{searchQuery}".</div>
          )}
        </div>

        <div className="governor-guidance">
          <h3>Cross-Project Guidance</h3>
          <div className="governor-input-row">
            <input
              type="text"
              value={guidanceProject}
              onChange={(e) => { setGuidanceProject(e.target.value); setGuidanceResult(null); }}
              placeholder="Enter project name..."
            />
            <button onClick={handleGuidance}>Get Guidance</button>
          </div>
          {guidanceResult && (
            <div className="governor-guidance-result">
              <div className="governor-metric">
                <span className="governor-label">Lifecycle</span>
                <strong>{guidanceResult.lifecycle}</strong>
              </div>
              {guidanceResult.dangerZones && guidanceResult.dangerZones.length > 0 && (
                <ul className="governor-zone-list">
                  {guidanceResult.dangerZones.map((zone, idx) => (
                    <li key={idx}>⚠️ {zone}</li>
                  ))}
                </ul>
              )}
              {guidanceResult.notes && (
                <ul className="governor-guidance-notes">
                  {guidanceResult.notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="governor-danger-zones">
          <h3>Danger Zones</h3>
          {context && (context.dangerZones ?? []).length > 0 ? (
            <ul className="governor-zone-list">
              {(context.dangerZones ?? []).map((zone, idx) => (
                <li key={idx} className="governor-zone-item">⚠️ {zone}</li>
              ))}
            </ul>
          ) : (
            <div className="empty">No danger zones configured.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function SharedKnowledgePanel({ items = [] }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🧠 Shared Knowledge</h2>
        <span className="badge">{items.length} items</span>
      </div>
      <div className="panel-content knowledge-feed shared-knowledge">
        {items.length === 0 ? (
          <div className="empty">No shared learning yet.</div>
        ) : (
          items
            .slice()
            .reverse()
            .map((item) => (
              <div key={item.id} className={`knowledge-item impact-${item.impact_level || "low"}`}>
                <div className="knowledge-head">
                  <strong>{item.topic}</strong>
                  <span className="knowledge-impact">{(item.impact_level || "low").toUpperCase()}</span>
                </div>
                <div className="knowledge-details">{item.details}</div>
                <div className="knowledge-meta">
                  <span>From: {item.source_model}</span>
                  <span>Conf: {((item.confidence ?? 0) * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}

function AgentChatPanel({
  title = "💬 Agent Console",
  messages,
  draft,
  setDraft,
  onSend,
  onReset,
  isRunning,
  sessionId,
}) {
  const [fontSize, setFontSize] = useState(32);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!draft.trim() || isRunning) return;
    onSend();
  };

  return (
    <div className="panel chat-panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <span className="badge success">{sessionId ? "Connected" : "New Session"}</span>
      </div>
      <div className="panel-content chat-panel-content">
        <div className="chat-controls">
          <div className="font-size-control">
            <label>Font Size:</label>
            <input
              type="range"
              min="12"
              max="48"
              value={fontSize}
              onChange={(e) => setFontSize(Number(e.target.value))}
            />
            <span>{fontSize}px</span>
          </div>
        </div>
        <div className="chat-session-bar">
          <span className="chat-session-label">
            Session: {sessionId ? `${sessionId.substring(0, 12)}...` : "Not started yet"}
          </span>
          <button type="button" className="chat-reset-btn" onClick={onReset} disabled={isRunning}>
            Reset Chat
          </button>
        </div>

        <div className="chat-thread">
          {messages.length === 0 ? (
            <div className="empty chat-empty">
              No conversation yet. Talk to an agent here and the backend will keep session context alive.
            </div>
          ) : (
            messages.map((message, idx) => (
              <div key={`${message.role}-${idx}-${message.timestamp || idx}`} className={`chat-message ${message.role}`}>
                <div className="chat-message-head">
                  <span className="chat-role">{message.role === "user" ? "You" : message.role === "assistant" ? "Agent" : "System"}</span>
                  <span className="chat-time">{new Date(message.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="chat-message-body" style={{ fontSize: fontSize + 'px' }}>{message.content}</div>
                {Array.isArray(message.steps) && message.steps.length > 0 && (
                  <div className="chat-message-steps">
                    {message.steps.map((step) => (
                      <div key={`${message.timestamp}-${step.step}`} className="chat-step-item">
                        <span>[{step.type}]</span>
                        <span>{step.input}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <form className="chat-compose" onSubmit={handleSubmit}>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={title.includes('Free Coding') ? 'Enter coding task…' : 'Talk to your agents here. You can still use QUERY:/CALC: chaining if you want.'}
            disabled={isRunning}
            style={{ fontSize: fontSize + 'px' }}
          />
          <div className="chat-compose-actions">
            <button type="submit" disabled={isRunning || !draft.trim()}>
              {isRunning ? (title.includes('Free Coding') ? 'Running...' : 'Sending...') : (title.includes('Free Coding') ? 'Run Free Coding' : 'Send to Agent')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ============== MODAL COMPONENT ==============

function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

// ============== TASK INPUT COMPONENT ==============

function TaskInput({ onSubmit, isRunning, onMaximize }) {
  const [task, setTask] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (task.trim() && !isRunning) {
      onSubmit(task);
      setTask("");
    }
  };

  return (
    <form className="task-input-form" onSubmit={handleSubmit}>
    <textarea rows="2" placeholder="Enter task…" value={task} onChange={(e) => setTask(e.target.value)} disabled={isRunning}></textarea>
      <div className="task-input-buttons">
        <button type="submit" disabled={isRunning || !task.trim()}>
          {isRunning ? "Running..." : "Run Agent"}
        </button>
        <button type="button" className="maximize-btn" onClick={onMaximize} title="Expand input" aria-label="Expand input">
          ⛶
        </button>
      </div>
    </form>
  );
}

function TaskInputMaximized({ onSubmit, isRunning, onClose }) {
  const [task, setTask] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (task.trim() && !isRunning) {
      onSubmit(task);
      setTask("");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
      <textarea
        value={task}
        onChange={(e) => setTask(e.target.value)}
        placeholder="Enter task (e.g., 'QUERY: What is the capital of Japan? Then CALC: 25 * 4')"
        disabled={isRunning}
        style={{ minHeight: "300px", flex: 1 }}
        autoFocus
      />
      <div style={{ display: "flex", gap: "12px" }}>
        <button type="submit" disabled={isRunning || !task.trim()}>
          {isRunning ? "Running..." : "Run Agent"}
        </button>
        <button type="button" onClick={onClose}>Cancel</button>
      </div>
    </form>
  );
}

// ============== INGEST COMPONENT ==============

function IngestInput({ onIngest, isLoading, onMaximize }) {
  const [content, setContent] = useState("");

  const handleIngest = (e) => {
    e.preventDefault();
    if (content.trim() && !isLoading) {
      onIngest(content);
      setContent("");
    }
  };

  return (
    <form className="ingest-input-form" onSubmit={handleIngest}>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste document text here…"
        disabled={isLoading}
        rows={3}
      />
      <div className="ingest-input-buttons">
        <button type="submit" disabled={isLoading || !content.trim()}>
          {isLoading ? "Ingesting..." : "Ingest Document"}
        </button>
        <button type="button" className="maximize-btn" onClick={onMaximize} title="Expand input" aria-label="Expand input">
          ⛶
        </button>
      </div>
    </form>
  );
}

function IngestInputMaximized({ onIngest, isLoading, onClose }) {
  const [content, setContent] = useState("");

  const handleIngest = (e) => {
    e.preventDefault();
    if (content.trim() && !isLoading) {
      onIngest(content);
      setContent("");
    }
  };

  return (
    <form onSubmit={handleIngest} style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste document text here…"
        disabled={isLoading}
        style={{ minHeight: "400px", flex: 1 }}
        autoFocus
      />
      <div style={{ display: "flex", gap: "12px" }}>
        <button type="submit" disabled={isLoading || !content.trim()}>
          {isLoading ? "Ingesting..." : "Ingest Document"}
        </button>
        <button type="button" onClick={onClose}>Cancel</button>
      </div>
    </form>
  );
}

function ThoughtInput({ onIngestThought, isLoading }) {
  const [content, setContent] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (content.trim() && !isLoading) {
      onIngestThought(content);
      setContent("");
    }
  };

  return (
    <form className="thought-input-form" onSubmit={handleSubmit}>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Enter a thought…"
        disabled={isLoading}
        rows={4}
      />
      <button type="submit" disabled={isLoading || !content.trim()}>
        {isLoading ? "Ingesting..." : "Ingest Thought"}
      </button>
    </form>
  );
}

function SwarmQueueInput({ onQueueTask, isLoading }) {
  const [task, setTask] = useState("");
  const [agentType, setAgentType] = useState("research_worker");
  const [priority, setPriority] = useState("normal");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (task.trim() && !isLoading) {
      onQueueTask({ task, agentType, priority });
      setTask("");
    }
  };

  return (
    <form className="swarm-queue-form" onSubmit={handleSubmit}>
      <textarea
        value={task}
        onChange={(e) => setTask(e.target.value)}
        placeholder="Enter swarm task…"
        rows={3}
        disabled={isLoading}
      />
      <div className="swarm-queue-row">
        <select value={agentType} onChange={(e) => setAgentType(e.target.value)} disabled={isLoading}>
          <option value="planner_worker">planner_worker</option>
          <option value="research_worker">research_worker</option>
          <option value="analyzer_worker">analyzer_worker</option>
          <option value="builder_worker">builder_worker</option>
          <option value="reviewer_worker">reviewer_worker</option>
          <option value="idea_worker">idea_worker</option>
        </select>
        <select value={priority} onChange={(e) => setPriority(e.target.value)} disabled={isLoading}>
          <option value="high">high</option>
          <option value="normal">normal</option>
          <option value="low">low</option>
        </select>
      </div>
      <button type="submit" disabled={isLoading || !task.trim()}>
        {isLoading ? "Queueing..." : "Queue Swarm Task"}
      </button>
      {task && (
        <div className="swarm-queue-list">
          <div className="swarm-queue-item">{task}</div>
        </div>
      )}
    </form>
  );
}

function MemoryLearnInput({ onSubmitLearning, isLoading }) {
  const [sourceModel, setSourceModel] = useState("gpt-4o-mini");
  const [topic, setTopic] = useState("");
  const [details, setDetails] = useState("");
  const [impactLevel, setImpactLevel] = useState("low");
  const [confidence, setConfidence] = useState(0.7);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!topic.trim() || !details.trim() || isLoading) return;
    onSubmitLearning({
      source_model: sourceModel,
      topic,
      details,
      impact_level: impactLevel,
      confidence: Number(confidence),
    });
    setTopic("");
    setDetails("");
  };

  return (
    <form className="memory-learn-form" onSubmit={handleSubmit}>
      <input
        value={sourceModel}
        onChange={(e) => setSourceModel(e.target.value)}
        placeholder="Source model"
        disabled={isLoading}
      />
      <input
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Topic"
        disabled={isLoading}
      />
      <textarea
        value={details}
        onChange={(e) => setDetails(e.target.value)}
        placeholder="Details"
        rows={4}
        disabled={isLoading}
      />
      <div className="memory-learn-row">
        <select value={impactLevel} onChange={(e) => setImpactLevel(e.target.value)} disabled={isLoading}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
        <input
          type="number"
          min="0"
          max="1"
          step="0.05"
          value={confidence}
          onChange={(e) => setConfidence(e.target.value)}
          disabled={isLoading}
        />
      </div>
      <button type="submit" disabled={isLoading || !topic.trim() || !details.trim()}>
        {isLoading ? "Saving..." : "Add Learning"}
      </button>
    </form>
  );
}

function MemoryInjectionInput({
  onPreviewInjection,
  onApplyInjection,
  isPreviewing,
  isApplying,
  preview,
  selectedIds,
  setSelectedIds,
}) {
  const [sessionId, setSessionId] = useState("global");
  const [agentType, setAgentType] = useState("");
  const [domain, setDomain] = useState("");
  const [layersCsv, setLayersCsv] = useState("");
  const [impactCsv, setImpactCsv] = useState("");
  const [query, setQuery] = useState("");
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [maxItems, setMaxItems] = useState(8);

  const parseCsv = (value) =>
    value
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);

  const buildPayload = () => ({
    session_id: sessionId.trim() || "global",
    agent_type: agentType.trim() || undefined,
    domain: domain.trim() || undefined,
    layers: parseCsv(layersCsv),
    impact_levels: parseCsv(impactCsv),
    query: query.trim() || undefined,
    min_confidence: Number(minConfidence),
    max_items: Number(maxItems),
  });

  const handlePreview = async (e) => {
    e.preventDefault();
    onPreviewInjection(buildPayload());
  };

  const handleApply = async () => {
    onApplyInjection(buildPayload(), selectedIds);
  };

  const toggleSelected = (itemId) => {
    if (!itemId) return;
    setSelectedIds((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  };

  return (
    <div className="memory-injection-wrap">
      <form className="memory-injection-form" onSubmit={handlePreview}>
        <input
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Session ID"
          disabled={isPreviewing || isApplying}
        />
        <div className="memory-injection-row">
          <input
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="Domain (optional)"
            disabled={isPreviewing || isApplying}
          />
          <input
            value={agentType}
            onChange={(e) => setAgentType(e.target.value)}
            placeholder="Agent type (optional)"
            disabled={isPreviewing || isApplying}
          />
        </div>
        <input
          value={layersCsv}
          onChange={(e) => setLayersCsv(e.target.value)}
          placeholder="Layers CSV (e.g. diagnostic,triage)"
          disabled={isPreviewing || isApplying}
        />
        <input
          value={impactCsv}
          onChange={(e) => setImpactCsv(e.target.value)}
          placeholder="Impact CSV (low,medium,high)"
          disabled={isPreviewing || isApplying}
        />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search query"
          disabled={isPreviewing || isApplying}
        />
        <div className="memory-injection-row">
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(e.target.value)}
            disabled={isPreviewing || isApplying}
          />
          <input
            type="number"
            min="1"
            max="100"
            step="1"
            value={maxItems}
            onChange={(e) => setMaxItems(e.target.value)}
            disabled={isPreviewing || isApplying}
          />
        </div>
        <div className="memory-injection-actions">
          <button type="submit" disabled={isPreviewing || isApplying}>
            {isPreviewing ? "Previewing..." : "Preview Injection"}
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={isApplying || isPreviewing || selectedIds.length === 0}
          >
            {isApplying ? "Applying..." : `Apply (${selectedIds.length})`}
          </button>
        </div>
      </form>

      <div className="memory-injection-preview">
        {((preview && preview.candidates) || []).length === 0 ? (
          <div className="empty">No preview items. Run preview with filters.</div>
        ) : (
          preview.candidates.map((candidate) => (
            <label key={candidate.item.id} className="memory-injection-item">
              <input
                type="checkbox"
                checked={selectedIds.includes(candidate.item.id)}
                onChange={() => toggleSelected(candidate.item.id)}
                disabled={isApplying || isPreviewing}
              />
              <div>
                <div className="memory-injection-item-head">
                  <strong>{candidate.item.topic}</strong>
                  <span>{candidate.score.toFixed(2)}</span>
                </div>
                <div className="memory-injection-item-meta">
                  {candidate.item.impact_level} • {(candidate.item.confidence * 100).toFixed(0)}% • {candidate.reasons.join(", ")}
                </div>
              </div>
            </label>
          ))
        )}
      </div>
    </div>
  );
}

// ============== PROJECT VAULT ==============

const PROJECT_ROOT = (import.meta.env.VITE_PROJECT_ROOT || "/workspace").replace(/\/$/, "");
const GAME_PATH = `${PROJECT_ROOT}/federation-game/index.html`;

const VAULT_PATHS = [
  {
    id: "federation-game",
    label: "🎮 Quantum-Ahead Universe Game",
    path: GAME_PATH,
    description: "Kid-friendly agent/universe game built for my son. Teaches AI concepts through play.",
    category: "game",
    tags: ["game", "workspace", "path-registry"],
    openUrl: `file://${GAME_PATH}`,
  },
  {
    id: "ensemble-storage",
    label: "🧠 Memory Bank / Ensemble Storage",
    path: `${PROJECT_ROOT}/ensemble_storage`,
    description: "Primary memory bank. Ensemble storage for long-term knowledge across sessions.",
    category: "memory-bank",
    tags: ["memory-bank", "workspace", "path-registry"],
    openUrl: null,
  },
  {
    id: "session-records",
    label: "📋 Session Records",
    path: `${PROJECT_ROOT}/SESSION_RECORDS`,
    description: "Historical session records including DESKTOP_CLAUDE_SESSION_FEB15_2026 and others.",
    category: "records",
    tags: ["records", "workspace", "path-registry"],
    openUrl: null,
  },
  {
    id: "src",
    label: "💾 Source / Game Remnants",
    path: `${PROJECT_ROOT}/src`,
    description: "Source code remnants, possibly early game versions and experimental code.",
    category: "source",
    tags: ["source", "workspace", "path-registry"],
    openUrl: null,
  },
  {
    id: "swarm-tools",
    label: "🐝 Swarm Tools",
    path: `${PROJECT_ROOT}/swarm_tools`,
    description: "Swarm coordination tools and agent orchestration utilities.",
    category: "swarm",
    tags: ["swarm", "workspace", "path-registry"],
    openUrl: null,
  },
  {
    id: "root-workspace",
    label: "📁 Root Workspace (100+ docs)",
    path: PROJECT_ROOT,
    description: "Root workspace directory. Contains 100+ scattered documents, notes, and project artifacts to be preserved in memory.",
    category: "workspace",
    tags: ["workspace", "path-registry", "documents"],
    openUrl: null,
  },
];

function ProjectVaultPanel({ onSaveToBrain, savingVaultId }) {
  return (
    <div className="project-vault">
      <ul className="project-vault-list">
        {VAULT_PATHS.map((entry) => (
          <li key={entry.id} className="project-vault-entry">
            <div className="project-vault-entry-head">
              <span className="project-vault-label">{entry.label}</span>
            </div>
            <div className="project-vault-path">{entry.path}</div>
            <div className="project-vault-desc">{entry.description}</div>
            <div className="project-vault-actions">
              <button
                className="vault-save-btn"
                disabled={savingVaultId === entry.id}
                onClick={() => onSaveToBrain(entry)}
              >
                {savingVaultId === entry.id ? "Saving..." : "💾 Save to Brain"}
              </button>
              {entry.openUrl && (
                <a
                  className="vault-open-btn"
                  href={entry.openUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  🚀 Open Game
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ============== MAIN APP ==============

function App() {
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [timeline, setTimeline] = useState([]);
  const [tokenUsage, setTokenUsage] = useState({ total: 0, bySession: {} });
  const [_currentTask, setCurrentTask] = useState("");
  const [_currentSteps, setCurrentSteps] = useState([]);
  const [currentCost, setCurrentCost] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isQueueingSwarmTask, setIsQueueingSwarmTask] = useState(false);
  const [isTickingSwarm, setIsTickingSwarm] = useState(false);
  const [isLearning, setIsLearning] = useState(false);
  const [isPreviewingInjection, setIsPreviewingInjection] = useState(false);
  const [isApplyingInjection, setIsApplyingInjection] = useState(false);
  const [sharedKnowledge, setSharedKnowledge] = useState([]);
  const [memoryInjectionPreview, setMemoryInjectionPreview] = useState({ candidates: [] });
  const [memoryInjectionSelectedIds, setMemoryInjectionSelectedIds] = useState([]);
  const [capabilities, setCapabilities] = useState({
    memoryInjection: false,
  });
  const [savingVaultId, setSavingVaultId] = useState(null);
  const [agentChatSessionId, setAgentChatSessionId] = useState(() => {
    try {
      return window.localStorage.getItem("snac-agent-chat-session") || "";
    } catch {
      return "";
    }
  });
  const [agentChatMessages, setAgentChatMessages] = useState([]);
  const [agentChatDraft, setAgentChatDraft] = useState("");

  // Free Coding Agent chat state
  const [task, setTask] = useState("");
  const [freeAgentMessages, setFreeAgentMessages] = useState([]);
  const [freeAgentDraft, setFreeAgentDraft] = useState("");
  const [freeAgentRunning, setFreeAgentRunning] = useState(false);
  const FREE_AGENT_API = "/free-coding-agent";
  const [swarmStatus, setSwarmStatus] = useState({
    queue_depth: { high: 0, normal: 0, low: 0 },
    queue_depth_total: 0,
    active_workers: 0,
    desired_workers: 0,
    guardrails: {},
  });
  const [swarmGraphSnapshot, setSwarmGraphSnapshot] = useState(null);
  const [swarmIntelligenceSummary, setSwarmIntelligenceSummary] = useState(null);
  const [maximizedInputType, setMaximizedInputType] = useState(null); // "task" | "ingest"

  // Check backend status
  useEffect(() => {
    fetch(`${API_BASE}/`)
      .then((res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
      .then((data) => setBackendStatus((data && data.status) || "ok"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    try {
      if (agentChatSessionId) {
        window.localStorage.setItem("snac-agent-chat-session", agentChatSessionId);
      } else {
        window.localStorage.removeItem("snac-agent-chat-session");
      }
    } catch {
      // Ignore local storage failures.
    }
  }, [agentChatSessionId]);

  // Poll for timeline updates
  const fetchTimeline = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/timeline`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTimeline((data && data.events) || []);
    } catch (e) {
      console.error("Failed to fetch timeline:", e);
      setTimeline([]);
    }
  }, []);

  // Poll for token usage
  const fetchTokenUsage = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/tokens/usage`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTokenUsage((data && { total: data.total || 0, bySession: data.bySession || {} }) || { total: 0, bySession: {} });
    } catch (e) {
      console.error("Failed to fetch token usage:", e);
      setTokenUsage({ total: 0, bySession: {} });
    }
  }, []);

  const fetchSwarmStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/swarm/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSwarmStatus(data || {
        queue_depth: { high: 0, normal: 0, low: 0 },
        queue_depth_total: 0,
        active_workers: 0,
        desired_workers: 0,
        guardrails: {},
      });
    } catch (e) {
      console.error("Failed to fetch swarm status:", e);
      setSwarmStatus({
        queue_depth: { high: 0, normal: 0, low: 0 },
        queue_depth_total: 0,
        active_workers: 0,
        desired_workers: 0,
        guardrails: {},
      });
    }
  }, []);

  const fetchSharedKnowledge = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/feed?limit=50`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSharedKnowledge((data && data.items) || []);
    } catch (e) {
      console.error("Failed to fetch shared knowledge:", e);
      setSharedKnowledge([]);
    }
  }, []);

  const fetchSwarmGraph = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/swarm/graph/snapshot`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSwarmGraphSnapshot(data || null);
    } catch (e) {
      console.error("Failed to fetch swarm graph:", e);
    }
  }, []);

  const fetchSwarmIntelligence = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/swarm/intelligence/summary`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSwarmIntelligenceSummary(data || null);
    } catch (e) {
      console.error("Failed to fetch swarm intelligence:", e);
    }
  }, []);

  const fetchCapabilities = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/openapi.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const paths = (data && data.paths) || {};
      const hasInjectPreview = Boolean(paths["/memory/inject/preview"]);
      const hasInjectApply = Boolean(paths["/memory/inject/apply"]);

      setCapabilities({
        memoryInjection: hasInjectPreview && hasInjectApply,
      });
    } catch (e) {
      console.warn("Capability detection failed, using safe defaults:", e.message);
      setCapabilities({ memoryInjection: false });
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchTimeline();
    fetchTokenUsage();
    fetchSwarmStatus();
    fetchSharedKnowledge();
    fetchCapabilities();
    fetchSwarmGraph();
    fetchSwarmIntelligence();

    const interval = setInterval(() => {
      fetchTimeline();
      fetchTokenUsage();
      fetchSwarmStatus();
      fetchSharedKnowledge();
      fetchSwarmGraph();
      fetchSwarmIntelligence();
    }, 2000);

    return () => clearInterval(interval);
  }, [fetchTimeline, fetchTokenUsage, fetchSwarmStatus, fetchSharedKnowledge, fetchCapabilities, fetchSwarmGraph, fetchSwarmIntelligence]);

  const runAgentTask = useCallback(async (task, sessionId = "") => {
    const payload = { task };
    if (sessionId) payload.session_id = sessionId;

    const res = await fetch(`${API_BASE}/agent/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }, []);

  // Handle task submission
  const handleTaskSubmit = async (task) => {
    setMaximizedInputType(null);
    setIsRunning(true);
    setCurrentTask(task);
    setCurrentSteps([]);
    setCurrentCost(0);

    try {
      const data = await runAgentTask(task);
      setCurrentSteps((data && data.steps) || []);
      setCurrentCost((data && data.cost) || 0);
      
      // Refresh data after task completes
      setTimeout(() => {
        fetchTimeline();
        fetchTokenUsage();
      }, 500);
    } catch (e) {
      console.error("Task failed:", e);
      alert("Task failed: " + e.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleAgentChatSubmit = async () => {
    const task = agentChatDraft.trim();
    if (!task || isRunning) return;

    const startedAt = new Date().toISOString();
    setIsRunning(true);
    setAgentChatDraft("");
    setCurrentTask(task);
    setCurrentSteps([]);
    setCurrentCost(0);
    setAgentChatMessages((prev) => [
      ...prev,
      { role: "user", content: task, timestamp: startedAt },
    ]);

    try {
      const data = await runAgentTask(task, agentChatSessionId);
      setAgentChatSessionId((data && data.session_id) || agentChatSessionId);
      setCurrentSteps((data && data.steps) || []);
      setCurrentCost((data && data.cost) || 0);
      setAgentChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: (data && data.result) || "",
          steps: (data && data.steps) || [],
          timestamp: new Date().toISOString(),
        },
      ]);

      setTimeout(() => {
        fetchTimeline();
        fetchTokenUsage();
      }, 500);
    } catch (e) {
      console.error("Agent chat failed:", e);
      setAgentChatMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Error: ${e.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleAgentChatReset = () => {
    if (isRunning) return;
    setAgentChatSessionId("");
    setAgentChatMessages([]);
    setAgentChatDraft("");
    setCurrentTask("");
    setCurrentSteps([]);
    setCurrentCost(0);
  };

  // Free Coding Agent handlers
  const handleFreeAgentReset = () => {
    if (freeAgentRunning) return;
    setFreeAgentMessages([]);
    setFreeAgentDraft("");
  };

  const handleFreeAgentSubmit = async () => {
    const task = freeAgentDraft.trim();
    if (!task || freeAgentRunning) return;

    const startedAt = new Date().toISOString();
    setFreeAgentRunning(true);
    setFreeAgentDraft("");
    setFreeAgentMessages((prev) => [
      ...prev,
      { role: "user", content: task, timestamp: startedAt },
    ]);

    try {
      const res = await fetch(`${FREE_AGENT_API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, provider: "ollama" }),
      });
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      // Handle streaming response
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "chunk") {
                fullResponse += event.content;
                setFreeAgentMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg && lastMsg.role === "assistant") {
                    lastMsg.content = fullResponse;
                  } else {
                    newMessages.push({
                      role: "assistant",
                      content: fullResponse,
                      timestamp: new Date().toISOString(),
                    });
                  }
                  return newMessages;
                });
              }
            } catch (e) {
                console.error("Failed to parse SSE event:", e);
              }
          }
        }
      }
    } catch (e) {
      console.error("Free agent chat failed:", e);
      setFreeAgentMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Error: ${e.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setFreeAgentRunning(false);
    }
  };

  // Handle document ingestion
  const handleIngest = async (content) => {
    setMaximizedInputType(null);
    setIsIngesting(true);
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      alert(`Ingested ${(data && data.chunks) || 0} chunks`);
      
      // Refresh timeline
      setTimeout(fetchTimeline, 500);
    } catch (e) {
      console.error("Ingest failed:", e);
      alert("Ingest failed: " + e.message);
    } finally {
      setIsIngesting(false);
    }
  };

  // Handle thought ingestion
  const handleThoughtIngest = async (content) => {
    setIsThinking(true);
    try {
      const res = await fetch(`${API_BASE}/ingest-thought`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      alert(
        `Thought ingested\nCategory: ${(data && data.category) || "AI_SYSTEMS"}\nLinks: ${((data && data.linked_thought_ids) || []).length}`
      );

      setTimeout(fetchTimeline, 500);
    } catch (e) {
      console.error("Thought ingest failed:", e);
      alert("Thought ingest failed: " + e.message);
    } finally {
      setIsThinking(false);
    }
  };

  const handleQueueSwarmTask = async ({ task, agentType, priority }) => {
    setIsQueueingSwarmTask(true);
    try {
      const res = await fetch(`${API_BASE}/swarm/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, agent_type: agentType, priority }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      alert(`Swarm task queued: ${(data && data.task_id) || "unknown"}`);
      setTimeout(() => {
        fetchSwarmStatus();
        fetchTimeline();
      }, 300);
    } catch (e) {
      console.error("Swarm queue failed:", e);
      alert("Swarm queue failed: " + e.message);
    } finally {
      setIsQueueingSwarmTask(false);
    }
  };

  const handleSwarmTick = async () => {
    setIsTickingSwarm(true);
    try {
      const res = await fetch(`${API_BASE}/swarm/scaler/tick`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await res.json();
      setTimeout(() => {
        fetchSwarmStatus();
        fetchTimeline();
      }, 300);
    } catch (e) {
      console.error("Swarm tick failed:", e);
      alert("Swarm tick failed: " + e.message);
    } finally {
      setIsTickingSwarm(false);
    }
  };

  const handleMemoryLearn = async (payload) => {
    setIsLearning(true);
    try {
      const res = await fetch(`${API_BASE}/memory/learn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await res.json();
      setTimeout(() => {
        fetchSharedKnowledge();
        fetchTimeline();
      }, 300);
    } catch (e) {
      console.error("Memory learn failed:", e);
      alert("Memory learn failed: " + e.message);
    } finally {
      setIsLearning(false);
    }
  };

  const handleMemoryInjectPreview = async (payload) => {
    if (!capabilities.memoryInjection) {
      console.info("Memory injection not available on backend; skipping preview.");
      return;
    }
    setIsPreviewingInjection(true);
    try {
      const res = await fetch(`${API_BASE}/memory/inject/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMemoryInjectionPreview(data || { candidates: [] });
      const candidateIds = ((data && data.candidates) || [])
        .map((candidate) => candidate.item && candidate.item.id)
        .filter(Boolean);
      setMemoryInjectionSelectedIds(candidateIds);
    } catch (e) {
      console.error("Memory inject preview failed:", e);
      alert("Memory inject preview failed: " + e.message);
      setMemoryInjectionPreview({ candidates: [] });
      setMemoryInjectionSelectedIds([]);
    } finally {
      setIsPreviewingInjection(false);
    }
  };

  const handleMemoryInjectApply = async (payload, selectedIds) => {
    if (!capabilities.memoryInjection) {
      console.info("Memory injection not available on backend; skipping apply.");
      return;
    }
    setIsApplyingInjection(true);
    try {
      const res = await fetch(`${API_BASE}/memory/inject/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, selected_item_ids: selectedIds }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      alert(`Applied ${data.applied_count || 0} memory items to ${data.session_id || "session"}`);
      setTimeout(() => {
        fetchTimeline();
      }, 300);
    } catch (e) {
      console.error("Memory inject apply failed:", e);
      alert("Memory inject apply failed: " + e.message);
    } finally {
      setIsApplyingInjection(false);
    }
  };

  const handleVaultSaveToBrain = async (entry) => {
    setSavingVaultId(entry.id);
    try {
      const res = await fetch(`${API_BASE}/memory/learn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_model: "project-vault",
          topic: entry.label.replace(/^[^a-zA-Z]+/, "").trim(),
          details: `Path: ${entry.path}\n\n${entry.description}`,
          impact_level: "high",
          confidence: 0.9,
          tags: entry.tags,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      alert(`Saved "${entry.label}" to brain!`);
      setTimeout(() => {
        fetchTimeline();
        fetchSharedKnowledge();
      }, 300);
    } catch (e) {
      console.error("Vault save failed:", e);
      alert("Save failed: " + e.message);
    } finally {
      setSavingVaultId(null);
    }
  };

  return (
    <div className="cockpit-new">
      <header className="cockpit-header">
        <h1>🚀 SNAC-v2 Cockpit</h1>
        <span className={`status-badge ${backendStatus === "ok" ? "online" : "offline"}`}>
          Backend: {backendStatus}
        </span>
      </header>

      <div className="cockpit-main">
        <aside className="cockpit-sidebar">
          <section className="sidebar-section">
            <h3>Agent Task</h3>
            <TaskInput
              onSubmit={handleTaskSubmit}
              isRunning={isRunning}
              onMaximize={() => setMaximizedInputType("task")}
            />
          </section>
          <section className="sidebar-section">
            <h3>Ingest Document</h3>
            <IngestInput
              onIngest={handleIngest}
              isLoading={isIngesting}
              onMaximize={() => setMaximizedInputType("ingest")}
            />
          </section>
          <section className="sidebar-section">
            <h3>Quick Thought</h3>
            <ThoughtInput onIngestThought={handleThoughtIngest} isLoading={isThinking} />
          </section>
          <section className="sidebar-section">
            <h3>Swarm Queue</h3>
            <SwarmQueueInput onQueueTask={handleQueueSwarmTask} isLoading={isQueueingSwarmTask} />
          </section>
          <section className="sidebar-section">
            <h3>Add Learning</h3>
            <MemoryLearnInput onSubmitLearning={handleMemoryLearn} isLoading={isLearning} />
          </section>
          <section className="sidebar-section">
            <h3>Memory Injection</h3>
            {capabilities.memoryInjection ? (
              <MemoryInjectionInput
                onPreviewInjection={handleMemoryInjectPreview}
                onApplyInjection={handleMemoryInjectApply}
                isPreviewing={isPreviewingInjection}
                isApplying={isApplyingInjection}
                preview={memoryInjectionPreview}
                selectedIds={memoryInjectionSelectedIds}
                setSelectedIds={setMemoryInjectionSelectedIds}
              />
            ) : (
              <div className="feature-note">
                Memory injection is not enabled on this backend yet.
              </div>
            )}
          </section>
          <section className="sidebar-section">
            <h3>🗄️ Project Vault</h3>
            <ProjectVaultPanel
              onSaveToBrain={handleVaultSaveToBrain}
              savingVaultId={savingVaultId}
            />
          </section>
        </aside>

        <main className="cockpit-content">
          <div className="panels-grid">
            <div className="chat-row">
              <AgentChatPanel
                title="🤖 SNAC Agent"
                messages={agentChatMessages}
                draft={agentChatDraft}
                setDraft={setAgentChatDraft}
                onSend={handleAgentChatSubmit}
                onReset={handleAgentChatReset}
                isRunning={isRunning}
                sessionId={agentChatSessionId}
              />
    <div className="free-coding-agent">
      <AgentChatPanel
        title="🔥 Free Coding Agent"
        messages={freeAgentMessages}
        draft={freeAgentDraft}
        setDraft={setFreeAgentDraft}
        onSend={handleFreeAgentSubmit}
        onReset={handleFreeAgentReset}
        isRunning={freeAgentRunning}
        sessionId={null}
      />
    <div className="task-input-wrapper">
      <form className="task-input-form" onSubmit={(e)=>{e.preventDefault(); if(task.trim() && !isRunning){handleTaskSubmit(task); setTask("");}}}>
        <textarea rows="2" placeholder="Enter task…" value={task} onChange={(e)=>setTask(e.target.value)} disabled={isRunning}></textarea>
        <div className="task-input-buttons">
          <button type="submit" disabled={isRunning || !task.trim()}>Run Agent</button>
        </div>
      </form>
    </div>
    </div>
            </div>
            <div className="panels-second-row">
              <GovernorPanel />
              <MemoryTimeline events={timeline} isLoading={backendStatus !== "ok"} />
              {/* IDETerminal component disabled */}
              <TokenMonitor usage={tokenUsage} currentCost={currentCost} />
              <SwarmMonitor status={swarmStatus} onScalerTick={handleSwarmTick} isTicking={isTickingSwarm} />
            </div>
            <div className="panels-bottom-row">
              <SharedKnowledgePanel items={sharedKnowledge} />
              <SwarmGraphPanel snapshot={swarmGraphSnapshot} />
              <SwarmIntelligencePanel summary={swarmIntelligenceSummary} />
            </div>
          </div>
        </main>
      </div>

      <Modal
        isOpen={maximizedInputType === "task"}
        onClose={() => setMaximizedInputType(null)}
        title="Agent Task Input"
      >
        <TaskInputMaximized
          onSubmit={handleTaskSubmit}
          isRunning={isRunning}
          onClose={() => setMaximizedInputType(null)}
        />
      </Modal>

      <Modal
        isOpen={maximizedInputType === "ingest"}
        onClose={() => setMaximizedInputType(null)}
        title="Document Ingest"
      >
        <IngestInputMaximized
          onIngest={handleIngest}
          isLoading={isIngesting}
          onClose={() => setMaximizedInputType(null)}
        />
      </Modal>
    </div>
  );
}

export default App;
