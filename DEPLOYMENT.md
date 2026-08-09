# Deployment Guide

Complete guide for deploying the AI Interview Agent to Vercel and managing deployment issues.

## 📋 Pre-Deployment Checklist

### 1. Local Testing
- [ ] Clone repository
- [ ] Create `.env` file with `ANTHROPIC_API_KEY`
- [ ] Install dependencies: `pip install -r interview-agent/backend/requirements.txt`
- [ ] Run locally: `python interview-agent/backend/main.py`
- [ ] Test endpoints via http://localhost:8000
- [ ] Run tests: `pytest interview-agent/backend/tests/ -v`

### 2. Repository Setup
- [ ] Push all code to GitHub (main branch)
- [ ] Ensure `.env` file is in `.gitignore` (never commit secrets)
- [ ] Verify `.gitignore` exists and is correct
- [ ] Check `Dockerfile` and `docker-compose.yml` are committed

### 3. Vercel Setup
- [ ] Login to https://vercel.com
- [ ] Connect GitHub account (or create Vercel account)
- [ ] Import project `Kamal811500/ai-agent-`
- [ ] Select `main` branch
- [ ] Set project name: `interview-agent-opal`

## 🔑 Environment Variables

In Vercel Dashboard → Settings → Environment Variables, add:

```
ANTHROPIC_API_KEY = sk-ant-your-actual-key-here
DEBUG = false
LOG_LEVEL = INFO
PORT = 8000
LLM_FAST_MODEL = claude-3-5-haiku-20241022
LLM_SMART_MODEL = claude-3-5-sonnet-20241022
```

⚠️ **Important**: Never commit your actual API key. Only set it in Vercel's Environment Variables panel.

## 🚀 Deployment URL Verification

### Check Deployment Status

1. **Vercel Dashboard**
   - Go to https://vercel.com/dashboard
   - Select project `interview-agent-opal`
   - Check "Deployments" tab
   - Latest deployment should show status: **Ready** ✅

2. **Check URL**
   - Default: `https://interview-agent-opal.vercel.app`
   - Ensure URL has no typos
   - Try accessing it in browser

### Verify Deployment Exists

```bash
# Test if deployment is live
curl https://interview-agent-opal.vercel.app/api/health

# Expected response:
# {"status": "ok"}
```

If you get a 404 or connection error → deployment doesn't exist or failed

## 🐛 Troubleshooting Deployment Issues

### Issue 1: Deployment Shows "Failed"

**Check Vercel Logs:**
1. Dashboard → Deployments → Click failed deployment
2. Click "Runtime Logs" tab
3. Look for error messages

**Common Error Patterns:**

| Error | Solution |
|-------|----------|
| `Python 3.11 not found` | Update `Dockerfile` to `python:3.12-slim` |
| `requirements.txt not found` | Path should be `interview-agent/backend/requirements.txt` |
| `ModuleNotFoundError: anthropic` | Install deps: `pip install -r requirements.txt` |
| `ANTHROPIC_API_KEY not set` | Add to Vercel Environment Variables |
| `No module named 'main'` | Check `PYTHONPATH` in Dockerfile |

### Issue 2: URL Returns 404 or Connection Error

**Diagnosis:**
```bash
# Test if domain resolves
ping interview-agent-opal.vercel.app

# Check HTTP status
curl -I https://interview-agent-opal.vercel.app

# If you get 404 → deployment failed or doesn't exist
```

**Solution:**
1. Verify deployment status in Vercel dashboard
2. Check build logs for errors
3. Try redeploying: Click "Redeploy" button in Vercel dashboard
4. Ensure `vercel.json` configuration is correct (if using custom config)

### Issue 3: API Endpoints Return 500 Errors

**Check Runtime Logs:**
1. Dashboard → Deployments → Click deployment → "Runtime Logs"
2. Look for backend errors

**Common Issues:**

- **Missing Environment Variable:**
  ```
  Error: ANTHROPIC_API_KEY not found
  ```
  → Add to Vercel Environment Variables

