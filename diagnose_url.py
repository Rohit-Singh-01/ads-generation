"""
URL Scraping Diagnostic Tool
Helps identify why a URL might fail to scrape
"""

import requests
from bs4 import BeautifulSoup
import sys

def diagnose_url(url):
    print(f"\n{'='*70}")
    print(f"🔍 DIAGNOSING URL: {url}")
    print(f"{'='*70}\n")

    # 1. Check URL accessibility
    print("1️⃣  Checking URL accessibility...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ✅ Content Length: {len(response.content):,} bytes")

        if response.status_code != 200:
            print(f"   ⚠️  Non-200 status code might indicate issues")
            return

    except Exception as e:
        print(f"   ❌ Failed to access URL: {str(e)}")
        return

    # 2. Detect platform
    print("\n2️⃣  Detecting platform...")
    content = response.text.lower()

    platforms = {
        'Shopify': ['shopify', 'myshopify.com', '/collections/'],
        'WooCommerce': ['woocommerce', 'wp-content', 'product-category'],
        'Magento': ['magento', 'mage/cookies'],
        'BigCommerce': ['bigcommerce'],
    }

    detected = []
    for platform, indicators in platforms.items():
        if any(ind in content or ind in url for ind in indicators):
            detected.append(platform)

    if detected:
        print(f"   ✅ Detected platform(s): {', '.join(detected)}")
    else:
        print(f"   ℹ️  Platform: Generic/Unknown")

    # 3. Check for product elements
    print("\n3️⃣  Searching for product elements...")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Common product indicators
    product_selectors = [
        ('Product divs', 'div[class*="product"]'),
        ('Product items', '[class*="product-item"]'),
        ('Product cards', '[class*="product-card"]'),
        ('Grid products', '[class*="grid-product"]'),
        ('WooCommerce products', '.woocommerce-loop-product'),
        ('Schema.org products', '[itemtype*="Product"]'),
    ]

    found_any = False
    for name, selector in product_selectors:
        try:
            elements = soup.select(selector)
            if elements:
                print(f"   ✅ {name}: Found {len(elements)} elements")
                found_any = True
        except:
            pass

    if not found_any:
        print(f"   ⚠️  No standard product elements found")

    # 4. Check for images
    print("\n4️⃣  Checking for product images...")
    images = soup.find_all('img')
    product_images = [img for img in images if img.get('src') and len(img.get('alt', '')) > 3]
    print(f"   ✅ Total images: {len(images)}")
    print(f"   ✅ Images with alt text: {len(product_images)}")

    # 5. Check for prices
    print("\n5️⃣  Looking for price indicators...")
    price_patterns = ['price', 'amount', 'cost', '$', '₹', '€', '£']
    price_elements = []
    for pattern in price_patterns:
        elements = soup.find_all(string=lambda text: text and pattern in text.lower())
        price_elements.extend(elements)

    if price_elements:
        print(f"   ✅ Found {len(set(price_elements))} potential price mentions")
    else:
        print(f"   ⚠️  No obvious price indicators found")

    # 6. Check for anti-scraping
    print("\n6️⃣  Checking for anti-scraping measures...")
    anti_scraping_indicators = {
        'Cloudflare': 'cloudflare',
        'reCAPTCHA': 'recaptcha',
        'Bot detection': 'bot-detection',
        'Access denied': 'access denied',
    }

    found_protection = []
    for protection, indicator in anti_scraping_indicators.items():
        if indicator in content:
            found_protection.append(protection)

    if found_protection:
        print(f"   ⚠️  Detected: {', '.join(found_protection)}")
        print(f"   💡 This site may require browser automation (Playwright)")
    else:
        print(f"   ✅ No obvious anti-scraping detected")

    # 7. Recommendations
    print(f"\n{'='*70}")
    print("💡 RECOMMENDATIONS:")
    print(f"{'='*70}")

    if not found_any:
        print("❌ This page doesn't appear to be a product listing page.")
        print("   Try:")
        print("   - Using a /collections/, /shop/, or /products/ URL")
        print("   - A category or search results page")
        print("   - Not the homepage")
    elif found_protection:
        print("⚠️  This site has anti-scraping protection.")
        print("   Solutions:")
        print("   - Deploy with full Playwright support")
        print("   - Or manually upload product images")
    else:
        print("✅ This page looks scrapable!")
        print("   If scraping still fails, the HTML structure might be non-standard.")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_url.py <url>")
        print("\nExample:")
        print("  python diagnose_url.py https://yourstore.com/collections/all")
        sys.exit(1)

    diagnose_url(sys.argv[1])
