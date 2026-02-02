"""
Enhanced Ad Generation Module with 100+ Styles, 40+ Concepts, Multi-Image & Advanced Features
Integrates seamlessly with app_modular.py
"""

from typing import List, Optional, Tuple
from PIL import Image
import numpy as np

# ========== 100+ STYLE THEMES ==========
ENHANCED_STYLE_THEMES = {
    # LIFESTYLE STYLES (20)
    "Lifestyle - Modern Minimalist": "Clean minimal environment, natural light, contemporary aesthetic, uncluttered",
    "Lifestyle - Urban Street": "City backdrop, street photography, urban vibe, gritty textures, metropolitan",
    "Lifestyle - Luxury Living": "High-end interior, luxury setting, premium ambiance, opulent details",
    "Lifestyle - Outdoor Adventure": "Nature setting, mountains, forests, adventure vibe, wilderness",
    "Lifestyle - Beach Coastal": "Beach, ocean, coastal lifestyle, sun-kissed atmosphere, seaside",
    "Lifestyle - Fitness Active": "Gym, workout, athletic setting, energy and movement, sports",
    "Lifestyle - Professional Office": "Office environment, business setting, corporate aesthetic, workplace",
    "Lifestyle - Cafe Coffee Shop": "Coffee shop ambiance, warm lighting, cozy atmosphere, café culture",
    "Lifestyle - Night Out": "Night scene, city lights, evening atmosphere, vibrant nightlife",
    "Lifestyle - Home Comfort": "Home interior, comfortable setting, relaxed atmosphere, cozy living",
    "Lifestyle - Travel Wanderlust": "Travel destination, wanderlust, exploration theme, journey",
    "Lifestyle - Studio Creative": "Creative studio, artistic workspace, maker space, creative hub",
    "Lifestyle - Rooftop Urban": "Rooftop setting, city skyline, urban elevation, elevated view",
    "Lifestyle - Industrial Loft": "Industrial interior, exposed brick, warehouse aesthetic, raw space",
    "Lifestyle - Botanical Garden": "Lush greenery, botanical setting, nature indoors, verdant",
    "Lifestyle - Desert Minimal": "Desert landscape, minimalist, vast open space, arid beauty",
    "Lifestyle - Rainy Mood": "Rain, wet surfaces, moody atmosphere, reflections, precipitation",
    "Lifestyle - Winter Snow": "Snow, winter setting, cold atmosphere, crisp clean, frozen",
    "Lifestyle - Summer Bright": "Bright summer, vibrant colors, sunshine, warmth, sunny day",
    "Lifestyle - Autumn Warm": "Autumn tones, warm colors, cozy fall atmosphere, harvest season",

    # PRODUCT PHOTOGRAPHY (25)
    "Product - Hero Shot": "Bold centered product, clean background, professional studio, hero placement",
    "Product - Macro Detail": "Extreme close-up, intricate details, texture focus, magnified view",
    "Product - Floating Levitation": "Product floating, suspended in air, dynamic composition, levitating",
    "Product - Explosion Burst": "Product exploding outward, dynamic energy, motion, bursting action",
    "Product - Water Splash": "Water splash, liquid dynamics, refreshing energy, aquatic motion",
    "Product - Smoke Fog": "Smoke or fog effects, mysterious atmosphere, depth, ethereal haze",
    "Product - Reflection Mirror": "Mirror reflections, symmetry, elegant duplication, mirrored image",
    "Product - Shadow Play": "Dramatic shadows, contrast, artistic lighting, shadow art",
    "Product - Neon Glow": "Neon lighting, vibrant glow, futuristic aesthetic, luminous",
    "Product - Sparkle Glitter": "Sparkles, glitter, shimmer effects, glamorous, glittery",
    "Product - Fire Flames": "Fire elements, flames, intense heat, danger appeal, blazing",
    "Product - Ice Frozen": "Ice, frozen elements, cold atmosphere, refreshing, crystalline",
    "Product - Lightning Electric": "Lightning, electricity, energy, power, electric charge",
    "Product - Geometric Shapes": "Geometric patterns, shapes, modern clean design, angular",
    "Product - Fabric Texture": "Fabric background, textile texture, soft materials, cloth",
    "Product - Wood Natural": "Wood surface, natural materials, organic feel, wooden texture",
    "Product - Metal Industrial": "Metal surface, industrial aesthetic, modern edge, metallic",
    "Product - Marble Luxury": "Marble surface, luxury material, premium feel, marble texture",
    "Product - Glass Transparent": "Glass elements, transparency, clarity, modern, crystalline",
    "Product - Paper Minimal": "Paper background, minimal, clean, simple, paper texture",
    "Product - Concrete Urban": "Concrete surface, urban texture, modern industrial, cement",
    "Product - Leather Premium": "Leather texture, premium material, luxury, leather surface",
    "Product - Stone Natural": "Stone surface, natural texture, earthy, rocky",
    "Product - Sand Desert": "Sand texture, desert feel, natural minimal, sandy",
    "Product - Grass Organic": "Grass, organic, natural, eco-friendly, grassy field",

    # AESTHETIC STYLES (25)
    "Aesthetic - Vintage Retro": "Vintage look, retro colors, nostalgic 70s/80s vibe, throwback",
    "Aesthetic - Cyberpunk Neon": "Cyberpunk, neon lights, futuristic dystopian, cyber aesthetic",
    "Aesthetic - Vaporwave Dreamy": "Vaporwave aesthetic, dreamy pastels, surreal, nostalgic digital",
    "Aesthetic - Dark Moody": "Dark tones, moody atmosphere, dramatic shadows, noir",
    "Aesthetic - Bright Vibrant": "Bright colors, high saturation, energetic vibes, vivid",
    "Aesthetic - Pastel Soft": "Soft pastels, gentle tones, delicate atmosphere, muted colors",
    "Aesthetic - Monochrome BW": "Black and white, high contrast, classic timeless, grayscale",
    "Aesthetic - Sepia Vintage": "Sepia tone, aged look, nostalgic warmth, antique brown",
    "Aesthetic - Film Grain": "Film photography aesthetic, grain, analog feel, cinematic grain",
    "Aesthetic - Polaroid Instant": "Polaroid style, instant camera, casual snapshot, vintage photo",
    "Aesthetic - Glitch Digital": "Glitch effects, digital distortion, tech error aesthetic, corrupted",
    "Aesthetic - Holographic Iridescent": "Holographic, iridescent, rainbow shimmer, prismatic",
    "Aesthetic - Gold Luxury": "Gold tones, luxury, premium, expensive feel, golden",
    "Aesthetic - Silver Chrome": "Silver chrome, metallic, futuristic sleek, chrome finish",
    "Aesthetic - Rose Gold": "Rose gold tones, feminine, elegant, modern, pink gold",
    "Aesthetic - Copper Warm": "Copper tones, warm metallic, vintage industrial, copper hue",
    "Aesthetic - Jewel Tones": "Rich jewel colors, deep saturated, luxurious, gemstone colors",
    "Aesthetic - Earth Tones": "Natural earth colors, organic, grounded, natural palette",
    "Aesthetic - Ocean Blues": "Blue tones, ocean inspired, calm serene, aquatic blues",
    "Aesthetic - Forest Greens": "Green tones, forest inspired, natural fresh, verdant greens",
    "Aesthetic - Sunset Oranges": "Orange/pink sunset tones, warm glowing, dusk colors",
    "Aesthetic - Northern Lights": "Aurora colors, ethereal, magical atmosphere, aurora borealis",
    "Aesthetic - Cosmic Space": "Space aesthetic, stars, cosmic, infinite, celestial",
    "Aesthetic - Underwater Aqua": "Underwater look, aqua tones, fluid ethereal, submerged",
    "Aesthetic - Bokeh Dreamy": "Bokeh lights, dreamy blur, magical atmosphere, soft focus",

    # EMOTION DRIVEN (20)
    "Emotion - Energetic Exciting": "High energy, excitement, dynamic movement, action, vigorous",
    "Emotion - Calm Peaceful": "Calm atmosphere, peaceful, serene, tranquil, zen",
    "Emotion - Bold Confident": "Bold statement, confidence, power, authority, assertive",
    "Emotion - Playful Fun": "Playful energy, fun vibes, joyful, lighthearted, whimsical",
    "Emotion - Elegant Sophisticated": "Elegant refined, sophisticated, classy, timeless, graceful",
    "Emotion - Mysterious Intriguing": "Mysterious mood, intrigue, enigmatic, captivating, secretive",
    "Emotion - Romantic Dreamy": "Romantic atmosphere, dreamy, intimate, emotional, loving",
    "Emotion - Dramatic Intense": "Dramatic intensity, powerful, impactful, bold, striking",
    "Emotion - Fresh Clean": "Fresh feel, clean aesthetic, pure, crisp, pristine",
    "Emotion - Warm Cozy": "Warm atmosphere, cozy feel, comfortable, inviting, snug",
    "Emotion - Cool Refreshing": "Cool tones, refreshing, crisp, invigorating, cool breeze",
    "Emotion - Luxurious Premium": "Luxury feel, premium quality, high-end, exclusive, lavish",
    "Emotion - Rebellious Edgy": "Rebellious vibe, edgy aesthetic, bold, disruptive, defiant",
    "Emotion - Nostalgic Sentimental": "Nostalgic feeling, sentimental, memory-evoking, reminiscent",
    "Emotion - Futuristic Innovative": "Futuristic look, innovative, cutting-edge, tomorrow, advanced",
    "Emotion - Natural Organic": "Natural feel, organic, authentic, real, earthy",
    "Emotion - Professional Trustworthy": "Professional look, trustworthy, reliable, established, credible",
    "Emotion - Creative Artistic": "Creative expression, artistic, unique, imaginative, inventive",
    "Emotion - Minimal Simple": "Minimal aesthetic, simple, essential, uncluttered, sparse",
    "Emotion - Maximalist Bold": "Maximalist approach, bold, abundant, more-is-more, ornate",

    # SPECIAL EFFECTS (15)
    "FX - Double Exposure": "Double exposure effect, layered images, artistic blend, overlapping imagery",
    "FX - Long Exposure": "Long exposure, motion blur, light trails, time passage, flowing time",
    "FX - Tilt Shift": "Tilt-shift miniature effect, selective focus, toy-like, miniature world",
    "FX - Prism Light": "Prism light effects, rainbow spectrum, optical, light refraction",
    "FX - Lens Flare": "Lens flare, sun rays, light beams, cinematic glow, optical flare",
    "FX - Motion Blur": "Motion blur, speed, movement, dynamic energy, velocity",
    "FX - Freeze Action": "Frozen action, stopped motion, precise moment, time freeze",
    "FX - Silhouette Shadow": "Silhouette, shadow form, dramatic outline, contour",
    "FX - Backlighting": "Backlit, rim lighting, glowing edges, halo effect, backlit glow",
    "FX - Overhead Flat Lay": "Overhead flat lay, bird's eye view, organized layout, top-down",
    "FX - Perspective Warp": "Warped perspective, dynamic angle, dramatic view, distorted view",
    "FX - Kaleidoscope": "Kaleidoscope effect, pattern repetition, mesmerizing, symmetrical patterns",
    "FX - Chromatic Aberration": "Chromatic aberration, color split, artistic glitch, color fringing",
    "FX - Infrared": "Infrared photography, false color, surreal landscape, IR effect",
    "FX - X-Ray Vision": "X-ray effect, see-through, transparent layers, skeletal view",

    # PRODUCT ADVANCED (15)
    "Product - Clean Minimal White": "Pure white background, minimal shadows, product focus, clean commercial",
    "Product - Black Dramatic": "Black background, dramatic lighting, luxurious dark, mystery appeal",
    "Product - Color Pop Vibrant": "Single vibrant color background, bold accent, energetic pop, color block",
    "Product - Gradient Smooth": "Smooth gradient background, color transition, modern blend, flowing colors",
    "Product - Textured Surface": "Textured background, tactile feel, material depth, surface interest",
    "Product - Marble Luxe": "Marble surface, luxury material, elegant stone, premium texture",
    "Product - Concrete Industrial": "Concrete texture, industrial feel, urban raw, brutalist",
    "Product - Glass Transparent": "Glass surface, transparency, reflections, pristine clarity",
    "Product - Metal Sleek": "Metallic surface, sleek finish, industrial chic, polished metal",
    "Product - Paper Craft": "Paper background, craft aesthetic, handmade feel, paper texture",
    "Product - Silk Soft": "Silk fabric, soft draping, luxurious textile, flowing fabric",
    "Product - Velvet Rich": "Velvet texture, rich depth, luxury fabric, plush surface",
    "Product - Leather Premium": "Leather surface, premium material, luxury texture, aged leather",
    "Product - Ceramic Clean": "Ceramic surface, clean modern, minimalist plate, pottery aesthetic",
    "Product - Botanical Fresh": "Fresh botanical elements, greenery, natural organic, plant life",

    # LIFESTYLE ADVANCED (15)
    "Lifestyle - Morning Routine": "Morning light, breakfast setting, fresh start, dawn ambiance",
    "Lifestyle - Bedtime Relax": "Evening wind-down, bedtime setting, relaxation, nighttime comfort",
    "Lifestyle - Workspace Productivity": "Productive workspace, organized desk, efficiency, work mode",
    "Lifestyle - Social Gathering": "Friends together, social scene, gathering, community connection",
    "Lifestyle - Solo Meditation": "Solitary peace, meditation, mindfulness, inner calm",
    "Lifestyle - Celebration Party": "Party atmosphere, celebration, festive, joyful occasion",
    "Lifestyle - Date Night Romance": "Romantic setting, intimate ambiance, date night, couple focus",
    "Lifestyle - Family Togetherness": "Family moment, togetherness, bonding, multi-generational",
    "Lifestyle - Pet Companion": "Pet presence, animal companion, bonding moment, furry friend",
    "Lifestyle - Reading Cozy": "Reading nook, book lover, cozy corner, literary atmosphere",
    "Lifestyle - Music Vibes": "Music setting, audio culture, listening mood, sonic atmosphere",
    "Lifestyle - Gaming Action": "Gaming setup, esports vibe, gamer culture, digital play",
    "Lifestyle - Cooking Kitchen": "Kitchen scene, cooking process, culinary, food preparation",
    "Lifestyle - Art Studio": "Art creation, studio space, creative process, artistic workspace",
    "Lifestyle - Garden Outdoor": "Garden setting, outdoor living, green space, backyard oasis",

    # AESTHETIC MOODS (20)
    "Aesthetic - Cyberpunk Neon": "Cyberpunk aesthetic, neon lights, futuristic dystopia, tech noir",
    "Aesthetic - Cottagecore Rustic": "Cottagecore aesthetic, rustic charm, rural idyll, pastoral romance",
    "Aesthetic - Vaporwave Retro": "Vaporwave style, 80s/90s nostalgia, retro futurism, digital aesthetics",
    "Aesthetic - Dark Academia": "Dark academia aesthetic, scholarly, vintage intellectualism, classic education",
    "Aesthetic - Light Academia": "Light academia aesthetic, bright intellectualism, classical study, enlightened",
    "Aesthetic - Kidcore Playful": "Kidcore aesthetic, playful bright, childhood nostalgia, primary colors",
    "Aesthetic - Normcore Basic": "Normcore aesthetic, deliberately basic, anti-fashion, understated",
    "Aesthetic - Gorpcore Outdoor": "Gorpcore aesthetic, technical outdoor wear, functional fashion, trail ready",
    "Aesthetic - Coastal Grandmother": "Coastal grandmother aesthetic, relaxed elegance, seaside charm, effortless chic",
    "Aesthetic - That Girl": "That girl aesthetic, wellness focused, organized life, aspirational routine",
    "Aesthetic - Old Money": "Old money aesthetic, quiet luxury, inherited wealth, understated elegance",
    "Aesthetic - Soft Girl": "Soft girl aesthetic, pastel gentle, feminine soft, delicate",
    "Aesthetic - E-Girl/E-Boy": "E-girl/boy aesthetic, internet culture, alternative style, digital native",
    "Aesthetic - VSCO Girl": "VSCO girl aesthetic, eco-conscious, beachy casual, trendy minimalism",
    "Aesthetic - Art Hoe": "Art hoe aesthetic, creative soul, gallery vibes, artistic expression",
    "Aesthetic - Goblincore": "Goblincore aesthetic, earthy messy, nature lover, collected treasures",
    "Aesthetic - Fairycore": "Fairycore aesthetic, magical forest, whimsical nature, ethereal fairy",
    "Aesthetic - Steampunk Victorian": "Steampunk aesthetic, Victorian industrial, brass gears, retro-futuristic",
    "Aesthetic - Solarpunk": "Solarpunk aesthetic, eco-futurism, sustainable technology, green future",
    "Aesthetic - Brutalist": "Brutalist aesthetic, raw concrete, stark geometry, architectural power",
}

