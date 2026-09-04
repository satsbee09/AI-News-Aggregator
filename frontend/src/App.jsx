import React, { useState, useEffect, useRef } from 'react';
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
  ArrowRight,
  MessageSquareText,
  Bot,
  RotateCcw,
  Search
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

const SUGGESTED_PROMPTS = [
  "What are the latest breakthroughs in AI & LLMs?",
  "Give me a summary of current cricket & sports news",
  "What are the top national & world geopolitics stories?",
  "What is the latest weather update in Delhi NCR?"
];

export default function App() {
  const [email, setEmail] = useState('');
  const [_userProfile, setUserProfile] = useState(null);
  const [inputEmail, setInputEmail] = useState('');
  
  // Tab State: 'topics' | 'news' | 'ask'
  const [activeTab, setActiveTab] = useState('topics');
  
  // Topic State
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [customName, setCustomName] = useState('');
  const [customScope, setCustomScope] = useState('general');
  
  // Live News State
  const [previewData, setPreviewData] = useState([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState(false);

  // Live Web Search State (Google + Brave)
  const [liveSearchQuery, setLiveSearchQuery] = useState('');
  const [liveSearchResults, setLiveSearchResults] = useState(null);
  const [liveSearchLoading, setLiveSearchLoading] = useState(false);
  
  // Schedule Settings State
  const [schedTime, setSchedTime] = useState('23:00');
  const [schedFreq, setSchedFreq] = useState('daily');
  const [schedTz, setSchedTz] = useState(() => Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata');

  // RAG Ask News State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);
  
  // UI States
  const [toast, setToast] = useState(null);
  const [savingTopics, setSavingTopics] = useState(false);
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [triggeringDigest, setTriggeringDigest] = useState(false);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
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
      console.error('Account creation error:', err);
      showToast('Could not connect to backend server', 'error');
    }
  };

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
        await createUserAccount(userEmail);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
    }
  };

  // 1. Initial Load from LocalStorage
  useEffect(() => {
    const savedEmail = localStorage.getItem('news_aggregator_user_email');
    const cachedFeed = localStorage.getItem('news_aggregator_cached_feed');

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
      console.error('Error saving topics:', err);
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
      console.error('Error saving schedule:', err);
      showToast('Server error saving schedule', 'error');
    } finally {
      setSavingSchedule(false);
    }
  };

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (activeTab === 'ask') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, chatLoading, activeTab]);

  // Send Question to RAG Endpoint
  const handleSendQuestion = async (customQuery = null) => {
    const query = (customQuery || chatInput).trim();
    if (!query || chatLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatMessages(prev => [...prev, userMsg]);
    if (!customQuery) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          question: query,
          topics: selectedTopics.map(t => t.name)
        })
      });

      const data = await res.json();
      if (res.ok) {
        const aiMsg = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: data.answer || 'No answer generated.',
          sources: data.sources || [],
          from_live_search: data.from_live_search || false,
          grounded: data.grounded,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, aiMsg]);
      } else {
        const errorMsg = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: data.error || 'Failed to retrieve an answer. Please try again.',
          sources: [],
          from_live_search: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, errorMsg]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setChatMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: 'Network error connecting to the AI intelligence engine. Please ensure services are running.',
        sources: [],
        from_live_search: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleClearChat = () => {
    setChatMessages([]);
    showToast('Chat history cleared', 'info');
  };

  // Live Web Search Handler (Google CSE -> Brave Search)
  const handleLiveSearch = async (overrideQuery = null) => {
    const q = (overrideQuery || liveSearchQuery).trim();
    if (!q || liveSearchLoading) return;

    setLiveSearchLoading(true);
    try {
      const res = await fetch('/api/search/live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          topic: selectedTopics[0]?.name || 'general'
        })
      });

      const data = await res.json();
      if (res.ok) {
        const results = data.results || [];
        setLiveSearchResults(results);
        showToast(`Found ${results.length} live search result(s) for "${q}"`, results.length > 0 ? 'success' : 'info');
      } else {
        showToast(data.error || 'Live search failed', 'error');
      }
    } catch (err) {
      console.error('Live search error:', err);
      showToast('Error connecting to live search proxy', 'error');
    } finally {
      setLiveSearchLoading(false);
    }
  };

  const handleClearLiveSearch = () => {
    setLiveSearchResults(null);
    setLiveSearchQuery('');
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
      console.error('Pipeline execution error:', err);
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
          <button
            className={`tab-btn ${activeTab === 'ask' ? 'active' : ''}`}
            onClick={() => setActiveTab('ask')}
          >
            <MessageSquareText size={16} /> Ask News (RAG)
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
            
            {/* Standalone Live Search Bar */}
            <div className="live-search-container">
              <form onSubmit={(e) => { e.preventDefault(); handleLiveSearch(); }} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <div style={{ position: 'relative', flex: 1 }}>
                  <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search live web news (e.g. OpenAI updates, SpaceX Starship, Delhi AQI, Ghaziabad transit)..."
                    value={liveSearchQuery}
                    onChange={(e) => setLiveSearchQuery(e.target.value)}
                    style={{ paddingLeft: '44px', borderRadius: 'var(--radius-full)' }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={liveSearchLoading || !liveSearchQuery.trim()}
                  className="btn-primary"
                  style={{ padding: '12px 22px', borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap' }}
                >
                  <Search size={16} /> {liveSearchLoading ? 'Searching...' : 'Search Live Web'}
                </button>
                {liveSearchResults && (
                  <button
                    type="button"
                    onClick={handleClearLiveSearch}
                    className="btn-secondary"
                    style={{ padding: '12px 18px', borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap' }}
                  >
                    <X size={16} /> Clear
                  </button>
                )}
              </form>
            </div>

            {/* Live Search Results View (When Active) */}
            {liveSearchResults && (
              <div style={{ marginBottom: '36px', background: '#F8F8FD', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1.5px solid rgba(108, 92, 231, 0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>🔎</span> Live Web Results for "{liveSearchQuery}"
                    </h3>
                    <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                      Retrieved in real-time via Google Custom Search / Brave Search fallback.
                    </p>
                  </div>
                  <button
                    onClick={handleClearLiveSearch}
                    className="btn-secondary"
                    style={{ fontSize: '12.5px', padding: '6px 14px' }}
                  >
                    ← Back to Curated Feed
                  </button>
                </div>

                {liveSearchResults.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                    No live web search results found for this query. Try different keywords.
                  </div>
                ) : (
                  <div className="news-grid">
                    {liveSearchResults.map((item, idx) => (
                      <div key={idx} className="news-card" style={{ '--card-accent': item.source === 'google' ? '#4285F4' : '#FF5500' }}>
                        <div>
                          <div className="card-top-row">
                            <span className={`source-badge ${item.source === 'google' ? 'search-badge-google' : item.source === 'brave' ? 'search-badge-brave' : 'search-badge-web'}`}>
                              {item.source ? item.source.toUpperCase() : 'WEB'}
                            </span>
                          </div>
                          <h4 className="card-title">
                            <a href={item.url} target="_blank" rel="noopener noreferrer">
                              {item.title}
                            </a>
                          </h4>
                          <p className="card-snippet">
                            {item.summary || item.snippet}
                          </p>
                        </div>
                        <div className="card-footer">
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            {item.published ? new Date(item.published).toLocaleDateString() : 'Live Web'}
                          </span>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="read-more-link"
                            style={{ color: item.source === 'google' ? '#4285F4' : '#FF5500' }}
                          >
                            Read Source <ExternalLink size={13} />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Standard Curated Feed Header */}
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

        {/* =================================================================== */}
        {/* TAB 3: ASK NEWS (RAG Natural Language Search & Q&A)                 */}
        {/* =================================================================== */}
        {activeTab === 'ask' && (
          <div className="chat-container">
            {/* Header bar */}
            <div className="chat-header-bar">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(108, 92, 231, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                  <Bot size={20} />
                </div>
                <div>
                  <h2 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-main)', margin: 0 }}>
                    AI News Assistant
                  </h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
                    Grounded RAG Search over {previewData.length > 0 ? `${totalArticlesLoaded} active` : 'all'} ingested news articles
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '11px', background: 'rgba(0, 217, 165, 0.12)', color: '#00D9A5', fontWeight: '700', padding: '4px 10px', borderRadius: 'var(--radius-full)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  ● Vector Search Online
                </span>
                {chatMessages.length > 0 && (
                  <button
                    onClick={handleClearChat}
                    className="btn-secondary"
                    style={{ fontSize: '12px', padding: '6px 12px' }}
                    title="Clear conversation"
                  >
                    <RotateCcw size={13} /> Clear
                  </button>
                )}
              </div>
            </div>

            {/* Message scroll area */}
            <div className="chat-messages-scroll">
              {chatMessages.length === 0 ? (
                <div style={{ textAlign: 'center', margin: 'auto', maxWidth: '520px', padding: '32px 16px' }}>
                  <div style={{ width: '56px', height: '56px', borderRadius: '18px', background: 'rgba(108, 92, 231, 0.1)', color: 'var(--primary)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <Sparkles size={28} />
                  </div>
                  <h3 style={{ fontSize: '19px', fontWeight: '800', color: 'var(--text-main)', marginBottom: '8px' }}>
                    Ask anything about the news
                  </h3>
                  <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '24px' }}>
                    Query our vector-indexed news repository. Every answer is synthesized with factual anti-hype context and direct citations to original sources.
                  </p>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
                    <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                      Try asking:
                    </div>
                    {SUGGESTED_PROMPTS.map((prompt, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendQuestion(prompt)}
                        className="suggested-chip"
                        style={{ textAlign: 'left', padding: '10px 16px', fontSize: '13px', borderRadius: 'var(--radius-lg)' }}
                      >
                        ⚡ {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                chatMessages.map(msg => (
                  <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    {msg.role === 'user' ? (
                      <div className="chat-bubble-user">
                        <div>{msg.text}</div>
                        <div style={{ fontSize: '11px', opacity: 0.75, textAlign: 'right', marginTop: '4px' }}>
                          {msg.timestamp}
                        </div>
                      </div>
                    ) : (
                      <div className="chat-bubble-ai">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            ✨ Intelligence Briefing
                          </span>
                          {msg.from_live_search ? (
                            <span className="live-search-notice-pill">
                              🔎 Live Web Search Fallback
                            </span>
                          ) : (
                            msg.grounded && (
                              <span style={{ fontSize: '10.5px', background: 'rgba(0, 217, 165, 0.12)', color: '#00D9A5', fontWeight: '700', padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>
                                Grounded in Collection
                              </span>
                            )
                          )}
                        </div>

                        <div style={{ whiteSpace: 'pre-line', fontSize: '14.5px', lineHeight: '1.65', color: 'var(--text-main)' }}>
                          {msg.text}
                        </div>

                        {/* Grounded Sources Cards */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="chat-sources-container">
                            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span>📚 Grounded Sources ({msg.sources.length}):</span>
                            </div>
                            <div className="chat-source-grid">
                              {msg.sources.map((src, sIdx) => {
                                const topicColor = getCategoryColor(src.topic);
                                return (
                                  <a
                                    key={sIdx}
                                    href={src.source_url || '#'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="chat-source-card"
                                  >
                                    <div>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                        <span style={{ fontSize: '10.5px', fontWeight: '700', background: topicColor, color: '#ffffff', padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>
                                          {src.topic || 'NEWS'}
                                        </span>
                                        {src.similarity && (
                                          <span style={{ fontSize: '10.5px', color: 'var(--text-muted)', fontWeight: '600' }}>
                                            {(src.similarity * 100).toFixed(0)}% match
                                          </span>
                                        )}
                                      </div>
                                      <div style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-main)', lineHeight: '1.35', display: '-webkit-box', WebkitLineClamp: 2, lineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                        {src.title}
                                      </div>
                                    </div>
                                    <div style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                      View Source <ExternalLink size={11} />
                                    </div>
                                  </a>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'right', marginTop: '10px' }}>
                          {msg.timestamp}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}

              {chatLoading && (
                <div className="typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: '6px', fontWeight: '600' }}>
                    Searching vector embeddings & synthesizing answer...
                  </span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Quick suggested prompts bar (if chat is not empty) */}
            {chatMessages.length > 0 && (
              <div className="suggested-prompts-bar">
                <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: '700', alignSelf: 'center', marginRight: '4px' }}>
                  Quick:
                </span>
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendQuestion(prompt)}
                    disabled={chatLoading}
                    className="suggested-chip"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuestion();
              }}
              className="chat-input-bar"
            >
              <input
                type="text"
                className="form-input"
                placeholder="Ask any question about today's news..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
                style={{ flex: 1, padding: '12px 18px', borderRadius: 'var(--radius-full)' }}
              />
              <button
                type="submit"
                disabled={chatLoading || !chatInput.trim()}
                className="btn-primary"
                style={{ borderRadius: 'var(--radius-full)', padding: '12px 22px' }}
              >
                <Send size={16} /> Send
              </button>
            </form>
          </div>
        )}

      </main>
    </div>
  );
}
