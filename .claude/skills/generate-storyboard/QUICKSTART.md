# 快速开始指南

最简单的方式使用 generate-storyboard 技能。

## 1. 测试 API（可选）

```bash
export STORYBOARD_USERNAME="your_username"
export STORYBOARD_PROJECT="test_project"
python scripts/test_api.py
```

如果看到 `🎉 所有测试通过！` 说明 API 正常。

## 2. 创建项目

```bash
mkdir my_storyboard
cd my_storyboard
```

## 3. 创建元素配置

创建 `elements_config.json`：
```json
{
  "characters": [
    {
      "id": "char_01",
      "name": "主角",
      "variants": [
        {
          "variant_id": "char_01_v1",
          "label": "日常装",
          "ai_prompt": "A young hero, casual clothes, determined eyes"
        }
      ]
    }
  ],
  "scenes": [
    {
      "id": "scene_01",
      "name": "街道",
      "variants": [
        {
          "variant_id": "scene_01_v1",
          "label": "白天",
          "ai_prompt": "City street, daytime, cinematic"
        }
      ]
    }
  ],
  "props": []
}
```

## 4. 生成参考图

```bash
python ../scripts/generate_references.py .
```

生成的图片在 `references/` 目录。

## 5. 创建故事板

创建 `storyboard.json`（简化示例，6个分镜）：
```json
{
  "episodes": [
    {
      "episode_number": 1,
      "title": "开始",
      "frames": [
        {
          "frame_number": 1,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角站在街道上",
          "camera": {"type": "中景", "movement": "固定", "angle": "平视"}
        },
        {
          "frame_number": 2,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角奔跑",
          "camera": {"type": "特写", "movement": "跟", "angle": "侧面"}
        },
        {
          "frame_number": 3,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角停下",
          "camera": {"type": "近景", "movement": "推", "angle": "俯视"}
        },
        {
          "frame_number": 4,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角抬头",
          "camera": {"type": "特写", "movement": "固定", "angle": "平视"}
        },
        {
          "frame_number": 5,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角微笑",
          "camera": {"type": "全景", "movement": "拉", "angle": "平视"}
        },
        {
          "frame_number": 6,
          "characters": [{"variant_id": "char_01_v1", "name": "主角"}],
          "scene_variant_id": "scene_01_v1",
          "scene_description": "主角转身离开",
          "camera": {"type": "中景", "movement": "固定", "angle": "仰视"}
        }
      ]
    }
  ]
}
```

## 6. 生成分镜图

**直接使用命令行参数（最简单）**：
```bash
python ../scripts/generate_storyboard_image.py . "cinematic" gemini_3_pro_image your_username your_project
```

或者**使用环境变量**：
```bash
export STORYBOARD_USERNAME="your_username"
export STORYBOARD_PROJECT="your_project"
python ../scripts/generate_storyboard_image.py . "cinematic"
```

## 7. 查看结果

```bash
ls -lh storyboards/
```

你会看到 `storyboard_ep01_group01.png` - 一张 9:16 的 6 宫格分镜图！

## 完成！

现在你已经成功生成了第一张分镜图。

## 下一步

- 添加更多角色、场景、道具
- 创建更多分镜（24个/集）
- 尝试不同的视觉风格
- 生成多集内容

查看 `example_workflow.md` 了解完整的工作流程。
