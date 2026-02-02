"""
🎯 ULTRA Brand Extractor + AI Ad Generator (MODULAR VERSION)
Enhanced with confidence scoring, source tracking, and comprehensive brand intelligence
"""

import streamlit as st
import json
import re
import requests
import os
from PIL import Image

# Import our modules
from utils import (
    save_brand_to_cache, load_brand_from_cache, list_cached_brands, delete_brand_cache,
    save_ad_to_cache, load_ad_from_cache, list_cached_ads, delete_ad_cache,
    safe_open_image, download_image_from_url, enhance_product_image,
    create_collection_collage, truncate_to_limit, remove_background
)
from crawler_fallback import run_crawl_with_fallback
from brand_extractor import create_brand_data_structure
from ai_generator import (
    generate_ad_with_replicate,
    AI_MODELS,
    AD_STYLE_CATEGORIES
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="🎯 ULTRA Brand Extractor + AI Ad Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STYLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    .main {background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%); min-height: 100vh;}
    h1, h2, h3, p, label {color: white; font-family: 'Helvetica Neue', Arial, sans-serif;}
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 12px;
        font-size: 16px; font-weight: 700; padding: 12px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    .step-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #667eea;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        border-radius: 8px;
    }
    .product-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        text-align: center;
    }
    .product-card:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_NEGATIVE_PROMPT = """blurry, distorted, warped, unclear, pixelated, low resolution, fake, cheap,
ugly, deformed, bad proportions, watermark, amateur, unprofessional, poor lighting,
white borders, borders around image, picture frame, white space around edges"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    st.title("🎯 ULTRA Brand Extractor + AI Ad Generator (MODULAR)")
    st.markdown("### Extract brand intelligence with confidence scoring & AI insights")

    # Initialize session state
    if 'brand_data' not in st.session_state:
        st.session_state.brand_data = None
    if 'generated_ads' not in st.session_state:
        st.session_state.generated_ads = []
    if 'results' not in st.session_state:
        st.session_state.results = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SIDEBAR: Cached Brands
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    with st.sidebar:
        st.header("📚 Cached Brands")
        st.caption("💾 Permanent cache (never expires)")
        cached_brands = list_cached_brands()

        if cached_brands:
            selected_cache = st.selectbox("Select cached brand", [""] + cached_brands)
            if selected_cache:
                # Show cache info
                cached_data = load_brand_from_cache(selected_cache)
                if cached_data:
                    with st.expander("ℹ️ Cache Info", expanded=False):
                        st.write(f"**Extracted:** {cached_data.get('extraction_date', 'Unknown')[:10]}")
                        st.write(f"**Pages:** {cached_data.get('metadata', {}).get('pages_crawled', 'N/A')}")
                        st.write(f"**Category:** {cached_data.get('brand_identity', {}).get('category_niche', {}).get('primary_category', 'N/A')}")
                        st.write(f"**Size:** {len(str(cached_data))} chars")

                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📂 Load", use_container_width=True):
                        cached_data = load_brand_from_cache(selected_cache)
                        if cached_data:
                            st.session_state.brand_data = cached_data
                            st.success(f"✅ Loaded {selected_cache}")
                            st.rerun()
                with col2:
                    if st.button("🔄 Update", use_container_width=True, help="Re-extract and replace cached data"):
                        # Pre-fill extraction form
                        st.session_state.update_brand = selected_cache
                        st.session_state.force_cache = True
                        st.info(f"Go to Extract tab to update {selected_cache}")
                with col3:
                    if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                        if delete_brand_cache(selected_cache):
                            st.success(f"🗑️ Deleted {selected_cache}")
                            if st.session_state.brand_data and st.session_state.brand_data.get('brand_name') == selected_cache:
                                st.session_state.brand_data = None
                            st.rerun()
        else:
            st.info("No cached brands yet")

        # ════════════════════════════════════════════════════════════
        st.markdown("---")
        st.header("🎨 Cached Generated Ads")
        st.caption("💾 Previously generated ads")
        cached_ads = list_cached_ads()

        if cached_ads:
            # Display options for cached ads
            ad_options = [f"{ad['brand_name']} - {ad['size']} ({ad['cached_at'][:10]})" for ad in cached_ads]
            selected_ad_idx = st.selectbox(
                "Select cached ad",
                range(len(ad_options)),
                format_func=lambda x: ad_options[x] if x < len(ad_options) else "",
                key="cached_ad_selector"
            )

            if selected_ad_idx is not None:
                selected_ad = cached_ads[selected_ad_idx]
                cache_id = selected_ad['cache_id']

                # Load and preview the ad
                cached_ad_data = load_ad_from_cache(cache_id)
                if cached_ad_data:
                    st.image(cached_ad_data['image'], caption=f"{selected_ad['brand_name']} - {selected_ad['size']}", use_column_width=True)

                    with st.expander("ℹ️ Ad Info", expanded=False):
                        metadata = cached_ad_data['metadata']
                        st.write(f"**Brand:** {metadata.get('brand_name', 'N/A')}")
                        st.write(f"**Size:** {metadata.get('size', 'N/A')}")
                        st.write(f"**Generated:** {metadata.get('cached_at', 'N/A')[:10]}")
                        st.write(f"**Style:** {metadata.get('style', 'N/A')}")
                        st.write(f"**Concept:** {metadata.get('concept', 'N/A')}")
                        if metadata.get('prompt'):
                            with st.expander("📝 Prompt Used"):
                                st.text(metadata['prompt'])

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        # Download button
                        import io
                        buf = io.BytesIO()
                        cached_ad_data['image'].save(buf, format='PNG', quality=95)
                        st.download_button(
                            "⬇️ Download",
                            data=buf.getvalue(),
                            file_name=f"{cache_id}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    with col2:
                        if st.button("🗑️ Delete", use_container_width=True, type="secondary", key="delete_cached_ad"):
                            if delete_ad_cache(cache_id):
                                st.success(f"🗑️ Deleted cached ad")
                                st.rerun()
        else:
            st.info("No cached ads yet. Generate some ads to see them here!")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TABS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Extract Brand", "🎨 Generate Ads", "📊 Brand Profile", "🔄 Auto-Sync"])

    # ════════════════════════════════════════════════════════════
    # TAB 1: EXTRACT BRAND
    # ════════════════════════════════════════════════════════════

    with tab1:
        st.subheader("🔍 Extract Brand Intelligence")

        # Check if updating existing cached brand
        update_mode = False
        if 'update_brand' in st.session_state and st.session_state.update_brand:
            update_mode = True
            update_brand_name = st.session_state.update_brand
            st.warning(f"🔄 **Update Mode:** Re-extracting {update_brand_name} (will replace cached data)")

            # Load existing cached data to get URL
            existing_data = load_brand_from_cache(update_brand_name)
            existing_url = existing_data.get('metadata', {}).get('url', '') if existing_data else ''
        else:
            update_brand_name = ''
            existing_url = ''

        col1, col2 = st.columns([3, 1])

        with col1:
            brand_name = st.text_input(
                "Brand Name",
                value=update_brand_name if update_mode else "",
                placeholder="e.g., Nike"
            )
            website_url = st.text_input(
                "Website URL",
                value=existing_url if update_mode else "",
                placeholder="https://www.example.com"
            )

        with col2:
            max_pages = st.number_input("Max Pages", min_value=5, max_value=100, value=30)
            max_depth = st.number_input("Max Depth", min_value=1, max_value=5, value=3)

        # Cache control
        st.markdown("---")

        # Auto-enable cache in update mode or use force_cache flag
        default_cache_value = False
        if update_mode or st.session_state.get('force_cache', False):
            default_cache_value = True

        save_to_cache = st.checkbox(
            "💾 Save to cache (unlimited lifetime storage)",
            value=default_cache_value,
            help="Enable to save this extraction permanently. Cache never expires and can be edited/replaced anytime."
        )

        if update_mode:
            st.info("ℹ️ Cache is enabled because you're updating an existing brand.")

        if st.button("🚀 Extract Brand Intelligence", type="primary"):
            if not brand_name or not website_url:
                st.error("Please provide both brand name and website URL")
            else:
                with st.spinner("Crawling and analyzing..."):
                    progress_bar = st.progress(0)

                    # Run crawler with fallback
                    scraped_data = run_crawl_with_fallback(
                        website_url,
                        max_depth,
                        max_pages,
                        progress_bar
                    )

                    if scraped_data['success']:
                        # Create brand data structure
                        brand_data = create_brand_data_structure(brand_name, scraped_data, website_url)

                        # Store in session
                        st.session_state.brand_data = brand_data

                        # Save to cache only if user enabled it
                        if save_to_cache:
                            if save_brand_to_cache(brand_name, brand_data):
                                if update_mode:
                                    st.success(f"✅ Brand '{brand_name}' updated in permanent cache!")
                                else:
                                    st.success("✅ Brand extraction complete! Saved to permanent cache.")
                            else:
                                st.warning("✅ Extraction complete, but cache save failed.")
                        else:
                            st.success("✅ Brand extraction complete! (Not cached - data only in session)")

                        # Clear update mode flags
                        if 'update_brand' in st.session_state:
                            del st.session_state.update_brand
                        if 'force_cache' in st.session_state:
                            del st.session_state.force_cache

                        st.rerun()
                    else:
                        st.error("Failed to crawl website")

    # ════════════════════════════════════════════════════════════
    # TAB 2: GENERATE ADS
    # ════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("🎨 Generate AI Ads - Enhanced Edition")
    
        if not st.session_state.brand_data:
            st.warning("⚠️ Please extract brand intelligence first in the 'Extract Brand' tab")
            st.info("💡 Or you can still generate ads without brand extraction - just upload images and logos manually!")

        # Import enhanced modules at runtime
        try:
            from ad_generator_enhanced import (
                ENHANCED_STYLE_THEMES,
                AD_CONCEPTS,
                generate_positive_prompt_elements,
                generate_negative_prompt_elements,
                combine_multiple_images_layout,
                add_logo_with_smart_positioning
            )
            enhanced_available = True
        except ImportError:
            st.warning("⚠️ Enhanced features not available. Using basic mode.")
            enhanced_available = False

        # ========== PRODUCT IMAGES SECTION ==========
        st.markdown("### 🖼️ Product Images")

        col_img1, col_img2 = st.columns([2, 1])

        with col_img1:
            # Multiple file uploader - NOW WITH WEBP SUPPORT!
            product_images = st.file_uploader(
                "Upload Product Image(s) - Up to 14 images",
                type=["png", "jpg", "jpeg", "webp"],  # ✅ WEBP ADDED!
                accept_multiple_files=True,
                key="product_imgs_multi",
                help="Upload 1-14 product images. Supports PNG, JPG, JPEG, WebP formats."
            )

            if product_images:
                st.success(f"✅ {len(product_images)} image(s) uploaded")

                # Preview uploaded images
                preview_cols = st.columns(min(len(product_images), 4))
                for idx, img_file in enumerate(product_images[:4]):
                    with preview_cols[idx]:
                        try:
                            preview = safe_open_image(img_file)
                            st.image(preview, use_column_width=True, caption=f"Image {idx+1}")
                        except Exception as e:
                            st.error(f"Error loading image {idx+1}")

                # ========== BATCH GENERATION: Individual Product Details ==========
                if len(product_images) > 1:
                    st.markdown("---")
                    st.markdown("#### 📝 Individual Product Details (for Batch Generation)")

                    with st.expander("✏️ Add custom text/price for each product", expanded=False):
                        st.caption("Add specific details for each product - these will be used in individual ad generation")

                        # Initialize session state for product details
                        if 'product_details' not in st.session_state:
                            st.session_state.product_details = {}

                        for idx, img_file in enumerate(product_images):
                            st.markdown(f"**Product {idx+1}:** `{img_file.name}`")
                            cols = st.columns(3)

                            with cols[0]:
                                product_name = st.text_input(
                                    "Product Name:",
                                    key=f"prod_name_{idx}",
                                    placeholder="e.g., Premium Lighter"
                                )
                            with cols[1]:
                                product_price = st.text_input(
                                    "Price:",
                                    key=f"prod_price_{idx}",
                                    placeholder="e.g., $29.99"
                                )
                            with cols[2]:
                                product_message = st.text_input(
                                    "Custom Message:",
                                    key=f"prod_message_{idx}",
                                    placeholder="e.g., Limited Edition"
                                )

                            # Store in session state
                            st.session_state.product_details[idx] = {
                                'name': product_name,
                                'price': product_price,
                                'message': product_message,
                                'file': img_file
                            }

                            if idx < len(product_images) - 1:
                                st.markdown("---")

                # Initialize generation_mode and image_layout as session state for persistence
                if 'generation_mode' not in st.session_state:
                    st.session_state.generation_mode = "🔀 Multi-Image Reference (AI blends all)"
                if 'image_layout' not in st.session_state:
                    st.session_state.image_layout = "Grid (Auto-arrange)"

                if len(product_images) > 1 and enhanced_available:
                    st.markdown("---")
                    st.markdown("#### 🎯 Generation Mode")

                    st.session_state.generation_mode = st.radio(
                        "Choose generation approach:",
                        [
                            "📦 Batch Generation (One ad per product)",
                            "🎨 Collection Ad (All products in one ad)",
                            "🔀 Multi-Image Reference (AI blends all)"
                        ],
                        index=0,  # Default to Batch
                        key="generation_mode_choice",
                        help="Batch: Generates separate ads for each product | Collection: Combines all into one ad | Reference: Uses all as AI input"
                    )

                    if "Collection" in st.session_state.generation_mode:
                        st.session_state.image_layout = st.radio(
                            "Collection Layout:",
                            [
                                "Grid (Auto-arrange)",
                                "Horizontal Row",
                                "Vertical Column"
                            ],
                            key="collection_layout_choice",
                            help="How to arrange products in the collection ad"
                        )
                    elif "Multi-Image" in st.session_state.generation_mode:
                        st.info("💡 All images will be sent to AI as references - AI will creatively blend them")

        with col_img2:
            st.markdown("**📥 Alternative: URL Fetch**")
            product_url = st.text_input(
                "Or fetch from URL:",
                placeholder="https://example.com/product.jpg",
                key="single_product_url"
            )

            if product_url and st.button("📥 Fetch Image", key="fetch_single_product"):
                with st.spinner("Fetching..."):
                    fetched = download_image_from_url(product_url)
                    if fetched:
                        st.session_state.fetched_product_image = fetched
                        st.success("✅ Image fetched!")
                        st.image(fetched, width=200)
                    else:
                        st.error("❌ Failed to fetch image")

            # Use extracted brand images
            if st.session_state.brand_data:
                brand_images = st.session_state.brand_data.get('10_images_and_ads', {}).get('images', [])
                if brand_images:
                    st.markdown("**🖼️ Use Extracted Images**")

                    # Show selectable extracted images
                    with st.expander(f"📸 {len(brand_images)} Images from Brand"):
                        for idx, img_data in enumerate(brand_images[:10]):  # Show first 10
                            img_url = img_data.get('url', '') if isinstance(img_data, dict) else img_data
                            if img_url:
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    if st.button("Use", key=f"use_brand_img_{idx}"):
                                        with st.spinner(f"Loading image {idx+1}..."):
                                            # Get base URL from brand data for relative paths
                                            base_url = st.session_state.brand_data.get('metadata', {}).get('url', '')
                                            fetched = download_image_from_url(img_url, base_url=base_url)
                                            if fetched:
                                                st.session_state.fetched_product_image = fetched
                                                st.success("✅ Image loaded!")
                                                st.rerun()
                                with col2:
                                    st.caption(f"{img_url[:60]}..." if len(img_url) > 60 else img_url)

        st.markdown("---")

        # ========== EXTRACTED TAGLINES & MESSAGES ==========
        if st.session_state.brand_data:
            ad_content = st.session_state.brand_data.get('ad_content', {})
            headlines = ad_content.get('headlines', [])
            subtext = ad_content.get('subtext', [])
            ctas = ad_content.get('ctas', [])

            if headlines or subtext or ctas:
                st.markdown("### 💬 Extracted Taglines & Messages")

                with st.expander("📝 View & Use Extracted Content", expanded=False):
                    if headlines:
                        st.markdown("**Headlines:**")
                        for idx, headline in enumerate(headlines[:5]):
                            st.markdown(f"• {headline}")

                    if subtext:
                        st.markdown("**Taglines/Subtext:**")
                        for idx, sub in enumerate(subtext[:3]):
                            st.markdown(f"• {sub}")

                    if ctas:
                        st.markdown("**Call-to-Actions:**")
                        cta_text = ", ".join(ctas[:5])
                        st.markdown(f"• {cta_text}")

                    st.info("💡 These will be automatically included in your ad prompts when generating")

                st.markdown("---")

        # ========== COLLECTION IMAGE INFUSION ==========
        st.markdown("### 🎨 Collection Image Infusion")
        st.info("💡 **NEW**: Upload multiple images and the AI will infuse/blend them into ONE cohesive ad image")

        with st.expander("🖼️ Collection Infusion Mode - Upload & Combine Multiple Images", expanded=False):
            st.markdown("""
            **What is Collection Infusion?**
            - Upload 2-10 product images
            - Images are first combined into a single composition
            - AI then generates a professional ad based on the combined images
            - Perfect for showcasing product collections, variants, or related items

            **How it works:**
            1. Upload multiple product images below (2-10 images recommended)
            2. Choose a layout mode (AI Auto-Blend, Grid, Horizontal, or Vertical)
            3. Images are combined according to your chosen layout
            4. Select your style and concept
            5. AI generates ONE cohesive ad featuring all your products

            **Layout Modes:**
            - **AI Auto-Blend**: Grid layout with creative AI interpretation
            - **Grid**: Structured grid arrangement (best for 4+ products)
            - **Horizontal**: Side-by-side layout (best for 2-4 products)
            - **Vertical**: Stacked layout (best for 2-3 products)
            """)

            collection_images = st.file_uploader(
                "Upload Collection Images (2-10 images):",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="collection_infusion_images",
                help="Upload 2-10 images that will be infused into one ad"
            )

            if collection_images:
                st.success(f"✅ {len(collection_images)} images uploaded for collection infusion")

                # Preview uploaded collection images
                st.markdown("**Preview of Collection Images:**")
                preview_cols = st.columns(min(len(collection_images), 5))
                for idx, img_file in enumerate(collection_images[:10]):
                    with preview_cols[idx % 5]:
                        try:
                            preview = safe_open_image(img_file)
                            st.image(preview, use_column_width=True, caption=f"#{idx+1}")
                        except Exception as e:
                            st.error(f"Error loading image {idx+1}")

                # Layout selection for collection
                collection_layout_mode = st.radio(
                    "📐 Collection Infusion Layout:",
                    [
                        "🧩 AI Auto-Blend (Recommended - Grid layout, AI reimagines creatively)",
                        "📊 Grid Layout (Structured grid arrangement)",
                        "➡️ Horizontal Row (Side-by-side arrangement)",
                        "⬇️ Vertical Column (Stacked arrangement)"
                    ],
                    key="collection_infusion_layout",
                    help="All modes combine images first, then AI generates the final ad based on the combined layout"
                )

                # Store collection images in session state
                if 'collection_infusion_imgs' not in st.session_state:
                    st.session_state.collection_infusion_imgs = []
                st.session_state.collection_infusion_imgs = collection_images
                st.session_state.collection_infusion_mode = collection_layout_mode

                st.success("🎨 Ready for collection infusion generation! Scroll down to configure style, concept, and generate.")
            else:
                st.info("👆 Upload 2+ images above to enable Collection Infusion mode")

        st.markdown("---")

        # ========== STYLE & CONCEPT SELECTION ==========
        st.markdown("### 🎨 Style & Concept Selection")
    
        col_style, col_concept = st.columns(2)
    
        with col_style:
            if enhanced_available:
                # Group styles by category
                style_categories = {"None": ["None - Custom Style"]}
                for style_name, description in ENHANCED_STYLE_THEMES.items():
                    category = style_name.split(' - ')[0]
                    if category not in style_categories:
                        style_categories[category] = []
                    style_categories[category].append(style_name)

                selected_category = st.selectbox(
                    "🎨 Style Category:",
                    options=list(style_categories.keys()),
                    key="style_category"
                )

                selected_style = st.selectbox(
                    f"Choose {selected_category} Style:",
                    options=style_categories[selected_category],
                    key="selected_style_enhanced",
                    help="Choose from 100+ professional style themes or 'None' for custom"
                )

                # Editable style description
                if selected_style == "None - Custom Style":
                    style_description = st.text_area(
                        "✏️ Custom Style Description:",
                        value="",
                        height=100,
                        key="custom_style_desc",
                        help="Write your own style description for the prompt",
                        placeholder="Example: Minimalist flat lay, natural lighting, white background..."
                    )
                else:
                    default_desc = ENHANCED_STYLE_THEMES[selected_style]
                    style_description = st.text_area(
                        "✏️ Style Description (Editable):",
                        value=default_desc,
                        height=100,
                        key="editable_style_desc",
                        help="You can edit this style description to customize the prompt"
                    )
            else:
                # Fallback to basic styles
                selected_style = st.selectbox("Ad Style", list(AD_STYLE_CATEGORIES.keys()))
                style_description = None  # No editing in basic mode
    
        with col_concept:
            if enhanced_available:
                selected_concept = st.selectbox(
                    "💡 Ad Concept:",
                    options=list(AD_CONCEPTS.keys()),
                    key="selected_concept_enhanced",
                    help="Choose advertising concept approach or 'None' for custom"
                )

                # Editable concept description
                if selected_concept == "None - Custom Only":
                    concept_description = st.text_area(
                        "✏️ Custom Concept Description:",
                        value="",
                        height=100,
                        key="custom_concept_desc",
                        help="Write your own concept description for the prompt",
                        placeholder="Example: Show product in use by happy customers..."
                    )
                else:
                    default_concept_desc = AD_CONCEPTS[selected_concept]
                    concept_description = st.text_area(
                        "✏️ Concept Description (Editable):",
                        value=default_concept_desc,
                        height=100,
                        key="editable_concept_desc",
                        help="You can edit this concept description to customize the prompt"
                    )
            else:
                selected_concept = "None - Custom Only"
                concept_description = None
    
        st.markdown("---")
    
        # ========== LOGO CONFIGURATION ==========
        st.markdown("### 🏷️ Logo Configuration")
        st.info("💡 Upload logos manually or use extracted brand logos")
    
        logo_tabs = st.tabs(["📤 Manual Upload (Recommended)", "🔍 Use Extracted Logos"])
    
        logo_configs = []
    
        with logo_tabs[0]:
            st.markdown("#### Upload Your Logos")

            col_logo1, col_logo2 = st.columns(2)

            # LOGO 1 - TOP LEFT
            with col_logo1:
                st.markdown("##### 🏷️ Logo 1 - Top Left")

                logo1_file = st.file_uploader(
                    "Upload Logo 1:",
                    type=["png", "jpg", "jpeg", "webp"],  # ✅ WEBP ADDED!
                    key="logo1_manual",
                    help="Upload logo for top-left position"
                )

                if logo1_file:
                    logo1_img = safe_open_image(logo1_file)
                    st.image(logo1_img, width=150, caption="Logo 1 Preview")

                    # Horizontal position control
                    logo1_h_pos = st.slider(
                        "Horizontal Position (px from left):",
                        min_value=-50,
                        max_value=100,
                        value=20,
                        step=5,
                        key="logo1_h_pos",
                        help="Distance from left edge (negative = outside, 0 = corner, positive = inside)"
                    )

                    # Vertical position control
                    logo1_v_pos = st.slider(
                        "Vertical Position (px from top):",
                        min_value=-50,
                        max_value=100,
                        value=20,
                        step=5,
                        key="logo1_v_pos",
                        help="Distance from top edge (negative = outside, 0 = corner, positive = inside)"
                    )

                    # Size control
                    logo1_size = st.slider(
                        "Logo Size (% of image height):",
                        min_value=3.0,
                        max_value=25.0,
                        value=8.0,
                        step=0.5,
                        key="logo1_size",
                        help="Logo height as percentage of image height"
                    )

                    # Background removal
                    logo1_remove_bg = st.checkbox(
                        "Remove Background",
                        value=True,
                        key="logo1_rmbg",
                        help="Auto-remove logo background"
                    )

                    logo_configs.append({
                        "image": logo1_img,
                        "position": "top-left",
                        "custom_x": logo1_h_pos,
                        "custom_y": logo1_v_pos,
                        "size_percent": logo1_size,
                        "remove_bg": logo1_remove_bg,
                        "label": "Logo 1 (Top-Left)"
                    })

            # LOGO 2 - TOP RIGHT
            with col_logo2:
                st.markdown("##### 🏷️ Logo 2 - Top Right")

                logo2_file = st.file_uploader(
                    "Upload Logo 2:",
                    type=["png", "jpg", "jpeg", "webp"],  # ✅ WEBP ADDED!
                    key="logo2_manual",
                    help="Upload logo for top-right position"
                )

                if logo2_file:
                    logo2_img = safe_open_image(logo2_file)
                    st.image(logo2_img, width=150, caption="Logo 2 Preview")

                    # Horizontal position control (from right edge)
                    logo2_h_pos = st.slider(
                        "Horizontal Position (px from right):",
                        min_value=-50,
                        max_value=100,
                        value=20,
                        step=5,
                        key="logo2_h_pos",
                        help="Distance from right edge (negative = outside, 0 = corner, positive = inside)"
                    )

                    # Vertical position control
                    logo2_v_pos = st.slider(
                        "Vertical Position (px from top):",
                        min_value=-50,
                        max_value=100,
                        value=20,
                        step=5,
                        key="logo2_v_pos",
                        help="Distance from top edge (negative = outside, 0 = corner, positive = inside)"
                    )

                    # Size control
                    logo2_size = st.slider(
                        "Logo Size (% of image height):",
                        min_value=3.0,
                        max_value=25.0,
                        value=8.0,
                        step=0.5,
                        key="logo2_size",
                        help="Logo height as percentage of image height"
                    )

                    # Background removal
                    logo2_remove_bg = st.checkbox(
                        "Remove Background",
                        value=True,
                        key="logo2_rmbg",
                        help="Auto-remove logo background"
                    )

                    # For top-right, store distance from right edge
                    logo_configs.append({
                        "image": logo2_img,
                        "position": "top-right",
                        "custom_x": None,  # Will be calculated from custom_x_from_right
                        "custom_x_from_right": logo2_h_pos,  # Distance from right edge
                        "custom_y": logo2_v_pos,
                        "size_percent": logo2_size,
                        "remove_bg": logo2_remove_bg,
                        "label": "Logo 2 (Top-Right)"
                    })
    
        with logo_tabs[1]:
            st.markdown("#### Use Extracted Brand Logos")

            if st.session_state.brand_data:
                logos = st.session_state.brand_data.get('1_brand_logo', {})

                col_extracted1, col_extracted2 = st.columns(2)

                with col_extracted1:
                    if logos.get('light_logo'):
                        st.markdown("##### Light Logo")
                        try:
                            st.image(logos['light_logo'], width=200)
                            if st.button("Use Light Logo", key="use_light_logo"):
                                extracted_logo = download_image_from_url(logos['light_logo'])
                                if extracted_logo:
                                    logo_configs.append({
                                        "image": extracted_logo,
                                        "position": "top-left",
                                        "custom_x": 40,
                                        "custom_y": 80,
                                        "size_percent": 10.0,
                                        "remove_bg": True,
                                        "label": "Extracted Light Logo"
                                    })
                                    st.success("✅ Light logo added!")
                        except:
                            st.warning("Could not load light logo")

                with col_extracted2:
                    if logos.get('dark_logo'):
                        st.markdown("##### Dark Logo")
                        try:
                            st.image(logos['dark_logo'], width=200)
                            if st.button("Use Dark Logo", key="use_dark_logo"):
                                extracted_logo = download_image_from_url(logos['dark_logo'])
                                if extracted_logo:
                                    logo_configs.append({
                                        "image": extracted_logo,
                                        "position": "top-right",
                                        "custom_x": None,
                                        "custom_y": 80,
                                        "size_percent": 10.0,
                                        "remove_bg": True,
                                        "label": "Extracted Dark Logo"
                                    })
                                    st.success("✅ Dark logo added!")
                        except:
                            st.warning("Could not load dark logo")
            else:
                st.warning("⚠️ No brand data available. Extract a brand first or use manual upload.")
    
        st.markdown("---")
    
        # ========== PROMPTS SECTION ==========
        st.markdown("### 📝 Prompt Configuration")
    
        col_prompts1, col_prompts2 = st.columns(2)
    
        with col_prompts1:
            st.markdown("**🎯 Positive Prompt (Do's)**")

            if enhanced_available and st.session_state.brand_data:
                # Auto-generate positive elements
                auto_positive = generate_positive_prompt_elements(
                    selected_concept if 'selected_concept' in locals() else "Hero Product",
                    selected_style if 'selected_style' in locals() else "Product - Hero Shot",
                    st.session_state.brand_data
                )
            else:
                auto_positive = "High quality professional photography, crystal clear details, proper exposure, accurate colors, clean composition"

            positive_prompt = st.text_area(
                "Positive Elements (What TO include):",
                value=auto_positive,
                height=150,
                key="positive_prompt_enhanced",
                help="What TO include in the generation"
            )
    
        with col_prompts2:
            st.markdown("**🚫 Negative Prompt (Don'ts)**")

            if enhanced_available:
                # Auto-generate negative elements
                auto_negative = generate_negative_prompt_elements(
                    selected_concept if 'selected_concept' in locals() else "Hero Product",
                    selected_style if 'selected_style' in locals() else "Product - Hero Shot"
                )
            else:
                auto_negative = DEFAULT_NEGATIVE_PROMPT

            negative_prompt = st.text_area(
                "Negative Elements (What to AVOID):",
                value=auto_negative,
                height=150,
                key="negative_prompt_enhanced",
                help="What to AVOID in the generation"
            )
    
        st.markdown("---")
    
        # ========== GENERATION SETTINGS ==========
        st.markdown("### ⚙️ Generation Settings")
    
        col_settings1, col_settings2, col_settings3 = st.columns(3)
    
        with col_settings1:
            # Output format selection
            output_format = st.radio(
                "📦 Output Format:",
                ["🖼️ Image Ads", "🎥 Video Ads (Collection)"],
                key="output_format",
                help="Choose between static image ads or video ads from image sequence"
            )

            if output_format == "🖼️ Image Ads":
                output_sizes = st.multiselect(
                    "📐 Output Sizes:",
                    ["Square (1:1)", "Story (9:16)", "Landscape (16:9)"],
                    default=["Square (1:1)"],
                    key="output_sizes_enhanced"
                )
            else:
                # Video generation options
                st.markdown("**🎥 Video Settings:**")
                video_duration = st.slider(
                    "Duration per image (seconds):",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.0,
                    step=0.5,
                    key="video_duration"
                )
                video_transition = st.selectbox(
                    "Transition Effect:",
                    ["Fade", "Slide", "Zoom", "None"],
                    key="video_transition"
                )
                video_size = st.selectbox(
                    "Video Size:",
                    ["1080x1080 (Square)", "1080x1920 (Story)", "1920x1080 (Landscape)"],
                    key="video_size"
                )

                st.info("""
                💡 **Video Collection Ad**:
                - Combines multiple product images into one video
                - Each image shows for selected duration
                - Smooth transitions between images
                - Perfect for showcasing product collections
                - Exports as MP4 file

                **Note**: Requires `moviepy` package:
                ```bash
                pip install moviepy
                ```
                """)

                output_sizes = []  # Empty for video mode

        with col_settings2:
            api_key = st.text_input(
                "Replicate API Key:",
                type="password",
                key="api_key_enhanced",
                help="Get your API key from replicate.com"
            )

        with col_settings3:
            model_options = [f"{v['name']}" for k, v in AI_MODELS.items()]
            model_keys = list(AI_MODELS.keys())
            selected_model_idx = st.selectbox(
                "AI Model:",
                range(len(model_options)),
                format_func=lambda x: model_options[x],
                key="model_enhanced"
            )
            selected_model = model_keys[selected_model_idx]
    
        # ========== FINAL PROMPT PREVIEW ==========
        st.markdown("### 📄 Final Prompt Preview")

        if st.session_state.brand_data:
            brand_identity = st.session_state.brand_data['brand_identity']
            brand_name = brand_identity.get('brand_name', 'Product')
            market_pos = brand_identity.get('market_position', {}).get('position', 'premium')
            category = brand_identity.get('category_niche', {}).get('primary_category', 'product').replace('_', ' ')

            if enhanced_available:
                # Use the edited style description from the text area
                style_desc = style_description if style_description else ENHANCED_STYLE_THEMES.get(selected_style, "Professional photography")
                # Use the edited concept description from the text area
                concept_desc = concept_description if concept_description else AD_CONCEPTS.get(selected_concept, "High quality ad")
            else:
                style_desc = AD_STYLE_CATEGORIES.get(selected_style, "Professional")
                concept_desc = "Professional advertisement"

            # Extract ad content for enhanced prompts
            ad_content = st.session_state.brand_data.get('ad_content', {})
            headlines = ad_content.get('headlines', [])
            ctas = ad_content.get('ctas', [])
            features = ad_content.get('features', [])
            ingredients = ad_content.get('ingredients', [])

            # Build ad content section
            ad_content_section = ""
            if headlines:
                ad_content_section += f"\nHEADLINE/TEXT: {headlines[0]}\n"
            if ctas:
                ad_content_section += f"CALL-TO-ACTION: {', '.join(ctas[:3])}\n"
            if "Ingredient" in selected_concept and ingredients:
                ad_content_section += f"INGREDIENTS: {', '.join(ingredients[:10])}\n"
            if features and ("Feature" in selected_concept or "Product" in selected_concept):
                ad_content_section += f"FEATURES: {', '.join(features[:5])}\n"

            auto_final_prompt = f"""Professional advertising photograph.

