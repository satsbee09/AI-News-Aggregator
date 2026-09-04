import React, { useState, useEffect } from 'react';
import { 
  Newspaper, 
  Clock, 
  Settings, 
  Sparkles, 
  Zap, 
  Check, 
  X, 
  LogOut, 
  RefreshCw, 
  Send, 
  ExternalLink, 
  MapPin, 
  CloudSun, 
  Cpu, 
  Trophy, 
  Globe, 
  Briefcase, 
  Film, 
  AlertCircle, 
  CheckCircle2, 
  Info,
  ArrowRight
} from 'lucide-react';

const CATEGORY_META = {
  ai: { name: 'Frontier AI & LLMs', scope: 'ai', category: 'ai', color: '#6C5CE7', icon: Cpu },
  local: { name: 'Local Ghaziabad News', scope: 'local', category: 'local', color: '#FF9F43', icon: MapPin },
  national: { name: 'National Politics & India', scope: 'national', category: 'politics', color: '#EE5A6F', icon: Globe },
  international: { name: 'Global Geopolitics', scope: 'international', category: 'international', color: '#6C5CE7', icon: Globe },
  sports: { name: 'Cricket & Sports', scope: 'sports', category: 'sports', color: '#00D9A5', icon: Trophy },
  weather: { name: 'Delhi NCR Weather', scope: 'weather', category: 'weather', color: '#4ECDC4', icon: CloudSun },
  business: { name: 'Global Markets & Business', scope: 'general', category: 'business', color: '#FFD93D', icon: Briefcase },
  tech: { name: 'Tech Startups & Venture', scope: 'general', category: 'tech', color: '#A29BFE', icon: Cpu },
  entertainment: { name: 'Cinema & Pop Culture', scope: 'general', category: 'entertainment', color: '#FD79A8', icon: Film },
};

const PREDEFINED_TOPICS = Object.values(CATEGORY_META);

