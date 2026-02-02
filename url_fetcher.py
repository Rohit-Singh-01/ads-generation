"""
Universal E-commerce URL Fetcher
Supports: Shopify, WooCommerce, Magento, and Generic sites
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Tuple

def format_price_with_commas(price_str):
    """Format price with proper commas"""
    try:
        price_str = str(price_str).strip()
        numbers = re.findall(r'[\d,]+\.?\d*', price_str)
        if not numbers:
            return price_str

        if price_str.startswith('Rs'):
            currency = 'Rs.'
        elif price_str.startswith('₹'):
            currency = '₹'
        elif '$' in price_str:
            currency = '$'
        elif '€' in price_str:
            currency = '€'
        elif '£' in price_str:
            currency = '£'
        else:
            currency = 'Rs.'

        number_part = numbers[0].replace(',', '').replace(' ', '')

        try:
            amount = float(number_part)
            formatted = f"{amount:,.2f}"
            return f"{currency} {formatted}"
        except:
            return price_str
    except:
        return price_str

def fetch_products_from_url(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Universal product scraper - works with ANY e-commerce site
    Supports: Shopify, WooCommerce, Magento, and generic sites

    Returns: (products_list, error_message)
    """
    try:
        # Detect platform and route to appropriate scraper
        if '/collections/' in url or 'myshopify.com' in url:
            return fetch_shopify_products(url)
        elif 'product-category' in url or '/shop/' in url:
            return fetch_woocommerce_products(url)
        else:
            # Generic scraper for any site
            return fetch_generic_ecommerce(url)
    except Exception as e:
        return None, f"Error fetching products: {str(e)}"

