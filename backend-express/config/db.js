const dns = require('dns');
// Use public DNS to resolve MongoDB Atlas SRV records reliably on Windows
try {
  dns.setServers(['8.8.8.8', '1.1.1.1']);
} catch (e) {
  // Ignore if unable to override
}

const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const uri = process.env.MONGODB_URI || process.env.MONGO_URI;
    if (!uri) {
      console.error('[EXPRESS DB ERROR] MONGODB_URI environment variable is missing! Please set MONGODB_URI in your Render Environment settings.');
      process.exit(1);
    }
    const conn = await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 10000,
    });
    console.log(`[EXPRESS DB] MongoDB Atlas Connected: ${conn.connection.host}`);
    return conn;
  } catch (error) {
    console.error(`[EXPRESS DB ERROR] ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;
