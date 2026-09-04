const axios = require('axios');

// Centralized Axios client with X-Internal-Secret header baked in
const fastapiClient = axios.create({
  baseURL: process.env.FASTAPI_BASE_URL || 'http://localhost:8000',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
    'X-Internal-Secret': process.env.INTERNAL_API_SECRET
  }
});

module.exports = fastapiClient;
