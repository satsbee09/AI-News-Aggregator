# AI News Aggregator — Master Project & Interview Handbook

This living guide contains everything you need to deeply understand the project and speak about it with confidence and clarity in technical interviews.

---

## 1. 30-Second Elevator Pitch (For Interviewers)

> *"I built an automated, end-to-end **AI News Intelligence & Digest Pipeline** that aggregates, summarizes, curates, and delivers daily updates from top AI labs (OpenAI, Anthropic) and technical YouTube channels directly to a user's inbox.*
>
> *The system is architected around clean software engineering principles: a decoupled scraper registry, an idempotent SQLite persistence layer using SQLAlchemy, an LLM-driven summarization and profile-based ranking engine using Groq/Gemini, and serverless daily scheduling via GitHub Actions—all built at **zero infrastructure cost**."*

---

## 2. Problem Statement & Motivation

### The Problem
* **Information Overload:** The AI field evolves daily across scattered sources (company research blogs, YouTube teardowns, arXiv, social media).
* **Clickbait & Noise:** Many AI articles and videos are filled with marketing hype rather than technical substance.
* **Cost & Maintenance Overhead:** Traditional aggregators rely on paid APIs (GPT-4o, hosted Postgres, cloud cron servers), making them expensive and heavy for personal or small-team use.

### The Solution
* **Multi-source Automated Scraping:** Extracts raw articles and video transcripts automatically.
* **Hype-Free LLM Summarization:** Converts long articles and 30-minute videos into 3-bullet core takeaways.
* **Personalized Curation:** Uses an AI agent to score and rank news based on a customizable user profile (e.g., *"Focus on LLM architectures, ignore marketing buzz"*).
* **Zero-Cost Serverless Pipeline:** Powered 100% by free tiers (Groq LLaMA 3.3, SQLite, GitHub Actions, Gmail SMTP).

---

## 3. High-Level Architecture & Data Flow

```text
[Sources: RSS / YouTube] 
       │
       ▼
[Scraper Layer] ────────► Normalizes data into unified Article schemas
       │
       ▼
[Database (SQLite)] ─────► Persists raw articles & prevents duplicate scraping
       │
       ▼
[LLM Summarizer Agent] ──► Generates concise 3-bullet takeaways (Groq / Gemini)
       │
       ▼
[Curator Agent] ─────────► Scores & ranks articles against User Profile
       │
       ▼
[Email Service] ─────────► Builds styled HTML email & delivers via Gmail SMTP
       │
       ▼
[Sent Logs] ─────────────► Tracks delivered IDs to guarantee 0 duplicate emails
```

---

## 4. Tech Stack & "Why This Tool?" (Interview Justifications)

| Technology | Purpose | Why We Chose It (Interview Answer) |
| :--- | :--- | :--- |
| **Python 3.12+** | Core Language | Robust ecosystem for scraping, data manipulation, ORMs, and AI/LLM SDKs. |
| **`uv`** | Package & Environment Manager | Up to 10–100x faster than standard `pip`/`venv`, built in Rust, single binary, with deterministic lockfiles. |
| **Pydantic & Pydantic-Settings** | Config & Data Validation | Guarantees type safety, parses environment variables, and fails fast at startup if configuration is missing. |
| **SQLAlchemy (ORM)** | Persistence Layer | Provides decoupled database models, migration flexibility, and protects against raw SQL injection. |
| **SQLite** | Database Engine | Zero-configuration, serverless, single-file database. Perfect for single-user workloads with 0 cloud cost. |
| **Feedparser** | RSS Parsing | Handles malformed or non-standard RSS/Atom feeds reliably across diverse blogs. |
| **`youtube-transcript-api`** | Video Content Extraction | Extracts closed captions/transcripts directly from YouTube video IDs without requiring paid quotas or proxies. |
| **Groq API (LLaMA 3.3 70B)** | LLM Inference | Ultra-low latency (~500 tokens/sec), OpenAI-compatible client, and generous free tier. |
| **Gmail SMTP (`smtplib`)** | Delivery | Standard, reliable email protocol using secure TLS/SSL and 16-character Google App Passwords. |
| **GitHub Actions** | Automation & Scheduling | Completely serverless cron runner (`on: schedule`), eliminating the need for a 24/7 paid server. |

---

## 5. Core Concepts & Definitions (Explained in Plain English)

### 1. What is an ORM (Object-Relational Mapping)?
* **Definition:** A library (like SQLAlchemy) that lets you interact with database tables as if they were regular Python classes and objects.
* **Why use it?** Instead of writing `INSERT INTO articles VALUES (...)` in raw SQL strings, you write `session.add(Article(title="..."))`. It prevents syntax errors and SQL injection.

