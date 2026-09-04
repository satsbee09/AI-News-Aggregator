const axios = require('axios');
const http = require('http');
const app = require('../server');

const TEST_PORT = 5007;
let server;

async function runPhase3AskTests() {
  console.log('--- STARTING PHASE 3 TEST: EXPRESS ASK / RAG PROXY ---');

  server = http.createServer(app);
  await new Promise((resolve) => server.listen(TEST_PORT, resolve));
  console.log(`[PASS] Test server started on port ${TEST_PORT}`);

  const client = axios.create({
    baseURL: `http://localhost:${TEST_PORT}/api`,
    validateStatus: () => true
  });

  try {
    // 1. Validation error on missing question
    console.log('\n1. Testing validation failure on empty question...');
    const resInvalid = await client.post('/ask', {
      email: 'test@example.com',
      question: ''
    });
    console.log(`   Response status: ${resInvalid.status}`);
    if (resInvalid.status === 422) {
      console.log('   [PASS] 422 returned on empty question.');
    } else {
      console.error(`   [FAIL] Expected 422, got ${resInvalid.status}`);
      process.exitCode = 1;
    }

    // 2. Valid proxy call
    console.log('\n2. Testing live RAG proxy call for "What are the latest AI news and breakthroughs?"...');
    const resProxy = await client.post('/ask', {
      email: 'satsbee4921@gmail.com',
      question: 'What are the latest AI news and breakthroughs?'
    });

    console.log(`   Response status: ${resProxy.status}`);
    if (resProxy.status === 200 && resProxy.data.status === 'success') {
      console.log(`   Answer snippet:\n   ${resProxy.data.answer.substring(0, 180)}...`);
      console.log(`   Sources count: ${resProxy.data.sources?.length || 0}`);
      if (resProxy.data.sources && resProxy.data.sources.length > 0) {
        console.log(`   Sample source: "${resProxy.data.sources[0].title}"`);
      }
      console.log('   [PASS] RAG question answering proxied successfully from Express -> FastAPI!');
    } else {
      console.error(`   [FAIL] RAG proxy failed: ${JSON.stringify(resProxy.data)}`);
      process.exitCode = 1;
    }

  } catch (err) {
    console.error(`[ERROR] Phase 3 Ask test error: ${err.message}`);
    process.exitCode = 1;
  } finally {
    if (server) {
      server.close();
      console.log('[PASS] Test server closed.');
    }
    process.exit(process.exitCode || 0);
  }
}

runPhase3AskTests();
