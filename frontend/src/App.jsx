import React, { useState, useEffect } from 'react';

const PREDEFINED_TOPICS = [
  { name: 'Frontier AI & LLMs', scope: 'ai', category: 'ai', icon: '🤖' },
  { name: 'Local Ghaziabad News', scope: 'local', category: 'local', icon: '📍' },
  { name: 'National News & Politics', scope: 'national', category: 'national', icon: '🇮🇳' },
  { name: 'Global Geopolitics', scope: 'international', category: 'international', icon: '🌍' },
  { name: 'Cricket & Sports', scope: 'sports', category: 'sports', icon: '🏏' },
  { name: 'Delhi NCR Weather', scope: 'weather', category: 'weather', icon: '🌦️' },
  { name: 'Global Markets & Business', scope: 'general', category: 'general', icon: '💼' },
  { name: 'Tech Startups & Venture', scope: 'general', category: 'general', icon: '💻' },
  { name: 'Cinema & Entertainment', scope: 'general', category: 'general', icon: '🎬' },
];

export default function App() {
  const [email, setEmail] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [inputEmail, setInputEmail] = useState('');
  
  // Tab Management State ('topics' | 'news')
  const [activeTab, setActiveTab] = useState('topics');
  
  // Topic Management State
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [customName, setCustomName] = useState('');
  const [customScope, setCustomScope] = useState('general');
  
  // Live News Preview State
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

  // Toggle Predefined Topic
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

  // Add Custom Topic
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
    showToast(`Added custom topic "${newTopic.name}"`, 'success');
  };

  // Remove Topic
  const handleRemoveTopic = (name) => {
    if (selectedTopics.length === 1) {
      showToast('At least one topic is required.', 'error');
      return;
    }
    setSelectedTopics(selectedTopics.filter(t => t.name !== name));
  };

  // Save Topics to Backend (ONLY saves preferences, does NOT auto-fetch preview)
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
        showToast('Topics saved successfully!', 'success');
      } else {
        showToast('Failed to save topics', 'error');
      }
    } catch (err) {
      showToast('Server error while saving topics', 'error');
    } finally {
      setSavingTopics(false);
    }
  };

  // Fetch Live News Preview on Explicit User Demand
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
        showToast(`Schedule updated! Digest scheduled for ${schedTime} (${schedFreq.replace('_', ' ')})`, 'success');
      } else {
        showToast('Failed to save schedule', 'error');
      }
    } catch (err) {
      showToast('Server error saving schedule', 'error');
    } finally {
      setSavingSchedule(false);
    }
  };

  // Manual Trigger Test Digest
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
    const bg = toast.type === 'success' ? '#059669' : toast.type === 'error' ? '#e11d48' : '#2563eb';
    return (
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        background: bg,
        color: '#ffffff',
        padding: '12px 20px',
        borderRadius: '10px',
        fontWeight: '600',
        fontSize: '13.5px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
        zIndex: 9999,
        animation: 'slideIn 0.2s ease-out'
      }}>
        {toast.message}
      </div>
    );
  };

  // ---------------------------------------------------------------------------
  // View 1: Email Entry / Landing Page (Phase A)
  // ---------------------------------------------------------------------------
  if (!email) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        {renderToast()}
        <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '40px 32px', textAlign: 'center' }}>
          <div style={{ fontSize: '42px', marginBottom: '12px' }}>🌐</div>
          <h1 style={{ fontSize: '26px', fontWeight: '800', marginBottom: '8px' }}>
            Universal News Intelligence
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '28px', lineHeight: '1.6' }}>
            Get factual, anti-hype news summaries on <strong>any topic you care about</strong> — Local, National, Global, Frontier AI, Cricket, and Weather.
          </p>

          <form onSubmit={handleEmailSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input
              type="email"
              className="input-field"
              placeholder="Enter your email address..."
              value={inputEmail}
              onChange={(e) => setInputEmail(e.target.value)}
              required
              autoFocus
            />
            <button type="submit" className="btn-primary" style={{ justifyContent: 'center', padding: '14px' }}>
              Access Your Dashboard &rarr;
            </button>
          </form>
          
          <div style={{ marginTop: '24px', fontSize: '12px', color: 'var(--text-dim)' }}>
            100% Free • No password required • Automated Daily Email Delivery
          </div>
        </div>
      </div>
    );
  }

  // Count total articles loaded
  const totalArticlesLoaded = previewData.reduce((acc, g) => acc + (g.articles?.length || 0), 0);

  // ---------------------------------------------------------------------------
  // View 2: Main Dashboard with Persistent Navbar & Tabs
  // ---------------------------------------------------------------------------
  return (
    <div style={{ minHeight: '100vh', paddingBottom: '60px' }}>
      {renderToast()}
      
      {/* Persistent App Header with Tabs and Logout */}
      <header className="app-header">
        <div className="brand-title" onClick={() => setActiveTab('topics')}>
          <span>🌐</span> Universal News Intelligence
        </div>

        {/* Tab Switcher in Navbar */}
        <nav className="nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'topics' ? 'active' : ''}`}
            onClick={() => setActiveTab('topics')}
          >
            ⚙️ Topics & Schedule
          </button>
          <button
            className={`tab-btn ${activeTab === 'news' ? 'active' : ''}`}
            onClick={() => setActiveTab('news')}
          >
            📰 News Feed {totalArticlesLoaded > 0 && <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.2)', padding: '1px 6px', borderRadius: '99px' }}>{totalArticlesLoaded}</span>}
          </button>
        </nav>

        {/* User Info & Logout Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="user-badge">
            <span>👤</span>
            <strong>{email}</strong>
          </div>
          <button onClick={handleLogout} className="btn-logout" title="Logout and switch account">
            Logout
          </button>
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '32px auto', padding: '0 24px' }}>
        
        {/* =================================================================== */}
        {/* TAB 1: TOPICS & SCHEDULE SETTINGS                                  */}
        {/* =================================================================== */}
        {activeTab === 'topics' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px' }}>
              
              {/* TOPIC SELECTION CARD */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h2 style={{ fontSize: '18px', fontWeight: '700' }}>1. Your Interest Topics</h2>
                  <span style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: '600' }}>
                    {selectedTopics.length} selected
                  </span>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                  Select from curated channels or type custom keywords and cities.
                </p>

                {/* Predefined Chips */}
                <div style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: '0.5px' }}>
                  Predefined Categories
                </div>
                <div className="topic-grid">
                  {PREDEFINED_TOPICS.map((pt) => {
                    const isSelected = selectedTopics.some(t => t.name.toLowerCase() === pt.name.toLowerCase());
                    return (
                      <div
                        key={pt.name}
                        className={`topic-chip ${isSelected ? 'active' : ''}`}
                        onClick={() => togglePredefinedTopic(pt)}
                      >
                        <span>{pt.icon}</span>
                        <span>{pt.name}</span>
                        {isSelected && <span style={{ fontSize: '11px' }}>✓</span>}
                      </div>
                    );
                  })}
                </div>

                {/* Custom Topic Form */}
                <form onSubmit={handleAddCustomTopic} style={{ marginTop: '20px', display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="Type custom topic (e.g. Noida Tech, EV Cars)..."
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    style={{ flex: 1, padding: '9px 12px', fontSize: '13px' }}
                  />
                  <select
                    className="input-field"
                    value={customScope}
                    onChange={(e) => setCustomScope(e.target.value)}
                    style={{ width: '130px', padding: '9px', fontSize: '12px' }}
                  >
                    <option value="general">General</option>
                    <option value="local">Local</option>
                    <option value="national">National</option>
                    <option value="international">Global</option>
                    <option value="weather">Weather</option>
                    <option value="sports">Sports</option>
                    <option value="ai">AI / Tech</option>
                  </select>
                  <button type="submit" className="btn-secondary" style={{ padding: '8px 14px' }}>
                    + Add
                  </button>
                </form>

                {/* Selected Active Chips */}
                <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', marginBottom: '8px', fontWeight: '600' }}>
                    ACTIVE TOPICS QUEUE:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {selectedTopics.map((t) => (
                      <span
                        key={t.name}
                        style={{
                          background: 'rgba(56, 189, 248, 0.08)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          color: 'var(--text-main)',
                          borderRadius: '6px',
                          padding: '4px 10px',
                          fontSize: '12px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <span>{t.name}</span>
                        <span className="chip-remove" onClick={() => handleRemoveTopic(t.name)}>×</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Save Topics Button */}
                <div style={{ marginTop: '20px' }}>
                  <button
                    onClick={handleSaveTopics}
                    disabled={savingTopics}
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    {savingTopics ? 'Saving Topics...' : 'Save Topic Preferences'}
                  </button>
                </div>
              </div>

              {/* SCHEDULE SETTINGS CARD */}
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: '700' }}>2. Delivery Schedule</h2>
                    <span style={{ fontSize: '12px', color: 'var(--accent-emerald)', fontWeight: '600' }}>
                      ● Automated
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '20px' }}>
                    Set when you want your summarized multi-topic newsletter delivered to your inbox.
                  </p>

                  <form onSubmit={handleSaveSchedule} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>
                        DELIVERY TIME (24-Hour format)
                      </label>
                      <input
                        type="time"
                        className="input-field"
                        value={schedTime}
                        onChange={(e) => setSchedTime(e.target.value)}
                        required
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>
                          FREQUENCY
                        </label>
                        <select
                          className="input-field"
                          value={schedFreq}
                          onChange={(e) => setSchedFreq(e.target.value)}
                        >
                          <option value="daily">Daily</option>
                          <option value="every_6_hours">Every 6 Hours</option>
                          <option value="every_12_hours">Every 12 Hours</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>
                          TIMEZONE
                        </label>
                        <input
                          type="text"
                          className="input-field"
                          value={schedTz}
                          onChange={(e) => setSchedTz(e.target.value)}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={savingSchedule}
                      className="btn-primary"
                      style={{ marginTop: '8px', justifyContent: 'center' }}
                    >
                      {savingSchedule ? 'Updating Schedule...' : 'Save Delivery Schedule'}
                    </button>
                  </form>
                </div>

                {/* Test Email Now Action */}
                <div style={{ marginTop: '24px', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-main)' }}>Instant Dispatch</div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Send a live test digest to {email} now</div>
                    </div>
                    <button
                      onClick={handleTriggerTest}
                      disabled={triggeringDigest}
                      className="btn-secondary"
                      style={{ fontSize: '12px' }}
                    >
                      {triggeringDigest ? 'Sending...' : '⚡ Send Test Email'}
                    </button>
                  </div>
                </div>

              </div>
            </div>

            {/* BIG ACTION BAR: "GET NEWS NOW" */}
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-main)' }}>
                  Ready to read today's headlines?
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                  Fetch live articles & LLM summaries on demand across all {selectedTopics.length} selected topics.
                </p>
              </div>
              <button
                onClick={() => fetchPreviewNews(selectedTopics, true)}
                disabled={loadingPreview}
                className="btn-primary"
                style={{ padding: '14px 28px', fontSize: '15px' }}
              >
                {loadingPreview ? 'Fetching Stories...' : '🚀 Get News Now &rarr;'}
              </button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* TAB 2: NEWS FEED                                                   */}
        {/* =================================================================== */}
        {activeTab === 'news' && (
          <div className="glass-panel" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: '800' }}>
                  🔥 Your Multi-Topic News Feed
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                  Anti-hype factual summaries curated for your selected topics.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => fetchPreviewNews(selectedTopics, false)}
                  disabled={loadingPreview}
                  className="btn-secondary"
                >
                  {loadingPreview ? 'Refreshing...' : '🔄 Refresh Feed'}
                </button>
                <button
                  onClick={() => setActiveTab('topics')}
                  className="btn-secondary"
                >
                  ⚙️ Edit Topics
                </button>
              </div>
            </div>

            {/* Loading Skeletons */}
            {loadingPreview && (
              <div style={{ marginTop: '24px' }}>
                <div style={{ color: 'var(--accent-cyan)', fontSize: '13.5px', fontWeight: '600', marginBottom: '16px' }}>
                  Fetching live feeds and generating AI summaries...
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
                <div style={{ fontSize: '36px', marginBottom: '12px' }}>⚠️</div>
                <h3 style={{ fontSize: '17px', fontWeight: '700', marginBottom: '6px' }}>Could not load news feed</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                  There was a problem communicating with the news scrapers or summarization engine.
                </p>
                <button onClick={() => fetchPreviewNews(selectedTopics, false)} className="btn-primary">
                  Try Again
                </button>
              </div>
            )}

            {/* Empty State before fetching */}
            {!loadingPreview && !previewError && previewData.length === 0 && (
              <div className="empty-state-box">
                <div style={{ fontSize: '42px', marginBottom: '12px' }}>📡</div>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>
                  No news fetched yet
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '13.5px', maxWidth: '440px', margin: '0 auto 20px auto', lineHeight: '1.6' }}>
                  Configure your topics and click <strong>"Get News Now"</strong> to generate your personalized live intelligence feed.
                </p>
                <button onClick={() => fetchPreviewNews(selectedTopics, false)} className="btn-primary">
                  🚀 Get News Now
                </button>
              </div>
            )}

            {/* Grouped Topic News Cards */}
            {!loadingPreview && !previewError && previewData.map(group => {
              const badgeClass = `badge-${group.scope || 'general'}`;
              return (
                <div key={group.topic_name} style={{ marginTop: '28px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <span className={`news-badge ${badgeClass}`} style={{ fontSize: '12px', padding: '4px 10px' }}>
                      {group.scope.toUpperCase()}
                    </span>
                    <h3 style={{ fontSize: '17px', fontWeight: '700' }}>
                      {group.topic_name}
                    </h3>
                    <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                      ({group.articles.length} stories)
                    </span>
                  </div>

                  {group.articles.length === 0 ? (
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', fontSize: '13px', color: 'var(--text-dim)' }}>
                      No recent stories found in the last 48 hours for this topic.
                    </div>
                  ) : (
                    <div className="news-grid" style={{ marginTop: '0' }}>
                      {group.articles.map((art, idx) => (
                        <div key={idx} className="news-card">
                          <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: '600' }}>
                                {art.source?.toUpperCase()}
                              </span>
                            </div>

                            <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '10px', lineHeight: '1.4' }}>
                              <a href={art.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none' }}>
                                {art.title}
                              </a>
                            </h4>

                            <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '14px' }}>
                              {art.summary}
                            </p>

                            {art.key_takeaways && art.key_takeaways.length > 0 && (
                              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', marginBottom: '12px' }}>
                                <ul style={{ paddingLeft: '16px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                                  {art.key_takeaways.slice(0, 3).map((pt, pidx) => (
                                    <li key={pidx} style={{ marginBottom: '4px' }}>{pt.replace(/^[-•*]\s*/, '')}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          <div style={{ marginTop: '12px', textAlign: 'right', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
                            <a href={art.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: '600' }}>
                              Read full story &rarr;
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
