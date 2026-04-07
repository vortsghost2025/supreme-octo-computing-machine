# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/ui_verification.test.ts >> SNAC Cockpit UI end‑to‑end verification >> Governor refresh updates without errors
- Location: tests/ui_verification.test.ts:80:3

# Error details

```
<<<<<<< Updated upstream
Error: browserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /home/agent/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-client-side-phishing-detection --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-extensions --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints --enable-features=CDPScreenshotNewSurface --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --edge-skip-compat-layer-relaunch --enable-automation --disable-infobars --disable-search-engine-choice-screen --disable-sync --enable-unsafe-swiftshader --headless --hide-scrollbars --mute-audio --blink-settings=primaryHoverType=2,availableHoverTypes=2,primaryPointerType=4,availablePointerTypes=4 --no-sandbox --user-data-dir=/tmp/playwright_chromiumdev_profile-SYDI1I --remote-debugging-pipe --no-startup-window
<launched> pid=2631
[pid=2631][err] /home/agent/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell: error while loading shared libraries: libatk-1.0.so.0: cannot open shared object file: No such file or directory
Call log:
  - <launching> /home/agent/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-client-side-phishing-detection --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-extensions --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints --enable-features=CDPScreenshotNewSurface --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --edge-skip-compat-layer-relaunch --enable-automation --disable-infobars --disable-search-engine-choice-screen --disable-sync --enable-unsafe-swiftshader --headless --hide-scrollbars --mute-audio --blink-settings=primaryHoverType=2,availableHoverTypes=2,primaryPointerType=4,availablePointerTypes=4 --no-sandbox --user-data-dir=/tmp/playwright_chromiumdev_profile-SYDI1I --remote-debugging-pipe --no-startup-window
  - <launched> pid=2631
  - [pid=2631][err] /home/agent/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell: error while loading shared libraries: libatk-1.0.so.0: cannot open shared object file: No such file or directory
  - [pid=2631] <gracefully close start>
  - [pid=2631] <kill>
  - [pid=2631] <will force kill>
  - [pid=2631] exception while trying to kill process: Error: kill ESRCH
  - [pid=2631] <process did exit: exitCode=127, signal=null>
  - [pid=2631] starting temporary directories cleanup
  - [pid=2631] finished temporary directories cleanup
  - [pid=2631] <gracefully close end>

=======
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:5178/
Call log:
  - navigating to "http://127.0.0.1:5178/", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | // Base URL can be overridden via PLAYWRIGHT_BASE_URL env var.
  4  | const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5178';
  5  | 
  6  | test.describe('SNAC Cockpit UI end‑to‑end verification', () => {
  7  |   test.beforeEach(async ({ page }) => {
  8  |     // Capture console messages for later checks
  9  |     const consoleMessages: string[] = [];
  10 |     page.on('console', msg => consoleMessages.push(`${msg.type()}: ${msg.text()}`));
> 11 |     await page.goto(BASE_URL);
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:5178/
  12 |     // Store messages on the page object for later assertions
  13 |     (page as any)._consoleMessages = consoleMessages;
  14 |   });
  15 | 
  16 |   test('no fetch errors on initial load', async ({ page }) => {
  17 |     const msgs = (page as any)._consoleMessages as string[];
  18 |     const fetchErrors = msgs.filter(m => m.includes('fetch') && /error|failed|status/i.test(m));
  19 |     expect(fetchErrors).toHaveLength(0);
  20 |   });
  21 | 
  22 |   test('Agent Task runs and returns a response', async ({ page }) => {
  23 |     await page.fill('textarea[placeholder="Enter task…"]', 'Summarize the recent Git commits');
  24 |     await page.click('button:has-text("Run Agent")');
  25 |     // Wait for a response bubble in the SNAC Agent chat pane
  26 |     const response = await page.waitForSelector('.cockpit-content .chat-panel .panel-content >> text=Summarize', { timeout: 15000 });
  27 |     expect(response).toBeTruthy();
  28 |   });
  29 | 
  30 |   test('Ingest Document shows success toast', async ({ page }) => {
  31 |     await page.fill('textarea[placeholder="Paste document text here…"]', 'Hello world');
  32 |     await page.click('button:has-text("Ingest Document")');
  33 |     const toast = await page.waitForSelector('.toast-success, .toast >> text=success', { timeout: 10000 });
  34 |     expect(toast).toBeTruthy();
  35 |   });
  36 | 
  37 |   test('Quick Thought is added to Memory Timeline', async ({ page }) => {
  38 |     await page.fill('textarea[placeholder="Enter a thought…"]', 'Quick thought test');
  39 |     await page.click('button:has-text("Ingest Thought")');
  40 |     const entry = await page.waitForSelector('.memory-timeline .thought-entry:has-text("Quick thought test")', { timeout: 10000 });
  41 |     expect(entry).toBeTruthy();
  42 |   });
  43 | 
  44 |   test('Swarm Queue task enqueues', async ({ page }) => {
  45 |     await page.fill('textarea[placeholder="Enter swarm task…"]', 'Echo test');
  46 |     await page.click('button:has-text("Queue Swarm Task")');
  47 |     const listItem = await page.waitForSelector('.swarm-queue-list >> text=Echo test', { timeout: 10000 });
  48 |     expect(listItem).toBeTruthy();
  49 |   });
  50 | 
  51 |   test('Add Learning creates shared knowledge entry', async ({ page }) => {
  52 |     await page.fill('input[placeholder="Source model"]', 'llama3:8b');
  53 |     await page.fill('input[placeholder="Topic"]', 'Test topic');
  54 |     await page.fill('textarea[placeholder="Details"]', 'Some details for testing');
  55 |     await page.click('button:has-text("Add Learning")');
  56 |     const entry = await page.waitForSelector('.shared-knowledge .knowledge-item:has-text("Test topic")', { timeout: 10000 });
  57 |     expect(entry).toBeTruthy();
  58 |   });
  59 | 
  60 |   test('Project Vault Save to Brain works', async ({ page }) => {
  61 |     await page.click('button:has-text("Save to Brain")');
  62 |     const toast = await page.waitForSelector('.toast-success, .toast >> text=success', { timeout: 10000 });
  63 |     expect(toast).toBeTruthy();
  64 |   });
  65 | 
  66 |   test('SNAC Agent chat returns a non‑mock response', async ({ page }) => {
  67 |     await page.fill('textarea[placeholder="Talk to your agents here…"]', 'Hello');
  68 |     await page.click('button:has-text("Send to Agent")');
  69 |     const reply = await page.waitForSelector('.snac-agent .chat-panel .panel-content >> text=Hello', { timeout: 15000 });
  70 |     expect(reply).toBeTruthy();
  71 |   });
  72 | 
  73 |   test('Free Coding Agent produces code', async ({ page }) => {
  74 |     await page.fill('textarea[placeholder="Enter coding task…"]', 'Generate a Python hello‑world script');
  75 |     await page.click('button:has-text("Run Free Coding")');
  76 |     const code = await page.waitForSelector('.free-coding-agent .panel-content pre >> text=print', { timeout: 15000 });
  77 |     expect(code).toBeTruthy();
  78 |   });
  79 | 
  80 |   test('Governor refresh updates without errors', async ({ page }) => {
  81 |     await page.click('button:has-text("Refresh")');
  82 |     const msgs = (page as any)._consoleMessages as string[];
  83 |     const errorMsgs = msgs.filter(m => /error/i.test(m));
  84 |     expect(errorMsgs).toHaveLength(0);
  85 |   });
  86 | 
  87 |   test('All monitors display data after interactions', async ({ page }) => {
  88 |     // Memory Timeline count
  89 |     const memCount = await page.textContent('.memory-timeline .count');
  90 |     expect(parseInt(memCount || '0')).toBeGreaterThan(0);
  91 |     // Token Cost Monitor
  92 |     const tokenCount = await page.textContent('.token-cost-monitor .count');
  93 |     expect(parseInt(tokenCount || '0')).toBeGreaterThan(0);
  94 |     // Swarm Monitor
  95 |     const swarmCount = await page.textContent('.swarm-monitor .count');
  96 |     expect(parseInt(swarmCount || '0')).toBeGreaterThan(0);
  97 |   });
  98 | });
  99 | 
>>>>>>> Stashed changes
```