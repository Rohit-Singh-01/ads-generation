# Production Deployment Guide

## 🎯 Goal: Full Playwright with Maximum Accuracy

For production, you need **100% reliable Playwright** extraction. Here are your options, ranked by reliability:

---

## Option 1: Streamlit Community Cloud (Current - Medium Reliability)

### Pros:
- ✅ Free hosting
- ✅ Easy deployment
- ✅ Auto-deploys from GitHub

### Cons:
- ⚠️ Limited resources (1GB RAM)
- ⚠️ Playwright can be unstable
- ⚠️ Cold starts may timeout
- ⚠️ Browser automation may fail

### Setup Steps:

1. **Push all files to GitHub**:
   ```bash
   git add .
   git commit -m "Add Playwright production setup"
   git push
   ```

2. **Configure Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Select your app → Settings (⚙️)
   - **Advanced Settings** → **Pre-install script**: `bash setup.sh`
   - **Python version**: 3.11 (recommended)
   - **Save** and redeploy

3. **Verify Installation**:
   - Watch deployment logs
   - Look for "✅ Playwright installed successfully"
   - Test with a sample URL

### Test Locally First:
```bash
# Verify Playwright works
python verify_playwright.py

# If it passes, push to Streamlit
git push
```

### Success Rate: ~60-70%
(Depends on Streamlit Cloud resources)

---

## Option 2: Heroku (High Reliability) ⭐ RECOMMENDED

### Pros:
- ✅ More resources (512MB+ RAM)
- ✅ Better Playwright support
- ✅ Stable browser automation
- ✅ Custom buildpacks

### Cons:
- 💰 Not free ($5-7/month for Hobby tier)
- 📝 More setup required

### Setup Steps:

1. **Create `Procfile`**:
   ```bash
   web: streamlit run app_modular.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Create `runtime.txt`**:
   ```
   python-3.11.7
   ```

3. **Create `Aptfile`** (system dependencies):
   ```
   libglib2.0-0
   libnss3
   libnspr4
   libatk1.0-0
   libatk-bridge2.0-0
   libcups2
   libdrm2
   libdbus-1-3
   libxcb1
   libxkbcommon0
   libx11-6
   libxcomposite1
   libxdamage1
   libxext6
   libxfixes3
   libxrandr2
   libgbm1
   libpango-1.0-0
   libcairo2
   libasound2
   libatspi2.0-0
   ```

4. **Deploy**:
   ```bash
   heroku create your-app-name
   heroku buildpacks:add --index 1 heroku-community/apt
   heroku buildpacks:add --index 2 heroku/python
   git push heroku main
   ```

5. **Post-deploy setup** (run once):
   ```bash
   heroku run python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()"
   ```

### Success Rate: ~95%

---

## Option 3: Railway.app (High Reliability) ⭐ RECOMMENDED

### Pros:
- ✅ Excellent Playwright support
- ✅ More resources (8GB RAM free tier)
- ✅ Simple deployment
- ✅ Free tier available

### Cons:
- 💳 Requires credit card for free tier
- ⏰ 500 hours/month free (then $0.02/hour)

### Setup Steps:

1. **Create `railway.json`**:
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "bash setup.sh && streamlit run app_modular.py --server.port=$PORT --server.address=0.0.0.0",
       "healthcheckPath": "/_stcore/health"
     }
   }
   ```

2. **Deploy**:
   - Go to https://railway.app
   - Connect GitHub repo
   - Deploy automatically
   - Set environment variables if needed

### Success Rate: ~95%

---

## Option 4: Google Cloud Run (Highest Reliability) 💎

### Pros:
- ✅ Production-grade
- ✅ Auto-scaling
- ✅ Full Playwright support
- ✅ Pay only for usage

### Cons:
- 💰 Costs $5-20/month (depending on traffic)
- 🔧 More complex setup

### Setup Steps:

1. **Create `Dockerfile`**:
   ```dockerfile
   FROM python:3.11-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \\
       wget gnupg ca-certificates \\
       libglib2.0-0 libnss3 libnspr4 libatk1.0-0 \\
       libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 \\
       libxcb1 libxkbcommon0 libx11-6 libxcomposite1 \\
       libxdamage1 libxext6 libxfixes3 libxrandr2 \\
       libgbm1 libpango-1.0-0 libcairo2 libasound2 \\
       libatspi2.0-0 && \\
       rm -rf /var/lib/apt/lists/*

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   RUN playwright install chromium
   RUN playwright install-deps chromium

   COPY . .

   EXPOSE 8080
   CMD streamlit run app_modular.py --server.port=8080 --server.address=0.0.0.0
   ```

2. **Deploy**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/ads-generator
   gcloud run deploy ads-generator --image gcr.io/PROJECT_ID/ads-generator --platform managed --region us-central1 --allow-unauthenticated
   ```

### Success Rate: ~99%

---

## Option 5: DigitalOcean App Platform (High Reliability)

### Pros:
- ✅ Simple deployment
- ✅ Good Playwright support
- ✅ Fixed pricing

### Cons:
- 💰 $5/month minimum
- 📝 Manual setup needed

### Setup: Similar to Heroku

### Success Rate: ~90%

---

## 🎯 My Recommendation

### For Immediate Production:
**Railway.app** - Best balance of:
- ✅ Easy setup (like Streamlit)
- ✅ High reliability (95%+)
- ✅ Good free tier
- ✅ Full Playwright support

### For Serious/Scale Production:
**Google Cloud Run** - If you need:
- ✅ 99%+ uptime
- ✅ Auto-scaling
- ✅ Enterprise-grade

### For Testing/MVP:
**Streamlit Cloud** - Good for:
- ✅ Quick prototypes
- ✅ Demo apps
- ⚠️ But use enhanced fallback as backup

---

## 📊 Cost Comparison

| Platform | Free Tier | Paid (Production) | Reliability |
|----------|-----------|-------------------|-------------|
| Streamlit Cloud | ✅ Unlimited | Free only | 60-70% |
| Railway.app | 500hrs/month | $10-20/month | 95% |
| Heroku | ❌ None | $7/month | 95% |
| Google Cloud Run | $0 up to limits | $10-30/month | 99% |
| DigitalOcean | ❌ None | $5/month | 90% |

---

## 🚀 Action Plan

### Week 1: Try Streamlit Cloud
1. Deploy with `setup.sh` pre-install script
2. Monitor success rate over 1 week
3. Keep enhanced fallback as backup

### Week 2: If Success Rate < 80%
**Migrate to Railway.app**:
1. Takes ~30 minutes to setup
2. Near 100% reliability
3. Still affordable

### Long-term: Scale to Cloud Run
When you have paying customers, migrate to Google Cloud Run for production-grade reliability.

---

## 🔍 Testing Checklist

Before going production, verify:

- [ ] Run `python verify_playwright.py` - passes locally
- [ ] Deploy to platform
- [ ] Test 10 different e-commerce URLs
- [ ] Check extraction accuracy (colors, logos, products)
- [ ] Monitor error rates over 1 week
- [ ] Load test (10+ concurrent users)

---

## Need Help?

1. **Test locally first**: `python verify_playwright.py`
2. **Check deployment logs**: Look for Playwright errors
3. **Try different platform**: If one fails, try Railway.app

Would you like me to help set up any of these platforms?
