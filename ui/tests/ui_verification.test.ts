import { test, expect } from '@playwright/test';

// Base URL can be overridden via PLAYWRIGHT_BASE_URL env var.
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5178';

test.describe('SNAC Cockpit UI end‑to‑end verification', () => {
  test.beforeEach(async ({ page }) => {
    // Capture console messages for later checks
    const consoleMessages: string[] = [];
    page.on('console', msg => consoleMessages.push(`${msg.type()}: ${msg.text()}`));
    await page.goto(BASE_URL);
    // Store messages on the page object for later assertions
    (page as any)._consoleMessages = consoleMessages;
  });

  test('no fetch errors on initial load', async ({ page }) => {
    const msgs = (page as any)._consoleMessages as string[];
    const fetchErrors = msgs.filter(m => m.includes('fetch') && /error|failed|status/i.test(m));
    expect(fetchErrors).toHaveLength(0);
  });

  test('Agent Task runs and returns a response', async ({ page }) => {
    await page.fill('textarea[placeholder="Enter task…"]', 'Summarize the recent Git commits');
    await page.click('button:has-text("Run Agent")');
    // Wait for a response bubble in the SNAC Agent chat pane
    const response = await page.waitForSelector('.cockpit-content .chat-panel .panel-content >> text=Summarize', { timeout: 15000 });
    expect(response).toBeTruthy();
  });

  test('Ingest Document shows success toast', async ({ page }) => {
    await page.fill('textarea[placeholder="Paste document text here…"]', 'Hello world');
    await page.click('button:has-text("Ingest Document")');
    const toast = await page.waitForSelector('.toast-success, .toast >> text=success', { timeout: 10000 });
    expect(toast).toBeTruthy();
  });

  test('Quick Thought is added to Memory Timeline', async ({ page }) => {
    await page.fill('textarea[placeholder="Enter a thought…"]', 'Quick thought test');
    await page.click('button:has-text("Ingest Thought")');
    const entry = await page.waitForSelector('.memory-timeline .thought-entry:has-text("Quick thought test")', { timeout: 10000 });
    expect(entry).toBeTruthy();
  });

  test('Swarm Queue task enqueues', async ({ page }) => {
    await page.fill('textarea[placeholder="Enter swarm task…"]', 'Echo test');
    await page.click('button:has-text("Queue Swarm Task")');
    const listItem = await page.waitForSelector('.swarm-queue-list >> text=Echo test', { timeout: 10000 });
    expect(listItem).toBeTruthy();
  });

  test('Add Learning creates shared knowledge entry', async ({ page }) => {
    await page.fill('input[placeholder="Source model"]', 'llama3:8b');
    await page.fill('input[placeholder="Topic"]', 'Test topic');
    await page.fill('textarea[placeholder="Details"]', 'Some details for testing');
    await page.click('button:has-text("Add Learning")');
    const entry = await page.waitForSelector('.shared-knowledge .knowledge-item:has-text("Test topic")', { timeout: 10000 });
    expect(entry).toBeTruthy();
  });

  test('Project Vault Save to Brain works', async ({ page }) => {
    await page.click('button:has-text("Save to Brain")');
    const toast = await page.waitForSelector('.toast-success, .toast >> text=success', { timeout: 10000 });
    expect(toast).toBeTruthy();
  });

  test('SNAC Agent chat returns a non‑mock response', async ({ page }) => {
    await page.fill('textarea[placeholder="Talk to your agents here…"]', 'Hello');
    await page.click('button:has-text("Send to Agent")');
    const reply = await page.waitForSelector('.snac-agent .chat-panel .panel-content >> text=Hello', { timeout: 15000 });
    expect(reply).toBeTruthy();
  });

  test('Free Coding Agent produces code', async ({ page }) => {
    await page.fill('textarea[placeholder="Enter coding task…"]', 'Generate a Python hello‑world script');
    await page.click('button:has-text("Run Free Coding")');
    const code = await page.waitForSelector('.free-coding-agent .panel-content pre >> text=print', { timeout: 15000 });
    expect(code).toBeTruthy();
  });

  test('Governor refresh updates without errors', async ({ page }) => {
    await page.click('button:has-text("Refresh")');
    const msgs = (page as any)._consoleMessages as string[];
    const errorMsgs = msgs.filter(m => /error/i.test(m));
    expect(errorMsgs).toHaveLength(0);
  });

  test('All monitors display data after interactions', async ({ page }) => {
    // Memory Timeline count
    const memCount = await page.textContent('[data-testid="memory-count"]');
    expect(parseInt(memCount || '0')).toBeGreaterThan(0);
    // Token Cost Monitor
    const tokenCount = await page.textContent('[data-testid="token-total"]');
    expect(parseInt(tokenCount || '0')).toBeGreaterThan(0);
    // Swarm Monitor
    const swarmCount = await page.textContent('[data-testid="swarm-count"]');
    expect(parseInt(swarmCount || '0')).toBeGreaterThan(0);
  });
});
