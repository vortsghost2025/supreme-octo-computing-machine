const express = require('express');
const bodyParser = require('body-parser');

const {
  ClusterScheduler,
  ResourceManager,
  AutonomousDecisionEngine,
} = require('../medical/intelligence/autonomous-orchestration');

const scheduler = new ClusterScheduler({ maxWorkers: 10, minWorkers: 2 });
const resourceManager = new ResourceManager();
const decisionEngine = new AutonomousDecisionEngine();

// Import Governor core functions
const {
  loadProjectContext,
  validateOperation,
  searchLibrary,
  getCrossProjectGuidance,
  generateNarration,
  refreshContext,
  // Policy functions – will be added later if needed
} = require('../kilocode/packages/opencode/src/kilocode/tools/governor');

const app = express();
app.use(bodyParser.json());

// Simple helper to get project root – for demo we use cwd
const PROJECT_ROOT = process.cwd();

app.post('/api/governor/load_context', async (req, res) => {
  try {
    const ctx = await loadProjectContext(PROJECT_ROOT);
    res.json(ctx);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/governor/validate', async (req, res) => {
  const { operationPath } = req.body;
  try {
    const ctx = await loadProjectContext(PROJECT_ROOT);
    const result = await validateOperation(ctx, operationPath);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/governor/search', async (req, res) => {
  const { query } = req.body;
  try {
    const results = await searchLibrary(query);
    res.json(results);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/governor/guidance', async (req, res) => {
  const { projectName } = req.body;
  try {
    const guidance = await getCrossProjectGuidance(projectName);
    res.json(guidance);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/governor/narrate', async (req, res) => {
  const { message } = req.body;
  try {
    const ssml = generateNarration(message);
    res.json({ ssml });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/governor/refresh', async (req, res) => {
  try {
    const refreshed = await refreshContext(PROJECT_ROOT);
    res.json(refreshed);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============== ORCHESTRATION API ROUTES ==============

// POST /api/orchestration/tasks — submit a task
app.post('/api/orchestration/tasks', async (req, res) => {
  try {
    const { task, type, priority } = req.body;
    if (!task) {
      return res.status(400).json({ error: 'task is required' });
    }
    const taskRecord = scheduler.submitTask({ task, type: type || 'default', priority: priority || 'normal' });
    res.json({ success: true, task: taskRecord });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/orchestration/tasks/:id — get task status
app.get('/api/orchestration/tasks/:id', async (req, res) => {
  try {
    const task = scheduler.getTaskStatus(req.params.id);
    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }
    res.json(task);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// POST /api/orchestration/decisions — trigger autonomous decision
app.post('/api/orchestration/decisions', async (req, res) => {
  try {
    const { context } = req.body;
    const decision = await decisionEngine.makeDecision(context || {});
    res.json({ success: true, decision });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/orchestration/stats — get orchestration stats
app.get('/api/orchestration/stats', async (req, res) => {
  try {
    res.json({
      scheduler: scheduler.getStats(),
      resources: resourceManager.getAllStats(),
      decisions: decisionEngine.getStats(),
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Governor server listening on port ${PORT}`));
