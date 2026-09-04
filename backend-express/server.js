require('dotenv').config();
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const connectDB = require('./config/db');
const usersRoutes = require('./routes/users');
const newsRoutes = require('./routes/news');
const askRoutes = require('./routes/ask');
const searchRoutes = require('./routes/search');

const app = express();
const PORT = process.env.PORT || 5000;

// Connect to MongoDB Atlas
connectDB();

// Middleware
app.use(cors());
app.use(express.json());

// Mount Routes
app.use('/api/users', usersRoutes);
app.use('/api/news', newsRoutes);
app.use('/api/ask', askRoutes);
app.use('/api/search', searchRoutes);

const { startScheduler } = require('./services/scheduler');

// Health check route
app.get('/api/health', (req, res) => {
  const dbState = mongoose.connection.readyState;
  const statusMap = {
    0: 'disconnected',
    1: 'connected',
    2: 'connecting',
    3: 'disconnecting'
  };

  res.status(200).json({
    status: 'healthy',
    service: 'Node/Express API Gateway (Service A)',
    mongodb: statusMap[dbState] || 'unknown',
    fastapi_target: process.env.FASTAPI_BASE_URL || 'http://localhost:8000'
  });
});

if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`[EXPRESS SERVER] Service A running on port ${PORT}`);
    startScheduler();
  });
}

module.exports = app;
