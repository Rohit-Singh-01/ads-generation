# Streamlit Cloud Setup Guide

## The Problem
Playwright requires browser binaries that aren't available by default on Streamlit Cloud, causing the error:
```
playwright._impl._errors.Error: This app has encountered an error.
```

## ✅ Solution Implemented

Your app now uses an **intelligent fallback strategy**:

1. **First**: Tries the full Playwright-based crawler (for JavaScript-heavy sites)
2. **Fallback**: Automatically switches to the lightweight HTTP scraper if Playwright fails

This means:
- ✅ Works immediately on Streamlit Cloud (no browser needed)
- ✅ Still supports complex sites when Playwright is available
- ✅ No manual intervention required

## Files Added/Modified

### 1. `packages.txt` (NEW)
System dependencies needed for Playwright (if available):
- Browser rendering libraries
- Audio/video codecs
- Accessibility libraries

### 2. `crawler_fallback.py` (NEW)
Intelligent wrapper that:
- Tries Playwright first
- Falls back to simple HTTP scraper
- Returns data in consistent format

### 3. `app_modular.py` (MODIFIED)
Changed:
```python
# Before:
from web_crawler_comprehensive import run_comprehensive_crawl

# After:
from crawler_fallback import run_crawl_with_fallback
```

### 4. `.streamlit/config.toml` (NEW)
Streamlit configuration for Cloud deployment

### 5. `setup.sh` (NEW - OPTIONAL)
Script to install Playwright browsers (for full functionality)

## Deployment Options

### Option A: Quick Deploy (Recommended)
Just push the changes. The app will:
- Use the lightweight scraper automatically
- Work for most e-commerce sites (Shopify, WooCommerce, etc.)
- No additional setup needed

### Option B: Full Playwright Support
To enable full browser automation on Streamlit Cloud:

1. In Streamlit Cloud dashboard, go to your app settings
2. Navigate to "Advanced Settings"
3. Under "Pre-install script", add:
   ```bash
   bash setup.sh
   ```
4. Redeploy the app

**Note**: This requires more resources and may increase deployment time.

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium

# Run the app
streamlit run app_modular.py
```

## Supported Platforms

The fallback scraper ([url_fetcher.py](url_fetcher.py)) supports:
- ✅ Shopify stores
- ✅ WooCommerce sites
- ✅ Magento stores
- ✅ Generic e-commerce sites

For JavaScript-heavy sites that require browser rendering, you'll need Option B (full Playwright).

## Troubleshooting

### App still fails on Streamlit Cloud
1. Check Streamlit Cloud logs for specific errors
2. Verify `packages.txt` is in the root directory
3. Ensure `requirements.txt` includes all dependencies

### Products not being extracted
1. Try a different product page URL (collection/category page works best)
2. Check if the site blocks scraping (some sites require browser automation)
3. For sites that block scrapers, enable full Playwright support (Option B)

### Need more help?
Check the logs in Streamlit Cloud:
- Click "Manage app" (bottom right)
- View full error logs
- Look for specific scraping errors
