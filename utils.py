"""
Utility Functions for Brand Extractor
Handles: caching, image processing, file operations
"""

import json
import re
import io
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import requests
import streamlit as st


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CACHE SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CACHE_DIR = Path("brand_cache")
CACHE_DIR.mkdir(exist_ok=True)

AD_CACHE_DIR = Path("ad_cache")
AD_CACHE_DIR.mkdir(exist_ok=True)


def save_brand_to_cache(brand_name: str, brand_data: Dict) -> bool:
    """Save brand data to cache file"""
    filename = CACHE_DIR / f"{brand_name.lower().replace(' ', '_')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(brand_data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        return False


def load_brand_from_cache(brand_name: str) -> Optional[Dict]:
    """Load brand data from cache file"""
    filename = CACHE_DIR / f"{brand_name.lower().replace(' ', '_')}.json"
    if filename.exists():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def list_cached_brands() -> List[str]:
    """List all cached brand names"""
    cached = []
    for file in CACHE_DIR.glob("*.json"):
        cached.append(file.stem.replace('_', ' ').title())
    return sorted(cached)


def delete_brand_cache(brand_name: str) -> bool:
    """Delete brand from cache"""
    filename = CACHE_DIR / f"{brand_name.lower().replace(' ', '_')}.json"
    if filename.exists():
        filename.unlink()
        return True
    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AD CACHE SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_ad_to_cache(ad_name: str, ad_data: Dict, image: Image.Image) -> bool:
    """
    Save generated ad to cache
    Args:
        ad_name: Name for the cached ad (e.g., "BrandName_Square_2024-01-01")
        ad_data: Metadata dict with prompt, settings, timestamp, etc.
        image: PIL Image object
    Returns:
        True if saved successfully
    """
    try:
        # Create unique cache ID
        from datetime import datetime
        cache_id = f"{ad_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        safe_id = cache_id.lower().replace(' ', '_').replace('(', '').replace(')', '')

        # Save image
        img_path = AD_CACHE_DIR / f"{safe_id}.png"
        image.save(img_path, format='PNG', quality=95)

        # Save metadata
        meta_path = AD_CACHE_DIR / f"{safe_id}.json"
        ad_data['cache_id'] = safe_id
        ad_data['cached_at'] = datetime.now().isoformat()
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(ad_data, f, indent=2, ensure_ascii=False, default=str)

        return True
    except Exception as e:
        if st:
            st.error(f"Failed to cache ad: {str(e)}")
        return False


def load_ad_from_cache(cache_id: str) -> Optional[Dict]:
    """
    Load cached ad with its image and metadata
    Returns: Dict with 'image' (PIL Image) and 'metadata' (Dict)
    """
    try:
        img_path = AD_CACHE_DIR / f"{cache_id}.png"
        meta_path = AD_CACHE_DIR / f"{cache_id}.json"

        if not img_path.exists() or not meta_path.exists():
            return None

        # Load image
        image = Image.open(img_path)

        # Load metadata
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        return {
            'image': image,
            'metadata': metadata
        }
    except Exception as e:
        return None


