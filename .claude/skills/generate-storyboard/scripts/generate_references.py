#!/usr/bin/env python3
"""
Reference image generation script (two-phase concurrent).

Phase 1: Generate first variant of ALL elements (characters, scenes, props) concurrently.
Phase 2: Generate remaining variants concurrently, using the first variant as reference image.
         Variants wait for their element's first variant, but are concurrent among themselves.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Optional, List, Dict, Tuple
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
    if not config.get("username"):
        config["username"] = os.environ.get("STORYBOARD_USERNAME", "default_user")
    if not config.get("project_title"):
        config["project_title"] = os.environ.get("STORYBOARD_PROJECT", "storyboard")
    return config


def download_image(image_url: str, output_path: str) -> bool:
    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def upload_image_to_tos(image_path: str, username: str, project_title: str, category: str = "reference") -> Optional[str]:
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
        print(f"  Upload failed: {e}")
        return None


def generate_image(model, prompt, aspect_ratio, reference_images=None):
    payload = {"model": model, "prompt": prompt, "aspect_ratio": aspect_ratio}
    if reference_images:
        payload["reference_images"] = reference_images
    try:
        response = requests.post(GENERATE_IMAGE_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            image_url = result.get("image_url") or result.get("original_url")
            if image_url:
                gt = result.get("generation_time", 0)
                print(f"  gen_time: {gt:.2f}s")
                return image_url
            return None
        print(f"  gen failed: {result.get('error', 'unknown')}")
        return None
    except requests.exceptions.Timeout:
        print("  timeout")
        return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def _build_character_prompt(vi):
    prompt = f"""
    Create a character reference sheet in 2x2 grid layout.

    {vi['ai_prompt']}

    Grid layout:
    - Top-Left: Front view full body
    - Top-Right: Side view full body
    - Bottom-Left: Back view full body
    - Bottom-Right: Face close-up portrait

    White background, clean design, character reference sheet style.
    Same character in all four views, consistent appearance.
    High quality, detailed.
    """
    return prompt, "1:1"


def _build_scene_prompt(vi):
    prompt = f"""
    {vi['ai_prompt']}

    16:9 aspect ratio, cinematic scene, high quality.
    Detailed environment, atmospheric lighting.
    """
    return prompt, "16:9"


def _build_prop_prompt(vi):
    prompt = f"""
    Create a prop reference sheet showing three views in horizontal layout.

    {vi['ai_prompt']}

    Layout (1x3 horizontal):
    - Left: Front view
    - Center: Side view
    - Right: Top/perspective view

    White background, clean design, product reference style.
    Same object in all three views, consistent appearance.
    High quality, detailed.
    """
    return prompt, "16:9"


PROMPT_BUILDERS = {
    "character": _build_character_prompt,
    "scene": _build_scene_prompt,
    "prop": _build_prop_prompt,
}


def _generate_single_reference(task, model):
    """Worker function for concurrent reference generation.
    Returns (variant_id, element_id, image_url, output_path, success)"""
    vid = task["variant_id"]
    vi = task["variant_info"]
    out = task["output_path"]
    et = task["element_type"]
    en = task["element_name"]
    eid = task["element_id"]
    ref_images = task.get("reference_images")
    label = f"{en}/{vid}"

    prompt, ar = PROMPT_BUILDERS[et](vi)

    ref_note = f" (with {len(ref_images)} ref)" if ref_images else ""
    print(f"  [{label}] generating...{ref_note}")
    url = generate_image(model=model, prompt=prompt, aspect_ratio=ar, reference_images=ref_images)

    if url:
        print(f"  [{label}] downloading...")
        if download_image(url, out):
            print(f"  [{label}] done: {Path(out).name}")
            return vid, eid, url, out, True
        print(f"  [{label}] download failed")
        return vid, eid, None, out, False
    print(f"  [{label}] generation failed")
    return vid, eid, None, out, False


def generate_character_reference(variant_info, output_path, model="gemini_3_pro_image"):
    """Generate character reference (backward compatible)"""
    task = {"variant_id": variant_info.get("variant_id", "unknown"), "variant_info": variant_info,
            "output_path": output_path, "element_type": "character", "element_name": "character",
            "element_id": "unknown"}
    _, _, _, _, ok = _generate_single_reference(task, model)
    return ok


def generate_scene_reference(variant_info, output_path, model="gemini_3_pro_image"):
    """Generate scene reference (backward compatible)"""
    task = {"variant_id": variant_info.get("variant_id", "unknown"), "variant_info": variant_info,
            "output_path": output_path, "element_type": "scene", "element_name": "scene",
            "element_id": "unknown"}
    _, _, _, _, ok = _generate_single_reference(task, model)
    return ok


def generate_prop_reference(variant_info, output_path, model="gemini_3_pro_image"):
    """Generate prop reference (backward compatible)"""
    task = {"variant_id": variant_info.get("variant_id", "unknown"), "variant_info": variant_info,
            "output_path": output_path, "element_type": "prop", "element_name": "prop",
            "element_id": "unknown"}
    _, _, _, _, ok = _generate_single_reference(task, model)
    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_references.py <project_dir> [model] [max_workers]")
        print(f"  max_workers default: {DEFAULT_MAX_WORKERS}")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else "gemini_3_pro_image"
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_MAX_WORKERS

    config_path = project_dir / "elements_config.json"
    ref_dir = project_dir / "references"

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    ref_dir.mkdir(exist_ok=True)
    config = load_config(project_dir)

    with open(config_path, encoding="utf-8") as f:
        elements_config = json.load(f)

    print(f"Model: {model}")
    print(f"Max workers: {max_workers}")

    # ---- Classify tasks into Phase 1 (first variants) and Phase 2 (rest) ----
    phase1_tasks = []
    phase2_groups: Dict[str, list] = {}  # element_id -> remaining variant tasks
    first_variant_existing: Dict[str, str] = {}  # element_id -> local path (already on disk)
    skipped = 0

    type_map = [("characters", "character"), ("scenes", "scene"), ("props", "prop")]

    for config_key, element_type in type_map:
        for element in elements_config.get(config_key, []):
            eid = element["id"]
            variants = element["variants"]
            if not variants:
                continue

            first_variant = variants[0]
            first_output = str(ref_dir / f"{first_variant['variant_id']}_ref.png")

            if Path(first_output).exists():
                print(f"  skip: {first_variant['variant_id']}_ref.png")
                skipped += 1
                first_variant_existing[eid] = first_output
            else:
                phase1_tasks.append({
                    "variant_id": first_variant["variant_id"],
                    "variant_info": first_variant,
                    "output_path": first_output,
                    "element_type": element_type,
                    "element_name": element["name"],
                    "element_id": eid,
                })

            rest = []
            for variant in variants[1:]:
                out = str(ref_dir / f"{variant['variant_id']}_ref.png")
                if Path(out).exists():
                    print(f"  skip: {variant['variant_id']}_ref.png")
                    skipped += 1
                    continue
                rest.append({
                    "variant_id": variant["variant_id"],
                    "variant_info": variant,
                    "output_path": out,
                    "element_type": element_type,
                    "element_name": element["name"],
                    "element_id": eid,
                })
            if rest:
                phase2_groups[eid] = rest

    phase2_count = sum(len(v) for v in phase2_groups.values())
    total_tasks = len(phase1_tasks) + phase2_count
    print(f"\nPhase 1: {len(phase1_tasks)} first variants to generate")
    print(f"Phase 2: {phase2_count} remaining variants ({len(phase2_groups)} elements)")
    print(f"Skipped: {skipped}")

    if total_tasks == 0:
        print("All reference images exist already.")
        return

    start_time = time.time()
    stats = {"success": 0, "failed": 0}
    failed_items = []  # [(variant_id, element_name), ...]
    success_items = []
    first_variant_urls: Dict[str, str] = {}  # element_id -> image URL

    # ---- Phase 0: Upload existing first variants that have phase 2 tasks ----
    needs_upload = {eid: path for eid, path in first_variant_existing.items()
                    if eid in phase2_groups}

    if needs_upload:
        username = config.get("username", "default_user")
        project_title = config.get("project_title", "storyboard")
        print(f"\nUploading {len(needs_upload)} existing first variants for reference...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_eid = {}
            for eid, path in needs_upload.items():
                future = executor.submit(upload_image_to_tos, path, username, project_title)
                future_to_eid[future] = eid
            for future in as_completed(future_to_eid):
                eid = future_to_eid[future]
                try:
                    url = future.result()
                    if url:
                        first_variant_urls[eid] = url
                        print(f"  Uploaded {Path(needs_upload[eid]).name}")
                    else:
                        print(f"  Upload failed for {Path(needs_upload[eid]).name}")
                except Exception as e:
                    print(f"  Upload error for {eid}: {e}")

    # ---- Phase 1: Generate all first variants concurrently ----
    if phase1_tasks:
        print(f"\n{'='*60}")
        print(f"PHASE 1: First variants ({len(phase1_tasks)} images, {max_workers} workers)")
        print(f"{'='*60}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_generate_single_reference, task, model): task
                for task in phase1_tasks
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    vid, eid, url, out, ok = future.result()
                    if ok:
                        stats["success"] += 1
                        success_items.append(vid)
                        if url:
                            first_variant_urls[eid] = url
                    else:
                        stats["failed"] += 1
                        failed_items.append((vid, task["element_name"]))
                except Exception as e:
                    print(f"  Error [{task['variant_id']}]: {e}")
                    stats["failed"] += 1
                    failed_items.append((task["variant_id"], task["element_name"]))

    # ---- Phase 2: Generate remaining variants with reference ----
    if phase2_groups:
        phase2_tasks = []
        for eid, tasks in phase2_groups.items():
            ref_url = first_variant_urls.get(eid)
            for task in tasks:
                if ref_url:
                    task["reference_images"] = [ref_url]
                phase2_tasks.append(task)

        refs_count = sum(1 for t in phase2_tasks if t.get("reference_images"))
        print(f"\n{'='*60}")
        print(f"PHASE 2: Variant generation ({len(phase2_tasks)} images, {max_workers} workers)")
        print(f"  {refs_count}/{len(phase2_tasks)} with reference image")
        print(f"{'='*60}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_generate_single_reference, task, model): task
                for task in phase2_tasks
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    vid, eid, url, out, ok = future.result()
                    if ok:
                        stats["success"] += 1
                        success_items.append(vid)
                    else:
                        stats["failed"] += 1
                        failed_items.append((vid, task["element_name"]))
                except Exception as e:
                    print(f"  Error [{task['variant_id']}]: {e}")
                    stats["failed"] += 1
                    failed_items.append((task["variant_id"], task["element_name"]))

    elapsed = time.time() - start_time

    # Structured summary for agent parsing
    print(f"\n{'='*60}")
    print(f"RESULT: {'ALL_SUCCESS' if not failed_items else 'HAS_FAILURES'}")
    print(f"{'='*60}")
    print(f"Success: {stats['success']}, Skipped: {skipped}, Failed: {stats['failed']}")
    print(f"Total time: {elapsed:.1f}s (workers={max_workers})")
    if stats["success"] > 0:
        print(f"Avg: {elapsed / stats['success']:.1f}s/image (wall clock)")

    if success_items:
        print(f"\nSUCCESS_LIST: {', '.join(success_items)}")

    if failed_items:
        print(f"\nFAILED_LIST: {', '.join(f'{vid} ({name})' for vid, name in failed_items)}")
        failed_ids = [vid for vid, _ in failed_items]
        print(f"FAILED_IDS: {', '.join(failed_ids)}")
        print(f"\nTo retry: delete the failed files and re-run the same command.")


if __name__ == "__main__":
    main()
