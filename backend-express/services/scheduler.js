const cron = require('node-cron');
const User = require('../models/User');
const fastapiClient = require('./fastapiClient');

// In-memory set to prevent concurrent pipeline runs for the same user
const activeJobs = new Set();

/**
 * Get current time in specified timezone formatted as "HH:MM" (24-hour).
 * @param {string} timezone - IANA timezone (e.g., 'Asia/Kolkata', 'UTC')
 * @returns {string} HH:MM string
 */
function getCurrentTimeInTimezone(timezone = 'Asia/Kolkata') {
  try {
    const formatter = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    return formatter.format(new Date());
  } catch (e) {
    // Fallback to UTC if timezone is invalid
    console.warn(`[SCHEDULER] Invalid timezone '${timezone}', falling back to UTC`);
    const now = new Date();
    return `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}`;
  }
}

/**
 * Check if the user is due for a scheduled digest.
 * @param {Object} user - Mongoose User document
 * @param {boolean} forceCheck - If true, bypasses time-of-day check (for manual testing)
 * @returns {boolean}
 */
function isUserDueForDigest(user, forceCheck = false) {
  if (!user || !user.email) return false;
  if (!user.topics || user.topics.length === 0) return false;

  if (forceCheck) return true;

  const schedule = user.schedule || { time: '07:30', frequency: 'daily', timezone: 'Asia/Kolkata' };
  const currentTime = getCurrentTimeInTimezone(schedule.timezone);
  const targetTime = schedule.time || '07:30';

  const now = Date.now();
  const lastSent = user.lastSentAt ? new Date(user.lastSentAt).getTime() : 0;
  const hoursSinceLastSent = (now - lastSent) / (1000 * 60 * 60);

  if (schedule.frequency === 'every_6_hours') {
    return hoursSinceLastSent >= 5.9;
  } else if (schedule.frequency === 'every_12_hours') {
    return hoursSinceLastSent >= 11.9;
  } else {
    // 'daily' frequency
    // Match current minute window AND verify not sent in the last 20 hours
    const isMatchingTime = (currentTime === targetTime);
    return isMatchingTime && (hoursSinceLastSent >= 20);
  }
}

/**
 * Execute the pipeline for a single user via FastAPI client.
 * @param {Object} user - Mongoose User document
 * @param {Object} options - Options { dryRun: false }
 */
async function executeUserPipeline(user, options = {}) {
  try {
    const payload = {
      email: user.email,
      topics: user.topics,
      dry_run: !!options.dryRun
    };
    
    console.log(`[SCHEDULER] Dispatching pipeline for ${user.email} (dry_run: ${payload.dry_run})...`);
    const response = await fastapiClient.post('/internal/run-pipeline', payload);
    console.log(`[SCHEDULER SUCCESS] Pipeline finished for ${user.email}:`, response.data);

    // Update lastSentAt in DB
    user.lastSentAt = new Date();
    await user.save();
    return response.data;
  } catch (err) {
    console.error(`[SCHEDULER ERROR] Failed pipeline for ${user.email}: ${err.message}`);
    if (err.response) {
      console.error(`  FastAPI response:`, err.response.data);
    }
    throw err;
  } finally {
    activeJobs.delete(user.email);
  }
}

/**
 * Check users and trigger pipeline if due.
 * @param {Object} options - Options { force: false, dryRun: false, targetEmail: null, waitForCompletion: false }
 */
async function checkAndTriggerSchedules(options = { force: false, dryRun: false, targetEmail: null, waitForCompletion: false }) {
  try {
    const query = options.targetEmail ? { email: options.targetEmail.toLowerCase().trim() } : {};
    const users = await User.find(query);
    console.log(`[SCHEDULER TICK] Checking schedules for ${users.length} user(s)...`);

    const executions = [];

    for (const user of users) {
      if (activeJobs.has(user.email)) {
        console.log(`[SCHEDULER] Job for ${user.email} is already running. Skipping.`);
        continue;
      }

      if (isUserDueForDigest(user, options.force)) {
        console.log(`[SCHEDULER] User ${user.email} is due for digest (TZ: ${user.schedule?.timezone || 'Asia/Kolkata'}). Triggering pipeline...`);
        
        activeJobs.add(user.email);
        const p = executeUserPipeline(user, options);
        executions.push(p);
      }
    }

    if (options.waitForCompletion) {
      await Promise.allSettled(executions);
    }
  } catch (err) {
    console.error(`[SCHEDULER TICK ERROR] ${err.message}`);
  }
}

/**
 * Start the cron scheduler (runs every minute).
 */
let cronTask = null;

function startScheduler() {
  if (cronTask) {
    console.log('[SCHEDULER] Cron task already running.');
    return;
  }

  // Run every minute: "* * * * *"
  cronTask = cron.schedule('* * * * *', async () => {
    await checkAndTriggerSchedules({ force: false, dryRun: false });
  });

  console.log('[SCHEDULER] Node-cron scheduler started (ticks every minute: * * * * *).');
}

function stopScheduler() {
  if (cronTask) {
    cronTask.stop();
    cronTask = null;
    console.log('[SCHEDULER] Node-cron scheduler stopped.');
  }
}

module.exports = {
  startScheduler,
  stopScheduler,
  checkAndTriggerSchedules,
  executeUserPipeline,
  isUserDueForDigest,
  getCurrentTimeInTimezone
};
