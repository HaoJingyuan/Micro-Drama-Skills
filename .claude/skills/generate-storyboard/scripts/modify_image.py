#!/usr/bin/env python3
"""
Image modification script using reference image + prompt.

Usage:
    python modify_image.py <input_image> <output_image> <modification_prompt> [model] [aspect_ratio]

Examples:
    # Remove text bubbles
    python modify_image.py input.png output.png "Remove all text bubbles and dialogue boxes. Keep everything else unchanged."

    # Change character clothing
    python modify_image.py input.png output.png "Change the character's clothing to 1990s style. Keep face and pose unchanged."

    # Use different model
    python modify_image.py input.png output.png "Remove text" gemini-3-pro-openrouter
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


API_BASE_URL = "https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com"
GENERATE_IMAGE_URL = f"{API_BASE_URL}/api/generate-image"
UPLOAD_IMAGE_URL = f"{API_BASE_URL}/api/tos/upload-image"
DEFAULT_TIMEOUT = 120  # 120 seconds
DEFAULT_MODEL = "gemini_3_pro_image"
FALLBACK_MODEL = "gemini-3-pro-openrouter"


def load_config(project_dir: Path = None):
    """Load configuration from project directory or environment."""
    config = {}
    if project_dir:
        local_config_path = project_dir / "config.json"
        if local_config_path.exists():
            with open(local_config_path, encoding="utf-8") as f:
                config = json.load(f)
    if not config.get("username"):
        config["username"] = os.environ.get("STORYBOARD_USERNAME", "default_user")
    if not config.get("project_title"):
        config["project_title"] = os.environ.get("STORYBOARD_PROJECT", "storyboard")
    return config


def upload_image_to_tos(image_path: str, username: str, project_title: str, category: str = "modification"):
    """Upload image to TOS and return URL."""
    try:
        print(f"Uploading image: {Path(image_path).name}")
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {"username": username, "project_title": project_title, "category": category}
            response = requests.post(UPLOAD_IMAGE_URL, files=files, data=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                image_url = result.get("image_url")
                print(f"✓ Uploaded: {image_url}")
                return image_url
            else:
                print(f"✗ Upload failed: {result.get('error', 'unknown error')}")
                return None
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None


def generate_modified_image(prompt: str, reference_image_url: str, model: str, aspect_ratio: str, timeout: int = DEFAULT_TIMEOUT):
    """Generate modified image using reference image and prompt."""
    try:
        print(f"Generating modified image with model: {model}")
        print(f"Prompt: {prompt}")

        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "reference_images": [reference_image_url]
        }

        start_time = time.time()
        response = requests.post(GENERATE_IMAGE_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            image_url = result.get("image_url") or result.get("original_url")
            gen_time = time.time() - start_time
            print(f"✓ Generated in {gen_time:.1f}s: {image_url}")
            return image_url
        else:
            print(f"✗ Generation failed: {result.get('error', 'unknown error')}")
            return None
    except requests.exceptions.Timeout:
        print(f"✗ Generation timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"✗ Generation error: {e}")
        return None


def download_image(image_url: str, output_path: str):
    """Download image from URL to local file."""
    try:
        print(f"Downloading to: {Path(output_path).name}")
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✓ Saved: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Download error: {e}")
        return False


def main():
    if len(sys.argv) < 4:
        print("Usage: python modify_image.py <input_image> <output_image> <modification_prompt> [model] [aspect_ratio]")
        print()
        print("Arguments:")
        print("  input_image         Path to input image")
        print("  output_image        Path to save modified image")
        print("  modification_prompt Description of what to modify")
        print("  model              (Optional) Model name, default: gemini_3_pro_image")
        print("  aspect_ratio       (Optional) Aspect ratio, default: 9:16")
        print()
        print("Examples:")
        print('  python modify_image.py input.png output.png "Remove all text bubbles"')
        print('  python modify_image.py input.png output.png "Change clothing to 1990s style" gemini-3-pro-openrouter')
        sys.exit(1)

    input_image = sys.argv[1]
    output_image = sys.argv[2]
    modification_prompt = sys.argv[3]
    model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
    aspect_ratio = sys.argv[5] if len(sys.argv) > 5 else "9:16"

    # Validate input
    if not os.path.exists(input_image):
        print(f"✗ Input image not found: {input_image}")
        sys.exit(1)

    # Load config
    project_dir = Path(input_image).parent.parent if Path(input_image).parent.name in ["storyboards", "references"] else None
    config = load_config(project_dir)
    username = config.get("username", "default_user")
    project_title = config.get("project_title", "storyboard")

    print("=" * 60)
    print("IMAGE MODIFICATION")
    print("=" * 60)
    print(f"Input:  {input_image}")
    print(f"Output: {output_image}")
    print(f"Model:  {model}")
    print(f"Ratio:  {aspect_ratio}")
    print()

    # Step 1: Upload input image
    reference_url = upload_image_to_tos(input_image, username, project_title, "modification")
    if not reference_url:
        print("\n✗ Failed to upload input image")
        sys.exit(1)

    print()

    # Step 2: Generate modified image
    modified_url = generate_modified_image(modification_prompt, reference_url, model, aspect_ratio, DEFAULT_TIMEOUT)

    # If failed and using default model, try fallback model
    if not modified_url and model == DEFAULT_MODEL:
        print()
        print(f"Retrying with fallback model: {FALLBACK_MODEL}")
        modified_url = generate_modified_image(modification_prompt, reference_url, FALLBACK_MODEL, aspect_ratio, DEFAULT_TIMEOUT)

    if not modified_url:
        print("\n✗ Failed to generate modified image")
        sys.exit(1)

    print()

    # Step 3: Download modified image
    if download_image(modified_url, output_image):
        print()
        print("=" * 60)
        print("✓ SUCCESS")
        print("=" * 60)
        print(f"Modified image saved to: {output_image}")
    else:
        print("\n✗ Failed to download modified image")
        sys.exit(1)


if __name__ == "__main__":
    main()