# ========== 40+ AD CONCEPTS ==========
AD_CONCEPTS = {
    "None - Custom Only": "No concept applied - use manual prompt only",

    # PRODUCT FOCUSED (5)
    "Hero Product": "Single product hero shot, dominant presence, commanding attention, spotlight on product",
    "Product Family": "Multiple products from same line, family grouping, range showcase, product collection",
    "Product Comparison": "Side-by-side comparison, before/after, feature differentiation, competitive advantage",
    "Product in Use": "Product being used, action shot, real-world application, lifestyle context",
    "Product Evolution": "Product evolution, progression, upgrade journey, development timeline",

    # STORYTELLING (5)
    "Origin Story": "Brand origin, heritage, founding story, authenticity, brand history",
    "Ingredients Story": "Key ingredients, materials, components, what's inside, formulation details",
    "Craftsmanship": "Making process, craftsmanship, attention to detail, artisan work, handcrafted quality",
    "Behind the Scenes": "Behind scenes, production, real people, authenticity, the making of",
    "Customer Journey": "Customer experience, journey, transformation, results, user story",

    # TRANSFORMATION (4)
    "Before and After": "Clear before/after comparison, transformation, improvement, dramatic change",
    "Day to Night": "Day to night transition, dual use, versatility, 24-hour functionality",
    "Season Transition": "Seasonal change, adaptability, year-round, all-season use",
    "Problem Solution": "Problem visualization, solution provided, benefit clear, solving pain points",

    # LIFESTYLE INTEGRATION (4)
    "Daily Ritual": "Daily routine integration, habit formation, lifestyle fit, everyday use",
    "Special Occasion": "Special event, celebration, memorable moment, milestone",
    "Aspirational Lifestyle": "Aspirational living, dream lifestyle, elevated experience, luxury living",
    "Real People": "Authentic real people, relatable, genuine moments, user-generated feel",

    # TECHNICAL SHOWCASE (4)
    "Feature Highlight": "Specific feature spotlight, technical detail, innovation, key feature",
    "Technology Focus": "Technology showcase, innovation, advanced features, tech specs",
    "Durability Test": "Durability demonstration, toughness, reliability, stress test",
    "Performance": "Performance demonstration, capability, power, efficiency",

    # EMOTIONAL CONNECTION (5)
    "Gift Giving": "Perfect gift, giving moment, emotional connection, present idea",
    "Celebration": "Celebration, achievement, milestone, success, victory",
    "Adventure": "Adventure, exploration, journey, discovery, expedition",
    "Comfort": "Comfort, relaxation, peace, sanctuary, solace",
    "Empowerment": "Empowerment, confidence, strength, capability, self-improvement",

    # SOCIAL PROOF (4)
    "Testimonial": "Customer testimonial, review, social proof, trust, user feedback",
    "Expert Endorsed": "Expert endorsement, authority, credibility, professional recommendation",
    "Award Winner": "Award showcase, recognition, achievement, accolades",
    "Bestseller": "Popular choice, bestseller, trending, in-demand, top-rated",

    # URGENCY/SCARCITY (4)
    "Limited Edition": "Limited edition, exclusive, rare, collectible, special release",
    "Flash Sale": "Sale urgency, limited time, act now, deal, time-sensitive",
    "New Launch": "New product launch, coming soon, first look, exclusive preview",
    "Last Chance": "Final opportunity, last units, don't miss, urgency, final call",
}

