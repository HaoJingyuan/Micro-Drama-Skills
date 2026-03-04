#!/usr/bin/env python3
"""
Storyboard image generation script (concurrent).
Combines 6 frames into a 6-grid storyboard image (9:16 ratio).

Concurrency strategy:
1. Collect all unique reference images across groups, upload them in parallel (deduplicated).
2. Generate all storyboard groups in parallel (they only depend on uploaded refs).

Retry support:
  --retry all           Force regenerate everything
  --retry 1-2,1-5       Force regenerate Episode 1 Group 2 and Episode 1 Group 5
  --retry 1             Force regenerate all groups in Episode 1
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


API_BASE_URL = "https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com"
GENERATE_IMAGE_URL = f"{API_BASE_URL}/api/generate-image"
UPLOAD_IMAGE_URL = f"{API_BASE_URL}/api/tos/upload-image"
DEFAULT_MAX_WORKERS = 4


def load_config(project_dir: Path = None):
    config = {}
    if project_dir:
        local_config_path = project_dir / "config.json"
        if local_config_path.exists():
            with open(local_config_path, encoding="utf-8") as f:
                config = json.load(f)
                print(f"Using config: {local_config_path}")
    if not config.get("username"):
        config["username"] = os.environ.get("STORYBOARD_USERNAME", "default_user")
    if not config.get("project_title"):
        config["project_title"] = os.environ.get("STORYBOARD_PROJECT", "storyboard")
    return config


def parse_retry_spec(retry_str: str) -> Union[str, Set[Tuple[int, int]], None]:
    """Parse retry specification.

    Returns:
        None        - no retry (normal skip behavior)
        'all'       - force regenerate everything
        set of tuples - (ep_num, group_num) pairs to force regenerate
                        (ep_num, 0) means all groups in that episode
    """
    if not retry_str:
        return None
    retry_str = retry_str.strip()
    if retry_str.lower() == "all":
        return "all"

    result = set()
    for part in retry_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            ep_str, grp_str = part.split("-", 1)
            result.add((int(ep_str), int(grp_str)))
        else:
            result.add((int(part), 0))
    return result if result else None


def should_force_retry(ep_num: int, group_num: int, retry_spec) -> bool:
    if retry_spec is None:
        return False
    if retry_spec == "all":
        return True
    if (ep_num, group_num) in retry_spec:
        return True
    if (ep_num, 0) in retry_spec:
        return True
    return False


def upload_image_to_tos(image_path, username, project_title, category="reference"):
    try:
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {"username": username, "project_title": project_title, "category": category}
            response = requests.post(UPLOAD_IMAGE_URL, files=files, data=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                return result.get("image_url")
            return None
    except Exception as e:
        print(f"  upload error: {e}")
        return None


def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  download error: {e}")
        return False


def generate_image(model, prompt, aspect_ratio, reference_images=None):
    payload = {"model": model, "prompt": prompt, "aspect_ratio": aspect_ratio,
               "reference_images": reference_images or []}
    try:
        response = requests.post(GENERATE_IMAGE_URL, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            image_url = result.get("image_url") or result.get("original_url")
            if image_url:
                gt = result.get("generation_time", 0)
                print(f"  gen_time: {gt:.2f}s")
                return image_url
            return None
        print(f"  gen failed: {result.get('error', '?')}")
        return None
    except requests.exceptions.Timeout:
        print("  timeout")
        return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def _upload_single_ref(ref_path, username, project_title):
    """Upload a single reference image. Returns (local_path, url_or_None)."""
    url = upload_image_to_tos(ref_path, username, project_title, "reference")
    name = Path(ref_path).name
    if url:
        print(f"    uploaded: {name}")
    else:
        print(f"    upload failed: {name}")
    return ref_path, url


def upload_references_concurrent(ref_paths, username, project_title, max_workers=DEFAULT_MAX_WORKERS):
    """Upload all reference images concurrently. Returns {local_path: url} mapping."""
    print(f"  Uploading {len(ref_paths)} reference images (workers={max_workers})...")
    path_to_url = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_upload_single_ref, p, username, project_title): p
            for p in ref_paths
        }
        for future in as_completed(futures):
            try:
                local_path, url = future.result()
                if url:
                    path_to_url[local_path] = url
            except Exception as e:
                print(f"    upload exception: {e}")

    print(f"  Uploaded {len(path_to_url)}/{len(ref_paths)} reference images")
    return path_to_url


def _generate_single_group(group_info, ref_url_map, visual_style, model):
    """Generate a single storyboard group (for concurrent dispatch).
    Returns (group_label, success)."""
    group_label = group_info["label"]
    group_frames = group_info["frames"]
    output_path = group_info["output_path"]
    ref_paths = group_info["ref_paths"]

    uploaded_urls = [ref_url_map[p] for p in ref_paths if p in ref_url_map]

    frame_descriptions = []
    for frame in group_frames:
        desc = frame.get("scene_description", "")
        camera = frame.get("camera", {})
        camera_desc = f"{camera.get('type', '')} {camera.get('movement', '')} {camera.get('angle', '')}"
        frame_descriptions.append(f"{desc}. Camera: {camera_desc}.")

    grid_prompts = []
    for i, desc in enumerate(frame_descriptions[:6], start=1):
        grid_prompts.append(f"Grid {i}: {desc}")

    nl = chr(10)
    prompt = f"""
    Create a 6-grid storyboard image in 9:16 vertical aspect ratio (portrait orientation).

    Visual style: {visual_style}

    Layout (3 rows x 2 columns):
    {nl.join(grid_prompts)}

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

    print(f"  [{group_label}] generating storyboard...")
    image_url = generate_image(model=model, prompt=prompt, aspect_ratio="9:16", reference_images=uploaded_urls)

    if image_url:
        print(f"  [{group_label}] downloading...")
        if download_image(image_url, output_path):
            print(f"  [{group_label}] done: {Path(output_path).name}")
            return group_label, True
        print(f"  [{group_label}] download failed")
        return group_label, False
    print(f"  [{group_label}] generation failed")
    return group_label, False


