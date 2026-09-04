require('dotenv').config();
const connectDB = require('../config/db');
const mongoose = require('mongoose');

async function testPhase1() {
  console.log('1. Connecting to MongoDB via Mongoose...');
  await connectDB();
  console.log('   [SUCCESS] Mongoose connected successfully! ReadyState:', mongoose.connection.readyState);

  console.log('\n2. Testing Express Server Import & Initialization...');
  const app = require('../server');

  console.log('\n[SUCCESS] Node/Express Phase 1 Skeleton & MongoDB connection verified!');
  await mongoose.disconnect();
  process.exit(0);
}

testPhase1().catch((err) => {
  console.error('[FAILED] Phase 1 test failed:', err);
  process.exit(1);
});
