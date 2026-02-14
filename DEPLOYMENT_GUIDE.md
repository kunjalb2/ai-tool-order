# Kunjal Agents - Deployment Guide

## Table of Contents

1. [Deployment Prerequisites](#deployment-prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Deployment](#local-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Production Checklist](#production-checklist)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#deployment-troubleshooting)

---

## Deployment Prerequisites

### Required Software

| Software | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| PostgreSQL | 15+ | Database |
| Docker | 20.10+ | Containerization (optional) |
| Docker Compose | 2.20+ | Multi-container management (optional) |

### Required Services & Accounts

| Service | Purpose | How to Get |
|----------|---------|-------------|
| **OpenRouter API Key** | AI model access | Sign up at openrouter.ai |
| **Gmail Account** | Verification emails | Any Gmail account |
| **Gmail App Password** | SMTP authentication | Generate in Google Account settings |

---

## Environment Configuration

### Environment Variables Reference

Create a `.env` file in the project root:

```bash
# =================================================================
# AI Model Configuration
# =================================================================
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# =================================================================
# Database Configuration
# =================================================================
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://kunjal_user:kunjal_password@localhost:5432/kunjal_agents

# =================================================================
# Email Configuration (for verification codes)
# =================================================================
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# =================================================================
# Frontend Configuration (production only)
# =================================================================
# VITE_API_URL=http://your-backend-domain.com
```

### How to Get Gmail App Password

1. Go to https://myaccount.google.com/
2. Click **Security** on the left
3. Scroll down to **2-Step Verification**
4. Click **App passwords**
5. Select **Mail** app
6. Enter a name (e.g., "Kunjal Agents")
7. Click **Generate**
8. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

**IMPORTANT**: Use the App Password, NOT your regular Gmail password!

---

## Local Deployment

### Method 1: Using start.sh Script (Recommended for Development)

```bash
# 1. Navigate to project directory
cd kunjal-agents

# 2. Make start script executable (if not already)
chmod +x start.sh

# 3. Start both services
./start.sh
```

**Output:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

**To Stop**: Press `Ctrl+C`

### Method 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd server
pip install -r requirements.txt
python seed_db.py  # First time only - creates tables and sample data
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Quick Start (Docker Compose)

```bash
# 1. Navigate to project directory
cd kunjal-agents

# 2. Create .env file (see Environment Configuration above)
cp .env.example .env
# Edit .env with your values

# 3. Start all services
docker-compose up -d --build

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down

# 6. Stop and remove all data (fresh start)
docker-compose down -v
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Services Explained

| Service | Port | Description |
|---------|-------|-------------|
| postgres | 5432 | PostgreSQL database |
| backend | 8000 | FastAPI backend |
| frontend | 5173 | Vite dev server |

### Docker Tips

**View environment variables in container:**
```bash
docker-compose exec backend env
```

**Access PostgreSQL directly:**
```bash
docker-compose exec postgres psql -U kunjal_user -d kunjal_agents
```

**Restart specific service:**
```bash
docker-compose restart backend
```

**Rebuild after code changes:**
```bash
docker-compose up -d --build backend
```

---

## Cloud Deployment

### Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLOUD INFRASTRUCTURE                        │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Frontend   │  │    Backend    │  │   Database   │   │
│  │   (React)     │  │   (FastAPI)   │  │ (PostgreSQL)  │   │
│  │   Nginx/Caddy │  │   Uvicorn    │  │              │   │
│  │   Port: 443   │  │   Port: 8000   │  │  Port: 5432   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                   │                    │              │
│         └───────────────────┼────────────────────┘              │
│                             │                                   │
│  ┌────────────────────────┴────────────────────────────────────┐   │
│  │              EXTERNAL SERVICES                             │   │
│  │  - OpenRouter API (AI Model)                            │   │
│  │  - Gmail SMTP (Email Delivery)                             │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Option 1: Deploy to Render.com

**Why Render?**
- Free tier available
- Simple deployment
- Built-in PostgreSQL
- SSL certificates included

**Backend Deployment (Render):**

1. Go to https://render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `server`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables** (from .env file above)
5. Deploy!

**Database (Render PostgreSQL):**

1. In Render dashboard: **New +** → **PostgreSQL**
2. Copy the **Internal Database URL**
3. Update `DATABASE_URL` in backend service
4. Run seed script via Render Shell:
   ```bash
   python seed_db.py
   ```

**Frontend Deployment (Vercel/Netlify):**

1. Build frontend:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy `dist/` folder to Vercel or Netlify
3. Set environment variable: `VITE_API_URL=https://your-backend.onrender.com`

### Option 2: Deploy to Railway

**Why Railway?**
- GitHub integration
- Automatic deployments
- Built-in PostgreSQL
- Simple CLI

**Quick Deploy:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

Then add environment variables in Railway dashboard.

### Option 3: VPS Deployment (DigitalOcean, AWS, etc.)

**Prerequisites:**
- Ubuntu 20.04+ server
- Domain name (optional)
- SSH access

**Step 1: Server Setup**

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**Step 2: Deploy Application**

```bash
# Clone repository
git clone your-repo-url
cd kunjal-agents

# Create production env file
cp .env.example .env.production
nano .env.production  # Edit with your values

# Start services
docker-compose -f docker-compose.prod.yml up -d --build
```

**Step 3: Setup Reverse Proxy (Nginx)**

```bash
# Install Nginx
apt install nginx -y

# Create site config
nano /etc/nginx/sites-available/kunjal-agents
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE endpoint (special handling)
    location /api/events {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # SSE specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        chunked_transfer_encoding on;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/kunjal-agents /etc/nginx/sites-enabled/

# Test and restart
nginx -t
systemctl restart nginx
```

**Step 4: Setup SSL (Certbot)**

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d your-domain.com

# Certbot automatically configures Nginx with SSL!
```

---

## Production Checklist

### Security MUST-DOs

- [ ] **Change JWT Secret Key** in `services/auth.py`
- [ ] **Use HTTPS** everywhere (SSL certificate)
- [ ] **Enable CORS** only for your domain
- [ ] **Disable DEBUG** logging in production
- [ ] **Use App Passwords** (not real passwords)
- [ ] **Set up firewalls** (only allow necessary ports)
- [ ] **Regular backups** of PostgreSQL database
- [ ] **Monitor logs** for suspicious activity

### Performance Optimizations

- [ ] **Enable PostgreSQL connection pooling**
- [ ] **Setup CDN** for frontend static assets
- [ ] **Enable gzip compression** in Nginx
- [ ] **Configure rate limiting** on API endpoints
- [ ] **Setup monitoring** (Sentry for errors, etc.)

### Configuration Changes

**Backend (`config.py`):**
```python
# CHANGE THIS IN PRODUCTION!
SECRET_KEY = "your-super-secret-key-change-in-production"

# Update CORS origins
CORS_ORIGINS = ["https://your-domain.com"]
```

**Database (`database.py`):**
```python
# Add connection pooling for production
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

---

## Monitoring & Maintenance

### Health Checks

**Backend Health Endpoint:**
```bash
curl https://your-domain.com/health
```

**Expected Response:**
```json
{"status": "ok"}
```

### Database Backups

**Automated Backup Script:**
```bash
#!/bin/bash
# backup.sh - Run daily via cron

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgres"
DB_NAME="kunjal_agents"
DB_USER="kunjal_user"

# Create backup
docker-compose exec -T postgres pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql"
```

**Setup Cron Job:**
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Log Monitoring

**View Backend Logs:**
```bash
# Docker
docker-compose logs -f backend

# Systemd
journalctl -u kunjal-backend -f
```

**View Frontend Logs:**
```bash
# Docker
docker-compose logs -f frontend

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Deployment Issues

#### Issue: Container Won't Start

**Check:**
```bash
# View container logs
docker-compose logs backend

# Common causes:
# - Missing environment variables
# - Port already in use
# - Database not ready
```

**Solution:**
```bash
# Check ports
netstat -tuln | grep -E '(8000|5173|5432)'

# Restart with fresh volumes
docker-compose down -v
docker-compose up -d --build
```

#### Issue: CORS Errors in Browser

**Symptom:** Browser console shows CORS policy errors

**Solution:**
1. Update `CORS_ORIGINS` in `config.py`:
   ```python
   CORS_ORIGINS = ["https://your-actual-domain.com"]
   ```
2. Rebuild and redeploy backend

#### Issue: SSE Connection Drops

**Symptom:** Chat shows "Connecting" status forever

**Check:**
```bash
# Test SSE endpoint directly
curl -N http://your-domain.com/api/events?session_id=test
```

**Solution:**
1. Ensure reverse proxy disables buffering for SSE
2. Check `proxy_set_header Connection ''` in Nginx config
3. Verify timeout settings (SSE needs long connections)

#### Issue: Emails Not Sending

**Check:**
```bash
# Test email config in Python container
docker-compose exec backend python -c "
from database import send_verification_email
send_verification_email('ORD-001', '123456', 'test@test.com', 'Test')
"
```

**Solutions:**
1. Verify GMAIL_APP_PASSWORD (not regular password)
2. Check "Less secure apps" is enabled for Gmail
3. Check spam/junk folders
4. Verify SMTP port (587) not blocked

### Database Issues

#### Issue: "relation does not exist"

**Solution:**
```bash
# Access backend container
docker-compose exec backend bash

# Run seed script
python seed_db.py

# Or manually init
python -c "from database import init_db; init_db()"
```

#### Issue: Connection Refused

**Check:**
```bash
# Test PostgreSQL connection
docker-compose exec backend python -c "
from database import engine
print(engine.connect())
"
```

**Solution:**
1. Verify DATABASE_URL format
2. Check postgres container is running
3. Ensure depends_on in docker-compose.yml

---

## Quick Reference

### Essential Commands

| Task | Command |
|-------|---------|
| Start all services | `docker-compose up -d` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Rebuild backend | `docker-compose up -d --build backend` |
| Access backend shell | `docker-compose exec backend bash` |
| Access PostgreSQL | `docker-compose exec postgres psql -U kunjal_user -d kunjal_agents` |
| View environment | `docker-compose exec backend env` |

### Port Reference

| Service | Default Port | Production Port |
|---------|---------------|-----------------|
| Frontend | 5173 | 443 (HTTPS) |
| Backend API | 8000 | 443 (proxied) |
| PostgreSQL | 5432 | 5432 (internal) |
| SSE Events | 8000/api/events | 443/api/events |

### File Locations

| File | Purpose |
|-------|---------|
| `.env` | Environment variables |
| `docker-compose.yml` | Docker services definition |
| `Dockerfile` | Backend container definition |
| `Dockerfile.frontend` | Frontend container definition |
| `server/api.py` | Backend entry point |
| `frontend/vite.config.ts` | Frontend build config |

---

## Summary

This deployment guide covers:

✅ **Local Development** - Run on your machine
✅ **Docker Deployment** - Containerized setup
✅ **Cloud Deployment** - Render, Railway, VPS options
✅ **Production Checklist** - Security and performance
✅ **Monitoring** - Health checks, backups, logging
✅ **Troubleshooting** - Common issues and solutions

For additional help, see:
- `END_TO_END_DOCUMENTATION.md` - Complete system documentation
- `CLAUDE.md` - Developer guide for Claude Code

**Happy Deploying! 🚀**
