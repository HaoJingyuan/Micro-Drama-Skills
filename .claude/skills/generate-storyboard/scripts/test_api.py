#!/usr/bin/env python3
"""
API 测试脚本
用于验证图片生成和上传接口是否正常工作
"""

import os
import json
import requests
from pathlib import Path


# API 配置
API_BASE_URL = "https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com"
GENERATE_IMAGE_URL = f"{API_BASE_URL}/api/generate-image"
UPLOAD_IMAGE_URL = f"{API_BASE_URL}/api/tos/upload-image"


def load_config():
    """
    从多种来源加载配置（优先级：环境变量 > 默认值）

    Returns:
        dict: 配置信息
    """
    config = {
        "username": os.environ.get("STORYBOARD_USERNAME", "test_user"),
        "project_title": os.environ.get("STORYBOARD_PROJECT", "test_project")
    }
    return config


def test_generate_image():
    """测试图片生成接口"""
    print("=" * 60)
    print("测试图片生成接口")
    print("=" * 60)

    payload = {
        "model": "gemini_3_pro_image",
        "prompt": "A simple test image: a red square on white background",
        "aspect_ratio": "9:16",
        "reference_images": []
    }

    print(f"🔗 URL: {GENERATE_IMAGE_URL}")
    print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()

    try:
        print("⏳ 发送请求...")
        response = requests.post(
            GENERATE_IMAGE_URL,
            json=payload,
            timeout=120
        )

        print(f"📊 状态码: {response.status_code}")
        print()

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if result.get("success"):
                print("\n✅ 图片生成测试通过！")
                image_url = result.get("image_url") or result.get("original_url")
                if image_url:
                    print(f"🖼️ 图片URL: {image_url}")
                return True
            else:
                print(f"\n❌ 生成失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时（120秒）")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_upload_image():
    """测试图片上传接口"""
    print("\n" + "=" * 60)
    print("测试图片上传接口")
    print("=" * 60)

    # 创建测试图片
    from PIL import Image
    import io

    test_image = Image.new("RGB", (256, 256), color="red")
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    config = load_config()
    username = config.get("username", "test_user")
    project_title = config.get("project_title", "test_project")

    print(f"🔗 URL: {UPLOAD_IMAGE_URL}")
    print(f"👤 用户: {username}")
    print(f"📁 项目: {project_title}")
    print()

    try:
        print("⏳ 上传测试图片...")
        files = {"file": ("test_image.png", img_bytes, "image/png")}
        data = {
            "username": username,
            "project_title": project_title,
            "category": "test"
        }

        response = requests.post(
            UPLOAD_IMAGE_URL,
            files=files,
            data=data,
            timeout=60
        )

        print(f"📊 状态码: {response.status_code}")
        print()

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if result.get("success"):
                print("\n✅ 图片上传测试通过！")
                image_url = result.get("image_url")
                if image_url:
                    print(f"🖼️ 图片URL: {image_url}")
                return True
            else:
                print(f"\n❌ 上传失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时（60秒）")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    print("\n🧪 API 接口测试")
    print(f"🔗 基础URL: {API_BASE_URL}\n")

    # 加载配置
    config = load_config()
    print(f"⚙️ 配置信息:")
    print(f"  - 用户名: {config.get('username', 'test_user')}")
    print(f"  - 项目名: {config.get('project_title', 'test_project')}")
    print()

    # 测试图片生成
    generate_ok = test_generate_image()

    # 测试图片上传
    upload_ok = test_upload_image()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"图片生成接口: {'✅ 通过' if generate_ok else '❌ 失败'}")
    print(f"图片上传接口: {'✅ 通过' if upload_ok else '❌ 失败'}")

    if generate_ok and upload_ok:
        print("\n🎉 所有测试通过！API 配置正确，可以开始使用。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接。")

    print("=" * 60)


if __name__ == "__main__":
    main()
