const http = require('http');
const app = require('../server');

const TEST_PORT = 5008;

function runPhase4Tests() {
  const server = http.createServer(app);

  server.listen(TEST_PORT, async () => {
    console.log(`\n--- STARTING PHASE 4 TEST: EXPRESS LIVE SEARCH PROXY ---`);
    console.log(`[PASS] Test server started on port ${TEST_PORT}\n`);

    try {
      // 1. Validation test on empty query
      console.log('1. Testing validation failure on empty query...');
      const invalidRes = await fetch(`http://localhost:${TEST_PORT}/api/search/live`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: '' })
      });

      console.log(`   Response status: ${invalidRes.status}`);
      if (invalidRes.status === 422) {
        console.log('   [PASS] 422 returned on empty query.\n');
      } else {
        throw new Error(`Expected 422, got ${invalidRes.status}`);
      }

      // 2. Live proxy call
      console.log('2. Testing live search proxy call for "latest tech news"...');
      const validRes = await fetch(`http://localhost:${TEST_PORT}/api/search/live`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'latest tech news',
          topic: 'tech'
        })
      });

      console.log(`   Response status: ${validRes.status}`);
      const data = await validRes.json();
      console.log(`   Query returned: "${data.query}"`);
      console.log(`   Results count: ${data.count}`);
      if (data.results && data.results.length > 0) {
        console.log(`   Sample result title: "${data.results[0].title}" (${data.results[0].source})`);
      }
      
      if (validRes.status === 200 && data.status === 'success') {
        console.log('   [PASS] Live search proxied successfully from Express -> FastAPI!\n');
      } else {
        throw new Error(`Proxy call failed with status ${validRes.status}`);
      }

    } catch (err) {
      console.error(`[FAIL] Phase 4 test failed:`, err);
      process.exit(1);
    } finally {
      server.close();
      console.log('[PASS] Test server closed.\n');
      process.exit(0);
    }
  });
}

runPhase4Tests();
