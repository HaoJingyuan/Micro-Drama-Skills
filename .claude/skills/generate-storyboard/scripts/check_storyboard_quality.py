#!/usr/bin/env python3
"""
分镜质量检查脚本
使用视觉 AI 检查生成的分镜图是否符合要求
"""

import os
import json
from pathlib import Path
from google import genai
from google.genai import types


def load_api_config():
    """从配置文件加载 API 配置"""
    config_path = Path("/data/dongman/.config/api_keys.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        return config.get("gemini_api_key"), config.get("gemini_base_url")

    api_key = os.environ.get("GEMINI_API_KEY")
    base_url = os.environ.get("GEMINI_BASE_URL")

    if not api_key:
        raise RuntimeError("未找到 GEMINI_API_KEY")

    return api_key, base_url


def check_storyboard_quality(
    image_path: str,
    reference_images: list,
    expected_style: str,
    frame_descriptions: list,
    client: genai.Client
) -> dict:
    """
    检查分镜图质量

    Args:
        image_path: 待检查的分镜图路径
        reference_images: 参考图列表（角色、场景等）
        expected_style: 预期的视觉风格
        frame_descriptions: 6个分镜的描述
        client: Gemini client

    Returns:
        dict: 检查结果
        {
            "passed": bool,
            "issues": [{"dimension": str, "severity": str, "description": str}],
            "suggestions": [str],
            "score": float  # 0-100
        }
    """
    # 上传图片
    storyboard_file = client.files.upload(file=image_path)

    ref_files = []
    for ref_path in reference_images:
        if os.path.exists(ref_path):
            ref_files.append(client.files.upload(file=ref_path))

    # 构建检查提示词
    check_prompt = f"""
    You are a professional storyboard quality inspector. Analyze this 6-grid storyboard image.

    Expected visual style: {expected_style}

    Expected content for each grid:
    {chr(10).join([f"Grid {i+1}: {desc}" for i, desc in enumerate(frame_descriptions)])}

    Reference images for characters/scenes are provided.

    Please check the following dimensions:

    1. **Character Consistency**
       - Are the characters consistent with the reference images?
       - Do the same characters look identical across different grids?
       - Rate: 0-100

    2. **Layout Correctness**
       - Is this a 6-grid layout (3 rows x 2 columns)?
       - Is the overall aspect ratio 9:16 (vertical)?
       - Are the panels clearly separated?
       - Rate: 0-100

    3. **Visual Style Match**
       - Does the visual style match "{expected_style}"?
       - Is the color palette appropriate?
       - Is the mood/atmosphere consistent?
       - Rate: 0-100

    4. **Cinematography**
       - Is there reasonable variation in shot types (wide, medium, close-up)?
       - Is the visual narrative flow smooth?
       - Are the compositions well-balanced?
       - Rate: 0-100

    Return your analysis in JSON format:
    {{
        "character_consistency": {{"score": 0-100, "issues": ["issue1", "issue2"]}},
        "layout_correctness": {{"score": 0-100, "issues": []}},
        "visual_style_match": {{"score": 0-100, "issues": []}},
        "cinematography": {{"score": 0-100, "issues": []}},
        "overall_score": 0-100,
        "passed": true/false,
        "suggestions": ["suggestion1", "suggestion2"]
    }}

    Passing criteria: all dimension scores >= 70, overall_score >= 75.
    """

    try:
        contents = ref_files + [storyboard_file, check_prompt]

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
        )

        # 解析响应
        response_text = response.text.strip()

        # 尝试提取 JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        # 转换为标准格式
        issues = []
        for dim in ["character_consistency", "layout_correctness", "visual_style_match", "cinematography"]:
            dim_data = result.get(dim, {})
            score = dim_data.get("score", 0)
            dim_issues = dim_data.get("issues", [])

            for issue in dim_issues:
                severity = "high" if score < 50 else ("medium" if score < 70 else "low")
                issues.append({
                    "dimension": dim,
                    "severity": severity,
                    "description": issue
                })

        return {
            "passed": result.get("passed", False),
            "issues": issues,
            "suggestions": result.get("suggestions", []),
            "score": result.get("overall_score", 0),
            "detailed_scores": {
                "character_consistency": result.get("character_consistency", {}).get("score", 0),
                "layout_correctness": result.get("layout_correctness", {}).get("score", 0),
                "visual_style_match": result.get("visual_style_match", {}).get("score", 0),
                "cinematography": result.get("cinematography", {}).get("score", 0),
            }
        }

    except Exception as e:
        print(f"  ❌ 质量检查失败: {e}")
        return {
            "passed": False,
            "issues": [{"dimension": "error", "severity": "high", "description": str(e)}],
            "suggestions": ["质量检查失败，请手动检查"],
            "score": 0,
            "detailed_scores": {}
        }