def list_cached_ads() -> List[Dict]:
    """
    List all cached ads with their metadata
    Returns: List of dicts with cache_id, brand_name, size, timestamp
    """
    cached = []
    for meta_file in AD_CACHE_DIR.glob("*.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Extract key info
            cached.append({
                'cache_id': metadata.get('cache_id', meta_file.stem),
                'brand_name': metadata.get('brand_name', 'Unknown'),
                'size': metadata.get('size', 'Unknown'),
                'cached_at': metadata.get('cached_at', 'Unknown'),
                'prompt_preview': metadata.get('prompt', '')[:100] + '...' if metadata.get('prompt') else ''
            })
        except:
            continue

    # Sort by timestamp (newest first)
    return sorted(cached, key=lambda x: x['cached_at'], reverse=True)


def delete_ad_cache(cache_id: str) -> bool:
    """Delete cached ad (both image and metadata)"""
    try:
        img_path = AD_CACHE_DIR / f"{cache_id}.png"
        meta_path = AD_CACHE_DIR / f"{cache_id}.json"

        if img_path.exists():
            img_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

        return True
    except Exception as e:
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGE PROCESSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def safe_open_image(file_obj) -> Image.Image:
    """Safely open image from various file object types"""
    errors = []

    # Try getvalue() method
    try:
        if hasattr(file_obj, 'getvalue'):
            file_obj.seek(0)
            data = file_obj.getvalue()
            return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception as e:
        errors.append(f"getvalue: {e}")

    # Try read() method
    try:
        if hasattr(file_obj, 'read'):
            file_obj.seek(0)
            data = file_obj.read()
            file_obj.seek(0)
            return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception as e:
        errors.append(f"read: {e}")

    # Try getbuffer() method
    try:
        if hasattr(file_obj, 'getbuffer'):
            data = file_obj.getbuffer()
            return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception as e:
        errors.append(f"getbuffer: {e}")

    # Try direct path
    try:
        if isinstance(file_obj, (str, Path)):
            return Image.open(file_obj).convert('RGB')
    except Exception as e:
        errors.append(f"direct: {e}")

    # Try bytes
    try:
        if isinstance(file_obj, bytes):
            return Image.open(io.BytesIO(file_obj)).convert('RGB')
    except Exception as e:
        errors.append(f"bytes: {e}")

    # Try nested file attribute
    try:
        if hasattr(file_obj, 'file'):
            file_obj.file.seek(0)
            data = file_obj.file.read()
            return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception as e:
        errors.append(f"file.file: {e}")

    name = getattr(file_obj, 'name', 'unknown')
    raise Exception(f"Cannot open image '{name}': {'; '.join(errors)}")


def remove_background(logo_img: Image.Image) -> Image.Image:
    """Remove background from logo with intelligent detection"""
    if logo_img.mode != 'RGB':
        logo_img = logo_img.convert('RGB')

    logo_rgba = logo_img.convert('RGBA')
    data = np.array(logo_rgba)
    h, w = data.shape[:2]

    # Sample corners to detect background color
    corners = [
        data[5:15, 5:15, :3].mean(axis=(0,1)),
        data[5:15, w-15:w-5, :3].mean(axis=(0,1)),
        data[h-15:h-5, 5:15, :3].mean(axis=(0,1)),
        data[h-15:h-5, w-15:w-5, :3].mean(axis=(0,1))
    ]
    bg_color = np.mean(corners, axis=0)

    # Detect if background is black, white, or colored
    is_black = bg_color.mean() < 100
    is_white = bg_color.mean() > 150

    if is_black:
        mask = (data[:, :, 0] < 80) & (data[:, :, 1] < 80) & (data[:, :, 2] < 80)
        data[mask, 3] = 0
    elif is_white:
        mask = (data[:, :, 0] > 175) & (data[:, :, 1] > 175) & (data[:, :, 2] > 175)
        data[mask, 3] = 0
    else:
        tolerance = 50
        mask = (
            (np.abs(data[:, :, 0] - bg_color[0]) < tolerance) &
            (np.abs(data[:, :, 1] - bg_color[1]) < tolerance) &
            (np.abs(data[:, :, 2] - bg_color[2]) < tolerance)
        )
        data[mask, 3] = 0

    return Image.fromarray(data, 'RGBA')


def enhance_product_image(product_image: Image.Image) -> Image.Image:
    """Enhance product image for better AI generation"""
    img = product_image.copy()

    # Convert RGBA to RGB
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.5)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # Ensure minimum size
    min_size = 1024
    if img.width < min_size or img.height < min_size:
        scale_factor = min_size / min(img.width, img.height)
        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Apply unsharp mask
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    # Enhance color
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.15)

    return img


