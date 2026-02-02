"""
AI Ad Generation Module using Replicate API
Supports FLUX models for generating professional advertisements
"""

import replicate
from PIL import Image
import requests
from io import BytesIO
from typing import Optional
import time

# ========== AI MODELS CONFIGURATION ==========
AI_MODELS = {
    "flux-1.1-pro": {
        "name": "FLUX 1.1 Pro (Fastest, Best Quality)",
        "model_id": "black-forest-labs/flux-1.1-pro",
        "description": "Latest FLUX model with improved speed and quality"
    },
    "flux-pro": {
        "name": "FLUX Pro (High Quality)",
        "model_id": "black-forest-labs/flux-pro",
        "description": "Professional grade image generation"
    },
    "flux-dev": {
        "name": "FLUX Dev (Balanced)",
        "model_id": "black-forest-labs/flux-dev",
        "description": "Development model with good balance"
    },
    "flux-schnell": {
        "name": "FLUX Schnell (Fastest)",
        "model_id": "black-forest-labs/flux-schnell",
        "description": "Fastest generation speed"
    }
}

# ========== AD STYLE CATEGORIES ==========
AD_STYLE_CATEGORIES = {
    # Lifestyle Styles
    "Modern Minimalist": "Clean minimal environment, natural light, contemporary aesthetic, uncluttered, simple elegance",
    "Luxury Premium": "High-end luxury setting, premium materials, sophisticated, elegant, opulent details",
    "Urban Contemporary": "Modern city setting, urban lifestyle, metropolitan vibe, contemporary design",

    # Aesthetic Styles
    "Vintage Retro": "Nostalgic vintage aesthetic, retro colors, classic styling, timeless appeal",
    "Futuristic": "Futuristic design, high-tech aesthetic, sci-fi elements, advanced technology",
    "Dark Moody": "Dark atmospheric lighting, moody tones, dramatic shadows, mysterious ambiance",
    "Bright Airy": "Bright natural lighting, airy atmosphere, light colors, fresh and clean",

    # Product Photography
    "Hero Studio": "Professional studio lighting, bold product hero shot, clean background, centered composition",
    "Lifestyle Action": "Product in real-life use, action shot, lifestyle context, natural environment",
    "Clean White": "Pure white background, crisp lighting, minimal distraction, product focus",
    "Natural Light": "Soft natural lighting, organic feel, authentic atmosphere, daylight",

    # Emotional Styles
    "Joy & Happiness": "Joyful atmosphere, vibrant colors, positive energy, cheerful mood",
    "Confidence & Power": "Bold powerful imagery, confident presentation, strong presence, assertive",

    # Additional Professional Styles
    "Elegant Sophisticated": "Refined elegance, sophisticated styling, graceful composition, polished",
    "Energetic Dynamic": "High energy, dynamic movement, action-packed, vibrant intensity",
    "Warm Inviting": "Warm tones, inviting atmosphere, cozy feel, welcoming ambiance",
    "Professional Corporate": "Professional business aesthetic, corporate styling, clean and formal"
}

