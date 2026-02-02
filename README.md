# 🎯 ULTRA Brand Extractor + AI Ad Generator

A powerful Streamlit application that extracts brand intelligence from websites and generates AI-powered advertisements with Google Drive & Sheets integration.

## ✨ Features

### Brand Intelligence Extraction
- **Automated Web Crawling**: Production-grade async crawler with comprehensive brand signal extraction
- **Deep Brand Analysis**: Automatically detects category, market position, voice & tone
- **Comprehensive Data**: Hero sections, FAQs, product bullets, pricing, reviews, team info, press mentions, and more
- **Visual Asset Extraction**: Logos, colors, images, and video embeds
- **Structured Data**: JSON-LD, Open Graph, Schema.org extraction
- **Anti-Bot Detection**: Retry logic, exponential backoff, CAPTCHA detection
- **Performance Optimizations**: Request interception, connection pooling, intelligent crawl budget

### AI Ad Generation
- **Multiple AI Models**: Support for FLUX 1.1 Pro, FLUX Pro, FLUX Dev, and Schnell
- **12+ Style Presets**: Professional ad styles (Lifestyle, Aesthetic, Product, Emotion)
- **Product Integration**: Upload product images or fetch from e-commerce URLs
- **Custom Prompts**: Full control over generation prompts with brand intelligence integration
- **Batch Generation**: Generate multiple ad sizes simultaneously

### E-commerce Integration
- **Universal URL Fetcher**: Scrapes products from ANY e-commerce site
- **Platform Support**: Shopify, WooCommerce, Magento, and generic sites
- **Auto-Detection**: Automatically detects platform and uses optimal scraping method
- **Product Data**: Extracts name, price, image URL, and product handle

### Google Drive & Sheets Integration
- **Auto-Upload to Drive**: Upload generated ads to Google Drive folders
- **Sheet Logging**: Automatically logs all generated ads with timestamps and links
- **Custom Column Mapping**: Map data fields to your preferred sheet column names
- **Worksheet Selection**: Choose specific worksheet tabs to update
- **Batch Operations**: Upload multiple ads at once with progress tracking
- **OAuth 2.0 Authentication**: Secure, one-time authentication with automatic token refresh

### Smart Features
- **Caching System**: Save and reload brand profiles instantly
- **Optimized Performance**: Fast async operations and efficient data processing
- **Clean Architecture**: Modular, maintainable code structure
- **Production-Grade Logging**: Comprehensive metrics and error tracking

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the Application

```bash
streamlit run app_modular.py
```

### 3. Get API Keys

**Replicate API Key** (for AI ad generation):
- Get your key from: https://replicate.com/account/api-tokens

**Google Cloud Credentials** (optional, for Drive & Sheets):
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable Google Drive API and Google Sheets API
- Create OAuth 2.0 credentials (Desktop app)
- Download credentials.json

## 📖 Usage

### Extract Brand Intelligence

1. Navigate to the "🔍 Extract Brand" tab
2. Enter the brand name and website URL
3. Adjust crawler settings:
   - Max pages: 5-50 (more pages = deeper analysis)
   - Max depth: 1-4 (crawl depth level)
4. Click "🚀 Extract Brand Intelligence"
5. Wait for the crawler to analyze the website (shows real-time progress)
6. View comprehensive brand data and export as JSON

### Fetch Products from E-commerce URLs

1. Navigate to the "🎨 Generate Ads" tab
2. Expand "📦 Fetch Products from URL" section
3. Enter any e-commerce collection/category URL:
   - Shopify: `https://store.com/collections/all`
   - WooCommerce: `https://store.com/shop/`
   - Any other e-commerce site
4. Click "🔗 Fetch Products"
5. Products are loaded automatically for ad generation

### Generate AI Ads

1. Navigate to the "🎨 Generate Ads" tab
2. Enter your Replicate API key
3. Select products to generate ads for:
   - Upload product images manually, OR
   - Fetch products from URL, OR
   - Upload CSV file with product data
4. Configure ad settings:
   - Select ad style preset
   - Choose aspect ratios (can select multiple)
   - Select AI model
   - Customize prompt (optional)
5. Click "🎨 Generate Ads"
6. Download individual ads or all at once

### Upload Ads to Google Drive & Sheets

1. Navigate to the "☁️ Auto-Sync" tab
2. Upload your `credentials.json` file
3. Enter Google Drive Folder ID (from Drive URL)
4. Enter Google Sheet URL
5. Select worksheet tab to update
6. Map columns to your sheet headers (optional)
7. Generate ads normally
8. Click "📤 Upload to Drive"
9. Ads are uploaded to Drive AND logged to Sheet automatically

**First-time authentication:**
- Browser will open for Google sign-in
- Grant permissions for Drive and Sheets
- Token is saved automatically for future use

### View Brand Profile

1. Navigate to the "📊 Brand Profile" tab
2. View extracted brand intelligence:
   - Identity (category, market position, region)
   - Voice & Tone (formality, energy, POV)
   - Brand Colors
   - Logos
   - Key Messages
   - Hero Sections
   - FAQs
   - Product Bullets
   - Pricing Data
   - Team Members
   - Press & Awards
   - Contact Information