- **Data Files Not Found:**
  ```
  Error: FileNotFoundError: [Errno 2] No such file or directory: 'data/candidates.json'
  ```
  → Ensure data files are committed to repo

- **LLM Connection Failed:**
  ```
  Error: Invalid API key provided
  ```
  → Verify `ANTHROPIC_API_KEY` is correct in Vercel

### Issue 4: Frontend Not Loading

**Symptom:** Browser shows blank page or 404 at root `/`

**Check:**
1. Verify `frontend/index.html` exists in repo
2. Check file path in `backend/main.py`:
   ```python
   frontend_dir = Path(__file__).parent.parent / "frontend"
   ```

3. Ensure directory structure matches:
   ```
   interview-agent/
   ├── backend/
   │   └── main.py
   ├── frontend/
   │   └── index.html
   ```

**Solution:** 
- If missing, create proper directory structure
- Recommit to GitHub
- Redeploy in Vercel

### Issue 5: Deployment Takes Too Long / Times Out

**Symptoms:** Build step hangs for >15 minutes

**Causes & Solutions:**
- Dependencies taking time to install
  → Pre-build Docker image locally and test
- Large files being uploaded
  → Check `.gitignore`, remove unnecessary files

**Solution:**
1. Redeploy (sometimes helps)
2. If persists, contact Vercel support

## ✅ Post-Deployment Verification

After deployment, run these checks:

### 1. Basic Health Check
```bash
curl https://interview-agent-opal.vercel.app/api/health
# Response: {"status": "ok"}
```

### 2. List Candidates
```bash
curl https://interview-agent-opal.vercel.app/api/candidates
# Response: [{"id": "...", "name": "...", ...}]
```

### 3. Check Frontend
```bash
# Visit in browser
https://interview-agent-opal.vercel.app
# Should load UI
```

### 4. Start Interview (Full Test)
```bash
curl -X POST https://interview-agent-opal.vercel.app/api/interviews \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": "candidate-1"}'
# Response: {"interview_id": "...", "status": "WAITING_FOR_ANSWER", ...}
```

## 📱 Vercel Dashboard Links

- **Dashboard:** https://vercel.com/dashboard
- **Project Settings:** https://vercel.com/Kamal811500/interview-agent-opal/settings
- **Deployments:** https://vercel.com/Kamal811500/interview-agent-opal/deployments
- **GitHub Integration:** https://vercel.com/integrations/github

## 🔄 Redeploying Changes

After pushing code to `main` branch:

**Automatic:** Vercel automatically redeploys on push to main

**Manual Redeploy:**
1. Vercel Dashboard → Deployments
2. Click "Redeploy" on latest deployment
3. Or delete previous deployment and push again

## 🆘 Emergency Troubleshooting

If deployment still fails after above steps:

1. **Clone and test locally:**
   ```bash
   git clone https://github.com/Kamal811500/ai-agent-.git
   cd interview-agent
   cp backend/.env.example backend/.env
   # Edit .env with your API key
   python -m pytest backend/tests/test_health.py -v
   ```

2. **Check Vercel build output:**
   - Download build logs from Vercel dashboard
   - Share error details with support

3. **Rebuild Docker image:**
   ```bash
   docker build -t interview-agent:latest interview-agent/
   docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... interview-agent
   ```

4. **Contact Support:**
   - Vercel Support: https://vercel.com/support
   - GitHub Issues: https://github.com/Kamal811500/ai-agent-/issues

## 📊 Monitoring

**Monitor deployment health:**

- Visit: https://vercel.com/Kamal811500/interview-agent-opal
- Check "Analytics" tab for:
  - Response times
  - Error rates
  - Traffic patterns

**Set up alerts (Vercel Pro):**
- Deployment failures
- Performance regressions
- High error rates

---

**Last Updated:** 2026-08-09  
**Deployment URL:** https://interview-agent-opal.vercel.app
