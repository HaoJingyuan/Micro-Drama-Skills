import os
import sys
import json
import time
import requests
from pathlib import Path

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

API_BASE_URL = "https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com"
GENERATE_IMAGE_URL = f"{API_BASE_URL}/api/generate-image"

def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def generate_image(model, prompt, aspect_ratio, reference_images=None):
    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
    }
    if reference_images:
        payload["reference_images"] = reference_images

    try:
        response = requests.post(GENERATE_IMAGE_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            image_url = result.get("image_url") or result.get("original_url")
            if image_url:
                print(f"Generated in {result.get('generation_time', 0):.2f}s")
                return image_url
        else:
            print(f"Generation failed: {result.get('error', 'Unknown error')}")
        return None
    except Exception as e:
        print(f"API call failed: {e}")
        return None

def generate_character_reference(variant_info, output_path, model="gemini_3_pro_image"):
    # 简化prompt，去除复杂布局要求
    prompt = f"{variant_info['ai_prompt']}, full body portrait, clean white background, character reference photo"

    print(f"Generating {Path(output_path).name}...")
    image_url = generate_image(model, prompt, "1:1")

    if image_url:
        if download_image(image_url, output_path):
            print(f"SUCCESS: {Path(output_path).name}")
            return True
    print(f"FAILED: {Path(output_path).name}")
    return False

# Main
project_dir = Path(sys.argv[1])
model = "gemini_3_pro_image"

config_path = project_dir / "elements_config.json"
ref_dir = project_dir / "references"
ref_dir.mkdir(exist_ok=True)

with open(config_path, encoding='utf-8') as f:
    elements_config = json.load(f)

print(f"Model: {model}\n")
stats = {"characters": 0, "failed": 0}

print("=" * 60)
print("GENERATING CHARACTER REFERENCES (RETRY)")
print("=" * 60)
for char in elements_config.get("characters", []):
    print(f"\nCharacter: {char['name']}")
    for variant in char["variants"]:
        variant_id = variant["variant_id"]
        output_path = str(ref_dir / f"{variant_id}_ref.png")

        if Path(output_path).exists():
            print(f"SKIP: {variant_id}_ref.png (exists)")
            stats["characters"] += 1
            continue

        if generate_character_reference(variant, output_path, model):
            stats["characters"] += 1
        else:
            stats["failed"] += 1
        time.sleep(1)

print("\n" + "=" * 60)
print("COMPLETE!")
print("=" * 60)
print(f"Characters: {stats['characters']}")
print(f"Failed: {stats['failed']}")
print("=" * 60)