BRAND: {brand_name} - {market_pos} {category}

STYLE: {style_desc}

CONCEPT: {concept_desc}
{ad_content_section}
POSITIVE ELEMENTS (DO):
{positive_prompt}

COMPOSITION GUIDELINES:
- Product clearly visible and prominent
- Professional commercial photography quality
- Clean, uncluttered composition
- Reserve top area for logos (will be added after generation)
- High quality 8K details, crystal clear focus
"""
        else:
            auto_final_prompt = f"""Professional advertising photograph.

STYLE: {selected_style if 'selected_style' in locals() else 'Professional'}

POSITIVE ELEMENTS (DO):
{positive_prompt}

High quality, professional, 8K resolution, crystal clear details.
"""
    
        final_prompt = st.text_area(
        "Final Generation Prompt:",
        value=auto_final_prompt,
        height=200,
        key="final_prompt_preview",
        help="Review and edit the complete prompt before generation"
        )
    
        # ========== GENERATE BUTTON ==========
        # Change button text based on mode
        is_collection_infusion_active = ('collection_infusion_imgs' in st.session_state and
                                         len(st.session_state.get('collection_infusion_imgs', [])) >= 2)

        if output_format == "🎥 Video Ads (Collection)":
            button_text = "🎥 GENERATE VIDEO"
        elif is_collection_infusion_active:
            button_text = "🎨 GENERATE COLLECTION INFUSION AD"
        else:
            button_text = "🚀 GENERATE ADS"

        if st.button(button_text, type="primary", key="gen_ads_enhanced", use_container_width=True):

            # Video generation mode
            if output_format == "🎥 Video Ads (Collection)":
                if not product_images or len(product_images) < 2:
                    st.error("⚠️ Please upload at least 2 images for video generation")
                else:
                    try:
                        st.info("🎥 Generating video collection ad...")

                        # Check if moviepy is installed
                        try:
                            from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip
                            from moviepy.video.fx.all import fadein, fadeout
                        except ImportError:
                            st.error("⚠️ Please install moviepy: `pip install moviepy`")
                            st.stop()

                        # Prepare images
                        clips = []
                        for idx, img_file in enumerate(product_images):
                            img = safe_open_image(img_file)

                            # Parse video size
                            if "Square" in video_size:
                                target_size = (1080, 1080)
                            elif "Story" in video_size:
                                target_size = (1080, 1920)
                            else:
                                target_size = (1920, 1080)

                            # Resize image
                            img_resized = img.resize(target_size, Image.Resampling.LANCZOS)

                            # Save temporarily
                            import tempfile
                            temp_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                            img_resized.save(temp_path)

                            # Create clip
                            clip = ImageClip(temp_path).set_duration(video_duration)

                            # Add transitions
                            if video_transition == "Fade":
                                clip = fadein(clip, 0.5).fadeout(0.5)

                            clips.append(clip)

                        # Concatenate clips
                        final_video = concatenate_videoclips(clips, method="compose")

                        # Save video
                        brand_name_clean = st.session_state.brand_data['brand_identity'].get('brand_name', 'Product').replace(' ', '_') if st.session_state.brand_data else 'Ad'
                        video_filename = f"{brand_name_clean}_collection_video.mp4"
                        video_path = os.path.join("ad_cache", video_filename)

                        st.info("💾 Rendering video (this may take a minute)...")
                        final_video.write_videofile(video_path, fps=30, codec='libx264')

                        st.success(f"✅ Video generated successfully!")
                        st.video(video_path)

                        # Download button
                        with open(video_path, "rb") as f:
                            st.download_button(
                                "⬇️ Download Video",
                                data=f.read(),
                                file_name=video_filename,
                                mime="video/mp4",
                                use_container_width=True
                            )

                    except Exception as e:
                        st.error(f"❌ Video generation error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

            # Image generation mode
            elif not api_key:
                st.error("⚠️ Please provide Replicate API key")
            elif not product_images and 'fetched_product_image' not in st.session_state and 'collection_infusion_imgs' not in st.session_state:
                st.error("⚠️ Please upload at least one product image, use Collection Infusion, or fetch from URL")
            elif not output_sizes:
                st.error("⚠️ Please select at least one output size")
            else:
                try:
                    # Check if Collection Infusion mode is active
                    is_collection_infusion = ('collection_infusion_imgs' in st.session_state and
                                             len(st.session_state.get('collection_infusion_imgs', [])) >= 2)

                    if is_collection_infusion:
                        st.info(f"🎨 **Collection Infusion Mode Active**: Processing {len(st.session_state.collection_infusion_imgs)} images...")

                    # Prepare product images
                    images_to_process = []

                    # Priority: Collection Infusion > Regular Upload > Fetched
                    if is_collection_infusion:
                        # Use collection infusion images
                        for img_file in st.session_state.collection_infusion_imgs:
                            img = safe_open_image(img_file)
                            images_to_process.append(img)
                        st.success(f"✅ Loaded {len(images_to_process)} images for collection infusion")
                    elif product_images:
                        for img_file in product_images:
                            img = safe_open_image(img_file)
                            # Enhance if single image
                            if len(product_images) == 1:
                                img = enhance_product_image(img)
                            images_to_process.append(img)

                    if 'fetched_product_image' in st.session_state and not is_collection_infusion:
                        images_to_process.append(st.session_state.fetched_product_image)

                    # Determine generation approach
                    generation_mode_value = st.session_state.get('generation_mode', "")
                    is_batch_mode = len(product_images) > 1 and "Batch" in generation_mode_value if product_images else False
                    is_collection_mode = (len(product_images) > 1 and "Collection" in generation_mode_value) if product_images else False

                    # Handle Collection Infusion Mode (takes priority)
                    if is_collection_infusion and enhanced_available:
                        st.info(f"🎨 Collection Infusion: Processing {len(images_to_process)} images...")

                        # Get collection infusion layout mode
                        infusion_layout = st.session_state.get('collection_infusion_mode', '🧩 AI Auto-Blend')

                        if "AI Auto-Blend" in infusion_layout:
                            # For AI Auto-Blend, combine images in a grid and let AI reimagine them creatively
                            combined = combine_multiple_images_layout(images_to_process[:10], "grid")
                            images_for_api = [combined]
                            st.success(f"✅ Combined {len(images_to_process)} images for AI auto-blending")
                        elif "Grid" in infusion_layout:
                            combined = combine_multiple_images_layout(images_to_process, "grid")
                            images_for_api = [combined]
                            st.success(f"✅ Combined {len(images_to_process)} images in grid layout")
                        elif "Horizontal" in infusion_layout:
                            combined = combine_multiple_images_layout(images_to_process, "horizontal")
                            images_for_api = [combined]
                            st.success(f"✅ Combined {len(images_to_process)} images horizontally")
                        elif "Vertical" in infusion_layout:
                            combined = combine_multiple_images_layout(images_to_process, "vertical")
                            images_for_api = [combined]
                            st.success(f"✅ Combined {len(images_to_process)} images vertically")
                        else:
                            # Default to grid layout
                            combined = combine_multiple_images_layout(images_to_process[:10], "grid")
                            images_for_api = [combined]
                            st.success(f"✅ Combined {len(images_to_process)} images for infusion")

                    # Handle Regular Collection Ad Mode
                    elif is_collection_mode and enhanced_available:
                        st.info(f"🎨 Creating collection ad with {len(images_to_process)} products...")

                        # Combine images based on layout
                        image_layout = st.session_state.get('image_layout', "Grid (Auto-arrange)")
                        if "Grid" in image_layout:
                            combined = combine_multiple_images_layout(images_to_process, "grid")
                        elif "Horizontal" in image_layout:
                            combined = combine_multiple_images_layout(images_to_process, "horizontal")
                        else:  # Vertical
                            combined = combine_multiple_images_layout(images_to_process, "vertical")

                        images_for_api = [combined]
                        st.success(f"✅ Combined {len(images_to_process)} products into one collection image")

                    # Handle Multi-Image Reference Mode
                    elif len(images_to_process) > 1 and not is_batch_mode:
                        images_for_api = images_to_process[:14]  # Max 14 for API
                        st.info(f"📊 Using {len(images_for_api)} images as references for AI blending")

                    # Single image or batch mode (each processed individually)
                    else:
                        images_for_api = images_to_process[:14]

                    # Generate for each size
                    st.session_state.results = []

                    aspect_map = {
                        "Square (1:1)": ("1:1", (1080, 1080)),
                        "Story (9:16)": ("9:16", (1080, 1920)),
                        "Landscape (16:9)": ("16:9", (1920, 1080))
                    }

                    # Batch Mode: Generate separate ads for each product
                    if is_batch_mode and 'product_details' in st.session_state:
                        st.info(f"📦 Batch Mode: Generating ads for {len(st.session_state.product_details)} products...")

                        for prod_idx, prod_data in st.session_state.product_details.items():
                            prod_name = prod_data.get('name', f"Product {prod_idx+1}")
                            prod_price = prod_data.get('price', '')
                            prod_message = prod_data.get('message', '')

                            # Build custom prompt for this product
                            product_specific_text = f"\n\nPRODUCT: {prod_name}" if prod_name else ""
                            product_specific_text += f"\nPRICE: {prod_price}" if prod_price else ""
                            product_specific_text += f"\nMESSAGE: {prod_message}" if prod_message else ""

                            custom_prompt = final_prompt + product_specific_text

                            # Load product image
                            prod_img = safe_open_image(prod_data['file'])
                            prod_img = enhance_product_image(prod_img)

                            st.markdown(f"#### 🔄 Generating for: **{prod_name or f'Product {prod_idx+1}'}**")

                            for size_name in output_sizes:
                                aspect_ratio, dimensions = aspect_map[size_name]

                                st.markdown(f"📱 {size_name}...")
                                progress_placeholder = st.empty()

                                # Generate using API
                                generated = generate_ad_with_replicate(
                                    prompt=custom_prompt,
                                    negative_prompt=negative_prompt,
                                    api_key=api_key,
                                    model_key=selected_model,
                                    aspect_ratio=aspect_ratio,
                                    product_image=prod_img,
                                    logo_image=None,
                                    progress_placeholder=progress_placeholder
                                )

                                if generated:
                                    # Resize to exact dimensions
                                    final_img = generated.resize(dimensions, Image.Resampling.LANCZOS)

                                    # Add logos
                                    if logo_configs and enhanced_available:
                                        for logo_config in logo_configs:
                                            final_img = add_logo_with_smart_positioning(
                                                final_img,
                                                logo_config["image"],
                                                position=logo_config["position"],
                                                size_percent=logo_config["size_percent"],
                                                custom_x=logo_config.get("custom_x"),
                                                custom_y=logo_config.get("custom_y"),
                                                custom_x_from_right=logo_config.get("custom_x_from_right"),
                                                remove_bg=logo_config["remove_bg"]
                                            )

                                    # Don't show preview here - will show in download section
                                    st.success(f"✅ {prod_name} - {size_name} generated successfully!")

                                    # Save to results
                                    import io
                                    buf = io.BytesIO()
                                    final_img.save(buf, format="PNG", quality=95)

                                    brand_name_clean = st.session_state.brand_data['brand_identity'].get('brand_name', 'Product').replace(' ', '_') if st.session_state.brand_data else 'Ad'
                                    prod_name_clean = prod_name.replace(' ', '_') if prod_name else f'Product{prod_idx+1}'

                                    st.session_state.results.append({
                                        "img": final_img,
                                        "bytes": buf.getvalue(),
                                        "name": f"{brand_name_clean}_{prod_name_clean}_{size_name.replace(' ', '_').replace('(', '').replace(')', '')}",
                                        "size": f"{dimensions[0]}x{dimensions[1]}"
                                    })

                                    # Cache the ad
                                    ad_metadata = {
                                        'brand_name': brand_name_clean,
                                        'product_name': prod_name,
                                        'size': f"{dimensions[0]}x{dimensions[1]}",
                                        'size_name': size_name,
                                        'style': selected_style if enhanced_available else selected_style,
                                        'concept': selected_concept if enhanced_available else 'N/A',
                                        'prompt': custom_prompt,
                                        'negative_prompt': negative_prompt,
                                        'model': selected_model,
                                        'aspect_ratio': aspect_ratio
                                    }
                                    save_ad_to_cache(
                                        ad_name=f"{brand_name_clean}_{prod_name_clean}_{size_name.replace(' ', '_')}",
                                        ad_data=ad_metadata,
                                        image=final_img
                                    )

                                    progress_placeholder.empty()
                                else:
                                    st.warning(f"⚠️ {size_name} generation failed")
                                    progress_placeholder.empty()

                            st.markdown("---")

                    # Normal Mode: Single generation (collection or single image)
                    else:
                        for size_name in output_sizes:
                            aspect_ratio, dimensions = aspect_map[size_name]

                            st.markdown(f"### 📱 Generating {size_name}...")
                            progress_placeholder = st.empty()

                            # Generate using API
                            generated = generate_ad_with_replicate(
                                prompt=final_prompt,
                                negative_prompt=negative_prompt,  # ✅ NOW USING EDITABLE NEGATIVE PROMPT!
                                api_key=api_key,
                                model_key=selected_model,
                                aspect_ratio=aspect_ratio,
                                product_image=images_for_api[0] if len(images_for_api) == 1 else None,
                                logo_image=None,  # Logos added after generation
                                progress_placeholder=progress_placeholder
                            )
    
                        if generated:
                            # Resize to exact dimensions
                            final_img = generated.resize(dimensions, Image.Resampling.LANCZOS)
    
                            # Add all logos with proper positioning
                            if logo_configs and enhanced_available:
                                st.info(f"🏷️ Adding {len(logo_configs)} logo(s)...")

                                for logo_config in logo_configs:
                                    final_img = add_logo_with_smart_positioning(
                                        final_img,
                                        logo_config["image"],
                                        position=logo_config["position"],
                                        size_percent=logo_config["size_percent"],
                                        custom_x=logo_config.get("custom_x"),
                                        custom_y=logo_config.get("custom_y"),
                                        custom_x_from_right=logo_config.get("custom_x_from_right"),
                                        remove_bg=logo_config["remove_bg"]
                                    )

                            # Don't show preview here - will show in download section
                            st.success(f"✅ {size_name} generated successfully!")

                            # Save to results
                            import io
                            buf = io.BytesIO()
                            final_img.save(buf, format="PNG", quality=95)
    
                            brand_name_clean = st.session_state.brand_data['brand_identity'].get('brand_name', 'Product').replace(' ', '_') if st.session_state.brand_data else 'Ad'
    
                            st.session_state.results.append({
                                "img": final_img,
                                "bytes": buf.getvalue(),
                                "name": f"{brand_name_clean}-{size_name.replace(' ', '_').replace('(', '').replace(')', '')}",
                                "size": f"{dimensions[0]}x{dimensions[1]}"
                            })

                            # Cache the generated ad
                            ad_metadata = {
                                'brand_name': brand_name_clean,
                                'size': f"{dimensions[0]}x{dimensions[1]}",
                                'size_name': size_name,
                                'style': selected_style if enhanced_available else selected_style,
                                'concept': selected_concept if enhanced_available else 'N/A',
                                'prompt': final_prompt,
                                'negative_prompt': negative_prompt,
                                'model': selected_model,
                                'aspect_ratio': aspect_ratio
                            }
                            save_ad_to_cache(
                                ad_name=f"{brand_name_clean}_{size_name.replace(' ', '_')}",
                                ad_data=ad_metadata,
                                image=final_img
                            )

                            progress_placeholder.empty()
                        else:
                            st.warning(f"⚠️ {size_name} generation failed - see error above")
                            progress_placeholder.empty()
    
                    if st.session_state.results:
                        st.balloons()
                        # Success message shown in download section
    
                except Exception as e:
                    st.error(f"❌ Error during generation: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
        # ========== DOWNLOAD SECTION ==========
        if st.session_state.results:
            # Initialize removed ads tracker
            if 'removed_ads' not in st.session_state:
                st.session_state.removed_ads = set()

            st.markdown("---")
            st.markdown("## 📥 Your Generated Ads")

            # Count remaining ads
            remaining_count = len([r for idx, r in enumerate(st.session_state.results) if idx not in st.session_state.removed_ads])
            st.info(f"✨ {remaining_count} ad(s) ready. Remove unwanted ads before uploading to Drive.")

            cols = st.columns(min(len(st.session_state.results), 3))
            for idx, result in enumerate(st.session_state.results):
                # Skip removed ads
                if idx in st.session_state.removed_ads:
                    continue

                with cols[idx % 3]:
                    st.image(result["img"], use_column_width=True, caption=f"✅ {result['size']}")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.download_button(
                            "⬇️ Download",
                            result["bytes"],
                            f"{result['name']}.png",
                            "image/png",
                            key=f"dl_enhanced_{idx}",
                            use_container_width=True,
                            help=f"Download {result['name']}"
                        )
                    with col_btn2:
                        if st.button("🗑️ Remove", key=f"remove_ad_{idx}", use_container_width=True, help="Remove from upload list"):
                            st.session_state.removed_ads.add(idx)
                            st.rerun()

            # Bulk download option
            if len(st.session_state.results) > 1:
                st.markdown("#### 📦 Bulk Download")
                if st.button("📦 Download All as ZIP", key="bulk_download"):
                    import zipfile
                    zip_buffer = io.BytesIO()
    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for result in st.session_state.results:
                            zip_file.writestr(
                                f"{result['name']}.png",
                                result["bytes"]
                            )
    
                    zip_buffer.seek(0)
                    st.download_button(
                        "⬇️ Download ZIP File",
                        zip_buffer.getvalue(),
                        "generated_ads.zip",
                        "application/zip",
                        key="zip_download"
                    )
    
    # ==================== END TAB2_REPLACEMENT ====================
    
        # ════════════════════════════════════════════════════════════
        # TAB 3: BRAND PROFILE
        # ════════════════════════════════════════════════════════════
    
    with tab3:
        st.subheader("📊 Brand Profile")

        if not st.session_state.brand_data:
            st.warning("⚠️ Please extract brand intelligence first in the 'Extract Brand' tab")
        else:
            data = st.session_state.brand_data

            # Extraction metrics
            st.markdown("### 📈 Extraction Metadata")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Pages Crawled", data['metadata']['pages_crawled'])
            with col2:
                st.metric("Total Characters", f"{data['metadata']['total_characters']:,}")
            with col3:
                st.metric("Nav Characters", f"{data['metadata']['nav_characters']:,}")
            with col4:
                st.metric("Reviews Characters", f"{data['metadata']['reviews_characters']:,}")

            # Brand Identity
            st.markdown("### 🏷️ Brand Identity")
            identity = data['brand_identity']

            with st.expander("Category & Market Position", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Primary Category:** {identity['category_niche']['primary_category']}")
                    st.write(f"**Confidence:** {identity['category_niche']['confidence']:.0%}")
                    st.write(f"**Source:** {identity['category_niche']['source']}")
                    if identity['category_niche'].get('secondary_categories'):
                        st.write(f"**Secondary:** {', '.join(identity['category_niche']['secondary_categories'])}")
                with col2:
                    st.write(f"**Market Position:** {identity['market_position']['position']}")
                    st.write(f"**Confidence:** {identity['market_position']['confidence']:.0%}")
                    st.write(f"**Premium Signals:** {identity['market_position']['premium_signals_found']}")
                    st.write(f"**Budget Signals:** {identity['market_position']['budget_signals_found']}")

            # User Persona
            st.markdown("### 👥 User Persona")
            persona = data['user_persona']

            with st.expander("Demographics & Persona", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Persona Label:** {persona['persona_snapshot']['persona_label']}")
                    st.write(f"**Age Range:** {persona['demographics']['age_range'] or 'Not detected'}")
                    st.write(f"**Life Stage:** {persona['demographics']['life_stage'] or 'Not detected'}")
                    st.write(f"**Confidence:** {persona['demographics']['confidence']:.0%}")
                    st.write(f"**Source:** {persona['demographics']['source']}")
                with col2:
                    st.write(f"**Primary Motivation:** {persona['motivation_type']['primary_motivation']}")
                    st.write(f"**Confidence:** {persona['motivation_type']['confidence']:.0%}")

            # Pain Points
            with st.expander("💡 Pain Points & Problems"):
                st.write(f"**Primary Pain:** {persona['core_problem']['primary_pain']}")
                if persona['core_problem'].get('all_pains'):
                    st.write("**All Pain Points:**")
                    for pain in persona['core_problem']['all_pains']:
                        st.write(f"  - {pain}")
                st.write(f"**Confidence:** {persona['core_problem']['confidence']:.0%}")
                st.write(f"**Source:** {persona['core_problem']['source']}")

            # Voice & Tone
            st.markdown("### 🎤 Voice & Tone")
            voice = data['voice_and_tone']

            with st.expander("Tone & Communication Style", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Formality Level:** {voice['formality_level']['label']}")
                    st.write(f"**Confidence:** {voice['formality_level']['confidence']:.0%}")
                    st.write(f"**Energy Level:** {voice['energy_level']['label']}")
                    st.write(f"**POV Usage:** {voice['pov_usage']['dominant']}")
                with col2:
                    if voice.get('tone_keywords'):
                        st.write("**Detected Tones:**")
                        for tone in voice['tone_keywords'][:3]:
                            st.write(f"  - {tone['tone']}: {tone['confidence']:.0%}")

            # Visual Assets
            st.markdown("### 🎨 Visual Assets")

            # Logos
            with st.expander("Brand Logos"):
                logos = data.get('1_brand_logo', {})
                col1, col2 = st.columns(2)
                with col1:
                    if logos.get('light_logo'):
                        st.write("**Light Logo:**")
                        try:
                            st.image(logos['light_logo'], width=200)
                            # Download button for light logo
                            try:
                                logo_response = requests.get(logos['light_logo'], timeout=10)
                                if logo_response.status_code == 200:
                                    st.download_button(
                                        "⬇️ Download Light Logo",
                                        data=logo_response.content,
                                        file_name="light_logo.png",
                                        mime="image/png",
                                        key="download_light_logo"
                                    )
                            except:
                                pass
                        except:
                            st.write(logos['light_logo'])
                with col2:
                    if logos.get('dark_logo'):
                        st.write("**Dark Logo:**")
                        try:
                            st.image(logos['dark_logo'], width=200)
                            # Download button for dark logo
                            try:
                                logo_response = requests.get(logos['dark_logo'], timeout=10)
                                if logo_response.status_code == 200:
                                    st.download_button(
                                        "⬇️ Download Dark Logo",
                                        data=logo_response.content,
                                        file_name="dark_logo.png",
                                        mime="image/png",
                                        key="download_dark_logo"
                                    )
                            except:
                                pass
                        except:
                            st.write(logos['dark_logo'])

            # Colors
            with st.expander("Brand Colors"):
                colors = data.get('2_brand_colours', {}).get('colors', [])
                if colors:
                    cols = st.columns(min(len(colors), 5))
                    for idx, color in enumerate(colors[:5]):
                        with cols[idx]:
                            st.markdown(f"""
                            <div style="background-color:{color['hex']}; width:100%; height:100px; border-radius:8px; margin-bottom:8px;"></div>
                            <p style="text-align:center; margin:0;">{color['hex']}</p>
                            <p style="text-align:center; font-size:12px; color:#888;">{color.get('type', 'N/A')}</p>
                            """, unsafe_allow_html=True)

            # Messaging Rules
            st.markdown("### 📝 Messaging Rules")
            messaging = data['messaging_rules']

            with st.expander("Words to Use/Avoid"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Words to Use:**")
                    for word_data in messaging['words_to_use'][:10]:
                        st.write(f"  - {word_data['word']} (freq: {word_data['frequency']})")
                with col2:
                    st.write("**Words to Avoid:**")
                    for word in messaging['words_to_avoid']:
                        st.write(f"  - {word}")

            # Ad Content (Headlines, Taglines, CTAs)
            st.markdown("### 💬 Ad Content & Messaging")
            ad_content = data.get('ad_content', {})

            if ad_content and (ad_content.get('headlines') or ad_content.get('subtext') or ad_content.get('ctas')):
                with st.expander("Headlines, Taglines & CTAs", expanded=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if ad_content.get('headlines'):
                            st.write("**Headlines:**")
                            for headline in ad_content['headlines'][:5]:
                                st.write(f"• {headline}")

                    with col2:
                        if ad_content.get('subtext'):
                            st.write("**Taglines/Subtext:**")
                            for sub in ad_content['subtext'][:5]:
                                st.write(f"• {sub}")

                    with col3:
                        if ad_content.get('ctas'):
                            st.write("**Call-to-Actions:**")
                            for cta in ad_content['ctas'][:5]:
                                st.write(f"• {cta}")

                if ad_content.get('features'):
                    with st.expander("Product Features"):
                        st.write("**Key Features:**")
                        for feature in ad_content['features'][:10]:
                            st.write(f"• {feature}")

                if ad_content.get('ingredients'):
                    with st.expander("Ingredients (Food/Beauty/Health)"):
                        st.write("**Ingredients:**")
                        ingredients_text = ", ".join(ad_content['ingredients'][:15])
                        st.write(ingredients_text)

            # Images & Ads from site
            st.markdown("### 📸 Images & Ads from Site")
            images_ads = data.get('10_images_and_ads', {})

            if images_ads.get('ads'):
                with st.expander("Ads Found on Site"):
                    cols = st.columns(3)
                    for idx, ad in enumerate(images_ads['ads'][:6]):
                        with cols[idx % 3]:
                            try:
                                st.image(ad['url'], caption=f"Ad {idx + 1}", use_column_width=True)
                            except:
                                st.write(ad['url'])

            # Download button
            st.markdown("---")
            st.download_button(
                "📥 Download Brand Profile (JSON)",
                json.dumps(data, indent=2),
                f"{data['brand_identity']['brand_name']}_profile.json",
                "application/json",
                use_container_width=True
            )

    # ════════════════════════════════════════════════════════════
    # TAB 4: AUTO-SYNC (GOOGLE DRIVE & EXCEL INTEGRATION)
    # ════════════════════════════════════════════════════════════

    with tab4:
        st.subheader("🔄 Auto-Sync with Google Drive & Excel")
        st.markdown("### Upload & Auto-Update from Google Drive / Excel")

        st.info("""
        💡 **Feature**: Automatic Google Drive upload with Sheet logging

        **✅ Simple Setup**:
        - **ONE** `credentials.json` file works for BOTH Drive & Sheets
        - Just enable both APIs in your Google Cloud project
        - OAuth 2.0 authentication (one-time browser login)

        **✨ Automated Workflow**:
        - 🎨 **Generate** ads normally (upload images → generate)
        - 📤 **Upload** to Google Drive with one click
        - 📝 **Auto-Log** to Google Sheet: Each upload automatically adds a new row with:
          - Product Name
          - Ad Size
          - Generated At (timestamp)
          - Status ("Complete")
          - Ad URL (Drive link)
        - 📊 **Result**: Your Sheet becomes a complete log of all generated ads!
        """)

        # Configuration Section
        st.markdown("---")
        st.markdown("### 🔑 API Configuration")

        with st.expander("⚙️ Setup Instructions", expanded=False):
            st.markdown("""
            #### 🔑 One Credentials File for Both Drive & Sheets

            **IMPORTANT**: You only need **ONE** `credentials.json` file that works for **BOTH** Google Drive and Google Sheets!

            #### Step-by-Step Setup:

            **1. Create Google Cloud Project**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Create a new project (or select existing)

            **2. Enable BOTH APIs** (in the same project):
               - Click "APIs & Services" → "Enable APIs and Services"
               - Search and enable: **Google Drive API**
               - Search and enable: **Google Sheets API**

            **3. Create OAuth 2.0 Credentials** (just once!):
               - Go to "APIs & Services" → "Credentials"
               - Click "Create Credentials" → "OAuth Client ID"
               - Application type: **Desktop app**
               - Click "Create" and download the JSON file
               - Rename it to `credentials.json`

            **4. Upload Credentials** (below):
               - Upload your single `credentials.json` file
               - It will work for BOTH Drive and Sheets automatically!

            **5. Install Python Packages**:
               ```bash
               pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread
               ```

            **6. First Authentication**:
               - First time you click any sync button, browser will open
               - Sign in and grant permissions for BOTH Drive and Sheets
               - Token saved automatically for future use

            **7. Configure**:
               - Enter your Drive Folder ID (from Drive URL)
               - Enter your Google Sheet URL
               - Start syncing!
            """)

        # File upload for credentials
        st.markdown("#### 1️⃣ Upload Google API Credentials")
        st.info("📌 **One file for both Drive & Sheets**: Upload your single `credentials.json` from Google Cloud Console")

        credentials_file = st.file_uploader(
            "Upload credentials.json (works for Drive + Sheets)",
            type=["json"],
            key="google_credentials",
            help="This one file provides access to BOTH Google Drive API and Google Sheets API"
        )

        if credentials_file:
            st.success("✅ Credentials uploaded successfully! This file enables BOTH Drive and Sheets access.")
            # Save to local
            with open("credentials.json", "wb") as f:
                f.write(credentials_file.read())

            st.caption("✓ Google Drive API - Ready")
            st.caption("✓ Google Sheets API - Ready")

        # Drive Configuration
        st.markdown("---")
        st.markdown("#### 2️⃣ Google Drive Configuration")

        col1, col2 = st.columns(2)

        with col1:
            drive_folder_id = st.text_input(
                "Drive Folder ID:",
                key="drive_folder_id",
                placeholder="1a2b3c4d5e6f7g8h9i0j",
                help="Right-click folder in Drive → Share → Copy link → Extract ID"
            )

            st.caption("Example: `https://drive.google.com/drive/folders/[THIS_IS_THE_ID]`")

        with col2:
            auto_upload = st.checkbox(
                "Auto-upload generated ads to Drive",
                key="auto_upload_drive",
                help="Automatically upload all generated ads to the specified folder"
            )

        # Excel/Sheets Configuration
        st.markdown("---")
        st.markdown("#### 3️⃣ Google Sheets Configuration")

        sheet_url = st.text_input(
            "Google Sheet URL:",
            key="sheet_url",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Full URL of your Google Sheet"
        )

        if sheet_url:
            # Extract sheet ID
            import re
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
            if match:
                sheet_id = match.group(1)
                st.success(f"✅ Sheet ID extracted: `{sheet_id}`")

                # Show expected format
                with st.expander("📋 Expected Sheet Format"):
                    st.markdown("""
                    **Required Columns**:
                    | Product Name | Product URL | Price | Message | Status | Generated At | Ad URL |
                    |--------------|-------------|-------|---------|--------|--------------|--------|
                    | Lighter A    | http://...  | $29.99| Limited | Pending| -            | -      |
                    | Lighter B    | http://...  | $34.99| New     | Pending| -            | -      |

                    **Auto-Update**:
                    - App reads rows with "Status = Pending"
                    - Generates ads for those products
                    - Updates "Status = Complete"
                    - Fills "Generated At" with timestamp
                    - Adds "Ad URL" with Drive link
                    """)

                # Get worksheet names and allow selection
                if os.path.exists("credentials.json"):
                    from google_sync import get_worksheet_names

                    worksheet_names, ws_error = get_worksheet_names(sheet_url)
                    if worksheet_names:
                        selected_worksheet = st.selectbox(
                            "📋 Select Worksheet Tab:",
                            options=worksheet_names,
                            help="Choose which tab/sheet to update"
                        )
                        st.session_state.selected_worksheet = selected_worksheet
                        st.success(f"✅ Will update: **{selected_worksheet}**")
                    elif ws_error:
                        st.warning(f"⚠️ Could not fetch worksheets: {ws_error}")
                        st.info("💡 Default worksheet 'Sheet1' will be used")
                        st.session_state.selected_worksheet = 'Sheet1'
                else:
                    st.info("💡 Upload credentials.json first to select worksheet tab")
                    st.session_state.selected_worksheet = 'Sheet1'

        # Column Customization
        st.markdown("---")
        st.markdown("#### 4️⃣ Column Mapping")

        with st.expander("⚙️ Configure Columns", expanded=False):
            # Fetch existing headers from selected worksheet
            existing_headers = []
            selected_ws = st.session_state.get('selected_worksheet', 'Sheet1')

            if sheet_url and os.path.exists("credentials.json"):
                from google_sync import get_worksheet_headers

                with st.spinner("📋 Fetching existing columns..."):
                    existing_headers, header_error = get_worksheet_headers(sheet_url, selected_ws)

                if header_error:
                    st.warning(f"⚠️ Could not fetch headers: {header_error}")
                    existing_headers = []
                elif existing_headers:
                    st.success(f"✅ Found {len(existing_headers)} existing column(s) in '{selected_ws}'")
                else:
                    st.info("📝 Sheet is empty. You can create new columns below.")
            else:
                st.info("💡 Upload credentials and enter Sheet URL to fetch existing columns")

            st.markdown("---")

            # Available data fields
            data_field_options = {
                "Product Name": "product_name",
                "Ad Size": "size",
                "Generated At": "generated_at",
                "Status": "status",
                "Ad URL": "drive_link",
                "-- Don't Use --": None
            }

            # Show existing headers with mapping options
            if existing_headers:
                st.markdown("**Existing Columns from Sheet:**")

                column_selections = {}

                for idx, header in enumerate(existing_headers):
                    col_check, col_map = st.columns([2, 3])

                    with col_check:
                        use_column = st.checkbox(
                            f"Use: {header}",
                            value=True,
                            key=f"use_header_{idx}"
                        )

                    with col_map:
                        # Try to auto-match based on header name
                        default_match = "-- Don't Use --"
                        header_lower = header.lower()
                        if "product" in header_lower or "name" in header_lower:
                            default_match = "Product Name"
                        elif "size" in header_lower or "dimension" in header_lower:
                            default_match = "Ad Size"
                        elif "generate" in header_lower or "date" in header_lower or "time" in header_lower:
                            default_match = "Generated At"
                        elif "status" in header_lower:
                            default_match = "Status"
                        elif "url" in header_lower or "link" in header_lower or "drive" in header_lower:
                            default_match = "Ad URL"

                        mapped_to = st.selectbox(
                            "Maps to:",
                            options=list(data_field_options.keys()),
                            index=list(data_field_options.keys()).index(default_match),
                            key=f"map_header_{idx}",
                            disabled=not use_column
                        )

                    if use_column and data_field_options[mapped_to] is not None:
                        column_selections[header] = data_field_options[mapped_to]

                st.markdown("---")

            # Allow creating new columns
            st.markdown("**Or Create New Columns:**")

            new_column_selections = {}

            # Product Name Column
            col_check1, col_input1, col_map1 = st.columns([1, 2, 2])
            with col_check1:
                enable_new_product = st.checkbox("Add", value=not existing_headers, key="enable_new_product")
            with col_input1:
                new_col_product = st.text_input("Column Name:", value="Product Name", key="new_col_product", disabled=not enable_new_product)
            with col_map1:
                st.selectbox("Maps to:", ["Product Name"], key="map_new_product", disabled=True)

            if enable_new_product:
                new_column_selections[new_col_product] = "product_name"

            # Ad Size Column
            col_check2, col_input2, col_map2 = st.columns([1, 2, 2])
            with col_check2:
                enable_new_size = st.checkbox("Add", value=not existing_headers, key="enable_new_size")
            with col_input2:
                new_col_size = st.text_input("Column Name:", value="Ad Size", key="new_col_size", disabled=not enable_new_size)
            with col_map2:
                st.selectbox("Maps to:", ["Ad Size"], key="map_new_size", disabled=True)

            if enable_new_size:
                new_column_selections[new_col_size] = "size"

            # Generated At Column
            col_check3, col_input3, col_map3 = st.columns([1, 2, 2])
            with col_check3:
                enable_new_generated = st.checkbox("Add", value=not existing_headers, key="enable_new_generated")
            with col_input3:
                new_col_generated = st.text_input("Column Name:", value="Generated At", key="new_col_generated", disabled=not enable_new_generated)
            with col_map3:
                st.selectbox("Maps to:", ["Generated At"], key="map_new_generated", disabled=True)

            if enable_new_generated:
                new_column_selections[new_col_generated] = "generated_at"

            # Status Column
            col_check4, col_input4, col_map4 = st.columns([1, 2, 2])
            with col_check4:
                enable_new_status = st.checkbox("Add", value=not existing_headers, key="enable_new_status")
            with col_input4:
                new_col_status = st.text_input("Column Name:", value="Status", key="new_col_status", disabled=not enable_new_status)
            with col_map4:
                st.selectbox("Maps to:", ["Status"], key="map_new_status", disabled=True)

            if enable_new_status:
                new_column_selections[new_col_status] = "status"

            # Ad URL Column
            col_check5, col_input5, col_map5 = st.columns([1, 2, 2])
            with col_check5:
                enable_new_url = st.checkbox("Add", value=not existing_headers, key="enable_new_url")
            with col_input5:
                new_col_url = st.text_input("Column Name:", value="Ad URL", key="new_col_url", disabled=not enable_new_url)
            with col_map5:
                st.selectbox("Maps to:", ["Ad URL"], key="map_new_url", disabled=True)

            if enable_new_url:
                new_column_selections[new_col_url] = "drive_link"

            # Merge existing and new column selections
            if existing_headers:
                all_selections = column_selections
            else:
                all_selections = new_column_selections

            # Build column mapping and enabled columns for upload
            st.session_state.column_mapping = {}
            st.session_state.enabled_columns = []
            st.session_state.column_order = []

            for col_name, data_field in all_selections.items():
                st.session_state.column_mapping[data_field] = col_name
                st.session_state.enabled_columns.append(data_field)
                st.session_state.column_order.append((data_field, col_name))

            st.caption(f"✅ {len(st.session_state.enabled_columns)} column(s) configured")

        # Sync Actions
        st.markdown("---")
        st.markdown("### 🔄 Sync Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Upload to Drive", use_container_width=True):
                if not drive_folder_id:
                    st.error("❌ Please enter a Google Drive folder ID first")
                elif not os.path.exists("credentials.json"):
                    st.error("❌ Please upload credentials.json first")
                elif not st.session_state.results:
                    st.error("❌ No generated ads to upload. Generate some ads first!")
                else:
                    # Check if there are any non-removed ads to upload
                    removed_ads = st.session_state.get('removed_ads', set())
                    ads_to_upload = [r for idx, r in enumerate(st.session_state.results) if idx not in removed_ads]

                    if not ads_to_upload:
                        st.error("❌ No ads selected. All ads have been removed.")
                    else:
                        try:
                            from google_sync import check_google_libraries, batch_upload_to_drive
                            import tempfile

                            # Check if libraries are installed
                            libs_ok, lib_error = check_google_libraries()
                            if not libs_ok:
                                st.error(f"❌ {lib_error}\n\nInstall with:\n```bash\npip install google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread\n```")
                            else:
                                # Save results to temporary files (only non-removed ads)
                                temp_files = []
                                file_to_result_map = {}  # Map temp file to result info
                                for idx, result in enumerate(st.session_state.results):
                                    if idx not in removed_ads:
                                        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                                        result['img'].save(temp_file.name, format='PNG')
                                        temp_files.append(temp_file.name)
                                        file_to_result_map[temp_file.name] = {
                                            'index': idx,
                                            'name': result.get('name', f'Ad_{idx}')
                                        }

                                # Upload with progress
                                progress_placeholder = st.empty()

                                def progress_callback(current, total, filename):
                                    progress_placeholder.progress(current / total, text=f"Uploading {current}/{total}: {filename}")

                                with st.spinner("📤 Uploading to Drive..."):
                                    upload_results = batch_upload_to_drive(temp_files, drive_folder_id, progress_callback)

                                # Show results
                                success_count = sum(1 for r in upload_results.values() if r['status'] == 'success')
                                st.success(f"✅ Uploaded {success_count}/{len(upload_results)} files to Drive!")

                                # Add to Google Sheet if Sheet URL is provided
                                if sheet_url:
                                    from google_sync import append_ads_to_sheet_custom
                                    from datetime import datetime

                                    st.info("📝 Adding ads to Google Sheet...")

                                    # Prepare ads data to append
                                    ads_data = []
                                    for temp_file, upload_result in upload_results.items():
                                        if upload_result['status'] == 'success':
                                            result_info = file_to_result_map.get(temp_file, {})
                                            result_index = result_info.get('index', 0)
                                            result_obj = st.session_state.results[result_index]

                                            # Extract product name from the ad name or use default
                                            product_name = result_info.get('name', f'Ad_{result_index}')
                                            # Clean up the name (remove size info if present)
                                            product_name = product_name.split('-')[0] if '-' in product_name else product_name

                                            ads_data.append({
                                                'product_name': product_name,
                                                'size': result_obj.get('size', 'Unknown'),
                                                'drive_link': upload_result.get('url', ''),
                                                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            })

                                    # Get selected worksheet, column mapping, and enabled columns from session state
                                    selected_worksheet = st.session_state.get('selected_worksheet', 'Sheet1')
                                    column_mapping = st.session_state.get('column_mapping', None)
                                    enabled_columns = st.session_state.get('enabled_columns', None)

                                    # Append to sheet
                                    if ads_data:
                                        append_results = append_ads_to_sheet_custom(
                                            sheet_url,
                                            ads_data,
                                            sheet_name=selected_worksheet,
                                            column_mapping=column_mapping,
                                            enabled_columns=enabled_columns
                                        )
                                        if append_results['succeeded'] > 0:
                                            st.success(f"✅ Added {append_results['succeeded']} row(s) to Google Sheet ('{selected_worksheet}')!")
                                        if append_results['failed'] > 0:
                                            st.warning(f"⚠️ Failed to add {append_results['failed']} row(s)")
                                            for error in append_results['errors']:
                                                st.error(error)

                                # Clean up temp files
                                for temp_file in temp_files:
                                    try:
                                        os.unlink(temp_file)
                                    except:
                                        pass

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

        with col2:
            if st.button("🔄 Full Sync", use_container_width=True):
                if not sheet_url or not drive_folder_id:
                    st.error("❌ Please configure both Sheet URL and Drive folder ID")
                elif not os.path.exists("credentials.json"):
                    st.error("❌ Please upload credentials.json first")
                else:
                    try:
                        from google_sync import check_google_libraries

                        # Check if libraries are installed
                        libs_ok, lib_error = check_google_libraries()
                        if not libs_ok:
                            st.error(f"❌ {lib_error}\n\nInstall with:\n```bash\npip install google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread\n```")
                        else:
                            st.success("""
                            ✅ **Full Sync Ready!**

                            Your workflow automation is configured. Here's how to use it:

                            **Step 1:** Generate Ads
                            - Go to the "🎨 Generate Ads" tab
                            - Upload product images and create ads normally

                            **Step 2:** Click "📤 Upload to Drive"
                            - Uploads all generated ads to your Google Drive folder
                            - **Automatically adds to your Google Sheet**:
                              - Product Name
                              - Ad Size (dimensions)
                              - Generated At (timestamp)
                              - Status ("Complete")
                              - Ad URL (Drive link)

                            **Result:** Your Google Sheet becomes a complete log of all generated ads! 🎉

                            **Note:** The Sheet can start empty. Headers will be added automatically if needed.
                            """)

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        # Implementation Status
        st.markdown("---")
        st.markdown("### 📊 Implementation Status")

        implementation_status = {
            "Google Drive API Integration": "🟡 In Progress",
            "Google Sheets API Integration": "🟡 In Progress",
            "OAuth 2.0 Authentication": "🟡 In Progress",
            "Auto-upload generated ads": "🟡 In Progress",
            "Read products from Sheet": "🟡 In Progress",
            "Update Sheet with status": "🟡 In Progress",
            "Batch sync workflow": "🟡 In Progress"
        }

        for feature, status in implementation_status.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{feature}**")
            with col2:
                st.write(status)

        st.info("""
        💡 **Note**: This feature requires additional setup and Google API credentials.

        **Quick Start**:
        1. Set up Google Cloud project
        2. Enable Drive & Sheets APIs
        3. Create OAuth credentials
        4. Upload credentials.json above
        5. Enter Drive folder ID and Sheet URL
        6. Click sync buttons to start

        **Benefits**:
        - Bulk product management via Excel
        - Automatic ad generation from sheet data
        - Cloud storage for all generated ads
        - Team collaboration on same sheet
        - Version history in Drive
        """)


if __name__ == "__main__":
    main()