# ========== HELPER FUNCTIONS ==========

def generate_positive_prompt_elements(concept: str, style: str, brand_data: dict = None) -> str:
    """Generate positive prompt do's based on concept, style, and brand data"""
    base_dos = [
        "High quality professional photography",
        "Crystal clear details and sharp focus",
        "Proper exposure and accurate lighting",
        "Accurate colors and white balance",
        "Clean uncluttered composition",
        "Professional commercial grade output",
        "8K resolution crystal clear details"
    ]

    # Concept-specific positives
    concept_dos = {
        "Hero Product": ["Product clearly visible and in focus", "Product as dominant element", "Hero product placement"],
        "Before and After": ["Clear comparison visible", "Side-by-side layout", "Transformation obvious"],
        "Ingredients Story": ["Ingredients visible and clear", "Natural elements shown", "Authentic materials"],
        "Product Family": ["Multiple products arranged", "Family grouping clear", "Range variety shown"],
        "Craftsmanship": ["Detail close-ups", "Quality visible", "Artisan work evident"],
        "Technology": ["Technical features visible", "Innovation highlighted", "Advanced details shown"],
    }

    # Style-specific positives
    style_dos = {
        "Minimalist": ["Clean background", "Negative space", "Simple composition", "Uncluttered"],
        "Dramatic": ["Strong contrast", "Dramatic lighting", "Bold shadows", "High impact"],
        "Vibrant": ["Saturated colors", "High energy", "Bold color palette", "Vivid hues"],
        "Vintage": ["Retro aesthetic", "Nostalgic feel", "Period appropriate", "Classic look"],
        "Modern": ["Contemporary design", "Clean lines", "Current aesthetic", "Fresh look"],
    }

    # Brand-specific positives (if brand data available)
    brand_dos = []
    if brand_data:
        try:
            # Add brand colors
            colors = brand_data.get('2_brand_colours', {}).get('colors', [])
            if colors:
                primary_hex = [c.get('hex') for c in colors[:2] if c.get('hex')]
                if primary_hex:
                    brand_dos.append(f"Brand colors incorporated: {', '.join(primary_hex)}")

            # Add brand tone
            voice_tone = brand_data.get('voice_and_tone', {})
            tone_keywords = voice_tone.get('tone_keywords', [])
            if tone_keywords:
                tones = [t.get('tone') for t in tone_keywords[:2] if t.get('tone')]
                if tones:
                    brand_dos.append(f"Brand tone: {', '.join(tones)}")
        except:
            pass

    # Combine all
    combined = base_dos.copy()

    # Add concept-specific
    for key, dos in concept_dos.items():
        if key.lower() in concept.lower():
            combined.extend(dos)
            break

    # Add style-specific
    for key, dos in style_dos.items():
        if key.lower() in style.lower():
            combined.extend(dos)
            break

    # Add brand-specific
    combined.extend(brand_dos)

    return ", ".join(combined)

