"""
Comprehensive Web Crawler Module - PRODUCTION VERSION
Extracts ALL brand intelligence signals with production-grade error handling
"""

import asyncio
import random
import logging
import time
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

# LOGGING: Setup production-level logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web_crawler_production')


class ComprehensiveWebCrawler:
    """
    PRODUCTION-GRADE Enhanced crawler that extracts:
    - Hero sections (headlines, subheadlines)
    - About Us content
    - Legal/footer/disclaimers
    - FAQs
    - Product bullet points
    - Pricing data
    - Banners/carousels
    - Social media embeds
    - Navigation (existing)
    - Reviews (existing)
    + Production error handling & anti-detection
    """

    # Production-level configurations
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900}
    ]

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    ]

    def __init__(self, base_url: str, max_depth: int = 3, max_pages: int = 50, concurrency: int = 5):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.visited_urls: Set[str] = set()
        self.pending_urls: asyncio.Queue = None
        self.results_lock = asyncio.Lock()
        self.collected_data = {
            'pages': [],
            'text_content': '',
            'nav_text': '',
            'reviews_text': '',
            'hero_sections': [],
            'about_us_content': '',
            'legal_footer_content': '',
            'faqs': [],
            'product_bullets': [],
            'pricing_data': [],
            'disclaimers': [],
            'banners_carousels': [],
            'social_embeds': [],
            'contact_data': [],  # NEW: Contact forms and info
            'team_members': [],  # NEW: Team/leadership data
            'press_media': [],  # NEW: Press mentions and awards
            'case_studies': [],  # NEW: Success stories
            'careers_data': [],  # NEW: Job listings and culture
            'events_data': [],  # NEW: Events and webinars
            'structured_data': [],  # NEW: JSON-LD, OG, Schema.org
            'videos': [],  # NEW: Video embeds and native
            'ctas': [],  # NEW: Call-to-action buttons
            'general_forms': [],  # NEW: All forms beyond contact
            'visual_elements': [],  # NEW: Animations, carousels, etc.
            'logos': [],
            'colors': set(),
            'images': [],
            'links': []
        }
        self.priority_keywords = {
            'critical': ['about', 'about-us', 'who-we-are', 'our-story', 'brand', 'mission', 'values'],
            'high': ['services', 'products', 'solutions', 'features', 'benefits', 'team', 'reviews', 'testimonials', 'faq', 'pricing'],
            'medium': ['story', 'history', 'awards', 'news', 'blog']
        }
        self.progress_callback = None
        self.crawl_complete = False

        # LOGGING: Performance metrics tracking
        self.metrics = {
            'pages_crawled': 0,
            'pages_failed': 0,
            'total_text_extracted': 0,
            'retry_count': 0,
            'captcha_count': 0,
            'blocked_count': 0,
            'crawl_start_time': None,
            'crawl_end_time': None,
            'crawl_duration': 0
        }

    def get_link_priority(self, url: str, link_text: str) -> int:
        """Calculate priority score for link crawling"""
        url_lower = url.lower()
        text_lower = link_text.lower()
        score = 0

        # Higher priority for key pages
        if any(kw in url_lower or kw in text_lower for kw in ['review', 'testimonial', 'feedback', 'faq', 'about', 'pricing']):
            score += 20

        for kw in self.priority_keywords['critical']:
            if kw in url_lower or kw in text_lower:
                score += 15
        for kw in self.priority_keywords['high']:
            if kw in url_lower or kw in text_lower:
                score += 8
        for kw in self.priority_keywords['medium']:
            if kw in url_lower or kw in text_lower:
                score += 4

        return score

    async def fetch_page_with_retry(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """
        Fetch page with exponential backoff retry logic
        Returns: True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Try networkidle first (best for SPAs)
                await page.goto(url, wait_until='networkidle', timeout=20000)
                return True
            except PlaywrightTimeout:
                self.metrics['retry_count'] += 1
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    logger.warning(f"Timeout on {url}, retry {attempt + 1}/{max_retries} after {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt with domcontentloaded
                    logger.warning(f"Final retry on {url} with domcontentloaded fallback")
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                        return True
                    except:
                        logger.error(f"Failed to fetch {url} after {max_retries} retries")
                        return False
            except Exception as e:
                self.metrics['retry_count'] += 1
                if attempt < max_retries - 1:
                    logger.warning(f"Error on {url}: {e}, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} retries: {e}")
                    return False
        return False

    async def handle_bot_detection(self, page: Page) -> str:
        """
        Detect and handle anti-bot challenges
        Returns: 'ok', 'cloudflare', 'captcha', or 'blocked'
        """
        try:
            # Check for Cloudflare challenge
            cloudflare_selectors = [
                'text="Checking your browser"',
                'text="Please wait"',
                'text="Verifying you are human"',
                '#challenge-running'
            ]

            for selector in cloudflare_selectors:
                if await page.locator(selector).count() > 0:
                    # Wait for challenge to complete
                    logger.warning(f"Cloudflare challenge detected on {page.url}, waiting 5s")
                    await asyncio.sleep(5)
                    return 'cloudflare'

            # Check for CAPTCHA
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                '.g-recaptcha',
                '.h-captcha'
            ]

            for selector in captcha_selectors:
                if await page.locator(selector).count() > 0:
                    self.metrics['captcha_count'] += 1
                    logger.warning(f"CAPTCHA detected on {page.url}")
                    return 'captcha'

            # Check for explicit blocks
            page_text = await page.content()
            block_keywords = ['access denied', 'blocked', '403 forbidden', 'too many requests']
            if any(keyword in page_text.lower() for keyword in block_keywords):
                self.metrics['blocked_count'] += 1
                logger.warning(f"Access blocked on {page.url}")
                return 'blocked'

            return 'ok'

        except Exception as e:
            return 'ok'  # Assume OK if detection fails

    async def add_human_behavior(self, page: Page):
        """Add human-like behavior patterns"""
        try:
            # Random mouse movement
            await page.mouse.move(
                random.randint(0, 200),
                random.randint(0, 200)
            )

            # Random small delay
            await asyncio.sleep(random.uniform(0.5, 1.5))

        except Exception:
            pass  # Silently fail if behavior simulation fails

    async def setup_request_interception(self, page: Page):
        """
        PERFORMANCE: Block unnecessary resources to speed up crawling
        Blocks: images (we extract them differently), stylesheets, fonts, media
        """
        async def route_handler(route):
            resource_type = route.request.resource_type
            # Block heavy resources we don't need for text extraction
            if resource_type in ['image', 'stylesheet', 'font', 'media']:
                await route.abort()
            else:
                await route.continue_()

        await page.route('**/*', route_handler)

    def get_page_value_score(self, page_type: str) -> int:
        """
        PERFORMANCE: Calculate value score for intelligent crawl budget
        Higher scores = more important pages to crawl
        """
        page_value_scores = {
            'home': 100,
            'about': 95,
            'reviews': 90,
            'product': 85,
            'pricing': 80,
            'faq': 75,
            'team': 70,
            'press': 70,
            'case-study': 65,
            'contact': 60,
            'careers': 55,
            'events': 50,
            'blog': 45,
            'collection': 40,
            'legal': 10,
            'general': 30
        }
        return page_value_scores.get(page_type, 30)

    @staticmethod
    def clean_extracted_text(text: str) -> str:
        """
        VALIDATION: Clean extracted text by removing noise patterns
        """
        import re

        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common noise patterns
        noise_patterns = [
            r'Cookie Policy.*?(?:Accept|OK|Close)',
            r'This site uses cookies.*?(?:Accept|OK|Close)',
            r'Subscribe to our newsletter.*?Sign Up',
            r'By continuing.*?you agree',
            r'We use cookies.*?(?:Learn more|OK)',
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove excessive punctuation
        text = re.sub(r'[!?]{2,}', '!', text)
        text = re.sub(r'\.{2,}', '.', text)

        # Trim and normalize
        text = text.strip()

        return text

    @staticmethod
    def validate_extracted_data(data: Dict) -> Dict:
        """
        VALIDATION: Validate extracted data and add quality scores
        """
        validations = {
            'has_text': len(data.get('text', '')) > 100,
            'has_title': len(data.get('title', '')) > 0,
            'has_nav': len(data.get('nav_text', '')) > 10,
            'has_page_type': data.get('page_type', '') != '',
            'has_links': len(data.get('links', [])) > 0,
        }

        # Calculate validation score
        data['validation_score'] = sum(validations.values()) / len(validations)
        data['validation_details'] = validations
        data['is_valid'] = data['validation_score'] >= 0.6  # At least 60% valid

        return data

    def _classify_page_type(self, url: str, title: str) -> str:
        """Classify page type"""
        url_lower = url.lower()
        title_lower = title.lower()

        if any(x in url_lower or x in title_lower for x in ['privacy', 'terms', 'legal', 'cookie']):
            return 'legal'
        if any(x in url_lower or x in title_lower for x in ['about', 'our-story', 'mission']):
            return 'about'
        if any(x in url_lower or x in title_lower for x in ['contact', 'get-in-touch', 'reach-us']):
            return 'contact'
        if any(x in url_lower or x in title_lower for x in ['team', 'leadership', 'our-team', 'people']):
            return 'team'
        if any(x in url_lower or x in title_lower for x in ['press', 'media', 'newsroom', 'in-the-news']):
            return 'press'
        if any(x in url_lower or x in title_lower for x in ['case-stud', 'success-stor', 'customer-stor']):
            return 'case-study'
        if any(x in url_lower or x in title_lower for x in ['career', 'job', 'join-us', 'hiring']):
            return 'careers'
        if any(x in url_lower or x in title_lower for x in ['event', 'webinar', 'conference', 'workshop']):
            return 'events'
        if any(x in url_lower or x in title_lower for x in ['faq', 'help', 'support']):
            return 'faq'
        if any(x in url_lower or x in title_lower for x in ['pricing', 'plans', 'price']):
            return 'pricing'
        if any(x in url_lower or x in title_lower for x in ['blog', 'article', 'post', 'news']):
            return 'blog'
        if any(x in url_lower or x in title_lower for x in ['product', 'item', 'shop']):
            return 'product'
        if any(x in url_lower or x in title_lower for x in ['collection', 'category', 'catalog']):
            return 'collection'
        if any(x in url_lower or x in title_lower for x in ['review', 'testimonial', 'feedback']):
            return 'reviews'
        if url_lower == self.base_url or 'home' in url_lower or 'index' in url_lower:
            return 'home'

        return 'general'

    async def extract_comprehensive_data(self, page: Page, url: str) -> Dict:
        """Extract ALL signals from page"""
        data = {
            'url': url,
            'title': '',
            'page_type': '',
            'text': '',
            'nav_text': '',
            'reviews_text': '',
            'hero_section': {},
            'legal_footer': '',
            'faqs': [],
            'product_bullets': [],
            'pricing': [],
            'disclaimers': [],
            'banners': [],
            'social_embeds': [],
            'contact_data': {},  # NEW
            'team_members': [],  # NEW
            'press_media': {},  # NEW
            'case_studies': [],  # NEW
            'careers_data': {},  # NEW
            'events_data': [],  # NEW
            'structured_data': {},  # NEW
            'videos': {},  # NEW
            'ctas': {},  # NEW
            'general_forms': [],  # NEW
            'visual_elements': {},  # NEW
            'logos': [],
            'colors': [],
            'images': [],
            'links': []
        }

        try:
            data['title'] = await page.title()
            data['page_type'] = self._classify_page_type(url, data['title'])

            # 1. HERO SECTION (Homepage primary)
            if data['page_type'] in ['home', 'general']:
                hero_data = await page.evaluate('''() => {
                    const heroSelectors = [
                        '.hero', '.banner', '.jumbotron', '[class*="hero"]',
                        'section:first-of-type', '.above-fold', '[class*="banner"]'
                    ];

                    let headline = '';
                    let subheadline = '';
                    let cta_text = '';

                    for (const sel of heroSelectors) {
                        const hero = document.querySelector(sel);
                        if (hero) {
                            // Get headline (h1, h2, or largest text)
                            const h1 = hero.querySelector('h1');
                            const h2 = hero.querySelector('h2');
                            headline = (h1 && h1.innerText) || (h2 && h2.innerText) || '';

                            // Get subheadline (p, h3, or subtitle class)
                            const p = hero.querySelector('p');
                            const h3 = hero.querySelector('h3');
                            const subtitle = hero.querySelector('[class*="subtitle"], [class*="subhead"]');
                            subheadline = (subtitle && subtitle.innerText) || (p && p.innerText) || (h3 && h3.innerText) || '';

                            // Get CTA button text
                            const cta = hero.querySelector('a, button');
                            cta_text = (cta && cta.innerText) || '';

                            if (headline) break;
                        }
                    }

                    return {headline, subheadline, cta_text};
                }''')
                data['hero_section'] = hero_data

            # 2. NAVIGATION (existing, enhanced)
            nav_text = await page.evaluate('''() => {
                const navElements = document.querySelectorAll('nav, .nav, .navigation, .menu, header, [role="navigation"]');
                let text = '';
                navElements.forEach(el => {
                    if (el.innerText) text += el.innerText + ' ';
                    el.querySelectorAll('[aria-label]').forEach(aria => {
                        text += aria.getAttribute('aria-label') + ' ';
                    });
                    el.querySelectorAll('a').forEach(a => {
                        text += a.innerText + ' ';
                    });
                });
                return text.replace(/\\s+/g, ' ').trim();
            }''')
            data['nav_text'] = nav_text[:10000]

            # 3. LEGAL/FOOTER/DISCLAIMERS (critical for ad safety)
            legal_footer = await page.evaluate('''() => {
                const legalSelectors = [
                    'footer', '.footer', '[role="contentinfo"]',
                    '.disclaimer', '[class*="disclaimer"]', '[class*="legal"]',
                    '.terms', '.privacy', '[class*="compliance"]'
                ];
                let text = '';
                legalSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el.innerText) text += el.innerText + ' ';
                    });
                });
                return text.replace(/\\s+/g, ' ').trim();
            }''')
            data['legal_footer'] = legal_footer[:50000]

            # 4. FAQs
            if data['page_type'] in ['faq', 'product', 'home']:
                faqs = await page.evaluate('''() => {
                    const faqSelectors = [
                        '.faq', '[class*="faq"]', '.accordion', '[class*="accordion"]',
                        '[itemtype*="Question"]', '[class*="question"]'
                    ];
                    const faqs = [];

                    faqSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            const question = el.querySelector('[class*="question"], h3, h4, summary, dt');
                            const answer = el.querySelector('[class*="answer"], p, dd');

                            if (question && answer) {
                                faqs.push({
                                    question: question.innerText.trim(),
                                    answer: answer.innerText.trim()
                                });
                            } else if (el.innerText) {
                                // Fallback: just grab the text
                                faqs.push({question: '', answer: el.innerText.trim()});
                            }
                        });
                    });

                    return faqs.slice(0, 20);
                }''')
                data['faqs'] = faqs

            # 5. PRODUCT BULLETS (PDPs)
            if data['page_type'] == 'product':
                bullets = await page.evaluate('''() => {
                    const bulletSelectors = [
                        '.product-description ul li', '.benefits li', '.features li',
                        '[class*="benefit"] li', '[class*="feature"] li',
                        '.bullet-point', '[class*="bullet"]'
                    ];
                    const bullets = [];

                    bulletSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            if (el.innerText && el.innerText.length > 5) {
                                bullets.push(el.innerText.trim());
                            }
                        });
                    });

                    return bullets.slice(0, 20);
                }''')
                data['product_bullets'] = bullets

            # 6. PRICING DATA
            pricing = await page.evaluate('''() => {
                const priceSelectors = [
                    '.price', '[class*="price"]', '[data-price]',
                    '.cost', '[class*="cost"]', '[class*="pricing"]'
                ];
                const pricing = [];
                const seen = new Set();

                priceSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        const text = el.innerText.trim();
                        const priceMatch = text.match(/[$£€₹]\\s*([\\d,]+(?:\\.\\d{2})?)/);
                        if (priceMatch && !seen.has(text)) {
                            seen.add(text);
                            pricing.push({
                                text: text,
                                currency: priceMatch[0][0],
                                amount: parseFloat(priceMatch[1].replace(',', ''))
                            });
                        }
                    });
                });

                return pricing.slice(0, 20);
            }''')
            data['pricing'] = pricing

            # 7. DISCLAIMERS (ad safety)
            disclaimers = await page.evaluate('''() => {
                const disclaimerPatterns = [
                    'results may vary', 'not intended to diagnose', 'consult your doctor',
                    'these statements have not been evaluated', 'not a substitute',
                    'individual results may vary', 'no guarantee'
                ];

                const disclaimers = [];
                const bodyText = document.body.innerText.toLowerCase();

                disclaimerPatterns.forEach(pattern => {
                    if (bodyText.includes(pattern)) {
                        // Find the sentence containing this pattern
                        const sentences = document.body.innerText.split(/[.!?]\\s+/);
                        sentences.forEach(sentence => {
                            if (sentence.toLowerCase().includes(pattern)) {
                                disclaimers.push(sentence.trim());
                            }
                        });
                    }
                });

                return [...new Set(disclaimers)].slice(0, 10);
            }''')
            data['disclaimers'] = disclaimers

            # 8. BANNERS/CAROUSELS (text density analysis)
            banners = await page.evaluate('''() => {
                const bannerSelectors = [
                    '.banner', '[class*="banner"]', '.carousel', '[class*="carousel"]',
                    '.slider', '[class*="slider"]', '.promo', '[class*="promo"]'
                ];
                const banners = [];

                bannerSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        const text = el.innerText.trim();
                        if (text && text.length > 3) {
                            const wordCount = text.split(/\\s+/).length;
                            banners.push({
                                text: text.slice(0, 200),
                                word_count: wordCount,
                                char_count: text.length
                            });
                        }
                    });
                });

                return banners.slice(0, 10);
            }''')
            data['banners'] = banners

            # 9. SOCIAL MEDIA EMBEDS (platform fit)
            social_embeds = await page.evaluate('''() => {
                const platforms = {
                    instagram: ['instagram.com', 'instagram-feed', 'insta-'],
                    tiktok: ['tiktok.com', 'tiktok-'],
                    youtube: ['youtube.com', 'youtu.be', 'youtube-'],
                    facebook: ['facebook.com', 'fb.com', 'facebook-'],
                    twitter: ['twitter.com', 'x.com', 'tweet-'],
                    pinterest: ['pinterest.com', 'pinterest-']
                };

                const embeds = {
                    instagram: 0,
                    tiktok: 0,
                    youtube: 0,
                    facebook: 0,
                    twitter: 0,
                    pinterest: 0
                };

                // Check iframes and links
                document.querySelectorAll('iframe, a').forEach(el => {
                    const src = el.src || el.href || '';
                    const classes = el.className || '';

                    Object.keys(platforms).forEach(platform => {
                        platforms[platform].forEach(pattern => {
                            if (src.includes(pattern) || classes.includes(pattern)) {
                                embeds[platform]++;
                            }
                        });
                    });
                });

                return embeds;
            }''')
            data['social_embeds'] = social_embeds

            # 10. CONTACT PAGE EXTRACTION
            if data['page_type'] in ['contact', 'general']:
                contact_data = await page.evaluate('''() => {
                    const contactData = {
                        forms: [],
                        contact_info: {
                            emails: [],
                            phones: [],
                            addresses: []
                        }
                    };

                    // Extract forms
                    document.querySelectorAll('form').forEach(form => {
                        const fields = [];
                        form.querySelectorAll('input, textarea, select').forEach(field => {
                            const type = field.type || field.tagName.toLowerCase();
                            const name = field.name || field.id || field.placeholder || '';
                            const required = field.hasAttribute('required');
                            if (name) {
                                fields.push({type, name, required});
                            }
                        });
                        if (fields.length > 0) {
                            contactData.forms.push({fields, field_count: fields.length});
                        }
                    });

                    // Extract emails
                    const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                    const bodyText = document.body.innerText;
                    const emails = bodyText.match(emailPattern) || [];
                    contactData.contact_info.emails = [...new Set(emails)].slice(0, 5);

                    // Extract phone numbers
                    const phonePattern = /(?:\\+?\\d{1,3}[-.])?\\(?\\d{3}\\)?[-.]?\\d{3}[-.]?\\d{4}/g;
                    const phones = bodyText.match(phonePattern) || [];
                    contactData.contact_info.phones = [...new Set(phones)].slice(0, 5);

                    return contactData;
                }''')
                data['contact_data'] = contact_data

            # 11. TEAM/LEADERSHIP PAGE EXTRACTION
            if data['page_type'] in ['team', 'about', 'general']:
                team_data = await page.evaluate('''() => {
                    const teamMembers = [];
                    const teamSelectors = [
                        '.team-member', '[class*="team"]', '.staff', '[class*="person"]',
                        '[class*="leader"]', '[class*="employee"]'
                    ];

                    teamSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(member => {
                            const name = member.querySelector('h1, h2, h3, h4, .name, [class*="name"]');
                            const title = member.querySelector('.title, [class*="title"], [class*="role"], [class*="position"]');
                            const bio = member.querySelector('p, .bio, [class*="bio"]');

                            if (name || title) {
                                teamMembers.push({
                                    name: name ? name.innerText.trim() : '',
                                    title: title ? title.innerText.trim() : '',
                                    bio: bio ? bio.innerText.trim().slice(0, 200) : ''
                                });
                            }
                        });
                    });

                    return teamMembers.slice(0, 20);
                }''')
                data['team_members'] = team_data

            # 12. PRESS/MEDIA PAGE EXTRACTION
            if data['page_type'] in ['press', 'blog', 'general']:
                press_data = await page.evaluate('''() => {
                    const pressItems = [];
                    const pressSelectors = [
                        '.press', '[class*="press"]', '.media', '[class*="media"]',
                        '.award', '[class*="award"]', '.news-item', '[class*="news"]'
                    ];

                    pressSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(item => {
                            const headline = item.querySelector('h1, h2, h3, h4, a');
                            const date = item.querySelector('.date, [class*="date"], time');
                            const source = item.querySelector('.source, [class*="source"]');

                            if (headline) {
                                pressItems.push({
                                    headline: headline.innerText.trim(),
                                    date: date ? date.innerText.trim() : '',
                                    source: source ? source.innerText.trim() : ''
                                });
                            }
                        });
                    });

                    // Also extract award mentions
                    const awards = [];
                    const awardKeywords = ['award', 'winner', 'recognized', 'honor', 'best', 'top'];
                    const sentences = document.body.innerText.split(/[.!?]\\s+/);
                    sentences.forEach(sentence => {
                        const lower = sentence.toLowerCase();
                        if (awardKeywords.some(kw => lower.includes(kw))) {
                            awards.push(sentence.trim());
                        }
                    });

                    return {
                        press_items: pressItems.slice(0, 15),
                        awards: [...new Set(awards)].slice(0, 10)
                    };
                }''')
                data['press_media'] = press_data

            # 13. CASE STUDIES/SUCCESS STORIES EXTRACTION
            if data['page_type'] in ['case-study', 'blog', 'general']:
                case_study_data = await page.evaluate('''() => {
                    const caseStudies = [];
                    const caseSelectors = [
                        '.case-study', '[class*="case"]', '.success-story', '[class*="success"]',
                        '.customer-story', '[class*="story"]'
                    ];

                    caseSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(cs => {
                            const title = cs.querySelector('h1, h2, h3');
                            const metrics = [];

                            // Extract metrics (numbers + percentage/growth)
                            const metricsPattern = /(\\d+%|\\d+x|\\$[\\d,]+|\\d+k|\\d+m)/gi;
                            const csText = cs.innerText;
                            const matches = csText.match(metricsPattern);
                            if (matches) {
                                metrics.push(...matches.slice(0, 5));
                            }

                            if (title || metrics.length > 0) {
                                caseStudies.push({
                                    title: title ? title.innerText.trim() : '',
                                    metrics: metrics
                                });
                            }
                        });
                    });

                    return caseStudies.slice(0, 10);
                }''')
                data['case_studies'] = case_study_data

            # 14. CAREERS PAGE EXTRACTION
            if data['page_type'] in ['careers', 'general']:
                careers_data = await page.evaluate('''() => {
                    const jobs = [];
                    const jobSelectors = [
                        '.job', '[class*="job"]', '.position', '[class*="position"]',
                        '.opening', '[class*="opening"]', '.career', '[class*="career"]'
                    ];

                    jobSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(job => {
                            const title = job.querySelector('h1, h2, h3, h4, .title, [class*="title"]');
                            const location = job.querySelector('.location, [class*="location"]');
                            const type = job.querySelector('.type, [class*="type"]');

                            if (title) {
                                jobs.push({
                                    title: title.innerText.trim(),
                                    location: location ? location.innerText.trim() : '',
                                    type: type ? type.innerText.trim() : ''
                                });
                            }
                        });
                    });

                    // Extract culture keywords
                    const cultureKeywords = ['culture', 'values', 'mission', 'vision', 'perks', 'benefits'];
                    const cultureSections = [];
                    document.querySelectorAll('h1, h2, h3, h4').forEach(heading => {
                        const headingText = heading.innerText.toLowerCase();
                        if (cultureKeywords.some(kw => headingText.includes(kw))) {
                            const nextSibling = heading.nextElementSibling;
                            if (nextSibling) {
                                cultureSections.push(nextSibling.innerText.trim().slice(0, 300));
                            }
                        }
                    });

                    return {
                        job_listings: jobs.slice(0, 20),
                        culture_sections: cultureSections.slice(0, 5)
                    };
                }''')
                data['careers_data'] = careers_data

            # 15. EVENTS PAGE EXTRACTION
            if data['page_type'] in ['events', 'general']:
                events_data = await page.evaluate('''() => {
                    const events = [];
                    const eventSelectors = [
                        '.event', '[class*="event"]', '.webinar', '[class*="webinar"]',
                        '.conference', '[class*="conference"]'
                    ];

                    eventSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(event => {
                            const title = event.querySelector('h1, h2, h3, h4, .title, [class*="title"]');
                            const date = event.querySelector('.date, [class*="date"], time');
                            const location = event.querySelector('.location, [class*="location"], [class*="venue"]');

                            if (title) {
                                events.push({
                                    title: title.innerText.trim(),
                                    date: date ? date.innerText.trim() : '',
                                    location: location ? location.innerText.trim() : ''
                                });
                            }
                        });
                    });

                    return events.slice(0, 15);
                }''')
                data['events_data'] = events_data

            # 16. STRUCTURED DATA EXTRACTION (JSON-LD, Open Graph, Schema.org)
            structured_data = await page.evaluate('''() => {
                const structuredData = {
                    jsonLd: [],
                    openGraph: {},
                    twitter: {},
                    metaTags: {},
                    schemaOrg: {}
                };

                // Extract JSON-LD scripts
                document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
                    try {
                        const data = JSON.parse(script.textContent);
                        structuredData.jsonLd.push(data);

                        // Extract specific Schema.org types
                        if (data['@type']) {
                            const type = Array.isArray(data['@type']) ? data['@type'][0] : data['@type'];
                            if (['Product', 'Organization', 'LocalBusiness', 'Person', 'Article'].includes(type)) {
                                structuredData.schemaOrg[type] = data;
                            }
                        }
                    } catch(e) {}
                });

                // Extract Open Graph meta tags
                document.querySelectorAll('meta[property^="og:"]').forEach(meta => {
                    const property = meta.getAttribute('property').replace('og:', '');
                    const content = meta.getAttribute('content');
                    if (content) {
                        structuredData.openGraph[property] = content;
                    }
                });

                // Extract Twitter Card meta tags
                document.querySelectorAll('meta[name^="twitter:"]').forEach(meta => {
                    const name = meta.getAttribute('name').replace('twitter:', '');
                    const content = meta.getAttribute('content');
                    if (content) {
                        structuredData.twitter[name] = content;
                    }
                });

                // Extract general meta tags
                const metaNames = ['description', 'keywords', 'author', 'viewport', 'theme-color', 'robots'];
                metaNames.forEach(name => {
                    const meta = document.querySelector(`meta[name="${name}"]`);
                    if (meta) {
                        structuredData.metaTags[name] = meta.getAttribute('content');
                    }
                });

                // Extract canonical URL
                const canonical = document.querySelector('link[rel="canonical"]');
                if (canonical) {
                    structuredData.metaTags.canonical = canonical.getAttribute('href');
                }

                return structuredData;
            }''')
            data['structured_data'] = structured_data

            # 17. VIDEO DETECTION (YouTube, Vimeo, native video)
            videos = await page.evaluate('''() => {
                const videos = {
                    youtube: [],
                    vimeo: [],
                    native: [],
                    count: 0
                };

                // Detect YouTube embeds
                document.querySelectorAll('iframe[src*="youtube.com"], iframe[src*="youtu.be"]').forEach(iframe => {
                    const src = iframe.src;
                    const videoId = src.match(/(?:embed\/|v=)([a-zA-Z0-9_-]+)/);
                    if (videoId) {
                        videos.youtube.push({url: src, id: videoId[1]});
                        videos.count++;
                    }
                });

                // Detect Vimeo embeds
                document.querySelectorAll('iframe[src*="vimeo.com"]').forEach(iframe => {
                    const src = iframe.src;
                    const videoId = src.match(/vimeo\\.com\\/video\\/(\\d+)/);
                    if (videoId) {
                        videos.vimeo.push({url: src, id: videoId[1]});
                        videos.count++;
                    }
                });

                // Detect native video elements
                document.querySelectorAll('video').forEach(video => {
                    const sources = Array.from(video.querySelectorAll('source')).map(s => s.src);
                    if (sources.length > 0 || video.src) {
                        videos.native.push({src: video.src || sources[0], poster: video.poster});
                        videos.count++;
                    }
                });

                return videos;
            }''')
            data['videos'] = videos

            # 18. CTA (CALL-TO-ACTION) EXTRACTION
            ctas = await page.evaluate('''() => {
                const ctas = {
                    primary: [],
                    secondary: [],
                    all_text: [],
                    count: 0
                };

                // CTA patterns
                const primaryPatterns = ['buy now', 'get started', 'sign up', 'start free', 'try', 'subscribe', 'purchase', 'order now', 'shop now'];
                const secondaryPatterns = ['learn more', 'contact', 'see more', 'view', 'explore', 'discover', 'read more'];

                // Check buttons and links
                document.querySelectorAll('button, a, [role="button"]').forEach(el => {
                    const text = el.innerText.toLowerCase().trim();
                    if (!text || text.length > 50) return;

                    const classes = (el.className || '').toLowerCase();
                    const isPrimary = classes.includes('primary') || classes.includes('cta') || classes.includes('btn-primary');
                    const isButton = el.tagName === 'BUTTON' || classes.includes('button') || classes.includes('btn');

                    if (primaryPatterns.some(pattern => text.includes(pattern))) {
                        ctas.primary.push({
                            text: el.innerText.trim(),
                            classes: el.className || '',
                            type: 'primary',
                            is_button: isButton
                        });
                        ctas.count++;
                    } else if (secondaryPatterns.some(pattern => text.includes(pattern))) {
                        ctas.secondary.push({
                            text: el.innerText.trim(),
                            classes: el.className || '',
                            type: 'secondary',
                            is_button: isButton
                        });
                        ctas.count++;
                    } else if (isButton && isPrimary) {
                        ctas.primary.push({
                            text: el.innerText.trim(),
                            classes: el.className || '',
                            type: 'inferred_primary',
                            is_button: true
                        });
                        ctas.count++;
                    }

                    if (ctas.count <= 50) {
                        ctas.all_text.push(el.innerText.trim());
                    }
                });

                return {
                    primary: ctas.primary.slice(0, 15),
                    secondary: ctas.secondary.slice(0, 15),
                    all_text: [...new Set(ctas.all_text)].slice(0, 30),
                    count: ctas.count
                };
            }''')
            data['ctas'] = ctas

            # 19. FORM ANALYSIS (General forms beyond contact forms)
            general_forms = await page.evaluate('''() => {
                const forms = [];

                document.querySelectorAll('form').forEach((form, index) => {
                    const formData = {
                        index: index,
                        action: form.action || '',
                        method: form.method || 'get',
                        fields: [],
                        field_types: {},
                        has_submit: false
                    };

                    // Analyze form fields
                    form.querySelectorAll('input, textarea, select').forEach(field => {
                        const type = field.type || field.tagName.toLowerCase();
                        const name = field.name || field.id || field.placeholder || '';
                        const required = field.hasAttribute('required');
                        const label = field.labels && field.labels.length > 0 ? field.labels[0].innerText : '';

                        formData.fields.push({
                            type: type,
                            name: name,
                            required: required,
                            label: label
                        });

                        // Count field types
                        formData.field_types[type] = (formData.field_types[type] || 0) + 1;
                    });

                    // Check for submit button
                    formData.has_submit = form.querySelector('button[type="submit"], input[type="submit"]') !== null;

                    // Classify form type
                    const formText = form.innerText.toLowerCase();
                    if (formText.includes('newsletter') || formText.includes('subscribe')) {
                        formData.form_type = 'newsletter';
                    } else if (formText.includes('contact') || formText.includes('message')) {
                        formData.form_type = 'contact';
                    } else if (formText.includes('search')) {
                        formData.form_type = 'search';
                    } else if (formText.includes('login') || formText.includes('sign in')) {
                        formData.form_type = 'login';
                    } else if (formText.includes('register') || formText.includes('sign up')) {
                        formData.form_type = 'registration';
                    } else {
                        formData.form_type = 'other';
                    }

                    if (formData.fields.length > 0) {
                        forms.push(formData);
                    }
                });

                return forms.slice(0, 10);
            }''')
            data['general_forms'] = general_forms

            # 20. VISUAL ELEMENTS DETECTION
            visual_elements = await page.evaluate('''() => {
                const visuals = {
                    has_animations: false,
                    has_parallax: false,
                    carousels: [],
                    sticky_elements: [],
                    interactive_count: 0
                };

                // Detect CSS animations
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    if (style.animation !== 'none' || style.animationName !== 'none') {
                        visuals.has_animations = true;
                        break;
                    }
                }

                // Detect parallax (rough heuristic)
                const parallaxSelectors = ['.parallax', '[data-parallax]', '[class*="parallax"]'];
                parallaxSelectors.forEach(sel => {
                    if (document.querySelector(sel)) {
                        visuals.has_parallax = true;
                    }
                });

                // Detect carousels/sliders
                const carouselSelectors = [
                    '.carousel', '.slider', '.swiper', '[class*="carousel"]',
                    '[class*="slider"]', '[class*="swiper"]', '[data-slide]'
                ];
                carouselSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(carousel => {
                        const slides = carousel.querySelectorAll('[class*="slide"], [class*="item"]');
                        if (slides.length > 1) {
                            visuals.carousels.push({
                                classes: carousel.className,
                                slide_count: slides.length
                            });
                        }
                    });
                });

                // Detect sticky elements
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'sticky' || style.position === 'fixed') {
                        const classes = el.className || '';
                        if (classes.includes('header') || classes.includes('nav') || classes.includes('cta')) {
                            visuals.sticky_elements.push({
                                type: el.tagName.toLowerCase(),
                                classes: classes
                            });
                        }
                    }
                });

                // Count interactive elements
                visuals.interactive_count = document.querySelectorAll('button, a, input, select, [onclick], [role="button"]').length;

                return {
                    has_animations: visuals.has_animations,
                    has_parallax: visuals.has_parallax,
                    carousels: visuals.carousels.slice(0, 5),
                    sticky_elements: visuals.sticky_elements.slice(0, 5),
                    interactive_count: visuals.interactive_count
                };
            }''')
            data['visual_elements'] = visual_elements

            # 21. REVIEWS (existing)
            reviews_text = await page.evaluate('''() => {
                const reviewSelectors = [
                    '.review', '.testimonial', '.feedback', '[class*="review"]',
                    '[class*="testimonial"]', '[data-testid*="review"]'
                ];
                let text = '';
                reviewSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el.innerText) text += el.innerText + ' ';
                    });
                });
                return text.replace(/\\s+/g, ' ').trim();
            }''')
            data['reviews_text'] = reviews_text[:20000]

            # 11. MAIN CONTENT (excluding footer now that we extract it separately)
            text_content = await page.evaluate('''() => {
                const excludeSelectors = [
                    'footer', 'script', 'style', 'noscript', 'iframe',
                    '.cookie-banner', '.cookie-notice', '[class*="cookie"]'
                ];

                const body = document.body.cloneNode(true);
                excludeSelectors.forEach(sel => {
                    body.querySelectorAll(sel).forEach(el => el.remove());
                });

                const mainSelectors = ['main', 'article', '.content', '.main-content', 'section'];
                let text = '';
                mainSelectors.forEach(sel => {
                    body.querySelectorAll(sel).forEach(el => {
                        if (el.innerText) text += el.innerText + ' ';
                    });
                });

                if (!text) {
                    text = body.innerText || '';
                }

                return text.replace(/\\s+/g, ' ').trim();
            }''')
            data['text'] = text_content[:100000]

            # 12. LOGOS (with prominence ranking)
            logos = await page.evaluate('''() => {
                const logoSelectors = [
                    'img[alt*="logo" i]', 'img[class*="logo" i]', 'img[src*="logo" i]',
                    '.logo img', 'header img', '.header img',
                    'svg[class*="logo" i]', 'svg[id*="logo" i]'
                ];
                const logos = [];
                const seen = new Set();

                logoSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(img => {
                        let src = img.src || img.dataset.src;

                        if (img.tagName === 'SVG') {
                            src = 'svg_' + (img.className || img.id);
                        }

                        if (src && !seen.has(src)) {
                            seen.add(src);
                            const rect = img.getBoundingClientRect();
                            const area = rect.width * rect.height;
                            const isInHeader = img.closest('header, .header, nav') !== null;
                            const prominence = area + (isInHeader ? 10000 : 0);

                            logos.push({
                                url: src,
                                alt: img.alt || '',
                                classes: img.className || '',
                                prominence: prominence,
                                width: rect.width,
                                height: rect.height
                            });
                        }
                    });
                });

                return logos.sort((a, b) => b.prominence - a.prominence);
            }''')
            data['logos'] = logos

            # 13. COLORS (by semantic usage)
            colors = await page.evaluate('''() => {
                const colorsByUsage = {
                    cta: new Set(),
                    background: new Set(),
                    text: new Set(),
                    other: new Set()
                };

                const hexPattern = /#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\\b/g;

                try {
                    document.querySelectorAll('button, .btn, .cta, a.button').forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bg = style.backgroundColor;
                        if (bg) colorsByUsage.cta.add(bg);
                    });

                    document.querySelectorAll('body, main, section, div').forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bg = style.backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)') colorsByUsage.background.add(bg);
                    });

                    Array.from(document.styleSheets).forEach(sheet => {
                        try {
                            Array.from(sheet.cssRules || []).forEach(rule => {
                                if (rule.cssText) {
                                    const matches = rule.cssText.match(hexPattern);
                                    if (matches) {
                                        matches.forEach(c => colorsByUsage.other.add(c.toUpperCase()));
                                    }
                                }
                            });
                        } catch(e) {}
                    });
                } catch(e) {}

                return {
                    cta: Array.from(colorsByUsage.cta).slice(0, 3),
                    background: Array.from(colorsByUsage.background).slice(0, 3),
                    text: Array.from(colorsByUsage.text).slice(0, 3),
                    other: Array.from(colorsByUsage.other).slice(0, 10)
                };
            }''')
            data['colors'] = colors

            # 14. IMAGES (excluding logos/icons)
            images = await page.evaluate('''() => {
                const images = [];
                const seen = new Set();
                document.querySelectorAll('main img, section img, article img, .hero img, .banner img').forEach(img => {
                    const src = img.src || img.dataset.src;
                    if (src && !seen.has(src) && src.startsWith('http')) {
                        const classes = (img.className || '').toLowerCase();
                        if (!classes.includes('logo') && !classes.includes('icon')) {
                            seen.add(src);
                            images.push({url: src, alt: img.alt || '', classes: classes});
                        }
                    }
                });
                return images.slice(0, 50);
            }''')
            data['images'] = images

            # 15. LINKS (for crawling)
            links = await page.evaluate('''() => {
                const links = [];
                const seen = new Set();
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.href;
                    if (href && !seen.has(href) && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('#')) {
                        seen.add(href);
                        links.push({url: href, text: (a.innerText || '').trim().slice(0, 100)});
                    }
                });
                return links;
            }''')
            data['links'] = links

        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")

        return data

    async def worker(self, worker_id: int, browser: Browser):
        """Async worker for crawling pages"""
        while not self.crawl_complete:
            try:
                try:
                    item = await asyncio.wait_for(self.pending_urls.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    if self.pending_urls.empty() and len(self.visited_urls) > 0:
                        break
                    continue

                url = item['url']
                depth = item['depth']

                async with self.results_lock:
                    if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
                        self.pending_urls.task_done()
                        continue
                    self.visited_urls.add(url)

                if urlparse(url).netloc != self.domain:
                    self.pending_urls.task_done()
                    continue

                try:
                    # PRODUCTION: Randomize viewport and user agent (anti-detection)
                    viewport = random.choice(self.VIEWPORTS)
                    user_agent = random.choice(self.USER_AGENTS)

                    page = await browser.new_page(user_agent=user_agent)
                    await page.set_viewport_size(viewport)

                    # PERFORMANCE: Block unnecessary resources (images, CSS, fonts)
                    await self.setup_request_interception(page)

                    # PRODUCTION: Use retry logic with exponential backoff
                    logger.info(f"Crawling {url} (depth: {depth})")
                    fetch_success = await self.fetch_page_with_retry(page, url, max_retries=3)

                    if not fetch_success:
                        self.metrics['pages_failed'] += 1
                        logger.error(f"Failed to fetch {url}")
                        await page.close()
                        self.pending_urls.task_done()
                        continue

                    # PRODUCTION: Check for anti-bot challenges
                    bot_status = await self.handle_bot_detection(page)

                    if bot_status == 'captcha':
                        self.metrics['pages_failed'] += 1
                        logger.warning(f"CAPTCHA detected on {url}, skipping")
                        await page.close()
                        self.pending_urls.task_done()
                        continue
                    elif bot_status == 'blocked':
                        self.metrics['pages_failed'] += 1
                        logger.warning(f"Access blocked on {url}, skipping")
                        await page.close()
                        self.pending_urls.task_done()
                        continue

                    # PRODUCTION: Add human-like behavior
                    await self.add_human_behavior(page)

                    # Wait for JS hydration
                    try:
                        await page.wait_for_function('''() => {
                            return document.readyState === 'complete' &&
                                   (!window.React || window.React.version) &&
                                   (!window.Vue || window.Vue.version);
                        }''', timeout=5000)
                    except:
                        pass

                    # Wait for navigation
                    try:
                        await page.wait_for_selector('nav, .nav, header', timeout=3000)
                    except:
                        pass

                    # Random delay (anti-detection)
                    await page.wait_for_timeout(random.randint(1000, 2000))

                    # Scroll to trigger lazy loading
                    await page.evaluate('''async () => {
                        for (let i = 0; i < 3; i++) {
                            window.scrollTo(0, document.body.scrollHeight * (i + 1) / 3);
                            await new Promise(r => setTimeout(r, 300));
                        }
                        window.scrollTo(0, 0);
                        await new Promise(r => setTimeout(r, 500));
                    }''')

                    page_data = await self.extract_comprehensive_data(page, url)

                    async with self.results_lock:
                        self.metrics['pages_crawled'] += 1
                        self.metrics['total_text_extracted'] += len(page_data.get('text', ''))
                        logger.info(f"✓ Extracted {len(page_data.get('text', ''))} chars from {url} | Type: {page_data.get('page_type', 'unknown')}")

                        self.collected_data['pages'].append(page_data)

                        # Aggregate content by type
                        if page_data['page_type'] != 'legal':
                            self.collected_data['text_content'] += f"\n\n=== PAGE: {url} ===\n{page_data['text']}\n"

                        if page_data['nav_text']:
                            self.collected_data['nav_text'] += f" {page_data['nav_text']}"

                        if page_data['reviews_text']:
                            self.collected_data['reviews_text'] += f"\n{page_data['reviews_text']}\n"

                        # Aggregate new comprehensive data
                        if page_data.get('hero_section'):
                            self.collected_data['hero_sections'].append(page_data['hero_section'])

                        if page_data.get('legal_footer'):
                            self.collected_data['legal_footer_content'] += f" {page_data['legal_footer']}"

                        if page_data.get('faqs'):
                            self.collected_data['faqs'].extend(page_data['faqs'])

                        if page_data.get('product_bullets'):
                            self.collected_data['product_bullets'].extend(page_data['product_bullets'])

                        if page_data.get('pricing'):
                            self.collected_data['pricing_data'].extend(page_data['pricing'])

                        if page_data.get('disclaimers'):
                            self.collected_data['disclaimers'].extend(page_data['disclaimers'])

                        if page_data.get('banners'):
                            self.collected_data['banners_carousels'].extend(page_data['banners'])

                        if page_data.get('social_embeds'):
                            # Merge social embed counts
                            for platform, count in page_data['social_embeds'].items():
                                if count > 0:
                                    existing = next((e for e in self.collected_data['social_embeds'] if e.get('platform') == platform), None)
                                    if existing:
                                        existing['count'] += count
                                    else:
                                        self.collected_data['social_embeds'].append({'platform': platform, 'count': count})

                        # Aggregate new page type data
                        if page_data.get('contact_data'):
                            self.collected_data['contact_data'].append(page_data['contact_data'])

                        if page_data.get('team_members'):
                            self.collected_data['team_members'].extend(page_data['team_members'])

                        if page_data.get('press_media'):
                            self.collected_data['press_media'].append(page_data['press_media'])

                        if page_data.get('case_studies'):
                            self.collected_data['case_studies'].extend(page_data['case_studies'])

                        if page_data.get('careers_data'):
                            self.collected_data['careers_data'].append(page_data['careers_data'])

                        if page_data.get('events_data'):
                            self.collected_data['events_data'].extend(page_data['events_data'])

                        if page_data.get('structured_data'):
                            self.collected_data['structured_data'].append(page_data['structured_data'])

                        if page_data.get('videos'):
                            self.collected_data['videos'].append(page_data['videos'])

                        if page_data.get('ctas'):
                            self.collected_data['ctas'].append(page_data['ctas'])

                        if page_data.get('general_forms'):
                            self.collected_data['general_forms'].extend(page_data['general_forms'])

                        if page_data.get('visual_elements'):
                            self.collected_data['visual_elements'].append(page_data['visual_elements'])

                        self.collected_data['logos'].extend(page_data['logos'])
                        self.collected_data['colors'].update(page_data.get('colors', {}).get('other', []))
                        self.collected_data['images'].extend(page_data['images'])

                        if self.progress_callback:
                            self.progress_callback(len(self.visited_urls), self.max_pages, url)

                    # Add child links to queue
                    if depth < self.max_depth:
                        for link in page_data['links']:
                            link_url = link['url'].split('#')[0].split('?')[0]
                            async with self.results_lock:
                                if link_url not in self.visited_urls and urlparse(link_url).netloc == self.domain:
                                    priority = self.get_link_priority(link_url, link['text'])
                                    await self.pending_urls.put({'url': link_url, 'depth': depth + 1, 'priority': priority})

                    await page.close()

                except Exception as e:
                    self.metrics['pages_failed'] += 1
                    logger.error(f"Worker {worker_id} error crawling {url}: {e}")

                self.pending_urls.task_done()

                async with self.results_lock:
                    if len(self.visited_urls) >= self.max_pages:
                        self.crawl_complete = True
                        logger.info(f"Max pages ({self.max_pages}) reached, stopping crawl")
                        break

            except Exception as e:
                logger.error(f"Worker {worker_id} critical error: {e}")

    async def crawl(self, progress_callback=None) -> Dict:
        """Main crawl method"""
        self.metrics['crawl_start_time'] = time.time()
        logger.info(f"🚀 Starting crawl of {self.base_url} | Max pages: {self.max_pages} | Max depth: {self.max_depth} | Workers: {self.concurrency}")

        self.progress_callback = progress_callback
        self.pending_urls = asyncio.Queue()
        await self.pending_urls.put({'url': self.base_url, 'depth': 0, 'priority': 100})

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            workers = [asyncio.create_task(self.worker(i, browser)) for i in range(self.concurrency)]
            try:
                await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=300)
            except asyncio.TimeoutError:
                logger.warning("Crawl timed out after 5 minutes")
                self.crawl_complete = True
            await browser.close()

        self.metrics['crawl_end_time'] = time.time()
        self.metrics['crawl_duration'] = self.metrics['crawl_end_time'] - self.metrics['crawl_start_time']

        logger.info(f"✓ Crawl completed | Pages: {self.metrics['pages_crawled']} | Failed: {self.metrics['pages_failed']} | " +
                   f"Text: {self.metrics['total_text_extracted']:,} chars | Duration: {self.metrics['crawl_duration']:.1f}s | " +
                   f"Retries: {self.metrics['retry_count']} | CAPTCHA: {self.metrics['captcha_count']} | Blocked: {self.metrics['blocked_count']}")

        return self.process_collected_data()

    def process_collected_data(self) -> Dict:
        """Process and return collected data with all comprehensive signals"""
        # VALIDATION: Clean all text content
        cleaned_text = self.clean_extracted_text(self.collected_data['text_content'])
        cleaned_nav_text = self.clean_extracted_text(self.collected_data['nav_text'])
        cleaned_reviews = self.clean_extracted_text(self.collected_data['reviews_text'])

        # Deduplicate logos
        seen_logos = set()
        unique_logos = []
        for logo in sorted(self.collected_data['logos'], key=lambda x: x.get('prominence', 0), reverse=True):
            if logo['url'] not in seen_logos:
                seen_logos.add(logo['url'])
                logo_type = 'dark' if any(x in (logo.get('classes', '') + logo.get('alt', '')).lower() for x in ['dark', 'white', 'inverse', 'light']) else 'light'
                unique_logos.append({**logo, 'type': logo_type})

        # Deduplicate images
        seen_images = set()
        unique_images = []
        for img in self.collected_data['images']:
            if img['url'] not in seen_images:
                seen_images.add(img['url'])
                unique_images.append(img)

        # Process colors
        colors = list(self.collected_data['colors'])[:10]
        color_list = []
        color_types = ['primary', 'secondary', 'accent', 'functional', 'supporting']
        for i, color in enumerate(colors):
            if len(color) == 4:
                color = '#' + ''.join([c*2 for c in color[1:]])
            color_list.append({'hex': color.upper(), 'type': color_types[min(i, 4)]})

        # Deduplicate FAQs
        unique_faqs = []
        seen_faq_q = set()
        for faq in self.collected_data['faqs']:
            q = faq.get('question', '')
            if q and q not in seen_faq_q:
                seen_faq_q.add(q)
                unique_faqs.append(faq)

        # Deduplicate product bullets
        unique_bullets = list(set(self.collected_data['product_bullets']))[:50]

        # Deduplicate disclaimers
        unique_disclaimers = list(set(self.collected_data['disclaimers']))[:20]

        # Deduplicate team members
        unique_team = []
        seen_team_names = set()
        for member in self.collected_data['team_members']:
            name = member.get('name', '')
            if name and name not in seen_team_names:
                seen_team_names.add(name)
                unique_team.append(member)

        # Deduplicate events
        unique_events = []
        seen_event_titles = set()
        for event in self.collected_data['events_data']:
            title = event.get('title', '')
            if title and title not in seen_event_titles:
                seen_event_titles.add(title)
                unique_events.append(event)

        # Merge press/media data
        all_press_items = []
        all_awards = []
        for press_data in self.collected_data['press_media']:
            if isinstance(press_data, dict):
                all_press_items.extend(press_data.get('press_items', []))
                all_awards.extend(press_data.get('awards', []))
        unique_press = {'press_items': all_press_items[:20], 'awards': list(set(all_awards))[:15]}

        # Merge contact data
        all_contact_forms = []
        all_emails = set()
        all_phones = set()
        for contact in self.collected_data['contact_data']:
            if isinstance(contact, dict):
                all_contact_forms.extend(contact.get('forms', []))
                all_emails.update(contact.get('contact_info', {}).get('emails', []))
                all_phones.update(contact.get('contact_info', {}).get('phones', []))
        merged_contact = {
            'forms': all_contact_forms[:5],
            'contact_info': {
                'emails': list(all_emails)[:5],
                'phones': list(all_phones)[:5]
            }
        }

        # Merge careers data
        all_jobs = []
        all_culture = []
        for career in self.collected_data['careers_data']:
            if isinstance(career, dict):
                all_jobs.extend(career.get('job_listings', []))
                all_culture.extend(career.get('culture_sections', []))
        merged_careers = {'job_listings': all_jobs[:25], 'culture_sections': all_culture[:10]}

        # Merge structured data
        all_jsonld = []
        merged_og = {}
        merged_twitter = {}
        merged_meta = {}
        merged_schema = {}
        for sd in self.collected_data['structured_data']:
            if isinstance(sd, dict):
                all_jsonld.extend(sd.get('jsonLd', []))
                # Merge OG/Twitter/Meta (prioritize first found values)
                for key, value in sd.get('openGraph', {}).items():
                    if key not in merged_og:
                        merged_og[key] = value
                for key, value in sd.get('twitter', {}).items():
                    if key not in merged_twitter:
                        merged_twitter[key] = value
                for key, value in sd.get('metaTags', {}).items():
                    if key not in merged_meta:
                        merged_meta[key] = value
                # Merge schema.org
                for schema_type, schema_data in sd.get('schemaOrg', {}).items():
                    if schema_type not in merged_schema:
                        merged_schema[schema_type] = schema_data

        merged_structured = {
            'jsonLd': all_jsonld[:10],
            'openGraph': merged_og,
            'twitter': merged_twitter,
            'metaTags': merged_meta,
            'schemaOrg': merged_schema
        }

        # Merge videos
        all_youtube = []
        all_vimeo = []
        all_native = []
        total_video_count = 0
        for video_data in self.collected_data['videos']:
            if isinstance(video_data, dict):
                all_youtube.extend(video_data.get('youtube', []))
                all_vimeo.extend(video_data.get('vimeo', []))
                all_native.extend(video_data.get('native', []))
                total_video_count += video_data.get('count', 0)
        merged_videos = {
            'youtube': all_youtube[:10],
            'vimeo': all_vimeo[:10],
            'native': all_native[:10],
            'total_count': total_video_count
        }

        # Merge CTAs
        all_primary_ctas = []
        all_secondary_ctas = []
        all_cta_text = set()
        for cta_data in self.collected_data['ctas']:
            if isinstance(cta_data, dict):
                all_primary_ctas.extend(cta_data.get('primary', []))
                all_secondary_ctas.extend(cta_data.get('secondary', []))
                all_cta_text.update(cta_data.get('all_text', []))
        merged_ctas = {
            'primary': all_primary_ctas[:20],
            'secondary': all_secondary_ctas[:20],
            'all_text': list(all_cta_text)[:40]
        }

        # Merge visual elements
        has_any_animations = any(v.get('has_animations', False) for v in self.collected_data['visual_elements'] if isinstance(v, dict))
        has_any_parallax = any(v.get('has_parallax', False) for v in self.collected_data['visual_elements'] if isinstance(v, dict))
        all_carousels = []
        all_sticky = []
        for visual_data in self.collected_data['visual_elements']:
            if isinstance(visual_data, dict):
                all_carousels.extend(visual_data.get('carousels', []))
                all_sticky.extend(visual_data.get('sticky_elements', []))
        merged_visuals = {
            'has_animations': has_any_animations,
            'has_parallax': has_any_parallax,
            'carousels': all_carousels[:10],
            'sticky_elements': all_sticky[:10]
        }

        # METRICS: Log data quality summary
        logger.info(f"📊 Data Summary | Unique FAQs: {len(unique_faqs)} | Bullets: {len(unique_bullets)} | " +
                   f"Team: {len(unique_team)} | Events: {len(unique_events)} | Logos: {len(unique_logos)} | Colors: {len(color_list)}")

        return {
            'success': True,
            'text': cleaned_text[:2000000],  # VALIDATION: Using cleaned text
            'nav_text': cleaned_nav_text[:50000],  # VALIDATION: Using cleaned text
            'reviews_text': cleaned_reviews[:100000],  # VALIDATION: Using cleaned text
            'hero_sections': self.collected_data['hero_sections'][:10],
            'about_us_content': self.collected_data['about_us_content'][:50000],
            'legal_footer_content': self.collected_data['legal_footer_content'][:50000],
            'faqs': unique_faqs[:30],
            'product_bullets': unique_bullets,
            'pricing_data': self.collected_data['pricing_data'][:30],
            'disclaimers': unique_disclaimers,
            'banners_carousels': self.collected_data['banners_carousels'][:15],
            'social_embeds': self.collected_data['social_embeds'],
            'contact_data': merged_contact,  # NEW
            'team_members': unique_team[:20],  # NEW
            'press_media': unique_press,  # NEW
            'case_studies': self.collected_data['case_studies'][:15],  # NEW
            'careers_data': merged_careers,  # NEW
            'events_data': unique_events[:15],  # NEW
            'structured_data': merged_structured,  # NEW
            'videos': merged_videos,  # NEW
            'ctas': merged_ctas,  # NEW
            'general_forms': self.collected_data['general_forms'][:15],  # NEW
            'visual_elements': merged_visuals,  # NEW
            'char_count': len(self.collected_data['text_content']),
            'pages_crawled': len(self.visited_urls),
            'logos': {
                'light': next((l['url'] for l in unique_logos if l['type'] == 'light'), None),
                'dark': next((l['url'] for l in unique_logos if l['type'] == 'dark'), None),
                'all': unique_logos[:20]
            },
            'colors': color_list,
            'images': unique_images[:100],
            'ads': [img for img in unique_images if any(x in img.get('classes', '').lower() for x in ['banner', 'promo', 'campaign', 'offer'])][:20],
            # METRICS: Include crawl metrics in return data
            'metrics': {
                'pages_crawled': self.metrics['pages_crawled'],
                'pages_failed': self.metrics['pages_failed'],
                'total_text_extracted': self.metrics['total_text_extracted'],
                'retry_count': self.metrics['retry_count'],
                'captcha_count': self.metrics['captcha_count'],
                'blocked_count': self.metrics['blocked_count'],
                'crawl_duration': self.metrics['crawl_duration'],
                'avg_page_load_time': self.metrics['crawl_duration'] / max(self.metrics['pages_crawled'], 1)
            }
        }


def run_comprehensive_crawl(url: str, max_depth: int, max_pages: int, progress_placeholder, concurrency: int = 5) -> Dict:
    """Run comprehensive crawler with all signal extraction"""
    def progress_callback(current, total, current_url):
        progress_placeholder.progress(current / total, f"🚀 Crawled {current}/{total} pages | {current_url[:40]}...")

    crawler = ComprehensiveWebCrawler(url, max_depth=max_depth, max_pages=max_pages, concurrency=concurrency)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(crawler.crawl(progress_callback))
    finally:
        loop.close()

    return result
