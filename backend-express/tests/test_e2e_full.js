require('dotenv').config();
const axios = require('axios');
const http = require('http');
const app = require('../server');
const User = require('../models/User');
const mongoose = require('mongoose');

const E2E_PORT = 5005;
let server;

async function runE2EFullTests() {
  console.log('===============================================================');
  console.log('--- STARTING COMPLETE END-TO-END TWO-SERVICE ARCHITECTURE TEST ---');
  console.log('===============================================================');

  // Start Express Test Server
  server = http.createServer(app);
  await new Promise((resolve) => server.listen(E2E_PORT, resolve));
  console.log(`[PASS] Service A (Express) test instance running on port ${E2E_PORT}`);

  const client = axios.create({
    baseURL: `http://localhost:${E2E_PORT}/api`,
    validateStatus: () => true
  });

  const testEmail = 'e2e_verified_user@example.com';

  try {
    // 1. Health Check
    console.log('\n[TEST 1] Express Health Check (GET /api/health)...');
    const resHealth = await client.get('/health');
    console.log(`   Response status: ${resHealth.status}`);
    console.log(`   Health payload:`, resHealth.data);
    if (resHealth.status === 200 && resHealth.data.status === 'healthy') {
      console.log('   [PASS] Service A is healthy and connected to MongoDB!');
    } else {
      throw new Error(`Health check failed: ${JSON.stringify(resHealth.data)}`);
    }

    // 2. User Account Creation
    console.log('\n[TEST 2] User Account Creation (POST /api/users)...');
    const resCreate = await client.post('/users', { email: testEmail });
    console.log(`   Response status: ${resCreate.status}`);
    if (resCreate.status === 200 && resCreate.data.email === testEmail) {
      console.log(`   [PASS] User account initialized: ${resCreate.data.email}`);
    } else {
      throw new Error(`User creation failed: ${JSON.stringify(resCreate.data)}`);
    }

    // 3. User Topic Preferences Update
    console.log('\n[TEST 3] Topic Preferences Update (PUT /api/users/:email/topics)...');
    const topicsPayload = [
      { name: 'AI & Machine Learning', scope: 'ai', category: 'ai' },
      { name: 'Delhi NCR Weather', scope: 'weather', category: 'weather' }
    ];
    const resTopics = await client.put(`/users/${testEmail}/topics`, { topics: topicsPayload });
    console.log(`   Response status: ${resTopics.status}`);
    if (resTopics.status === 200 && resTopics.data.topics.length === 2) {
      console.log(`   [PASS] Saved ${resTopics.data.topics.length} topic preferences in MongoDB.`);
    } else {
      throw new Error(`Topic update failed: ${JSON.stringify(resTopics.data)}`);
    }

    // 4. Delivery Schedule Configuration
    console.log('\n[TEST 4] Delivery Schedule Update (PUT /api/users/:email/schedule)...');
    const schedulePayload = {
      time: '08:00',
      frequency: 'daily',
      timezone: 'Asia/Kolkata'
    };
    const resSched = await client.put(`/users/${testEmail}/schedule`, schedulePayload);
    console.log(`   Response status: ${resSched.status}`);
    if (resSched.status === 200 && resSched.data.schedule.time === '08:00') {
      console.log(`   [PASS] Configured delivery schedule: ${resSched.data.schedule.time} (${resSched.data.schedule.frequency})`);
    } else {
      throw new Error(`Schedule update failed: ${JSON.stringify(resSched.data)}`);
    }

    // 5. On-Demand Live News Preview Proxy
    console.log('\n[TEST 5] Live News Preview Proxy (POST /api/news/preview)...');
    const resPreview = await client.post('/news/preview', {
      topics: [{ name: 'Frontier AI & LLMs', scope: 'ai', category: 'ai' }]
    });
    console.log(`   Response status: ${resPreview.status}`);
    if (resPreview.status === 200 && resPreview.data.status === 'success') {
      const topicCount = resPreview.data.topics?.length || 0;
      console.log(`   [PASS] Live news preview returned ${topicCount} topic(s) with summarized articles.`);
    } else {
      throw new Error(`News preview failed: ${JSON.stringify(resPreview.data)}`);
    }

    // 6. Manual Pipeline Trigger
    console.log('\n[TEST 6] Manual Pipeline Trigger (POST /api/users/:email/trigger?dry_run=true)...');
    const resTrigger = await client.post(`/users/${testEmail}/trigger?dry_run=true`);
    console.log(`   Response status: ${resTrigger.status}`);
    console.log(`   Trigger payload:`, resTrigger.data);
    if (resTrigger.status === 200 && resTrigger.data.status === 'success') {
      console.log(`   [PASS] Intelligence pipeline completed: ${resTrigger.data.stories_curated} stories curated.`);
    } else {
      throw new Error(`Manual trigger failed: ${JSON.stringify(resTrigger.data)}`);
    }

    // 7. Verify Security (Calling FastAPI internal endpoint directly without secret fails)
    console.log('\n[TEST 7] Security Verification: FastAPI direct access without secret...');
    const fastApiClientDirect = axios.create({
      baseURL: 'http://localhost:8000',
      validateStatus: () => true
    });
    const resUnauthorized = await fastApiClientDirect.post('/internal/news-preview', {
      topics: [{ name: 'AI', scope: 'ai', category: 'ai' }]
    });
    console.log(`   Direct call without secret status: ${resUnauthorized.status}`);
    if (resUnauthorized.status === 401) {
      console.log('   [PASS] Direct FastAPI internal access without X-Internal-Secret is strictly blocked (HTTP 401)!');
    } else {
      throw new Error(`Security verification failed. Expected 401, got ${resUnauthorized.status}`);
    }

    // Clean up test user
    await User.deleteOne({ email: testEmail });
    console.log(`\n[CLEANUP] Deleted test user: ${testEmail}`);

    console.log('\n===============================================================');
    console.log('>>> ALL END-TO-END TESTS PASSED COMPLETELY! <<<');
    console.log('===============================================================');

  } catch (err) {
    console.error(`\n[FATAL E2E ERROR] ${err.message}`);
    process.exitCode = 1;
  } finally {
    if (server) {
      server.close();
    }
    await mongoose.disconnect();
    process.exit(process.exitCode || 0);
  }
}

runE2EFullTests();