3. Export brand profile as JSON

## 🏗️ Architecture

### Core Components

- **ComprehensiveWebCrawler**: Production-grade async crawler with 20+ extraction signals
- **BrandExtractor**: Main extraction engine with advanced NLP analysis
- **TextAnalyzer**: Brand voice, tone, and messaging analysis
- **ImageProcessor**: Image manipulation and enhancement
- **AIGenerator**: Replicate API integration with multi-model support
- **URLFetcher**: Universal e-commerce product scraper
- **GoogleSync**: Google Drive & Sheets integration module
- **CacheManager**: Efficient brand data caching

### Key Improvements

✅ **Production Crawler**: Retry logic, anti-bot detection, error handling
✅ **Comprehensive Extraction**: 20+ brand intelligence signals
✅ **E-commerce Support**: Universal product scraping from any site
✅ **Cloud Integration**: Google Drive & Sheets auto-sync
✅ **Better Architecture**: Dataclasses, single responsibility principle
✅ **Async Performance**: Properly structured async operations
✅ **Memory Efficient**: Text size limits, smart deduplication
✅ **Type Safety**: Type hints throughout
✅ **Clean Code**: Modular design, no duplicates

## 🎨 Available Ad Styles

### Lifestyle
- Modern Minimalist
- Luxury Premium
- Urban Contemporary

### Aesthetic
- Vintage Retro
- Futuristic
- Dark Moody
- Bright Airy

### Product
- Hero Studio
- Lifestyle Action
- Clean White
- Natural Light

### Emotion
- Joy
- Confidence

## 🔧 Configuration

### Web Crawler Settings
- **max_pages**: Maximum pages to crawl (5-50, default: 30)
- **max_depth**: Crawl depth level (1-4, default: 3)
- **concurrency**: Parallel workers (default: 5)
- Priority keywords for intelligent crawling
- Anti-bot detection and retry logic

### AI Generation Settings
- **Models**: FLUX 1.1 Pro, FLUX Pro, FLUX Dev, FLUX Schnell
- **Aspect Ratios**: 1:1, 16:9, 9:16, 4:5, 3:2
- **Styles**: 12+ professional presets
- **Output Format**: PNG

### Google Integration Settings
- **Drive Folder ID**: From Drive URL (extract after `/folders/`)
- **Sheet URL**: Full Google Sheets URL
- **Worksheet**: Select specific tab/sheet
- **Column Mapping**: Custom field-to-column mapping
- **Auto-Sync**: Upload ads on generation (optional)

## 📁 Project Structure

```
UAT/
├── app_modular.py              # Main Streamlit application
├── web_crawler_comprehensive.py # Production-grade web crawler
├── brand_extractor.py          # Brand intelligence extraction
├── url_fetcher.py              # E-commerce product scraper
├── google_sync.py              # Google Drive & Sheets integration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore file
├── credentials.json            # Google API credentials (not in git)
├── token.json                  # Auto-generated auth token (not in git)
└── brand_cache/                # Cached brand profiles (auto-created)
```

## 🔐 Security & Credentials

### Important Files (DO NOT COMMIT)
- **credentials.json**: Google OAuth 2.0 client credentials (keep secret)
- **token.json**: Auto-generated authentication token (auto-refreshed)
- Both files are already in .gitignore

### Google API Setup
1. Only `credentials.json` is required from user
2. `token.json` is created automatically on first authentication
3. Token auto-refreshes when expired
4. One credentials file works for BOTH Drive and Sheets

## 🐛 Troubleshooting

### Playwright Issues
```bash
playwright install chromium
```

### Google Authentication Issues
- Delete `token.json` and re-authenticate
- Check credentials.json is valid OAuth 2.0 Desktop app credentials
- Ensure both Drive and Sheets APIs are enabled in Google Cloud Console

### Cache Directory
The app automatically creates a `brand_cache/` directory for storing brand profiles.

### API Limits
- Replicate API has rate limits. Generate ads in batches for best results.
- Google Drive/Sheets have rate limits. Large batch uploads may be throttled.

### E-commerce Scraping
- Some sites may block automated scraping
- Try different URLs if one doesn't work
- For Shopify, use `/collections/all` or specific collection URLs

## 📊 Crawl Metrics

The production crawler tracks:
- Pages crawled vs failed
- Total text extracted
- Retry attempts
- CAPTCHA encounters
- Blocked requests
- Crawl duration
- Average page load time

## 🆕 Recent Updates

- ✅ Removed "Import from Sheet" feature (simplified workflow)
- ✅ Production-grade web crawler with comprehensive brand signals
- ✅ Universal e-commerce product scraper
- ✅ Google Drive & Sheets integration
- ✅ Custom column mapping for sheets
- ✅ Batch ad generation and upload
- ✅ Enhanced error handling and logging
- ✅ Performance optimizations

## 📝 License

MIT License - Feel free to use and modify as needed.

## 🤝 Contributing

Contributions welcome! Please feel free to submit pull requests.

---

Built with ❤️ using Streamlit, Playwright, Replicate AI, and Google APIs
