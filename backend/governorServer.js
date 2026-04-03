const express = require('express');
const bodyParser = require('body-parser');

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

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Governor server listening on port ${PORT}`));
