# AI Interview Agent - Vercel Deployment Configuration

## Required Setup

### 1. Vercel Environment Variables
Add these to your Vercel project settings:
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
- `DEBUG` - Set to `false` (optional, default: false)
- `LOG_LEVEL` - Set to `INFO` (optional, default: INFO)
- `PORT` - Set to `8000` (optional, will be auto-detected)

### 2. vercel.json Configuration
The `vercel.json` file configures:
- **buildCommand**: Installs Python dependencies
- **outputDirectory**: Points to backend directory
- **functions**: Configures Python runtime for main.py
- **environment variables**: Passes secrets and config
- **rewrites**: Routes API requests correctly

### 3. Dockerfile
For local Docker testing and alternative deployment methods.

## Troubleshooting 404 Errors

### Issue 1: Deployment Shows "Status: Failed"
**Solution:**
1. Go to Vercel Dashboard
2. Click "Deployments"
3. Click failed deployment
4. Check "Build Logs" for Python errors
5. Common errors:
   - `pip: command not found` → Python not installed
   - `ModuleNotFoundError` → Missing dependencies in requirements.txt
   - `ANTHROPIC_API_KEY not set` → Add to Vercel Environment Variables

### Issue 2: Getting 404 on Deployment URL
**Check these:**
1. **Vercel dashboard** - Is deployment status "Ready"?
2. **URL is correct** - https://interview-agent-opal.vercel.app
3. **Test API endpoint:**
   ```bash
   curl https://interview-agent-opal.vercel.app/api/health
   ```
4. **Check Runtime Logs** - Go to deployment → "Runtime Logs" tab

### Issue 3: "Cannot Find Module 'main'"
**Solution:**
- Check outputDirectory in vercel.json points to backend
- Verify main.py is in interview-agent/backend/
- Check PYTHONPATH is set correctly

### Issue 4: Static Files Not Found
**Solution:**
- Ensure frontend/index.html exists
- Check path in main.py line 138:
  ```python
  frontend_dir = Path(__file__).parent.parent / "frontend"
  ```

## Testing Endpoints

### Local Testing
```bash
cd interview-agent
export ANTHROPIC_API_KEY=sk-ant-your-key
python backend/main.py
```

Then test:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/candidates
curl http://localhost:8000/
```

### Vercel Testing
```bash
curl https://interview-agent-opal.vercel.app/api/health
curl https://interview-agent-opal.vercel.app/api/candidates
curl https://interview-agent-opal.vercel.app/
```

## Deployment Flow

1. **Push to GitHub** → `git push origin main`
2. **Vercel Auto-deploys** → Automatically triggers on push
3. **Build Phase** → Runs buildCommand
4. **Deploy Phase** → Sets up Python runtime
5. **Runtime** → Starts FastAPI application

## Important Notes

- ⚠️ Never commit `.env` files with real API keys
- ✅ Always use Vercel Environment Variables for secrets
- ✅ Ensure `requirements.txt` has all dependencies
- ✅ FastAPI needs to listen on `0.0.0.0:8000`
- ✅ Health check endpoint must exist at `/api/health`

## Vercel Links

- Dashboard: https://vercel.com/dashboard
- Project: https://vercel.com/Kamal811500/interview-agent-opal
- Deployments: https://vercel.com/Kamal811500/interview-agent-opal/deployments
- Settings: https://vercel.com/Kamal811500/interview-agent-opal/settings

## Support

If deployment still fails:
1. Check Vercel build logs
2. Check Vercel runtime logs
3. Test locally first with Docker
4. Verify all files are committed to GitHub
5. Check GitHub repo is public or Vercel has access
