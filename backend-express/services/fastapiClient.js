const axios = require('axios');

let baseUrl = process.env.FASTAPI_BASE_URL || 'http://localhost:8000';
if (!baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
  baseUrl = `http://${baseUrl}`;
}

// Centralized Axios client with X-Internal-Secret header baked in
const fastapiClient = axios.create({
  baseURL: baseUrl,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
    'X-Internal-Secret': process.env.INTERNAL_API_SECRET
  }
});

module.exports = fastapiClient;
