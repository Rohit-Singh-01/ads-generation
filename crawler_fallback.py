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

        # Fallback to simple URL fetcher
        try:
            from url_fetcher import fetch_products_from_url
            logger.info("Falling back to simple HTTP scraper...")

            if progress_bar:
                progress_bar.progress(0.3)

            products, error = fetch_products_from_url(website_url)

            if progress_bar:
                progress_bar.progress(0.7)

            if products:
                # Convert to format expected by the app
                result = {
                    'success': True,
                    'url': website_url,
                    'products': products,
                    'text_content': ' '.join([p['name'] for p in products]),
                    'images': [{'url': p['image_url'], 'alt': p['name']} for p in products],
                    'colors': [],
                    'fonts': [],
                    'logos': [],
                    'social_links': {},
                    'contact_info': {},
                    'nav_structure': [],
                    'reviews_text': '',
                    'cta_buttons': [],
                    'metadata': {
                        'title': website_url,
                        'description': f"Products from {website_url}",
                        'method': 'url_fetcher_fallback'
                    },
                    'pages_crawled': 1,
                    'error': None
                }

                if progress_bar:
                    progress_bar.progress(1.0)

                logger.info(f"✓ Simple scraper found {len(products)} products")
                return result
            else:
                logger.error(f"Simple scraper failed: {error}")
                return {
                    'success': False,
                    'error': error or "Could not extract products from the website",
                    'url': website_url
                }

        except Exception as fallback_error:
            logger.error(f"Fallback scraper also failed: {fallback_error}")
            return {
                'success': False,
                'error': f"All crawling methods failed. Last error: {str(fallback_error)}",
                'url': website_url
            }