### 2. What is Idempotency?
* **Definition:** An operation is *idempotent* if running it once or running it 100 times produces the exact same result without duplicate side-effects.
* **How we apply it:** If the scraper runs twice in an hour, it checks `url` or `article_id` in SQLite and ignores existing items. No duplicate articles or duplicate emails are ever generated.

### 3. What is Decoupling / Separation of Concerns?
* **Definition:** Dividing a software application into distinct sections, where each section handles a specific responsibility.
* **How we apply it:** 
  - `scrapers/` only cares about fetching raw HTML/XML.
  - `database/` only cares about saving/querying data.
  - `agent/` only cares about prompting the LLM.
  - If we switch from SQLite to PostgreSQL, or from Groq to Gemini, we only modify one isolated module without breaking the others.

### 4. What is `pydantic-settings`?
* **Definition:** A tool that automatically reads environment variables (`.env`) and converts them into validated Python data types (integers, strings, booleans).
* **Why use it?** If `EMAIL_PORT` is not an integer or `GROQ_API_KEY` is empty, the application raises a clear error at startup rather than crashing halfway through a live pipeline run.

---

## 6. Code Walkthrough by Phase (Updated As We Build)

### Phase 0: Project Setup & Environment Configuration
* **Files Built:** `pyproject.toml`, `app/config.py`, `main.py`, `.env.example`, `.gitignore`.
* **Key Code Explained:**
  - `class Settings(BaseSettings)`: Defines configuration schema with default fallback values.
  - `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`: Tells Pydantic to read `.env` and ignore extra variables.
  - `settings = Settings()`: Instantiates a singleton settings object imported across the app.
  - `[tool.uv] package = false`: Configures `uv` for application-mode rather than packaging mode.

### Phase 1: Persistence Layer & SQLAlchemy ORM
* **Files Built:** `app/database/models.py`, `app/database/connection.py`, `app/database/repository.py`, `tests/test_db.py`.
* **Key Code Explained:**
  - **Modern SQLAlchemy 2.0 Syntax:** Uses `Mapped[T]` and `mapped_column()` for 100% static type safety across tables.
  - **Tables:** `Article` (raw content & source), `Digest` (LLM-generated summary, 1-to-1 with Article), and `SentLog` (tracks emails sent to prevent duplicates).
  - **Outer Join Query (`outerjoin`):** `select(Article).outerjoin(Digest).where(Digest.id.is_(None))` efficiently finds raw articles that have not yet been summarized by the LLM without loading everything into Python memory.
  - **Idempotency Guard:** `save_article()` queries `select(Article).where(Article.url == url)` before inserting. If the URL exists, it returns `None`, guaranteeing no duplicate rows even if a scraper runs 50 times a day.

### Phase 2: First RSS Scraper & Abstract Scraper Pattern
* **Files Built:** `app/scrapers/base.py`, `app/scrapers/rss_scraper.py`, `tests/test_rss_scraper.py`.
* **Key Code Explained:**
  - **Abstract Base Class (`BaseScraper`):** Enforces a uniform `get_articles(hours: int = 24) -> List[ScrapedArticle]` contract across all data sources (Polymorphism).
  - **HTML Sanitization:** Uses regex stripping (`re.sub(r'<[^>]+>', ' ', html)`) to extract clean, un-polluted text for the LLM.
  - **Timezone-Aware Filtering:** Normalizes heterogeneous RSS timestamps (RFC 822 / ISO 8601) to UTC `datetime` objects and filters items within an operational window (e.g. last 48-72 hours).

### Phase 3: YouTube Channel Scraper & Transcripts
* **Files Built:** `app/scrapers/youtube_scraper.py`, `tests/test_youtube_scraper.py`.
* **Key Code Explained:**
  - **Free Video Discovery via Channel RSS:** Uses `https://www.youtube.com/feeds/videos.xml?channel_id=...` to list new videos with zero Google Cloud API quota and zero authentication.
  - **Automated Caption Extraction (`youtube-transcript-api`):** Extracts full spoken subtitles and joins timed chunks into plain English text.
  - **Defensive Fallback Pattern:** If a video creator disables closed captions (`TranscriptsDisabled`, `NoTranscriptFound`), the scraper catches the error and falls back to the video description, ensuring pipeline continuity without crashing.

### Phase 4: LLM Summarization & Anti-Hype Prompting
* **Files Built:** `app/agent/base_llm.py`, `app/agent/digest_agent.py`, `app/services/process_digest.py`, `tests/test_digest_agent.py`.
* **Key Code Explained:**
  - **Model Fallback Chain:** Implemented resilient multi-model failover in `base_llm.py` (`qwen/qwen3.8-27b`, `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`) ensuring zero downtime if any single model is throttled or deprecated.
  - **Anti-Hype System Prompt:** Instructs the LLM to discard clickbait and marketing fluff (*"game-changing"*, *"shocking"*) and extract core technical contributions, model benchmarks, and architectural takeaways.
  - **Structured Schema (`Pydantic`):** Enforces a strict JSON contract (`summary`, `key_takeaways: list[str]`, `category`) that parses directly into typed Python objects.