def main():
    """主流程：检查所有分镜图"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python check_storyboard_quality.py <project_dir> [visual_style]")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    visual_style = sys.argv[2] if len(sys.argv) > 2 else "cinematic"

    storyboard_path = project_dir / "storyboard.json"
    ref_dir = project_dir / "references"
    storyboards_dir = project_dir / "storyboards"
    reports_dir = project_dir / "quality_reports"

    if not storyboard_path.exists():
        print(f"❌ 故事板配置不存在: {storyboard_path}")
        sys.exit(1)

    reports_dir.mkdir(exist_ok=True)

    # 加载故事板
    with open(storyboard_path) as f:
        storyboard = json.load(f)

    # 初始化 API
    api_key, base_url = load_api_config()
    http_options = types.HttpOptions(base_url=base_url) if base_url else None
    client = genai.Client(api_key=api_key, http_options=http_options)
    print(f"🔑 API 已配置 | Base URL: {base_url or '默认'}")
    print(f"🎨 视觉风格: {visual_style}\n")

    stats = {"total": 0, "passed": 0, "failed": 0}

    # 处理每一集
    for episode in storyboard.get("episodes", []):
        ep_num = episode["episode_number"]
        ep_title = episode["title"]
        frames = episode["frames"]

        print("=" * 60)
        print(f"📺 第{ep_num}集: {ep_title}")
        print("=" * 60)

        # 每6个分镜一组
        total_frames = len(frames)
        for group_idx in range(0, total_frames, 6):
            group_num = (group_idx // 6) + 1
            group_frames = frames[group_idx:group_idx + 6]

            if len(group_frames) < 6:
                continue

            print(f"\n--- 组{group_num}（第{group_idx + 1}-{group_idx + len(group_frames)}格）---")

            # 分镜图路径
            storyboard_filename = f"storyboard_ep{ep_num:02d}_group{group_num:02d}.png"
            storyboard_img_path = storyboards_dir / storyboard_filename

            if not storyboard_img_path.exists():
                print(f"  ⚠️ 分镜图不存在，跳过: {storyboard_filename}")
                continue

            # 收集参考图
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

            # 构建分镜描述
            frame_descriptions = [frame.get("scene_description", "") for frame in group_frames]

            # 质量检查
            print(f"  🔍 检查中...")
            result = check_storyboard_quality(
                image_path=str(storyboard_img_path),
                reference_images=reference_images,
                expected_style=visual_style,
                frame_descriptions=frame_descriptions,
                client=client
            )

            # 保存报告
            report_filename = f"ep{ep_num:02d}_group{group_num:02d}_check.json"
            report_path = reports_dir / report_filename
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 输出结果
            stats["total"] += 1
            if result["passed"]:
                stats["passed"] += 1
                print(f"  ✅ 通过 | 总分: {result['score']:.1f}")
            else:
                stats["failed"] += 1
                print(f"  ❌ 未通过 | 总分: {result['score']:.1f}")
                print(f"     问题数: {len(result['issues'])}")
                for issue in result['issues'][:3]:  # 只显示前3个
                    print(f"     - [{issue['severity']}] {issue['description']}")

            print(f"  📊 详细得分:")
            for dim, score in result.get("detailed_scores", {}).items():
                print(f"     {dim}: {score:.1f}")

    # 总结
    print("\n" + "=" * 60)
    print("🏁 质量检查完成!")
    print("=" * 60)
    print(f"📊 总计: {stats['total']} 组")
    print(f"✅ 通过: {stats['passed']} 组")
    print(f"❌ 未通过: {stats['failed']} 组")
    if stats['total'] > 0:
        pass_rate = (stats['passed'] / stats['total']) * 100
        print(f"📈 通过率: {pass_rate:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
