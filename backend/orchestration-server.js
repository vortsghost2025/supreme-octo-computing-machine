const express = require('express');
const bodyParser = require('body-parser');

const {
  ClusterScheduler,
  ResourceManager,
  AutonomousDecisionEngine,
} = require('../medical/intelligence/autonomous-orchestration');

const app = express();
app.use(bodyParser.json());

const scheduler = new ClusterScheduler({ maxWorkers: 10, minWorkers: 2 });
const resourceManager = new ResourceManager();
const decisionEngine = new AutonomousDecisionEngine();

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

app.post('/api/orchestration/decisions', async (req, res) => {
  try {
    const { context } = req.body;
    const decision = await decisionEngine.makeDecision(context || {});
    res.json({ success: true, decision });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

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

const PORT = process.env.PORT || 4001;
app.listen(PORT, () => console.log(`Orchestration server listening on port ${PORT}`));