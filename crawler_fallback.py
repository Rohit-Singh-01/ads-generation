"""
Intelligent Crawler with Fallback Strategy
Tries Playwright first, falls back to simple HTTP scraper if Playwright fails
"""

import logging
from typing import Dict
import streamlit as st

logger = logging.getLogger(__name__)

def run_crawl_with_fallback(website_url: str, max_depth: int, max_pages: int, progress_bar=None) -> Dict:
    """
    Try Playwright crawler first, fallback to simple URL fetcher if it fails
    """

    # Try Playwright-based comprehensive crawler first
    try:
        from web_crawler_comprehensive import run_comprehensive_crawl
        logger.info("Attempting Playwright-based comprehensive crawl...")

        result = run_comprehensive_crawl(website_url, max_depth, max_pages, progress_bar)

        if result.get('success'):
            logger.info("✓ Playwright crawl successful")
            return result
        else:
            logger.warning("Playwright crawl returned no success, trying fallback...")
            raise Exception("Playwright crawl failed")

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Playwright crawler failed: {error_msg}")

        # Check if it's a Playwright installation error
        if 'playwright' in error_msg.lower() or 'browser' in error_msg.lower():
            st.warning("⚠️ Browser automation unavailable. Using lightweight scraper instead...")

        # Fallback to enhanced scraper
        try:
            from url_fetcher import fetch_products_from_url
            from enhanced_fallback_scraper import enhanced_scrape
            logger.info("Falling back to enhanced HTTP scraper...")
            st.info("ℹ️ Using enhanced lightweight scraper (no browser needed)...")

            if progress_bar:
                progress_bar.progress(0.2)

            # Get brand intelligence
            brand_intel = enhanced_scrape(website_url)

            if progress_bar:
                progress_bar.progress(0.4)

            # Get products
            products, error = fetch_products_from_url(website_url)

            if progress_bar:
                progress_bar.progress(0.7)

            if products and len(products) > 0:
                # Merge product data with brand intelligence
                result = {
                    'success': True,
                    'url': website_url,
                    'products': products,
                    'text_content': ' '.join([p['name'] for p in products]),
                    'images': [{'url': p['image_url'], 'alt': p['name']} for p in products],
                    'colors': brand_intel.get('colors', []),
                    'fonts': brand_intel.get('fonts', []),
                    'logos': brand_intel.get('logos', {
                        'light': None,
                        'dark': None,
                        'all': []
                    }),
                    'social_links': brand_intel.get('social_links', {}),
                    'contact_info': brand_intel.get('contact_info', {}),
                    'nav_structure': brand_intel.get('nav_structure', []),
                    'reviews_text': '',
                    'cta_buttons': brand_intel.get('cta_buttons', []),
                    'ctas': brand_intel.get('cta_buttons', []),
                    'general_forms': [],
                    'visual_elements': [],
                    'char_count': sum(len(p['name']) for p in products),
                    'ads': [],
                    'metadata': {
                        'title': website_url,
                        'description': f"Products from {website_url}",
                        'method': 'enhanced_fallback'
                    },
                    'pages_crawled': 1,
                    'error': None
                }

                if progress_bar:
                    progress_bar.progress(1.0)

                # Show what was extracted
                extracted_items = []
                if products:
                    extracted_items.append(f"{len(products)} products")
                if brand_intel.get('colors'):
                    extracted_items.append(f"{len(brand_intel['colors'])} colors")
                if brand_intel.get('logos', {}).get('all'):
                    extracted_items.append(f"{len(brand_intel['logos']['all'])} logos")
                if brand_intel.get('social_links'):
                    extracted_items.append(f"{len(brand_intel['social_links'])} social links")

                logger.info(f"✓ Enhanced scraper extracted: {', '.join(extracted_items)}")
                st.success(f"✅ Extracted: {', '.join(extracted_items)}")
                return result
            else:
                error_details = error or "No products found on this page"
                logger.error(f"Simple scraper failed: {error_details}")
                st.error(f"Scraper error: {error_details}")
                return {
                    'success': False,
                    'error': error_details,
                    'url': website_url
                }

        except Exception as fallback_error:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Fallback scraper exception: {fallback_error}\n{error_trace}")
            st.error(f"Scraper exception: {str(fallback_error)}")
            return {
                'success': False,
                'error': f"Scraping failed: {str(fallback_error)}. Try a different URL or product page.",
                'url': website_url
            }
