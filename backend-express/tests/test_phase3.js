const axios = require('axios');
const http = require('http');
const app = require('../server');

const TEST_PORT = 5003;
let server;

async function runPhase3Tests() {
  console.log('--- STARTING PHASE 3 TEST: EXPRESS NEWS PREVIEW PROXY ---');

  // Start test Express server
  server = http.createServer(app);
  await new Promise((resolve) => server.listen(TEST_PORT, resolve));
  console.log(`[PASS] Test server started on port ${TEST_PORT}`);

  const client = axios.create({
    baseURL: `http://localhost:${TEST_PORT}/api`,
    validateStatus: () => true // Don't throw on non-2xx
  });

  try {
    // 1. Test 422 on empty topics
    console.log('\n1. Testing validation failure on empty topics...');
    const resEmpty = await client.post('/news/preview', { topics: [] });
    console.log(`   Response status: ${resEmpty.status}`);
    if (resEmpty.status === 422) {
      console.log('   [PASS] 422 returned on empty topics.');
    } else {
      console.error(`   [FAIL] Expected 422, got ${resEmpty.status}`);
      process.exitCode = 1;
    }

    // 2. Test valid proxy call to FastAPI /internal/news-preview
    console.log('\n2. Testing live news preview proxy call for ["AI & Machine Learning"]...');
    const resProxy = await client.post('/news/preview', {
      topics: ['AI & Machine Learning']
    });
    console.log(`   Response status: ${resProxy.status}`);
    console.log(`   Response data keys: ${Object.keys(resProxy.data).join(', ')}`);
    
    if (resProxy.status === 200 && resProxy.data.status === 'success') {
      const topicCount = resProxy.data.topics ? resProxy.data.topics.length : 0;
      console.log(`   Topics received: ${topicCount}`);
      if (topicCount > 0) {
        const firstTopic = resProxy.data.topics[0];
        console.log(`   Topic: ${firstTopic.topic_name} (${firstTopic.articles ? firstTopic.articles.length : 0} articles)`);
        if (firstTopic.articles && firstTopic.articles.length > 0) {
          console.log(`   Sample article title: "${firstTopic.articles[0].title}"`);
        }
      }
      console.log('   [PASS] Live news preview proxied successfully from Express -> FastAPI!');
    } else {
      console.error(`   [FAIL] Preview proxy failed: ${JSON.stringify(resProxy.data)}`);
      process.exitCode = 1;
    }

  } catch (err) {
    console.error(`[ERROR] Phase 3 test error: ${err.message}`);
    process.exitCode = 1;
  } finally {
    if (server) {
      server.close();
      console.log('[PASS] Test server closed.');
    }
    // Allow clean exit
    process.exit(process.exitCode || 0);
  }
}

runPhase3Tests();
