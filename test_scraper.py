"""
Quick test script to debug scraping issues
Usage: python test_scraper.py <url>
"""

import sys
from url_fetcher import fetch_products_from_url

def test_url(url):
    print(f"\n🔍 Testing URL: {url}\n")
    print("=" * 60)

    try:
        products, error = fetch_products_from_url(url)

        if products:
            print(f"✅ SUCCESS: Found {len(products)} products\n")
            print("Sample products:")
            for i, product in enumerate(products[:3], 1):
                print(f"\n{i}. {product['name']}")
                print(f"   Price: {product['price']}")
                print(f"   Image: {product['image_url'][:60]}...")
                print(f"   Source: {product.get('source', 'Unknown')}")
        else:
            print(f"❌ FAILED: {error}\n")
            print("Possible issues:")
            print("- URL might not be a product listing page")
            print("- Website might block scraping")
            print("- Page structure might be different than expected")

    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}\n")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_scraper.py <url>")
        print("\nExample URLs to try:")
        print("  - Shopify: https://store.com/collections/all")
        print("  - WooCommerce: https://store.com/shop/")
        sys.exit(1)

    test_url(sys.argv[1])