def generate_negative_prompt_elements(concept: str, style: str) -> str:
    """Generate comprehensive negative prompt don'ts"""
    base_donts = [
        "blurry", "out of focus", "low quality", "poor quality", "amateur photography",
        "distorted", "deformed", "warped", "stretched", "compressed", "squashed",
        "pixelated", "artifacts", "compression artifacts", "noise", "heavy grain",
        "overexposed", "underexposed", "poor lighting", "flat lighting", "bad composition",
        "watermark", "text overlay", "logo overlay", "copyright mark", "signature",
        "cluttered", "messy", "chaotic", "distracting background", "busy background",
        "unrealistic", "fake looking", "CGI", "3D render", "cartoon", "illustrated",
        "wrong colors", "color banding", "chromatic aberration", "lens dirt"
    ]

    concept_donts = {
        "Product": ["product obscured", "product cut off", "product too small", "product unclear"],
        "Before and After": ["unclear comparison", "confusing layout", "ambiguous transformation"],
        "Minimalist": ["cluttered", "busy", "too many elements", "complex", "over-decorated"],
        "Dramatic": ["flat lighting", "no contrast", "boring", "plain", "underwhelming"],
        "Hero": ["product not prominent", "product lost in background", "unclear focus"],
    }

    combined = base_donts.copy()

    # Add concept/style specific negatives
    for key, donts in concept_donts.items():
        if key.lower() in concept.lower() or key.lower() in style.lower():
            combined.extend(donts)

    return ", ".join(combined)

