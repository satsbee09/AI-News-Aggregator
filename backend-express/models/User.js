const mongoose = require('mongoose');

const TopicSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true },
  scope: { type: String, default: 'general' },
  category: { type: String, default: 'general' }
}, { _id: false });

const ScheduleSchema = new mongoose.Schema({
  time: { type: String, default: '23:00' },
  frequency: { type: String, default: 'daily' },
  timezone: { type: String, default: 'Asia/Kolkata' },
  enabled: { type: Boolean, default: true }
}, { _id: false });

const UserSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
    index: true
  },
  isSubscribed: {
    type: Boolean,
    default: true
  },
  topics: {
    type: [TopicSchema],
    default: [
      { name: 'Frontier AI & LLMs', scope: 'ai', category: 'ai' },
      { name: 'Local Ghaziabad News', scope: 'local', category: 'local' },
      { name: 'National Politics & India', scope: 'national', category: 'national' },
      { name: 'Cricket & Sports', scope: 'sports', category: 'sports' }
    ]
  },
  schedule: {
    type: ScheduleSchema,
    default: () => ({ time: '23:00', frequency: 'daily', timezone: 'Asia/Kolkata', enabled: true })
  },
  lastSentAt: {
    type: Date,
    default: null
  }
}, {
  timestamps: true,
  collection: 'users' // Reuses the same MongoDB 'users' collection
});

module.exports = mongoose.model('User', UserSchema);
