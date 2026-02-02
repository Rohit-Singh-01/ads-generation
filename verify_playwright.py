"""
Verify Playwright Installation
Run this script to check if Playwright is properly installed
"""

import sys

def verify_playwright():
    print("=" * 60)
    print("PLAYWRIGHT VERIFICATION")
    print("=" * 60)

    # 1. Check if playwright is installed
    print("\n1️⃣  Checking Playwright package...")
    try:
        import playwright
        print(f"   ✅ Playwright installed: {playwright.__version__}")
    except ImportError as e:
        print(f"   ❌ Playwright not installed: {e}")
        return False

    # 2. Check if browser binaries are available
    print("\n2️⃣  Checking browser binaries...")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                print(f"   ✅ Chromium browser available")
                browser.close()
            except Exception as e:
                print(f"   ❌ Browser launch failed: {e}")
                print(f"   💡 Run: playwright install chromium")
                return False
    except Exception as e:
        print(f"   ❌ Playwright API error: {e}")
        return False

    # 3. Test async API (used by your app)
    print("\n3️⃣  Testing async API...")
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def test_async():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto('https://example.com')
                title = await page.title()
                await browser.close()
                return title

        title = asyncio.run(test_async())
        print(f"   ✅ Async API working (tested: {title})")
    except Exception as e:
        print(f"   ❌ Async API failed: {e}")
        return False

    # 4. Summary
    print("\n" + "=" * 60)
    print("✅ VERIFICATION PASSED")
    print("Playwright is ready for production use!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = verify_playwright()
    sys.exit(0 if success else 1)
