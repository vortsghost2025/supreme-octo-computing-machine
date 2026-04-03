const {
  ClusterScheduler,
  ResourceManager,
  AutonomousDecisionEngine,
} = require('./medical/intelligence/autonomous-orchestration');

const http = require('http');

function makeRequest(options, body = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function runTests() {
  const HOST = process.env.HOST || 'localhost';
  const PORT = process.env.PORT || 4001;
  const BASE = `http://${HOST}:${PORT}`;
  
  console.log('Testing orchestration endpoints...\n');
  let passed = 0;
  let failed = 0;

  try {
    // Test 1: Submit a task
    console.log('Test 1: POST /api/orchestration/tasks');
    const taskRes = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/orchestration/tasks',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, { task: 'Test task', type: 'test', priority: 'high' });
    
    if (taskRes.status === 200 && taskRes.body.success && taskRes.body.task) {
      console.log('  ✓ Task submitted successfully');
      passed++;
      const taskId = taskRes.body.task.id;

      // Test 2: Get task status
      console.log('Test 2: GET /api/orchestration/tasks/:id');
      const statusRes = await makeRequest({
        hostname: HOST,
        port: PORT,
        path: `/api/orchestration/tasks/${taskId}`,
        method: 'GET'
      });
      
      if (statusRes.status === 200 && statusRes.body.id === taskId) {
        console.log('  ✓ Task status retrieved');
        passed++;
      } else {
        console.log('  ✗ Failed:', statusRes.body);
        failed++;
      }
    } else {
      console.log('  ✗ Failed:', taskRes.body);
      failed++;
    }

    // Test 3: Trigger autonomous decision
    console.log('Test 3: POST /api/orchestration/decisions');
    const decisionRes = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/orchestration/decisions',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, { context: { type: 'test', data: 'sample' } });
    
    if (decisionRes.status === 200 && decisionRes.body.success && decisionRes.body.decision) {
      console.log('  ✓ Decision triggered');
      passed++;
    } else {
      console.log('  ✗ Failed:', decisionRes.body);
      failed++;
    }

    // Test 4: Get orchestration stats
    console.log('Test 4: GET /api/orchestration/stats');
    const statsRes = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/orchestration/stats',
      method: 'GET'
    });
    
    if (statsRes.status === 200 && statsRes.body.scheduler && statsRes.body.resources && statsRes.body.decisions) {
      console.log('  ✓ Stats retrieved');
      passed++;
    } else {
      console.log('  ✗ Failed:', statsRes.body);
      failed++;
    }

    // Test 5: Import classes directly
    console.log('Test 5: Direct class imports');
    const testScheduler = new ClusterScheduler({ maxWorkers: 5, minWorkers: 1 });
    const testResource = new ResourceManager();
    const testDecision = new AutonomousDecisionEngine();
    
    if (testScheduler && testResource && testDecision) {
      console.log('  ✓ Classes imported and instantiated');
      passed++;
    } else {
      console.log('  ✗ Failed to instantiate classes');
      failed++;
    }

  } catch (e) {
    console.error('Test error:', e.message);
    failed++;
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();