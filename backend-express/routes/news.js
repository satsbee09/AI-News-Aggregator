const express = require('express');
const { body, validationResult } = require('express-validator');
const fastapiClient = require('../services/fastapiClient');
const User = require('../models/User');

const router = express.Router();

// POST /api/news/preview (Proxy live news preview request to FastAPI)
router.post(
  '/preview',
  async (req, res) => {
    let { topics, email } = req.body;

    // If email provided without topics, load from MongoDB
    if ((!topics || topics.length === 0) && email) {
      try {
        const user = await User.findOne({ email: email.toLowerCase().trim() });
        if (user && user.topics && user.topics.length > 0) {
          topics = user.topics;
        }
      } catch (e) {
        console.error(`[EXPRESS NEWS PREVIEW ERROR] Finding user: ${e.message}`);
      }
    }

    if (!topics || !Array.isArray(topics) || topics.length === 0) {
      return res.status(422).json({ error: 'At least one topic must be provided for news preview' });
    }

    try {
      console.log(`[EXPRESS PROXY] Forwarding news preview for ${topics.length} topic(s) to FastAPI...`);
      const response = await fastapiClient.post('/internal/news-preview', { topics });
      return res.status(200).json(response.data);
    } catch (err) {
      console.error(`[EXPRESS PROXY ERROR] FastAPI /internal/news-preview failed: ${err.message}`);
      if (err.response) {
        return res.status(err.response.status).json({
          error: 'FastAPI service returned an error',
          status: err.response.status,
          detail: err.response.data?.detail || 'Upstream service error'
        });
      } else {
        return res.status(502).json({
          error: 'Bad Gateway: Python Intelligence Engine is currently unreachable. Ensure FastAPI is running on port 8000.'
        });
      }
    }
  }
);

module.exports = router;
