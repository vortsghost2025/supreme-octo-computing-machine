'use strict';

const express = require('express');
const { createAgent } = require('./agent');

const app  = express();
const PORT = parseInt(process.env.PORT || '3001', 10);

app.use(express.json({ limit: '4mb' }));

// ── Health ────────────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'snac_free_agent', ts: new Date().toISOString() });
});

// ── List available tools ──────────────────────────────────────────────────────
app.get('/tools', async (_req, res) => {
  try {
    const agent = await createAgent();
    const tools = await agent.listTools();
    res.json({ tools, total: tools.length });
  } catch (err) {
    res.status(500).json({ error: err.message, tools: [], total: 0 });
  }
});

// ── Run a task ────────────────────────────────────────────────────────────────
app.post('/run', async (req, res) => {
  // HTTP body uses snake_case (REST convention); createAgent() uses camelCase internally.
  const { task, provider, model, no_approval: noApproval, working_dir: workingDir } = req.body || {};

  if (!task || typeof task !== 'string' || !task.trim()) {
    return res.status(400).json({ error: 'task field is required and must be a non-empty string' });
  }

  try {
    const agent = await createAgent({ provider, model, noApproval, workingDir });
    const result = await agent.run(task.trim());
    res.json({ status: 'complete', task, result });
  } catch (err) {
    console.error('[free-agent] run error:', err.message);
    res.status(500).json({ status: 'error', task, error: err.message });
  }
});

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[snac_free_agent] listening on port ${PORT}`);
  console.log(`[snac_free_agent] provider=${process.env.PROVIDER || 'ollama'} model=${process.env.MODEL || 'llama3.2'}`);
  console.log(`[snac_free_agent] GitHub MCP: ${process.env.GITHUB_TOKEN ? 'configured' : 'not configured'}`);
  console.log(`[snac_free_agent] Brave MCP:  ${process.env.BRAVE_API_KEY ? 'configured' : 'not configured'}`);
});