def fetch_shopify_products(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Shopify-specific scraper (JSON API + HTML fallback)"""
    try:
        parsed_url = url.split('?')[0]

        # Try JSON API first (Shopify has a .json endpoint)
        if '/collections/' in parsed_url:
            json_url = parsed_url + '.json'

            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(json_url, timeout=30, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    products = []

                    for product in data.get('products', []):
                        variants = product.get('variants', [])
                        if not variants:
                            continue

                        price = variants[0].get('price', '0')
                        price_formatted = format_price_with_commas(f"Rs. {price}")

                        images = product.get('images', [])
                        if not images:
                            continue

                        image_url = images[0].get('src', '')
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif not image_url.startswith('http'):
                            image_url = 'https:' + image_url

                        products.append({
                            'name': product.get('title', 'Unknown Product'),
                            'price': price_formatted,
                            'image_url': image_url,
                            'handle': product.get('handle', ''),
                            'source': 'Shopify JSON'
                        })

                    if products:
                        return products, None
            except:
                pass  # Fall through to HTML scraping

        # Fallback to HTML scraping
        return fetch_shopify_html(url)

    except Exception as e:
        return None, f"Shopify error: {str(e)}"

def fetch_shopify_html(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Shopify HTML scraper"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=30, headers=headers)

        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        products = []

        # Common Shopify selectors
        product_cards = soup.find_all(
            ['div', 'article', 'li'],
            class_=re.compile(r'product-item|product-card|grid-product|product__item', re.I)
        )

        if not product_cards:
            product_cards = soup.find_all(['div', 'article'], attrs={'data-product': True})

        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        for card in product_cards[:50]:  # Limit to first 50
            try:
                # Extract name
                name_elem = card.find(['h3', 'h2', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not name_elem:
                    name_elem = card.find('a')
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"

                if len(name) < 3:
                    continue

                # Extract price
                price_elem = card.find(['span', 'div', 'p'], class_=re.compile(r'price', re.I))
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = format_price_with_commas(price_text)
                else:
                    price = "Rs. 0.00"

                # Extract image
                img_elem = card.find('img')
                if img_elem:
                    image_url = (
                        img_elem.get('src') or
                        img_elem.get('data-src') or
                        img_elem.get('data-srcset', '').split(',')[0].split(' ')[0]
                    )

                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif not image_url.startswith('http'):
                        image_url = urljoin(base_url, image_url)
                else:
                    continue

                products.append({
                    'name': name,
                    'price': price,
                    'image_url': image_url,
                    'handle': name.lower().replace(' ', '-'),
                    'source': 'Shopify HTML'
                })
            except:
                continue

        if products:
            return products, None
        return None, "No products found in Shopify HTML"

    except Exception as e:
        return None, f"Shopify HTML error: {str(e)}"

def fetch_woocommerce_products(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """WooCommerce (WordPress) scraper"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=30, headers=headers)

        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        products = []

        # WooCommerce selectors
        product_cards = soup.find_all(
            ['li', 'div'],
            class_=re.compile(r'product(?!-)|woocommerce-loop-product', re.I)
        )

        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        for card in product_cards[:50]:
            try:
                # Extract name
                name_elem = card.find(
                    ['h2', 'h3', 'a'],
                    class_=re.compile(r'product.*title|woocommerce-loop-product__title', re.I)
                )
                if not name_elem:
                    name_elem = card.find('a')
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"

                if len(name) < 3:
                    continue

                # Extract price
                price_elem = card.find(['span'], class_=re.compile(r'price|amount', re.I))
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = format_price_with_commas(price_text)
                else:
                    price = "Rs. 0.00"

                # Extract image
                img_elem = card.find('img')
                if img_elem:
                    image_url = (
                        img_elem.get('src') or
                        img_elem.get('data-src') or
                        img_elem.get('data-lazy-src')
                    )

                    if image_url:
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif not image_url.startswith('http'):
                            image_url = urljoin(base_url, image_url)
                    else:
                        continue
                else:
                    continue

                products.append({
                    'name': name,
                    'price': price,
                    'image_url': image_url,
                    'handle': name.lower().replace(' ', '-'),
                    'source': 'WooCommerce'
                })
            except:
                continue

        if products:
            return products, None
        return None, "No WooCommerce products found"

    except Exception as e:
        return None, f"WooCommerce error: {str(e)}"

def fetch_generic_ecommerce(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Generic e-commerce scraper for any website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)

        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        products = []

        # Try multiple common patterns
        product_containers = []

        patterns = [
            {'tag': ['div', 'article', 'li'], 'class': re.compile(r'product|item', re.I)},
            {'tag': ['div'], 'attrs': {'itemtype': re.compile(r'schema.org/Product', re.I)}},
            {'tag': ['div', 'article'], 'attrs': {'data-product-id': True}},
        ]

        for pattern in patterns:
            found = soup.find_all(
                pattern['tag'],
                class_=pattern.get('class'),
                attrs=pattern.get('attrs')
            )
            if found and len(found) > 2:
                product_containers = found
                break

        # If no containers found, try finding divs with images and text
        if not product_containers:
            all_divs = soup.find_all('div', recursive=True)
            product_containers = [
                div for div in all_divs
                if div.find('img') and len(div.get_text(strip=True)) > 10
            ]

        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        for container in product_containers[:50]:
            try:
                # Extract name
                name = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'a']:
                    name_elem = container.find(tag)
                    if name_elem:
                        name_text = name_elem.get_text(strip=True)
                        if 3 < len(name_text) < 200:
                            name = name_text
                            break

                if not name:
                    continue

                # Extract price
                price = "Rs. 0.00"
                price_patterns = [
                    r'[\$₹€£]\s*[\d,]+\.?\d*',
                    r'Rs\.?\s*[\d,]+\.?\d*',
                    r'INR\s*[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*\s*[\$₹€£]'
                ]

                container_text = container.get_text()
                for pattern in price_patterns:
                    match = re.search(pattern, container_text)
                    if match:
                        price = format_price_with_commas(match.group())
                        break

                # Extract image
                img_elem = container.find('img')
                if img_elem:
                    image_url = (
                        img_elem.get('src') or
                        img_elem.get('data-src') or
                        img_elem.get('data-lazy-src') or
                        img_elem.get('data-original')
                    )

                    if image_url:
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = urljoin(base_url, image_url)
                        elif not image_url.startswith('http'):
                            image_url = urljoin(base_url, image_url)
                    else:
                        continue
                else:
                    continue

                products.append({
                    'name': name,
                    'price': price,
                    'image_url': image_url,
                    'handle': name.lower().replace(' ', '-')[:50],
                    'source': 'Generic'
                })
            except:
                continue

        # Remove duplicates based on name
        seen_names = set()
        unique_products = []
        for p in products:
            if p['name'] not in seen_names:
                seen_names.add(p['name'])
                unique_products.append(p)

        if unique_products:
            return unique_products, None

        return None, "No products found. Try a different URL or use manual upload."

    except Exception as e:
        return None, f"Generic scraper error: {str(e)}"