def generate_ad_with_replicate(
    prompt: str,
    negative_prompt: str,
    api_key: str,
    model_key: str = "flux-1.1-pro",
    aspect_ratio: str = "1:1",
    product_image: Optional[Image.Image] = None,
    logo_image: Optional[Image.Image] = None,
    progress_placeholder=None,
    num_inference_steps: int = 28,
    guidance_scale: float = 3.5,
    safety_tolerance: int = 2,
    max_retries: int = 3
) -> Optional[Image.Image]:
    """
    Generate advertisement image using Replicate API with FLUX models

    Args:
        prompt: Text prompt describing the desired image
        negative_prompt: Things to avoid in generation
        api_key: Replicate API key
        model_key: Key from AI_MODELS dict (default: "flux-1.1-pro")
        aspect_ratio: Image aspect ratio (e.g., "1:1", "16:9", "9:16")
        product_image: Optional product image for reference
        logo_image: Optional logo image (not used in generation, added post-process)
        progress_placeholder: Streamlit placeholder for progress updates
        num_inference_steps: Number of denoising steps (higher = better quality, slower)
        guidance_scale: How closely to follow prompt (3-15 recommended)
        safety_tolerance: Content moderation level (1-6, higher = more lenient)
        max_retries: Maximum number of retry attempts

    Returns:
        PIL Image object or None if generation fails
    """

    # Validate API key
    if not api_key or api_key.strip() == "":
        if progress_placeholder:
            progress_placeholder.error("❌ API key is required")
        return None

    # Get model configuration
    model_config = AI_MODELS.get(model_key, AI_MODELS["flux-1.1-pro"])
    model_id = model_config["model_id"]

    # Set API key for replicate
    client = replicate.Client(api_token=api_key)

    # Prepare input parameters
    input_params = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
        "output_format": "png",
        "output_quality": 100,
        "safety_tolerance": safety_tolerance
    }

    # Add negative prompt if provided and model supports it
    if negative_prompt and model_key in ["flux-dev", "flux-schnell"]:
        input_params["prompt"] = f"{prompt}\n\nNegative: {negative_prompt}"

    # Attempt generation with retries
    for attempt in range(max_retries):
        try:
            if progress_placeholder:
                progress_placeholder.info(f"🎨 Generating with {model_config['name']}... (Attempt {attempt + 1}/{max_retries})")

            # Run the model
            output = client.run(
                model_id,
                input=input_params
            )

            # Handle different output formats
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                raise ValueError(f"Unexpected output format: {type(output)}")

            # Download the generated image
            if progress_placeholder:
                progress_placeholder.info("📥 Downloading generated image...")

            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Convert to PIL Image
            image = Image.open(BytesIO(response.content))

            if progress_placeholder:
                progress_placeholder.success("✅ Image generated successfully!")

            return image

        except replicate.exceptions.ReplicateError as e:
            error_msg = str(e)

            if "NSFW" in error_msg or "safety" in error_msg.lower():
                if progress_placeholder:
                    progress_placeholder.warning(f"⚠️ Content filter triggered. Adjusting safety settings...")
                # Retry with higher safety tolerance
                input_params["safety_tolerance"] = min(safety_tolerance + 1, 6)
                time.sleep(2)
                continue

            elif "billing" in error_msg.lower() or "credit" in error_msg.lower():
                if progress_placeholder:
                    progress_placeholder.error("❌ Insufficient credits. Please add credits to your Replicate account.")
                return None

            elif "rate limit" in error_msg.lower():
                if progress_placeholder:
                    progress_placeholder.warning(f"⚠️ Rate limit hit. Waiting before retry...")
                time.sleep(5 * (attempt + 1))  # Exponential backoff
                continue

            else:
                if attempt < max_retries - 1:
                    if progress_placeholder:
                        progress_placeholder.warning(f"⚠️ Error: {error_msg}. Retrying...")
                    time.sleep(2)
                    continue
                else:
                    if progress_placeholder:
                        progress_placeholder.error(f"❌ Generation failed: {error_msg}")
                    return None

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                if progress_placeholder:
                    progress_placeholder.warning(f"⚠️ Network error. Retrying...")
                time.sleep(2)
                continue
            else:
                if progress_placeholder:
                    progress_placeholder.error(f"❌ Failed to download image: {str(e)}")
                return None

        except Exception as e:
            if attempt < max_retries - 1:
                if progress_placeholder:
                    progress_placeholder.warning(f"⚠️ Unexpected error. Retrying...")
                time.sleep(2)
                continue
            else:
                if progress_placeholder:
                    progress_placeholder.error(f"❌ Generation failed: {str(e)}")
                return None

    # If all retries failed
    if progress_placeholder:
        progress_placeholder.error("❌ Failed to generate image after multiple attempts")
    return None


def validate_api_key(api_key: str) -> bool:
    """
    Validate Replicate API key by making a test request

    Args:
        api_key: Replicate API key to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key or api_key.strip() == "":
        return False

    try:
        client = replicate.Client(api_token=api_key)
        # Try to list models as a validation check
        # This is a lightweight operation
        list(client.models.list())
        return True
    except:
        return False
