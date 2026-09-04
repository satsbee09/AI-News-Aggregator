require('dotenv').config();
const connectDB = require('../config/db');
const User = require('../models/User');
const {
  getCurrentTimeInTimezone,
  isUserDueForDigest,
  checkAndTriggerSchedules
} = require('../services/scheduler');
const mongoose = require('mongoose');

async function runPhase4Tests() {
  console.log('--- STARTING PHASE 4 TEST: EXPRESS NODE-CRON SCHEDULER ---');

  await connectDB();
  // Wait for connection to be ready
  if (mongoose.connection.readyState !== 1) {
    await new Promise((resolve) => mongoose.connection.once('open', resolve));
  }
  console.log('[PASS] Connected to MongoDB Atlas.');

  try {
    // 1. Test Timezone calculation
    console.log('\n1. Testing timezone formatting...');
    const kolkataTime = getCurrentTimeInTimezone('Asia/Kolkata');
    const nyTime = getCurrentTimeInTimezone('America/New_York');
    const utcTime = getCurrentTimeInTimezone('UTC');
    console.log(`   Asia/Kolkata time: ${kolkataTime}`);
    console.log(`   America/New_York time: ${nyTime}`);
    console.log(`   UTC time: ${utcTime}`);

    if (/^\d{2}:\d{2}$/.test(kolkataTime) && /^\d{2}:\d{2}$/.test(nyTime)) {
      console.log('   [PASS] Timezone calculation returned valid HH:MM formats.');
    } else {
      console.error('   [FAIL] Invalid HH:MM time format.');
      process.exitCode = 1;
    }

    // 2. Test isUserDueForDigest logic
    console.log('\n2. Testing schedule matching logic...');
    const mockUserDue = {
      email: 'test_sched@example.com',
      topics: [{ name: 'AI & Machine Learning' }],
      schedule: {
        time: kolkataTime,
        frequency: 'daily',
        timezone: 'Asia/Kolkata'
      },
      lastSentAt: new Date(Date.now() - 25 * 60 * 60 * 1000) // 25 hours ago
    };

    const mockUserNotDue = {
      email: 'test_sched@example.com',
      topics: [{ name: 'AI & Machine Learning' }],
      schedule: {
        time: '03:15', // Different time
        frequency: 'daily',
        timezone: 'Asia/Kolkata'
      },
      lastSentAt: new Date(Date.now() - 1 * 60 * 60 * 1000) // 1 hour ago
    };

    const isDue = isUserDueForDigest(mockUserDue);
    const isNotDue = isUserDueForDigest(mockUserNotDue);
    console.log(`   Mock user due evaluation (matching time & >20h): ${isDue}`);
    console.log(`   Mock user not due evaluation: ${isNotDue}`);

    if (isDue === true && isNotDue === false) {
      console.log('   [PASS] Digest due calculation works correctly.');
    } else {
      console.error('   [FAIL] Schedule evaluation failed.');
      process.exitCode = 1;
    }

    // 3. Test triggering pipeline via scheduler service (dry_run: true)
    console.log('\n3. Testing pipeline execution via checkAndTriggerSchedules (dry-run)...');
    const testEmail = 'phase4_test_user@example.com';
    await User.findOneAndUpdate(
      { email: testEmail },
      {
        email: testEmail,
        topics: [{ name: 'AI & Machine Learning', scope: 'ai', category: 'ai' }],
        schedule: {
          time: kolkataTime,
          frequency: 'daily',
          timezone: 'Asia/Kolkata'
        },
        lastSentAt: null
      },
      { upsert: true, new: true }
    );
    console.log(`   Created/updated test user: ${testEmail}`);

    console.log('   Triggering checkAndTriggerSchedules with force=true, dryRun=true, targetEmail=phase4_test_user@example.com...');
    await checkAndTriggerSchedules({
      force: true,
      dryRun: true,
      targetEmail: testEmail,
      waitForCompletion: true
    });

    const updatedUser = await User.findOne({ email: testEmail });
    console.log(`   User lastSentAt after trigger: ${updatedUser?.lastSentAt}`);

    if (updatedUser && updatedUser.lastSentAt) {
      console.log('   [PASS] Scheduler successfully executed pipeline and updated lastSentAt in MongoDB!');
    } else {
      console.error('   [FAIL] User lastSentAt was not updated.');
      process.exitCode = 1;
    }

    // Clean up test user
    await User.deleteOne({ email: testEmail });
    console.log(`   Cleaned up test user: ${testEmail}`);

  } catch (err) {
    console.error(`[ERROR] Phase 4 test failed: ${err.message}`);
    process.exitCode = 1;
  } finally {
    await mongoose.disconnect();
    console.log('[PASS] MongoDB disconnected. Phase 4 test completed.');
    process.exit(process.exitCode || 0);
  }
}

runPhase4Tests();
