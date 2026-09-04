const express = require('express');
const { body, validationResult } = require('express-validator');
const fastapiClient = require('../services/fastapiClient');

const router = express.Router();

// POST /api/ask (Proxy natural-language news QA to FastAPI RAG engine)
router.post(
  '/',
  [
    body('email').isEmail().withMessage('Valid email is required').normalizeEmail(),
    body('question').isString().trim().isLength({ min: 2 }).withMessage('Question must be at least 2 characters')
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    const { email, question } = req.body;

    try {
      console.log(`[EXPRESS RAG PROXY] Forwarding question from '${email}' to FastAPI /internal/ask...`);
      const response = await fastapiClient.post('/internal/ask', { email, question });
      return res.status(200).json(response.data);
    } catch (err) {
      console.error(`[EXPRESS RAG PROXY ERROR] FastAPI /internal/ask failed: ${err.message}`);
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