### Phase 5: Curation & User Profile-Based Ranking
* **Files Built:** `app/profiles/user_profile.py`, `app/agent/curator_agent.py`, `tests/test_curator_agent.py`.
* **Key Code Explained:**
  - **Declarative User Profile:** Defines targeted technical domains (e.g., LLM architectures, reasoning capabilities) and explicit exclusions (e.g., crypto buzzwords, generic PR) without altering core code.
  - **Relevance Scoring Engine:** The Curator Agent scores candidate digests from 1 to 10 and produces a human-readable justification for each score.
  - **Top-N Slicing:** Sorts digests in descending order of relevance and slices the top 5 articles, respecting the user's reading bandwidth.

### Phase 6: Email Generation & SMTP Delivery
* **Files Built:** `app/services/email_service.py`, `tests/test_email_service.py`.
* **Key Code Explained:**
  - **Zero-Cost Delivery with Gmail SMTP:** Uses Python's native `smtplib` + `MIMEMultipart` over TLS (Port 587) with a secure 16-character Google App Password.
  - **Client-Resilient HTML Email Design:** Formats cards, score badges, and bullet takeaways using standard inline CSS compatible with all major email clients (Gmail, Apple Mail, Outlook).
  - **Delivery State Tracking & Deduplication:** Commits sent digest IDs to `sent_logs` within the same transaction to guarantee that delivered stories are never repeated in future digests.
  - **Local HTML Artifact Preview:** Generates `data/latest_digest_preview.html` for offline visual inspection and dry-run testing.

### Phase 7: End-to-End Orchestrator & CLI Interface
* **Files Built:** `app/services/pipeline_service.py`, `main.py`.
* **Key Code Explained:**
  - **Unified Pipeline Orchestrator (`run_daily_pipeline`):** Coordinates Ingestion ➔ Persistence ➔ Summarization ➔ Ranking ➔ Delivery ➔ State Logging sequentially with structured timing logs.
  - **The Scraper Registry Pattern:** Scrapers are registered in a polymorphic array `SCRAPER_REGISTRY = [RssScraper(), YouTubeScraper()]`, making adding future sources (e.g. ArXiv) a single-line change.
  - **CLI Flags (`argparse`):** Enables operational flexibility via `--dry-run`, `--hours <N>`, `--limit <N>`, and `--scrape-only`.

### Phase 8: Free Serverless Automation with GitHub Actions
* **Files Built:** `.github/workflows/daily_digest.yml`.
* **Key Code Explained:**
  - **Zero-Server Infrastructure:** Replaces paid background workers (Render/AWS/GCP) with free GitHub Actions scheduled workflows (`on: schedule`, cron syntax).
  - **Secure Secrets Injection:** Securely loads `GROQ_API_KEY`, `EMAIL_USER`, and `EMAIL_APP_PASSWORD` from encrypted repository secrets directly into the runner environment.
  - **Manual Trigger Support (`workflow_dispatch`):** Allows instant on-demand pipeline execution directly from the GitHub web UI for testing and verification.

---

## 7. Top Interview Questions & How to Answer

### Q1: "Why did you choose SQLite over PostgreSQL or MongoDB?"
> **Answer:** *"For a single-user daily digest aggregator, PostgreSQL introduces unnecessary infrastructure complexity, network latency, and hosting costs. SQLite is a serverless, zero-maintenance ACID-compliant single-file database that handles millions of rows easily. Furthermore, because I used SQLAlchemy as the ORM layer, transitioning to PostgreSQL in the future requires changing only a single connection string in `.env` without rewriting any business logic."*

### Q2: "How do you handle API rate limits and scraper failures?"
> **Answer:** *"I implemented defensive programming with try/except boundaries around each individual scraper. If Anthropic's RSS feed is temporarily down or a YouTube video has disabled transcripts, the error is logged, and the pipeline continues gracefully with the remaining sources. For LLM calls, batching and retry logic prevent exceeding rate limits."*

### Q3: "How do you ensure you don't email the user the same article twice?"
> **Answer:** *"I use a dedicated `sent_logs` table in the database. Before generating the final email digest, the curation service filters out any article or digest ID that already exists in `sent_logs`. Once the email is successfully dispatched via SMTP, the new IDs are committed in a database transaction."*

### Q4: "Why use Groq instead of OpenAI?"
> **Answer:** *"Groq provides high-performance LPU (Language Processing Unit) inference for state-of-the-art open models like LLaMA 3.3 70B at near-instant speeds (~500 tokens/sec) with a free tier. It uses the OpenAI API standard format, making it trivial to switch backends with zero structural refactoring."*

---
*(This handbook will be updated as we complete subsequent phases!)*
