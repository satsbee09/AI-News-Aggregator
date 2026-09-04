process.env.NODE_ENV = 'test';
require('dotenv').config();
const connectDB = require('../config/db');
const mongoose = require('mongoose');
const User = require('../models/User');

async function testPhase2() {
  console.log('1. Connecting to MongoDB Atlas...');
  await connectDB();

  const testEmail = 'express_test_user@example.com';
  await User.deleteOne({ email: testEmail });

  console.log(`\n2. Testing User Creation in Mongoose: ${testEmail}...`);
  const user = await User.create({ email: testEmail });
  console.log(`   [SUCCESS] Created User: ${user.email} (Default topics: ${user.topics.length})`);
  if (user.topics.length < 1) throw new Error('Default topics missing');

  console.log('\n3. Testing Updating Topics...');
  const updatedTopics = [
    { name: 'Frontier AI & LLMs', scope: 'ai', category: 'ai' },
    { name: 'Noida Tech Startups', scope: 'local', category: 'local' },
    { name: 'Cricket & IPL', scope: 'sports', category: 'sports' }
  ];
  user.topics = updatedTopics;
  await user.save();
  console.log(`   [SUCCESS] Updated topics count: ${user.topics.length}`);

  console.log('\n4. Testing Updating Schedule...');
  user.schedule.time = '07:00';
  user.schedule.frequency = 'daily';
  user.schedule.timezone = 'Asia/Kolkata';
  await user.save();
  console.log(`   [SUCCESS] Updated schedule: ${user.schedule.time} (${user.schedule.frequency})`);

  console.log('\n5. Verifying DB Retrieval from MongoDB...');
  const retrieved = await User.findOne({ email: testEmail });
  if (!retrieved || retrieved.topics.length !== 3) throw new Error('Retrieval verification failed');
  console.log(`   [SUCCESS] Retrieved verified user: ${retrieved.email}`);

  await mongoose.disconnect();
  console.log('\n[SUCCESS] Node/Express Phase 2 User & Topic Models verified completely!');
  process.exit(0);
}

testPhase2().catch((err) => {
  console.error('[FAILED] Phase 2 test failed:', err);
  process.exit(1);
});