def generate_storyboard_image(
    reference_images,
    frame_descriptions,
    output_path,
    visual_style,
    username,
    project_title,
    model="gemini_3_pro_image"
):
    """Generate 6-grid storyboard image (backward compatible, single group serial)."""
    print(f"  Uploading references...")
    uploaded_urls = []
    for ref_path in reference_images:
        if os.path.exists(ref_path):
            url = upload_image_to_tos(ref_path, username, project_title, "reference")
            if url:
                uploaded_urls.append(url)
                print(f"    ok: {Path(ref_path).name}")
            else:
                print(f"    failed: {Path(ref_path).name}")
        else:
            print(f"    not found: {ref_path}")

    print(f"  Uploaded {len(uploaded_urls)}/{len(reference_images)} references")

    grid_prompts = []
    for i, desc in enumerate(frame_descriptions[:6], start=1):
        grid_prompts.append(f"Grid {i}: {desc}")

    nl = chr(10)
    prompt = f"""
    Create a 6-grid storyboard image in 9:16 vertical aspect ratio (portrait orientation).

    Visual style: {visual_style}

    Layout (3 rows x 2 columns):
    {nl.join(grid_prompts)}

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

    print(f"  Generating storyboard...")
    image_url = generate_image(model=model, prompt=prompt, aspect_ratio="9:16", reference_images=uploaded_urls)

    if image_url:
        print(f"  Downloading...")
        if download_image(image_url, output_path):
            print(f"  Done: {Path(output_path).name}")
            return True
        return False
    print(f"  Generation failed")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_storyboard_image.py <project_dir> [visual_style] [model] [max_workers] [--retry SPEC]")
        print(f"  max_workers default: {DEFAULT_MAX_WORKERS}")
        print(f"  --retry SPEC:")
        print(f"    all       Force regenerate everything")
        print(f"    1-2,1-5   Force regenerate Ep1-G2 and Ep1-G5")
        print(f"    1         Force regenerate all groups in Episode 1")
        sys.exit(1)

    # Parse --retry from argv before positional args
    retry_spec = None
    argv_clean = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--retry" and i + 1 < len(sys.argv):
            retry_spec = parse_retry_spec(sys.argv[i + 1])
            i += 2
        else:
            argv_clean.append(sys.argv[i])
            i += 1

    project_dir = Path(argv_clean[0])
    visual_style = argv_clean[1] if len(argv_clean) > 1 else "cinematic"
    model = argv_clean[2] if len(argv_clean) > 2 else "gemini_3_pro_image"
    max_workers_arg = argv_clean[3] if len(argv_clean) > 3 else None

    storyboard_path = project_dir / "storyboard.json"
    ref_dir = project_dir / "references"
    output_dir = project_dir / "storyboards"

    if not storyboard_path.exists():
        print(f"Storyboard not found: {storyboard_path}")
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    config = load_config(project_dir)
    username = config.get("username", "default_user")
    project_title = config.get("project_title", "storyboard")
    max_workers = int(max_workers_arg) if max_workers_arg else DEFAULT_MAX_WORKERS

    with open(storyboard_path, encoding="utf-8") as f:
        storyboard = json.load(f)

    print(f"User: {username}")
    print(f"Project: {project_title}")
    print(f"Style: {visual_style}")
    print(f"Model: {model}")
    print(f"Max workers: {max_workers}")
    if retry_spec:
        print(f"Retry: {retry_spec}")

    start_time = time.time()
    stats = {"success": 0, "skipped": 0, "retried": 0, "failed": 0}
    failed_groups = []  # [(ep_num, group_num, label), ...]
    success_groups = []

    for episode in storyboard.get("episodes", []):
        ep_num = episode["episode_number"]
        ep_title = episode["title"]
        frames = episode["frames"]
        total_frames = len(frames)

        print(f"\nEpisode {ep_num}: {ep_title} ({total_frames} frames)")

        all_ref_paths = set()
        groups = []

        for group_idx in range(0, total_frames, 6):
            group_num = (group_idx // 6) + 1
            group_frames = frames[group_idx:group_idx + 6]

            if len(group_frames) < 6:
                print(f"  Group {group_num}: only {len(group_frames)} frames, skip")
                continue

            output_filename = f"storyboard_ep{ep_num:02d}_group{group_num:02d}.png"
            output_path = str(output_dir / output_filename)

            if Path(output_path).exists():
                if should_force_retry(ep_num, group_num, retry_spec):
                    print(f"  retry: {output_filename} (forcing regeneration)")
                    Path(output_path).unlink()
                    stats["retried"] += 1
                else:
                    print(f"  skip (exists): {output_filename}")
                    stats["skipped"] += 1
                    continue

            ref_paths_for_group = set()
            for frame in group_frames:
                for char in frame.get("characters", []):
                    vid = char.get("variant_id")
                    if vid:
                        rp = ref_dir / f"{vid}_ref.png"
                        if rp.exists():
                            ref_paths_for_group.add(str(rp))
                scene_id = frame.get("scene_variant_id")
                if scene_id:
                    rp = ref_dir / f"{scene_id}_ref.png"
                    if rp.exists():
                        ref_paths_for_group.add(str(rp))
                for prop_id in frame.get("prop_variant_ids", []):
                    rp = ref_dir / f"{prop_id}_ref.png"
                    if rp.exists():
                        ref_paths_for_group.add(str(rp))

            all_ref_paths.update(ref_paths_for_group)

            groups.append({
                "label": f"Ep{ep_num}-G{group_num}",
                "ep_num": ep_num,
                "group_num": group_num,
                "frames": group_frames,
                "output_path": output_path,
                "ref_paths": list(ref_paths_for_group),
            })

        if not groups:
            continue

        ref_url_map = upload_references_concurrent(
            list(all_ref_paths), username, project_title, max_workers
        )

        print(f"\n  Generating {len(groups)} groups concurrently...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(_generate_single_group, g, ref_url_map, visual_style, model): g
                for g in groups
            }
            for future in as_completed(future_to_group):
                g = future_to_group[future]
                try:
                    _, ok = future.result()
                    if ok:
                        stats["success"] += 1
                        success_groups.append(g["label"])
                    else:
                        stats["failed"] += 1
                        failed_groups.append((g["ep_num"], g["group_num"], g["label"]))
                except Exception as e:
                    print(f"  Error [{g['label']}]: {e}")
                    stats["failed"] += 1
                    failed_groups.append((g["ep_num"], g["group_num"], g["label"]))

    elapsed = time.time() - start_time

    # Structured summary for agent parsing
    print(f"\n{'='*60}")
    print(f"RESULT: {'ALL_SUCCESS' if not failed_groups else 'HAS_FAILURES'}")
    print(f"{'='*60}")
    print(f"Success: {stats['success']}, Skipped: {stats['skipped']}, "
          f"Retried: {stats['retried']}, Failed: {stats['failed']}")
    print(f"Total time: {elapsed:.1f}s (workers={max_workers})")

    if success_groups:
        print(f"\nSUCCESS_LIST: {', '.join(success_groups)}")

    if failed_groups:
        failed_labels = [label for _, _, label in failed_groups]
        retry_spec_str = ",".join(f"{ep}-{grp}" for ep, grp, _ in failed_groups)
        print(f"\nFAILED_LIST: {', '.join(failed_labels)}")
        print(f"RETRY_COMMAND: --retry {retry_spec_str}")


if __name__ == "__main__":
    main()
