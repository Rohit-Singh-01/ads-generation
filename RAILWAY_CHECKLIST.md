# ✅ Railway Deployment Checklist

## Pre-Deployment (Already Done ✅)

- [x] railway.json configured
- [x] runtime.txt (Python 3.11.7)
- [x] requirements.txt updated
- [x] setup.sh for Playwright
- [x] packages.txt for system deps
- [x] Procfile for process management
- [x] All code pushed to GitHub

## Deployment Steps

### 1. Sign Up for Railway
- [ ] Go to https://railway.app
- [ ] Click "Start a New Project"
- [ ] Sign in with GitHub
- [ ] Add credit card (free tier verification)

### 2. Create Project
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose: `Rohit-Singh-01/ads-generation`
- [ ] Branch: `main`
- [ ] Click "Deploy Now"

### 3. Wait for Build (5-10 min)
- [ ] Watch deployment logs
- [ ] Look for: "Installing Playwright browsers..."
- [ ] Look for: "Playwright setup complete!"
- [ ] Look for: "App is ready"

### 4. Get Your URL
- [ ] Settings → Domains
- [ ] Click "Generate Domain"
- [ ] Copy URL: `https://[your-app].railway.app`

### 5. Test Your App
- [ ] Open Railway URL
- [ ] Test "Extract Brand" tab
- [ ] Enter: `Test Brand`
- [ ] URL: `https://www.nike.com/w/mens-shoes-nik1zy7ok`
- [ ] Click "Extract"
- [ ] Should see: "✅ Playwright crawl successful"

## Verification Checklist

### App Functionality
- [ ] App loads without errors
- [ ] Navigation works (tabs switch)
- [ ] Brand extraction works
- [ ] Playwright is active (no fallback warning)
- [ ] Products are extracted
- [ ] Colors are detected
- [ ] Logos are found
- [ ] Social links extracted

### AI Generation
- [ ] AI Model dropdown shows all models:
  - [ ] Google Imagen 4
  - [ ] Seedream 4
  - [ ] Nano Banana Pro
  - [ ] Nano Banana
  - [ ] FLUX models
- [ ] Can enter Replicate API key
- [ ] Can generate ads
- [ ] Images download correctly
- [ ] Can save generated ads

### Performance
- [ ] App loads in < 5 seconds
- [ ] Brand extraction in < 30 seconds
- [ ] Image generation works
- [ ] No memory errors
- [ ] No timeout errors

## Post-Deployment

### Security
- [ ] Add Replicate API key to Railway Variables (not hardcoded)
- [ ] Set environment variables in Railway dashboard
- [ ] Review deployment logs (no sensitive data exposed)

### Monitoring
- [ ] Set up deployment notifications
- [ ] Check resource usage (CPU/RAM)
- [ ] Set spending limit ($10/month recommended)
- [ ] Monitor error rate

### Optional
- [ ] Add custom domain
- [ ] Set up SSL certificate (automatic with Railway)
- [ ] Configure CDN (if needed)
- [ ] Set up backups

## Common Issues

### ❌ "Module not found"
- Check requirements.txt includes all packages
- Redeploy from Railway dashboard

### ❌ "Playwright not installed"
- Verify setup.sh ran in logs
- Check railway.json startCommand
- Redeploy

### ❌ "Port 8080 already in use"
- Railway auto-assigns $PORT
- Verify app uses $PORT variable
- Check railway.json config

### ❌ "Out of memory"
- Railway free tier = 8GB RAM
- If exceeded, upgrade to Pro ($5/month)

### ❌ "App won't start"
- Check deployment logs for errors
- Verify app_modular.py is in root
- Check Python version matches runtime.txt

## Support

If you encounter issues:

1. **Check Railway Logs**
   - Dashboard → Your Service → View Logs
   - Look for red error messages

2. **Railway Discord**
   - https://discord.gg/railway
   - Very responsive community

3. **Railway Docs**
   - https://docs.railway.app
   - Comprehensive guides

4. **Status Page**
   - https://status.railway.app
   - Check for outages

## Cost Estimate

### Free Tier (500 hours/month):
- **Monthly Cost:** $0
- **Usage:** ~16 hours/day
- **Perfect for:** Testing, demos, side projects

### After Free Tier:
- **Cost:** $0.02/hour
- **Typical Usage:** 200 hours/month = $4/month
- **Heavy Usage:** 500 hours/month = $10/month

**Much cheaper than managing your own server!**

## Success Criteria

Your deployment is successful when:

1. ✅ App loads at Railway URL
2. ✅ Playwright extracts brand data
3. ✅ All AI models appear in dropdown
4. ✅ Can generate ads
5. ✅ No console errors
6. ✅ Performance is good (< 30s extraction)

## Next Steps After Success

1. Share your Railway URL with users
2. Monitor usage and costs
3. Set up custom domain (optional)
4. Configure alerts
5. Plan for scaling if needed

---

# 🎉 Ready to Deploy!

All files are ready. Just:

1. Go to https://railway.app
2. Deploy from GitHub
3. Wait 10 minutes
4. Test your app
5. **It will work!** 🚀

Railway handles everything automatically!