export default function App() {
  const [email, setEmail] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [inputEmail, setInputEmail] = useState('');
  
  // Tab State: 'topics' | 'news'
  const [activeTab, setActiveTab] = useState('topics');
  
  // Topic State
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [customName, setCustomName] = useState('');
  const [customScope, setCustomScope] = useState('general');
  
  // Live News State
  const [previewData, setPreviewData] = useState([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  
  // Schedule Settings State
  const [schedTime, setSchedTime] = useState('23:00');
  const [schedFreq, setSchedFreq] = useState('daily');
  const [schedTz, setSchedTz] = useState('Asia/Kolkata');
  
  // UI States
  const [toast, setToast] = useState(null);
  const [savingTopics, setSavingTopics] = useState(false);
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [triggeringDigest, setTriggeringDigest] = useState(false);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // 1. Initial Load from LocalStorage
  useEffect(() => {
    const savedEmail = localStorage.getItem('news_aggregator_user_email');
    const cachedFeed = localStorage.getItem('news_aggregator_cached_feed');
    const detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
    setSchedTz(detectedTz);

    if (cachedFeed) {
      try {
        setPreviewData(JSON.parse(cachedFeed));
      } catch (e) {
        console.error('Failed to parse cached feed', e);
      }
    }

    if (savedEmail) {
      setEmail(savedEmail);
      loadUserProfile(savedEmail);
    }
  }, []);

  const loadUserProfile = async (userEmail) => {
    try {
      const res = await fetch(`/api/users/${encodeURIComponent(userEmail)}`);
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        setSelectedTopics(data.topics || []);
        if (data.schedule) {
          setSchedTime(data.schedule.time || '23:00');
          setSchedFreq(data.schedule.frequency || 'daily');
          setSchedTz(data.schedule.timezone || 'Asia/Kolkata');
        }
      } else {
        createUserAccount(userEmail);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
    }
  };

  const createUserAccount = async (userEmail) => {
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail })
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        setSelectedTopics(data.topics || []);
      }
    } catch (err) {
      showToast('Could not connect to backend server', 'error');
    }
  };

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    if (!inputEmail || !inputEmail.includes('@')) {
      showToast('Please enter a valid email address', 'error');
      return;
    }
    const cleanEmail = inputEmail.trim().toLowerCase();
    localStorage.setItem('news_aggregator_user_email', cleanEmail);
    setEmail(cleanEmail);
    createUserAccount(cleanEmail);
    showToast(`Welcome! Setting up dashboard for ${cleanEmail}`, 'success');
  };

  const handleLogout = () => {
    localStorage.removeItem('news_aggregator_user_email');
    localStorage.removeItem('news_aggregator_cached_feed');
    setEmail('');
    setUserProfile(null);
    setSelectedTopics([]);
    setPreviewData([]);
    setActiveTab('topics');
    showToast('Logged out successfully', 'info');
  };

  // Toggle Topic Chip
  const togglePredefinedTopic = (topic) => {
    const exists = selectedTopics.some(t => t.name.toLowerCase() === topic.name.toLowerCase());
    if (exists) {
      if (selectedTopics.length === 1) {
        showToast('You must keep at least one topic selected!', 'error');
        return;
      }
      setSelectedTopics(selectedTopics.filter(t => t.name.toLowerCase() !== topic.name.toLowerCase()));
    } else {
      setSelectedTopics([...selectedTopics, { name: topic.name, scope: topic.scope, category: topic.category }]);
    }
  };

  // Add Custom Topic Chip
  const handleAddCustomTopic = (e) => {
    e.preventDefault();
    if (!customName.trim()) return;
    
    const exists = selectedTopics.some(t => t.name.toLowerCase() === customName.trim().toLowerCase());
    if (exists) {
      showToast('This topic is already added!', 'error');
      return;
    }

    const newTopic = {
      name: customName.trim(),
      scope: customScope,
      category: customScope
    };

    setSelectedTopics([...selectedTopics, newTopic]);
    setCustomName('');
    showToast(`Added custom channel "${newTopic.name}"`, 'success');
  };

  const handleRemoveTopic = (name) => {
    if (selectedTopics.length === 1) {
      showToast('At least one topic is required.', 'error');
      return;
    }
    setSelectedTopics(selectedTopics.filter(t => t.name !== name));
  };

  // Save Topics (No auto-fetch)
  const handleSaveTopics = async () => {
    if (!email) return;
    setSavingTopics(true);
    try {
      const res = await fetch(`/api/users/${encodeURIComponent(email)}/topics`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics: selectedTopics })
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        showToast('Topic preferences saved!', 'success');
      } else {
        showToast('Failed to save topics', 'error');
      }
    } catch (err) {
      showToast('Server error while saving topics', 'error');
    } finally {
      setSavingTopics(false);
    }
  };

  // Fetch News Feed on Explicit Trigger
  const fetchPreviewNews = async (topicsToFetch = selectedTopics, switchTab = true) => {
    if (!topicsToFetch || topicsToFetch.length === 0) {
      showToast('Please select at least one topic first!', 'error');
      return;
    }
    
    if (switchTab) {
      setActiveTab('news');
    }
    
    setLoadingPreview(true);
    setPreviewError(false);
    
    try {
      const res = await fetch('/api/news/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics: topicsToFetch })
      });
      if (res.ok) {
        const data = await res.json();
        const fetchedTopics = data.topics || [];
        setPreviewData(fetchedTopics);
        localStorage.setItem('news_aggregator_cached_feed', JSON.stringify(fetchedTopics));
        showToast('Live news feed updated!', 'success');
      } else {
        setPreviewError(true);
        showToast('Could not fetch news feed', 'error');
      }
    } catch (err) {
      console.error('Preview error:', err);
      setPreviewError(true);
      showToast('Server error during news fetch', 'error');
    } finally {
      setLoadingPreview(false);
    }
  };

  // Save Delivery Schedule
  const handleSaveSchedule = async (e) => {
    e.preventDefault();
    if (!email) return;
    setSavingSchedule(true);
    try {
      const payload = {
        time: schedTime,
        frequency: schedFreq,
        timezone: schedTz
      };
      const res = await fetch(`/api/users/${encodeURIComponent(email)}/schedule`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        showToast(`Schedule updated for ${schedTime} (${schedFreq.replace('_', ' ')})`, 'success');
      } else {
        showToast('Failed to save schedule', 'error');
      }
    } catch (err) {
      showToast('Server error saving schedule', 'error');
    } finally {
      setSavingSchedule(false);
    }
  };

  // Instant Manual Dispatch Test
  const handleTriggerTest = async () => {
    if (!email) return;
    setTriggeringDigest(true);
    showToast(`Dispatching live intelligence digest to ${email}...`, 'info');
    try {
      const res = await fetch(`/api/users/${encodeURIComponent(email)}/trigger?dry_run=false`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Digest successfully delivered to ${email}!`, 'success');
      } else {
        showToast(data.message || 'Pipeline trigger completed', 'info');
      }
    } catch (err) {
      showToast('Error executing pipeline', 'error');
    } finally {
      setTriggeringDigest(false);
    }
  };

  // Toast Component
  const renderToast = () => {
    if (!toast) return null;
    const toastClass = toast.type === 'success' ? 'toast-success' : toast.type === 'error' ? 'toast-error' : 'toast-info';
    const IconComponent = toast.type === 'success' ? CheckCircle2 : toast.type === 'error' ? AlertCircle : Info;
    return (
      <div className="toast-container">
        <div className={`toast-pill ${toastClass}`}>
          <IconComponent size={18} />
          <span>{toast.message}</span>
        </div>
      </div>
    );
  };

  // Helper to get category color
  const getCategoryColor = (catKey) => {
    const key = (catKey || 'general').toLowerCase();
    return CATEGORY_META[key]?.color || '#6C5CE7';
  };

  // Count total articles
  const totalArticlesLoaded = previewData.reduce((acc, g) => acc + (g.articles?.length || 0), 0);

  // ---------------------------------------------------------------------------
  // View 1: Landing Page (Phase A)
  // ---------------------------------------------------------------------------
  if (!email) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px', background: 'radial-gradient(circle at 50% 20%, rgba(108, 92, 231, 0.12) 0%, transparent 60%), #F7F7FC' }}>
        {renderToast()}
        <div className="card-panel" style={{ maxWidth: '460px', width: '100%', padding: '44px 36px', textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', background: 'linear-gradient(135deg, #6C5CE7 0%, #8E78FF 100%)', borderRadius: '20px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', marginBottom: '20px', boxShadow: '0 8px 24px rgba(108, 92, 231, 0.3)' }}>
            <Newspaper size={32} />
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px', color: 'var(--text-main)' }}>
            Universal News
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '32px', lineHeight: '1.6' }}>
            Daily factual, anti-hype intelligence briefings on <strong>any topic you choose</strong> — AI, Cricket, Local, Weather & World News.
          </p>

          <form onSubmit={handleEmailSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input
              type="email"
              className="form-input"
              placeholder="Enter your email address..."
              value={inputEmail}
              onChange={(e) => setInputEmail(e.target.value)}
              required
              autoFocus
              style={{ fontSize: '15px', padding: '14px 18px', borderRadius: 'var(--radius-full)' }}
            />
            <button type="submit" className="btn-primary" style={{ padding: '14px', fontSize: '15px' }}>
              Access Dashboard <ArrowRight size={18} />
            </button>
          </form>
          
          <div style={{ marginTop: '28px', fontSize: '12.5px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
            <Sparkles size={14} color="#6C5CE7" /> 100% Free • Automated Email Delivery
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // View 2: Redesigned Friendly News Dashboard
  // ---------------------------------------------------------------------------
  return (
    <div style={{ minHeight: '100vh', paddingBottom: '80px' }}>
      {renderToast()}
      
      {/* 1. VIBRANT PURPLE NAVBAR */}
      <header className="app-header">
        <div className="brand-container" onClick={() => setActiveTab('topics')}>
          <div className="brand-icon">
            <Newspaper size={20} />
          </div>
          <div>
            <div className="brand-title">Universal News</div>
            <div className="brand-subtitle">AI Intelligence Feed</div>
          </div>
        </div>

        {/* 2. PILL-STYLE TAB SWITCHER */}
        <nav className="nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'topics' ? 'active' : ''}`}
            onClick={() => setActiveTab('topics')}
          >
            <Settings size={16} /> Topics & Schedule
          </button>
          <button
            className={`tab-btn ${activeTab === 'news' ? 'active' : ''}`}
            onClick={() => setActiveTab('news')}
          >
            <Zap size={16} /> News Feed 
            {totalArticlesLoaded > 0 && <span className="tab-count-badge">{totalArticlesLoaded}</span>}
          </button>
        </nav>

        {/* User Info & Outlined Logout Button */}
        <div className="navbar-user-info">
          <div className="user-email-pill">
            <span>👤</span>
            <span>{email}</span>
          </div>
          <button onClick={handleLogout} className="btn-navbar-logout">
            <LogOut size={14} /> Logout
          </button>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main style={{ maxWidth: '1200px', margin: '36px auto', padding: '0 24px' }}>
        
        {/* =================================================================== */}
        {/* TAB 1: TOPICS & SCHEDULE (Friendly & Colorful)                      */}
        {/* =================================================================== */}
        {activeTab === 'topics' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '28px' }}>
              
              {/* TOPIC SELECTION CARD */}
              <div className="card-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h2 style={{ fontSize: '20px', fontWeight: '700' }}>1. Pick Your Channels</h2>
                  <span style={{ fontSize: '13px', background: 'rgba(108, 92, 231, 0.1)', color: 'var(--primary)', fontWeight: '700', padding: '4px 12px', borderRadius: 'var(--radius-full)' }}>
                    {selectedTopics.length} Active
                  </span>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', marginBottom: '18px' }}>
                  Choose from popular categories or add any custom city/topic.
                </p>

                {/* Predefined Dynamic Category Chips */}
                <div className="topic-grid">
                  {PREDEFINED_TOPICS.map((pt) => {
                    const isSelected = selectedTopics.some(t => t.name.toLowerCase() === pt.name.toLowerCase());
                    const IconComp = pt.icon;
                    const chipClass = `chip-${pt.category}`;
                    return (
                      <div
                        key={pt.name}
                        className={`topic-chip ${chipClass} ${isSelected ? 'selected' : ''}`}
                        onClick={() => togglePredefinedTopic(pt)}
                      >
                        <IconComp size={16} />
                        <span>{pt.name}</span>
                        {isSelected && <Check size={14} strokeWidth={3} />}
                      </div>
                    );
                  })}
                </div>

                {/* Custom Topic Form */}
                <form onSubmit={handleAddCustomTopic} style={{ marginTop: '24px', display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Add custom topic (e.g. Noida Tech, EV Cars)..."
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    style={{ flex: 1, padding: '10px 16px' }}
                  />
                  <select
                    className="form-input"
                    value={customScope}
                    onChange={(e) => setCustomScope(e.target.value)}
                    style={{ width: '130px', padding: '10px', fontSize: '13px' }}
                  >
                    <option value="general">General</option>
                    <option value="local">Local</option>
                    <option value="national">National</option>
                    <option value="international">Global</option>
                    <option value="weather">Weather</option>
                    <option value="sports">Sports</option>
                    <option value="ai">AI / Tech</option>
                  </select>
                  <button type="submit" className="btn-secondary" style={{ padding: '10px 18px' }}>
                    + Add
                  </button>
                </form>

                {/* Active Topics Queue */}
                <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginBottom: '10px', fontWeight: '700', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                    Active Topic Queue:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {selectedTopics.map((t) => (
                      <span
                        key={t.name}
                        style={{
                          background: 'rgba(108, 92, 231, 0.08)',
                          border: '1px solid rgba(108, 92, 231, 0.25)',
                          color: 'var(--text-main)',
                          borderRadius: 'var(--radius-full)',
                          padding: '6px 14px',
                          fontSize: '12.5px',
                          fontWeight: '600',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <span>{t.name}</span>
                        <span className="chip-delete-btn" onClick={() => handleRemoveTopic(t.name)}>
                          <X size={14} color="#EE5A6F" />
                        </span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Save Topics Button */}
                <div style={{ marginTop: '24px' }}>
                  <button
                    onClick={handleSaveTopics}
                    disabled={savingTopics}
                    className="btn-primary"
                    style={{ width: '100%' }}
                  >
                    <Check size={16} /> {savingTopics ? 'Saving...' : 'Save Topic Preferences'}
                  </button>
                </div>
              </div>

              {/* SCHEDULE SETTINGS CARD */}
              <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h2 style={{ fontSize: '20px', fontWeight: '700' }}>2. Email Schedule</h2>
                    <span style={{ fontSize: '12px', background: 'rgba(0, 217, 165, 0.12)', color: '#00D9A5', fontWeight: '700', padding: '4px 12px', borderRadius: 'var(--radius-full)' }}>
                      ● Active
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', marginBottom: '22px' }}>
                    Set your preferred automated delivery time and frequency.
                  </p>

                  <form onSubmit={handleSaveSchedule} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '700', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>
                        Delivery Time (24-Hour)
                      </label>
                      <input
                        type="time"
                        className="form-input"
                        value={schedTime}
                        onChange={(e) => setSchedTime(e.target.value)}
                        required
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                      <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '700', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>
                          Frequency
                        </label>
                        <select
                          className="form-input"
                          value={schedFreq}
                          onChange={(e) => setSchedFreq(e.target.value)}
                        >
                          <option value="daily">Daily</option>
                          <option value="every_6_hours">Every 6 Hours</option>
                          <option value="every_12_hours">Every 12 Hours</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '700', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>
                          Timezone
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          value={schedTz}
                          onChange={(e) => setSchedTz(e.target.value)}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={savingSchedule}
                      className="btn-primary"
                      style={{ marginTop: '8px' }}
                    >
                      <Clock size={16} /> {savingSchedule ? 'Updating...' : 'Save Delivery Schedule'}
                    </button>
                  </form>
                </div>

                {/* Instant Email Test Action */}
                <div style={{ marginTop: '24px', background: '#F8F8FD', padding: '16px 20px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '13.5px', fontWeight: '700', color: 'var(--text-main)' }}>Instant Dispatch</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Send test digest to {email}</div>
                    </div>
                    <button
                      onClick={handleTriggerTest}
                      disabled={triggeringDigest}
                      className="btn-secondary"
                      style={{ fontSize: '12.5px', padding: '8px 16px' }}
                    >
                      <Send size={14} /> {triggeringDigest ? 'Sending...' : 'Send Now'}
                    </button>
                  </div>
                </div>

              </div>
            </div>

            {/* 4. PROMINENT WARM ACCENT "GET NEWS NOW" CTA */}
            <div className="card-panel" style={{ background: '#FFFFFF', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '2px solid rgba(255, 159, 67, 0.4)', padding: '28px 36px' }}>
              <div>
                <h3 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={22} color="#FF9F43" /> Ready for today's headlines?
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
                  Fetch live news and generate anti-hype briefings across all {selectedTopics.length} selected channels.
                </p>
              </div>
              <button
                onClick={() => fetchPreviewNews(selectedTopics, true)}
                disabled={loadingPreview}
                className="btn-warm-cta"
              >
                <Zap size={20} /> {loadingPreview ? 'Fetching Stories...' : 'Get News Now'}
              </button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* TAB 2: NEWS FEED (Flipboard / Inshorts Card Layout)                 */}
        {/* =================================================================== */}
        {activeTab === 'news' && (
          <div className="card-panel" style={{ padding: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--border-subtle)', paddingBottom: '18px' }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span>🔥</span> Your Curated News Feed
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', marginTop: '4px' }}>
                  Anti-hype factual summaries curated per your topic choices.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => fetchPreviewNews(selectedTopics, false)}
                  disabled={loadingPreview}
                  className="btn-secondary"
                >
                  <RefreshCw size={15} className={loadingPreview ? 'animate-spin' : ''} />
                  {loadingPreview ? 'Refreshing...' : 'Refresh Feed'}
                </button>
                <button
                  onClick={() => setActiveTab('topics')}
                  className="btn-secondary"
                >
                  <Settings size={15} /> Edit Channels
                </button>
              </div>
            </div>

            {/* 8. SKELETON LOADERS (Matching Card Shape) */}
            {loadingPreview && (
              <div style={{ marginTop: '28px' }}>
                <div style={{ color: 'var(--primary)', fontSize: '14px', fontWeight: '700', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={16} /> Gathering live stories and synthesizing anti-hype briefings...
                </div>
                <div className="news-grid">
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="skeleton skeleton-card" />
                  ))}
                </div>
              </div>
            )}

            {/* Error State */}
            {!loadingPreview && previewError && (
              <div className="empty-state-box">
                <div className="empty-icon-circle" style={{ background: 'rgba(238, 90, 111, 0.1)', color: '#EE5A6F' }}>
                  <AlertCircle size={36} />
                </div>
                <h3 style={{ fontSize: '19px', fontWeight: '700', marginBottom: '8px' }}>Could not load news feed</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '400px', margin: '0 auto 20px auto' }}>
                  There was a temporary issue communicating with the scrapers or LLM engine.
                </p>
                <button onClick={() => fetchPreviewNews(selectedTopics, false)} className="btn-primary">
                  <RefreshCw size={16} /> Try Again
                </button>
              </div>
            )}

            {/* 7. EMPTY STATE (Before Fetching) */}
            {!loadingPreview && !previewError && previewData.length === 0 && (
              <div className="empty-state-box">
                <div className="empty-icon-circle">
                  <Newspaper size={36} />
                </div>
                <h3 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '8px', color: 'var(--text-main)' }}>
                  No news fetched yet
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '440px', margin: '0 auto 24px auto', lineHeight: '1.6' }}>
                  Go to <strong>Topics & Schedule</strong> to choose your channels, then click <strong>"Get News Now"</strong> to see today's top stories.
                </p>
                <button onClick={() => fetchPreviewNews(selectedTopics, false)} className="btn-warm-cta">
                  <Zap size={18} /> Get News Now
                </button>
              </div>
            )}

            {/* 5 & 6. GROUPED TOPIC CARDS & SECTION HEADERS */}
            {!loadingPreview && !previewError && previewData.map(group => {
              const catColor = getCategoryColor(group.category || group.scope);
              return (
                <div key={group.topic_name}>
                  {/* Section Header with colored pill badge */}
                  <div className="news-section-header">
                    <span className="section-tag-pill" style={{ backgroundColor: catColor }}>
                      {group.scope || 'GENERAL'}
                    </span>
                    <h3 style={{ fontSize: '19px', fontWeight: '800', color: 'var(--text-main)' }}>
                      {group.topic_name}
                    </h3>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: '600' }}>
                      • {group.articles?.length || 0} Stories
                    </span>
                  </div>

                  {group.articles.length === 0 ? (
                    <div style={{ background: '#F8F8FD', padding: '20px', borderRadius: 'var(--radius-lg)', fontSize: '13.5px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                      No recent updates found in the last 48 hours for this channel.
                    </div>
                  ) : (
                    <div className="news-grid">
                      {group.articles.map((art, idx) => (
                        <div 
                          key={idx} 
                          className="news-card" 
                          style={{ '--card-accent': catColor }}
                        >
                          <div>
                            {/* Card Top Row: Source badge */}
                            <div className="card-top-row">
                              <span className="source-badge">
                                {art.source?.replace('gnews_', '')?.toUpperCase()}
                              </span>
                            </div>

                            {/* Card Title */}
                            <h4 className="card-title">
                              <a href={art.url} target="_blank" rel="noopener noreferrer">
                                {art.title}
                              </a>
                            </h4>

                            {/* Card Snippet */}
                            <p className="card-snippet">
                              {art.summary}
                            </p>

                            {/* Takeaways Box */}
                            {art.key_takeaways && art.key_takeaways.length > 0 && (
                              <div className="takeaways-box">
                                <ul>
                                  {art.key_takeaways.slice(0, 3).map((pt, pidx) => (
                                    <li key={pidx} style={{ marginBottom: '4px' }}>
                                      {pt.replace(/^[-•*]\s*/, '')}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Card Footer */}
                          <div className="card-footer">
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                              {art.published_at ? new Date(art.published_at).toLocaleDateString() : 'Today'}
                            </span>
                            <a 
                              href={art.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="read-more-link"
                              style={{ color: catColor }}
                            >
                              Read Full Story <ExternalLink size={13} />
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

          </div>
        )}

      </main>
    </div>
  );
}
