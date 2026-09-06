# 🚀 AI News Aggregator & Intelligence Feed — Production Deployment Guide

This guide walks you step-by-step through deploying the **AI News Aggregator** to:
1. **AWS EC2 (Recommended for full control & production Docker stack)**
2. **Render.com (Zero-ops cloud platform via `render.yaml` Blueprint)**
3. **Vercel + Render (Hybrid Edge Frontend + Cloud Backends)**

---

## 📋 Prerequisites & Required API Keys

Before deploying, ensure you have the following credentials ready:

| Secret / Config | Where to get it | Purpose | Required? |
| :--- | :--- | :--- | :--- |
| `MONGODB_URI` | [MongoDB Atlas](https://cloud.mongodb.com) | Database connection string (M0 Free Tier) | **Yes** |
| `GROQ_API_KEY` | [Groq Cloud Console](https://console.groq.com) | Free, ultra-fast LLM summarization & RAG synthesis | **Yes** |
| `INTERNAL_API_SECRET` | Generate random hex: `openssl rand -hex 32` | Shared secret securing Express $\leftrightarrow$ FastAPI communication | **Yes** |
| `EMAIL_USER` | Your Gmail address | Sender address for scheduled briefings | **Yes** (for email delivery) |
| `EMAIL_APP_PASSWORD` | [Google App Passwords](https://myaccount.google.com/apppasswords) | 16-character Gmail application password | **Yes** (for email delivery) |
| `GOOGLE_CSE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) | Custom Search JSON API fallback (Free 100/day) | Optional (Live search) |
| `GOOGLE_CSE_ID` | [Programmable Search Engine](https://programmablesearchengine.google.com/) | Google Search Engine ID (cx) | Optional (Live search) |
| `BRAVE_API_KEY` | [Brave Search API](https://brave.com/search/api/) | Secondary web search fallback (Free 2,000/mo) | Optional (Live search) |

> [!IMPORTANT]
> **MongoDB Atlas Network Access:**
> Go to your **MongoDB Atlas Dashboard** $\rightarrow$ **Network Access** $\rightarrow$ **Add IP Address** $\rightarrow$ select **"Allow Access from Anywhere" (`0.0.0.0/0`)** or enter your EC2 Elastic IP so your cloud backend can connect.

---

## Method 1: AWS EC2 Deployment (Docker Compose)

This runs the entire system (**React Frontend on NGINX**, **Node/Express API Gateway**, and **Python FastAPI AI Engine**) inside lightweight, isolated Docker containers on a single AWS EC2 instance.

### Step 1: Launch an AWS EC2 Instance
1. Open the [AWS EC2 Console](https://console.aws.amazon.com/ec2).
2. Click **Launch Instance**:
   - **Name**: `ai-news-aggregator`
   - **AMI**: `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` (or `Amazon Linux 2023`)
   - **Instance Type**: `t3.small` or `t3.medium` (recommended: 2 vCPUs, 2–4 GB RAM for FastEmbed model loading). A `t2.micro` or `t3.micro` works if you configure a 2GB swap file.
   - **Key Pair**: Select or create an SSH key pair (`.pem`).
3. **Configure Network / Security Group**:
   - Allow **SSH (Port 22)** from `My IP`.
   - Allow **HTTP (Port 80)** from `0.0.0.0/0` (Anywhere).
   - Allow **HTTPS (Port 443)** from `0.0.0.0/0` (Anywhere).
4. Click **Launch Instance**.

---

### Step 2: Connect to your EC2 Instance
From your local terminal (where your `.pem` file is located):
```bash
ssh -i "your-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP_OR_DNS>
```

---

### Step 3: Clone Repository & Run Automated Deploy Script
```bash
# 1. Clone your project
git clone https://github.com/satsbee09/AI-News-Aggregator.git
cd AI-News-Aggregator

# 2. Configure production environment variables
cp .env.production.example .env
nano .env   # (Add your MONGODB_URI, GROQ_API_KEY, EMAIL credentials, etc. Save with Ctrl+O, Enter, Ctrl+X)

# 3. Make deploy script executable and run
chmod +x deploy-aws.sh
./deploy-aws.sh
```

The script will automatically:
- Install Docker Engine and Docker Compose.
- Build the optimized Docker images for Python FastAPI, Node/Express, and React Nginx.
- Start all services with automated restart policies.
- Run health checks on all tiers.

---

### Step 4: Access Your Live Application
Open your browser and navigate to:
```
http://<YOUR_EC2_PUBLIC_IP>
```
Your full-featured React 19 Dashboard, Live Inshorts Feed, Ask News Chat, and Delivery Scheduler are now live!

---

### Step 5: (Optional) Attach Domain & Free SSL with Let's Encrypt / Certbot
If you have a domain name (e.g. `news.yourdomain.com` pointing to your EC2 IP):
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d news.yourdomain.com
```

---

## Method 2: Render.com 1-Click Blueprint Deployment

Render provides free/low-cost managed hosting with automated CI/CD directly from GitHub.

### Step 1: Push Code to GitHub
Ensure all latest files (`render.yaml`, Dockerfiles, etc.) are committed and pushed:
```bash
git add .
git commit -m "Add production deployment configurations"
git push origin main
```

### Step 2: Create Blueprint on Render
1. Log in to [Render.com](https://render.com).
2. In the top-right, click **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository: `satsbee09/AI-News-Aggregator`.
4. Render will read [`render.yaml`](file:///render.yaml) and automatically create:
   - `ai-news-fastapi` (Python Web Service)
   - `ai-news-express` (Node.js Web Service)
   - `ai-news-frontend` (Static Site)
5. Under **Environment Variables**, fill in your secret keys:
   - `MONGODB_URI`
   - `GROQ_API_KEY`
   - `EMAIL_USER` & `EMAIL_APP_PASSWORD`
   - `RECIPIENT_EMAIL`
6. Click **Apply**. Render will automatically build, link, and deploy all 3 services!

---

## Method 3: Hybrid Deployment (Vercel Frontend + Render Backends)

If you prefer deploying the React frontend on **Vercel's global edge network**:

1. Deploy `ai-news-express` and `ai-news-fastapi` on Render or Railway.
2. In [Vercel](https://vercel.com), click **Add New Project** $\rightarrow$ import `AI-News-Aggregator`.
3. Set **Root Directory** to `frontend`.
4. Add the Environment Variable:
   - `VITE_API_BASE_URL` = `https://your-express-service.onrender.com`
5. Click **Deploy**.

---

## 🛠️ Post-Deployment Verification Checklist

Once deployed, verify your live instance:

1. **Health Check Endpoints**:
   - NGINX / Frontend: `http://<YOUR_IP>/` $\rightarrow$ 200 OK
   - Express API Gateway: `http://<YOUR_IP>/api/health` $\rightarrow$ returns MongoDB `connected`
   - FastAPI Backend (internal or mapped): `http://<YOUR_IP>:8000/api/health`
2. **Account Creation & Preferences**:
   - Enter your email address on the Dashboard and select topics (e.g. Frontier AI, Sports, Weather).
   - Click **Save Preferences** $\rightarrow$ verify success toast.
3. **Live News Feed**:
   - Click **Live Preview Feed** $\rightarrow$ verify that articles and weather summaries render smoothly.
4. **LangGraph RAG Assistant**:
   - Navigate to the **Ask AI** tab and send a question (e.g. *"What are the latest AI breakthroughs?"*).
   - Verify grounded citations and instant synthesis.
5. **Instant Email Delivery**:
   - Click **Trigger Test Briefing** $\rightarrow$ verify an email digest arrives in your inbox.

---

## 🔧 Useful Maintenance & Docker Commands

| Action | Command on EC2 |
| :--- | :--- |
| **View all live container logs** | `sudo docker compose logs -f` |
| **View only FastAPI ML engine logs** | `sudo docker compose logs -f fastapi-backend` |
| **View only Node Express logs** | `sudo docker compose logs -f express-gateway` |
| **Restart all services** | `sudo docker compose restart` |
| **Rebuild and update containers after git pull** | `git pull && sudo docker compose up -d --build` |
| **Stop all containers** | `sudo docker compose down` |
| **Inspect container CPU & Memory usage** | `sudo docker stats` |
