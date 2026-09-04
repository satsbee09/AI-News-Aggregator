const express = require('express');
const { body, validationResult } = require('express-validator');
const fastapiClient = require('../services/fastapiClient');

const router = express.Router();

// POST /api/search/live (Proxy on-demand live search to FastAPI /internal/search-live)
router.post(
  '/live',
  [
    body('query').isString().trim().isLength({ min: 2 }).withMessage('Search query must be at least 2 characters'),
    body('topic').optional().isString().trim()
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    const { query, topic } = req.body;

    try {
      console.log(`[EXPRESS LIVE SEARCH PROXY] Forwarding query '${query}' (topic: ${topic || 'all'}) to FastAPI...`);
      const response = await fastapiClient.post('/internal/search-live', { query, topic });
      return res.status(200).json(response.data);
    } catch (err) {
      console.error(`[EXPRESS LIVE SEARCH PROXY ERROR] FastAPI /internal/search-live failed: ${err.message}`);
      if (err.response) {
        return res.status(err.response.status).json(err.response.data);
      }
      return res.status(502).json({
        error: 'Bad Gateway: Python Intelligence Engine is currently unreachable. Ensure FastAPI is running on port 8000.'
      });
    }
  }
);

module.exports = router;
