const express = require('express');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');

const router = express.Router();

// 1. POST /api/users (Create or Get User Profile)
router.post(
  '/',
  [body('email').isEmail().withMessage('Valid email is required').normalizeEmail()],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email } = req.body;
    try {
      let user = await User.findOne({ email });
      if (!user) {
        user = await User.create({ email });
        console.log(`[EXPRESS USER] Created new user: ${email}`);
      }
      return res.status(200).json(user);
    } catch (err) {
      console.error(`[EXPRESS USER ERROR] POST /api/users: ${err.message}`);
      return res.status(500).json({ error: 'Failed to process user' });
    }
  }
);

// 2. GET /api/users/:email (Fetch User Profile)
router.get('/:email', async (req, res) => {
  const email = req.params.email.toLowerCase().trim();
  try {
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(404).json({ error: `User with email '${email}' not found` });
    }
    return res.status(200).json(user);
  } catch (err) {
    console.error(`[EXPRESS USER ERROR] GET /api/users/:email: ${err.message}`);
    return res.status(500).json({ error: 'Failed to fetch user' });
  }
});

// 3. PUT /api/users/:email/topics (Update Topics Array)
router.put(
  '/:email/topics',
  [
    body('topics')
      .isArray({ min: 1 })
      .withMessage('At least one topic is required')
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    const email = req.params.email.toLowerCase().trim();
    const { topics } = req.body;

    const normalizedTopics = topics.map((t) => ({
      name: t.name.trim(),
      scope: t.scope || 'general',
      category: t.category || t.scope || 'general'
    }));

    try {
      const user = await User.findOneAndUpdate(
        { email },
        { $set: { topics: normalizedTopics } },
        { new: true, upsert: true }
      );
      return res.status(200).json(user);
    } catch (err) {
      console.error(`[EXPRESS USER ERROR] PUT /api/users/:email/topics: ${err.message}`);
      return res.status(500).json({ error: 'Failed to update topics' });
    }
  }
);

// 4. PUT /api/users/:email/schedule (Update Schedule Object)
router.put(
  '/:email/schedule',
  [
    body('time').optional().isString(),
    body('frequency').optional().isIn(['daily', 'every_6_hours', 'every_12_hours']),
    body('timezone').optional().isString()
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    const email = req.params.email.toLowerCase().trim();
    const { time, frequency, timezone } = req.body;

    const scheduleUpdate = {};
    if (time) scheduleUpdate['schedule.time'] = time;
    if (frequency) scheduleUpdate['schedule.frequency'] = frequency;
    if (timezone) scheduleUpdate['schedule.timezone'] = timezone;

    try {
      const user = await User.findOneAndUpdate(
        { email },
        { $set: scheduleUpdate },
        { new: true }
      );

      if (!user) {
        return res.status(404).json({ error: `User with email '${email}' not found` });
      }

      return res.status(200).json(user);
    } catch (err) {
      console.error(`[EXPRESS USER ERROR] PUT /api/users/:email/schedule: ${err.message}`);
      return res.status(500).json({ error: 'Failed to update schedule' });
    }
  }
);

const fastapiClient = require('../services/fastapiClient');

// 5. POST /api/users/:email/trigger (Manual Instant Digest Trigger)
router.post('/:email/trigger', async (req, res) => {
  const email = req.params.email.toLowerCase().trim();
  const dryRun = req.query.dry_run === 'true';

  try {
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(404).json({ error: `User with email '${email}' not found` });
    }

    if (!user.topics || user.topics.length === 0) {
      return res.status(400).json({ error: 'User has no configured topics' });
    }

    console.log(`[EXPRESS TRIGGER] Forwarding manual trigger for ${email} (dry_run: ${dryRun}) to FastAPI...`);
    const response = await fastapiClient.post('/internal/run-pipeline', {
      email: user.email,
      topics: user.topics,
      dry_run: dryRun
    });

    user.lastSentAt = new Date();
    await user.save();

    return res.status(200).json(response.data);
  } catch (err) {
    console.error(`[EXPRESS TRIGGER ERROR] POST /api/users/:email/trigger: ${err.message}`);
    if (err.response) {
      return res.status(err.response.status).json(err.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway: Python Intelligence Engine is currently unreachable'
    });
  }
});

module.exports = router;
