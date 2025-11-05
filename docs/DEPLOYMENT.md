# 🚀 Deployment Guide - Rohimaya Audiobook Generator

## Overview

This guide covers deploying the Rohimaya Audiobook Generator to various platforms.

**Recommended for:**
- **Development:** Local machine
- **Demo/Beta:** Streamlit Cloud (FREE)
- **Production:** Cloudflare Workers + Pages

---

## 📋 Prerequisites

### Required
- Python 3.10 or higher
- Git installed
- GitHub account
- OpenAI API key (or Inworld API key)

### Optional
- ffmpeg (for audio processing)
- Docker (for containerized deployment)

---

## 🏠 Option 1: Local Development

### Step 1: Clone Repository
```bash
git clone https://github.com/rohimayaventures/rohimaya-audiobook-generator.git
cd rohimaya-audiobook-generator
```

### Step 2: Create Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install ffmpeg

**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### Step 5: Configure API Keys
```bash
# Copy template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit with your API keys
nano .streamlit/secrets.toml
```

Add your keys:
```toml
[openai]
api_key = "sk-proj-xxxxxxxxxxxxx"

[inworld]
api_key = "your_inworld_key_here"
```

### Step 6: Run Application
```bash
streamlit run streamlit_app.py
```

**Access at:** http://localhost:8501

---

## ☁️ Option 2: Streamlit Cloud (Recommended for Beta)

### Benefits
- ✅ FREE hosting
- ✅ Auto-deploy on git push
- ✅ Easy secrets management
- ✅ Perfect for demos

### Step 1: Prepare Repository

Ensure these files exist:
```
✅ streamlit_app.py
✅ requirements.txt
✅ .streamlit/secrets.toml.example
✅ README.md
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - **Repository:** rohimayaventures/rohimaya-audiobook-generator
   - **Branch:** main
   - **Main file:** streamlit_app.py
5. Click "Deploy!"

### Step 4: Add Secrets

1. In Streamlit Cloud dashboard, click your app
2. Go to "Settings" → "Secrets"
3. Add your secrets:
```toml
[openai]
api_key = "sk-proj-xxxxxxxxxxxxx"

[inworld]
api_key = "your_inworld_key_here"
```

4. Click "Save"

### Step 5: Access Your App

**URL:** https://rohimaya-audiobook-generator.streamlit.app

Share this URL with beta users!

---

## 🐳 Option 3: Docker Deployment

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run
```bash
# Build image
docker build -t rohimaya-audiobook .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY="sk-xxxxx" \
  rohimaya-audiobook
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  audiobook-generator:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - INWORLD_API_KEY=${INWORLD_API_KEY}
    volumes:
      - ./data:/app/data
```

Run with:
```bash
docker-compose up
```

---

## ⚡ Option 4: Cloudflare Pages + Workers (Production)

### Architecture
```
Cloudflare Pages (Frontend)
    ↓
Cloudflare Workers (API)
    ↓
R2 Storage (Audio files)
    ↓
D1 Database (User data)
```

### Setup Steps

#### 1. Install Wrangler
```bash
npm install -g wrangler
wrangler login
```

#### 2. Create Worker
```javascript
// worker.js
export default {
  async fetch(request, env) {
    // Handle audiobook generation
    // Call TTS APIs
    // Store in R2
  }
}
```

#### 3. Deploy Worker
```bash
wrangler deploy
```

#### 4. Create R2 Bucket
```bash
wrangler r2 bucket create audiobooks
```

#### 5. Deploy Pages
```bash
# Build static frontend
npm run build

# Deploy to Pages
wrangler pages deploy ./dist
```

**Cost:** ~$5/month for 1000 users

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-xxxxx` |
| `INWORLD_API_KEY` | Inworld TTS key | `inworld-xxxxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHUNK_SIZE` | Chunk size in chars | `1500` |
| `MAX_FILE_SIZE` | Max upload MB | `50` |
| `RATE_LIMIT` | Requests per min | `60` |

---

## 🧪 Testing Deployment

### Health Check

Create `test_deployment.py`:
```python
import requests
import sys

def test_deployment(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Deployment successful!")
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
    test_deployment(url)
```

Run:
```bash
python test_deployment.py https://your-app.streamlit.app
```

---

## 📊 Monitoring

### Streamlit Cloud Metrics

Access at: https://share.streamlit.io → Your App → Metrics

**Available:**
- Active users
- Total views
- Error logs
- Resource usage

### Custom Logging

Add to `streamlit_app.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use throughout app
logger.info("User generated audiobook")
logger.error("TTS provider failed")
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/
      
      - name: Deploy
        run: echo "Streamlit Cloud auto-deploys on push"
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

#### Issue: "ffmpeg not found"
**Solution:**
- Mac: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download and add to PATH

#### Issue: "API key invalid"
**Solution:**
1. Check `.streamlit/secrets.toml`
2. Verify key format (starts with `sk-` for OpenAI)
3. Ensure no extra spaces

#### Issue: "Out of memory"
**Solution:**
- Reduce chunk_size in config
- Process smaller files
- Upgrade Streamlit Cloud plan

#### Issue: "Rate limit exceeded"
**Solution:**
- Reduce rate_limit in config
- Wait before retrying
- Consider upgrading API plan

---

## 📈 Scaling Considerations

### Current Limits (Streamlit Cloud Free)
- 1GB RAM
- 1 CPU core
- ~100 concurrent users

### Upgrade Path

| Users | Platform | Cost/Month |
|-------|----------|------------|
| 1-100 | Streamlit Free | $0 |
| 100-1000 | Streamlit Teams | $250 |
| 1000+ | Cloudflare Workers | $5-50 |

---

## 🔒 Security Checklist

### Pre-Deployment
- [ ] API keys in secrets (not code)
- [ ] .gitignore includes secrets.toml
- [ ] Rate limiting enabled
- [ ] File size limits set
- [ ] Input validation on uploads

### Post-Deployment
- [ ] HTTPS enabled
- [ ] Monitor error logs
- [ ] Set up usage alerts
- [ ] Regular dependency updates
- [ ] Backup important data

---

## 📞 Support

### Deployment Issues
- Check logs in Streamlit Cloud dashboard
- Review GitHub Actions runs
- Test locally first

### Contact
- Email: rohimayapublishing@gmail.com
- GitHub Issues: Create an issue on repo

---

## 🎉 Success Checklist

After deployment, verify:
- [ ] App loads without errors
- [ ] File upload works
- [ ] Voice selection displays
- [ ] Audio generation completes
- [ ] Download works
- [ ] Cost tracking updates
- [ ] History saves
- [ ] Mobile responsive

---

**Deployment Guide Version:** 1.0  
**Last Updated:** November 2025  
**Platform:** Streamlit Cloud (primary)
