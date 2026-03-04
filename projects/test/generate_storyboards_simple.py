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
UPLOAD_IMAGE_URL = f"{API_BASE_URL}/api/tos/upload-image"

def upload_image_to_tos(image_path, username, project_title, category="reference"):
    try:
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {
                "username": username,
                "project_title": project_title,
                "category": category
            }

            response = requests.post(UPLOAD_IMAGE_URL, files=files, data=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return result.get("image_url")
        return None
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

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
        "reference_images": reference_images or []
    }

    try:
        response = requests.post(GENERATE_IMAGE_URL, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            image_url = result.get("image_url") or result.get("original_url")
            if image_url:
                print(f"Generated in {result.get('generation_time', 0):.2f}s")
                return image_url
        else:
            print(f"Generation failed: {result.get('error', 'Unknown')}")
        return None
    except Exception as e:
        print(f"API call failed: {e}")
        return None

def generate_storyboard_image(reference_images, frame_descriptions, output_path, visual_style, username, project_title, model="gemini_3_pro_image"):
    print("Uploading reference images...")
    uploaded_urls = []
    for ref_path in reference_images:
        if os.path.exists(ref_path):
            url = upload_image_to_tos(ref_path, username, project_title, "reference")
            if url:
                uploaded_urls.append(url)
                print(f"  OK: {Path(ref_path).name}")

    print(f"Uploaded {len(uploaded_urls)}/{len(reference_images)} images")

    grid_prompts = []
    for i, desc in enumerate(frame_descriptions[:6], start=1):
        grid_prompts.append(f"Grid {i}: {desc}")

    prompt = f"""
    Create a 6-grid storyboard image in 9:16 vertical aspect ratio (portrait orientation).

    Visual style: {visual_style}

    Layout (3 rows x 2 columns):
    {chr(10).join(grid_prompts)}

    Requirements:
    - 6 panels in total, arranged in 3 rows and 2 columns
    - 9:16 aspect ratio (vertical/portrait)
    - Each panel shows a different scene/moment
    - Consistent character appearance across all panels (based on reference images)
    - Cinematic composition
    - Clear panel separation
    - High quality

    Character references are provided. Maintain character consistency.
    """

    print("Generating storyboard...")
    image_url = generate_image(model, prompt, "9:16", uploaded_urls)

    if image_url:
        print("Downloading...")
        if download_image(image_url, output_path):
            print(f"SUCCESS: {Path(output_path).name}")
            return True
    print("FAILED")
    return False

# Main
project_dir = Path(sys.argv[1])
visual_style = sys.argv[2] if len(sys.argv) > 2 else "cinematic"
model = sys.argv[3] if len(sys.argv) > 3 else "gemini_3_pro_image"

storyboard_path = project_dir / "storyboard.json"
ref_dir = project_dir / "references"
output_dir = project_dir / "storyboards"
config_path = project_dir / "config.json"

output_dir.mkdir(exist_ok=True)

# Load config
config = {}
if config_path.exists():
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

username = sys.argv[4] if len(sys.argv) > 4 else config.get("username", "default_user")
project_title = sys.argv[5] if len(sys.argv) > 5 else config.get("project_title", "storyboard")

# Load storyboard
with open(storyboard_path, encoding='utf-8') as f:
    storyboard = json.load(f)

print(f"User: {username}")
print(f"Project: {project_title}")
print(f"Style: {visual_style}")
print(f"Model: {model}\n")

stats = {"images": 0, "failed": 0}

for episode in storyboard.get("episodes", []):
    ep_num = episode["episode_number"]
    ep_title = episode["title"]
    frames = episode["frames"]

    print("=" * 60)
    print(f"Episode {ep_num}: {ep_title}")
    print("=" * 60)

    total_frames = len(frames)
    for group_idx in range(0, total_frames, 6):
        group_num = (group_idx // 6) + 1
        group_frames = frames[group_idx:group_idx + 6]

        if len(group_frames) < 6:
            print(f"Group {group_num} has only {len(group_frames)} frames, skipping")
            continue

        print(f"\nGroup {group_num} (frames {group_idx + 1}-{group_idx + len(group_frames)})")

        # Collect reference images
        reference_images = set()
        for frame in group_frames:
            for char in frame.get("characters", []):
                variant_id = char.get("variant_id")
                if variant_id:
                    ref_path = ref_dir / f"{variant_id}_ref.png"
                    if ref_path.exists():
                        reference_images.add(str(ref_path))

            scene_id = frame.get("scene_variant_id")
            if scene_id:
                ref_path = ref_dir / f"{scene_id}_ref.png"
                if ref_path.exists():
                    reference_images.add(str(ref_path))

            for prop_id in frame.get("prop_variant_ids", []):
                ref_path = ref_dir / f"{prop_id}_ref.png"
                if ref_path.exists():
                    reference_images.add(str(ref_path))

        reference_images = list(reference_images)
        print(f"Reference images: {len(reference_images)}")

        # Build descriptions
        frame_descriptions = []
        for frame in group_frames:
            desc = frame.get("scene_description", "")
            camera = frame.get("camera", {})
            camera_desc = f"{camera.get('type', '')} {camera.get('movement', '')} {camera.get('angle', '')}"
            full_desc = f"{desc}. Camera: {camera_desc}."
            frame_descriptions.append(full_desc)

        output_filename = f"storyboard_ep{ep_num:02d}_group{group_num:02d}.png"
        output_path = str(output_dir / output_filename)

        if Path(output_path).exists():
            print(f"SKIP: {output_filename} (exists)")
            stats["images"] += 1
            continue

        success = generate_storyboard_image(
            reference_images=reference_images,
            frame_descriptions=frame_descriptions,
            output_path=output_path,
            visual_style=visual_style,
            username=username,
            project_title=project_title,
            model=model
        )

        if success:
            stats["images"] += 1
        else:
            stats["failed"] += 1

        time.sleep(2)

print("\n" + "=" * 60)
print("COMPLETE!")
print("=" * 60)
print(f"Storyboards: {stats['images']}")
print(f"Failed: {stats['failed']}")
print("=" * 60)