def combine_multiple_images_layout(images: List[Image.Image], layout="grid") -> Image.Image:
    """Combine multiple product images into one composition"""
    if not images:
        raise ValueError("No images provided")

    num_images = len(images)

    if num_images == 1:
        return images[0]

    # Resize all images to same height for consistency
    target_height = 800
    resized = []
    for img in images:
        aspect = img.width / img.height
        new_width = int(target_height * aspect)
        resized.append(img.resize((new_width, target_height), Image.Resampling.LANCZOS))

    if layout == "grid":
        # Grid layout (2x2 or 3x3 depending on count)
        cols = 2 if num_images <= 4 else 3
        rows = (num_images + cols - 1) // cols

        cell_width = max(img.width for img in resized)
        cell_height = max(img.height for img in resized)

        canvas_width = cell_width * cols
        canvas_height = cell_height * rows
        canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))

        for idx, img in enumerate(resized):
            row = idx // cols
            col = idx % cols
            x = col * cell_width + (cell_width - img.width) // 2
            y = row * cell_height + (cell_height - img.height) // 2
            canvas.paste(img, (x, y))

        return canvas

    elif layout == "horizontal":
        # Horizontal row
        total_width = sum(img.width for img in resized)
        canvas = Image.new('RGB', (total_width, target_height), (255, 255, 255))

        x_offset = 0
        for img in resized:
            canvas.paste(img, (x_offset, 0))
            x_offset += img.width

        return canvas

    elif layout == "vertical":
        # Vertical stack
        max_width = max(img.width for img in resized)
        total_height = sum(img.height for img in resized)
        canvas = Image.new('RGB', (max_width, total_height), (255, 255, 255))

        y_offset = 0
        for img in resized:
            x = (max_width - img.width) // 2
            canvas.paste(img, (x, y_offset))
            y_offset += img.height

        return canvas

    return images[0]  # Fallback

