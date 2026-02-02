"""
Enhanced Fallback Scraper
Extracts more brand signals without requiring browser automation
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Optional
from collections import Counter

def extract_colors_from_css(css_text: str) -> List[str]:
    """Extract color codes from CSS"""
    colors = []
    # Hex colors
    colors.extend(re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b', css_text))
    # RGB colors
    rgb_matches = re.findall(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', css_text)
    for r, g, b in rgb_matches:
        hex_color = f"{int(r):02x}{int(g):02x}{int(b):02x}"
        colors.append(hex_color)
    return colors

def extract_brand_intelligence(url: str, html_content: str) -> Dict:
    """Extract comprehensive brand intelligence from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    intelligence = {
        'logos': {'light': None, 'dark': None, 'all': []},
        'colors': [],
        'fonts': [],
        'social_links': {},
        'contact_info': {},
        'nav_structure': [],
        'cta_buttons': [],
    }

    # 1. EXTRACT LOGOS
    logo_candidates = []

    # Common logo selectors
    logo_patterns = [
        {'tag': 'img', 'attrs': {'class': re.compile(r'logo', re.I)}},
        {'tag': 'img', 'attrs': {'alt': re.compile(r'logo', re.I)}},
        {'tag': 'img', 'attrs': {'id': re.compile(r'logo', re.I)}},
        {'tag': 'a', 'attrs': {'class': re.compile(r'logo', re.I)}},
    ]

    for pattern in logo_patterns:
        elements = soup.find_all(pattern['tag'], attrs=pattern['attrs'])
        for elem in elements:
            img = elem if elem.name == 'img' else elem.find('img')
            if img and img.get('src'):
                logo_url = img.get('src')
                if logo_url.startswith('//'):
                    logo_url = 'https:' + logo_url
                elif not logo_url.startswith('http'):
                    logo_url = urljoin(base_url, logo_url)

                logo_type = 'dark' if any(x in logo_url.lower() for x in ['dark', 'white', 'inverse']) else 'light'

                logo_candidates.append({
                    'url': logo_url,
                    'alt': img.get('alt', ''),
                    'type': logo_type,
                    'prominence': 10 if 'header' in str(elem.parent) else 5
                })

    # Sort by prominence and deduplicate
    seen_urls = set()
    unique_logos = []
    for logo in sorted(logo_candidates, key=lambda x: x['prominence'], reverse=True):
        if logo['url'] not in seen_urls:
            seen_urls.add(logo['url'])
            unique_logos.append(logo)

    intelligence['logos']['all'] = unique_logos[:10]
    intelligence['logos']['light'] = next((l['url'] for l in unique_logos if l['type'] == 'light'), None)
    intelligence['logos']['dark'] = next((l['url'] for l in unique_logos if l['type'] == 'dark'), None)

    # 2. EXTRACT COLORS
    all_colors = []

    # From inline styles
    inline_styles = soup.find_all(style=True)
    for elem in inline_styles:
        style = elem.get('style', '')
        all_colors.extend(extract_colors_from_css(style))

    # From style tags
    style_tags = soup.find_all('style')
    for style in style_tags:
        all_colors.extend(extract_colors_from_css(style.string or ''))

    # Count color frequency and get top colors
    color_counts = Counter(all_colors)
    top_colors = []
    for color, count in color_counts.most_common(20):
        # Skip very light or very dark (likely backgrounds)
        if len(color) == 6:
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            brightness = (r + g + b) / 3
            if 30 < brightness < 225:  # Skip pure white/black
                top_colors.append({
                    'hex': f'#{color}',
                    'rgb': f'rgb({r}, {g}, {b})',
                    'frequency': count
                })

    intelligence['colors'] = top_colors[:10]

    # 3. EXTRACT FONTS
    font_families = set()

    # From inline styles
    for elem in inline_styles:
        style = elem.get('style', '')
        fonts = re.findall(r'font-family:\s*([^;]+)', style, re.I)
        font_families.update(fonts)

    # From style tags
    for style in style_tags:
        fonts = re.findall(r'font-family:\s*([^;]+)', style.string or '', re.I)
        font_families.update(fonts)

    intelligence['fonts'] = [{'name': font.strip(), 'usage': 'detected'} for font in list(font_families)[:10]]

    # 4. EXTRACT SOCIAL LINKS
    social_platforms = {
        'facebook': r'facebook\.com',
        'instagram': r'instagram\.com',
        'twitter': r'twitter\.com|x\.com',
        'linkedin': r'linkedin\.com',
        'youtube': r'youtube\.com',
        'tiktok': r'tiktok\.com',
        'pinterest': r'pinterest\.com',
    }

    for platform, pattern in social_platforms.items():
        links = soup.find_all('a', href=re.compile(pattern, re.I))
        if links:
            intelligence['social_links'][platform] = links[0].get('href')

    # 5. EXTRACT CONTACT INFO
    # Email
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())
    if emails:
        intelligence['contact_info']['email'] = emails[0]

    # Phone
    phones = re.findall(r'\+?\d[\d\s\-\(\)]{8,}\d', soup.get_text())
    if phones:
        intelligence['contact_info']['phone'] = phones[0].strip()

    # 6. EXTRACT NAVIGATION
    nav_elements = soup.find_all(['nav', 'header'])
    for nav in nav_elements[:3]:
        links = nav.find_all('a')
        for link in links[:10]:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and len(text) > 1 and len(text) < 50:
                intelligence['nav_structure'].append({
                    'text': text,
                    'url': urljoin(base_url, href) if href else None
                })

    # 7. EXTRACT CTA BUTTONS
    cta_patterns = ['button', 'btn', 'cta']
    buttons = []

    for pattern in cta_patterns:
        elements = soup.find_all(['a', 'button'], class_=re.compile(pattern, re.I))
        for elem in elements:
            text = elem.get_text(strip=True)
            if text and len(text) < 50:
                buttons.append({
                    'text': text,
                    'url': urljoin(base_url, elem.get('href', '')) if elem.name == 'a' else None,
                    'style': elem.get('class', [])
                })

    intelligence['cta_buttons'] = buttons[:20]

    return intelligence

def enhanced_scrape(url: str) -> Dict:
    """
    Enhanced scraping with brand intelligence extraction
    Returns comprehensive data without browser automation
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)

        if response.status_code != 200:
            return {'success': False, 'error': f'HTTP {response.status_code}'}

        # Extract brand intelligence
        intelligence = extract_brand_intelligence(url, response.text)

        return {
            'success': True,
            'url': url,
            **intelligence
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