def download_image_from_url(image_url: str, base_url: str = "") -> Optional[Image.Image]:
    """
    Download image from URL with error handling and URL cleaning

    Args:
        image_url: Full or relative image URL
        base_url: Base URL for resolving relative paths

    Returns:
        PIL Image or None if failed
    """
    try:
        # Handle relative URLs
        if base_url and not image_url.startswith(('http://', 'https://', '//')):
            from urllib.parse import urljoin
            image_url = urljoin(base_url, image_url)

        # Handle protocol-relative URLs (starting with //)
        if image_url.startswith('//'):
            image_url = 'https:' + image_url

        # Validate URL format - silently skip invalid
        if not image_url.startswith(('http://', 'https://')):
            return None

        # Check if URL looks incomplete (common issue) - silently skip
        url_filename = image_url.split('/')[-1].lower()
        has_extension = any(ext in url_filename for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'])
        has_image_indicator = any(word in image_url.lower() for word in ['image', 'photo', 'picture', 'product', 'media', 'cdn', 'assets'])

        if len(url_filename) < 3 or (not has_extension and not has_image_indicator):
            # Silently skip invalid URLs - don't clutter UI with warnings
            return None

        # Clean URL - remove width placeholders
        clean_url = re.sub(r'[&?]width=\{width\}', '', image_url)
        clean_url = re.sub(r'\{width\}', '1200', clean_url)

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(clean_url, timeout=30, headers=headers)

        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type:
                if st:
                    st.warning(f"URL returned HTML instead of an image: {clean_url[:100]}")
                return None

            # Verify we have content
            if not response.content or len(response.content) < 100:
                if st:
                    st.warning(f"URL returned empty or invalid content: {clean_url[:100]}")
                return None

            # Try to open the image
            try:
                img_buffer = io.BytesIO(response.content)

                # Check if content looks like an image by checking first few bytes
                img_buffer.seek(0)
                header = img_buffer.read(16)
                img_buffer.seek(0)

                # Common image format signatures
                is_likely_image = (
                    header[:2] == b'\xff\xd8' or  # JPEG
                    header[:4] == b'\x89PNG' or    # PNG
                    header[:6] == b'GIF87a' or header[:6] == b'GIF89a' or  # GIF
                    header[:2] == b'BM' or         # BMP
                    header[:4] in (b'II*\x00', b'MM\x00*') or  # TIFF
                    header[:4] == b'RIFF'          # WebP
                )

                if not is_likely_image:
                    if st:
                        st.warning(f"URL content doesn't appear to be a valid image: {clean_url[:80]}")
                    return None

                img = Image.open(img_buffer)
                img.verify()  # Verify it's a valid image

                # Re-open after verify (verify closes the file)
                img_buffer.seek(0)
                img = Image.open(img_buffer)
                return img.convert('RGB')
            except Exception as img_error:
                if st:
                    st.warning(f"Invalid image format from URL: {clean_url[:80]} - {type(img_error).__name__}")
                return None
        else:
            if st:
                st.warning(f"Failed to fetch image (HTTP {response.status_code}): {clean_url[:100]}")
        return None
    except Exception as e:
        if st:
            st.warning(f"Could not load image from URL: {str(e)[:100]}")
        return None


def create_collection_collage(
    images: List[Image.Image],
    output_size: tuple = (1080, 1080),
    layout: str = "grid"
) -> Image.Image:
    """Create a collage from product images"""
    if not images:
        # Return blank canvas if no images
        return Image.new('RGB', output_size, (240, 240, 240))

    # Limit to 9 images for clean grid
    images = images[:9]
    num_images = len(images)

    # Calculate grid dimensions
    if num_images == 1:
        cols, rows = 1, 1
    elif num_images <= 4:
        cols, rows = 2, 2
    elif num_images <= 6:
        cols, rows = 3, 2
    else:
        cols, rows = 3, 3

    # Create blank canvas
    canvas = Image.new('RGB', output_size, (255, 255, 255))

    # Calculate cell size with padding
    padding = 10
    cell_width = (output_size[0] - padding * (cols + 1)) // cols
    cell_height = (output_size[1] - padding * (rows + 1)) // rows

    # Place images in grid
    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols

        # Resize image to fit cell
        img_resized = img.copy()
        img_resized.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)

        # Calculate position (center in cell)
        x = padding + col * (cell_width + padding) + (cell_width - img_resized.width) // 2
        y = padding + row * (cell_height + padding) + (cell_height - img_resized.height) // 2

        # Paste image
        canvas.paste(img_resized, (x, y))

    return canvas


def truncate_to_limit(text: str, max_chars: int = 9000) -> str:
    """Truncate text to limit while preserving sentence boundaries"""
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    last_period = truncated.rfind('.')

    if last_period > max_chars * 0.8:
        return truncated[:last_period + 1]

    return truncated