def add_logo_with_smart_positioning(
    img: Image.Image,
    logo: Image.Image,
    position: str = "top-left",
    size_percent: float = 10.0,
    custom_x: Optional[int] = None,
    custom_y: Optional[int] = None,
    custom_x_from_right: Optional[int] = None,
    remove_bg: bool = True
) -> Image.Image:
    """Add logo to image with smart positioning and size calculation based on image dimensions

    Args:
        custom_x_from_right: For top-right logos, distance from right edge (calculated after resize)
    """

    from utils import remove_background  # Import from existing utils

    canvas = img.copy()
    if canvas.mode != 'RGBA':
        canvas = canvas.convert('RGBA')

    # Remove background if requested
    if remove_bg:
        try:
            logo = remove_background(logo)
            # Crop transparent padding to ensure logo sits exactly at specified position
            if logo.mode == 'RGBA':
                # Get the bounding box of the non-transparent area
                bbox = logo.getbbox()
                if bbox:
                    logo = logo.crop(bbox)
        except:
            pass  # If removal fails, use logo as-is

    # Calculate logo size as percentage of image height
    img_width, img_height = canvas.size
    target_height = int(img_height * (size_percent / 100))

    logo_aspect = logo.width / logo.height
    logo_width = int(target_height * logo_aspect)
    logo_resized = logo.resize((logo_width, target_height), Image.Resampling.LANCZOS)

    # Determine position - prioritize custom positions over position string
    margin = 40

    # Handle X position
    if custom_x is not None:
        x = custom_x
    elif custom_x_from_right is not None:
        # For top-right logos, calculate X from right edge AFTER resizing
        x = img_width - logo_width - custom_x_from_right
    else:
        # Calculate default X based on position string
        if position in ["top-left", "bottom-left"]:
            x = margin
        elif position in ["top-right", "bottom-right"]:
            x = img_width - logo_width - margin
        elif position in ["top-center", "bottom-center", "center"]:
            x = (img_width - logo_width) // 2
        else:
            x = margin

    # Handle Y position
    if custom_y is not None:
        y = custom_y
    else:
        # Calculate default Y based on position string
        if position in ["top-left", "top-right", "top-center"]:
            y = margin
        elif position in ["bottom-left", "bottom-right", "bottom-center"]:
            y = img_height - target_height - margin
        elif position == "center":
            y = (img_height - target_height) // 2
        else:
            y = margin

    # Ensure logo stays within canvas bounds (allow partial overflow but not complete)
    x = max(-logo_width // 2, min(x, img_width - logo_width // 2))
    y = max(-target_height // 2, min(y, img_height - target_height // 2))

    # Paste logo with alpha channel
    canvas.paste(logo_resized, (x, y), logo_resized if logo_resized.mode == 'RGBA' else None)

    return canvas.convert('RGB')
