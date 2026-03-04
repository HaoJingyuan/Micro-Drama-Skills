# 完整工作流示例

本文档展示如何使用 generate-storyboard 技能从故事文本生成分镜图的完整流程。

## 准备工作

### 1. 选择配置方式

**推荐方式：使用命令行参数**
无需配置文件，直接在运行脚本时传入 username 和 project_title。

**可选方式一：项目本地配置**
在项目目录下创建 `config.json`：
```bash
cp project_config.example.json ./my_storyboard/config.json
# 编辑 config.json
```

**可选方式二：环境变量**
```bash
export STORYBOARD_USERNAME="manju"
export STORYBOARD_PROJECT="my_storyboard"
```

### 2. 测试 API

```bash
# 使用环境变量测试
export STORYBOARD_USERNAME="manju"
export STORYBOARD_PROJECT="test"
python scripts/test_api.py
```

确保两个接口测试都通过。

## 工作流步骤

### 步骤 1：创建项目目录

```bash
mkdir my_storyboard
cd my_storyboard
```

### 步骤 2：准备故事文本

创建 `story.txt`，输入你的故事内容（剧本或小说）。

### 步骤 3：创建元素配置

创建 `elements_config.json`，定义人物、场景、道具及其变体。

**示例**：

```json
{
  "characters": [
    {
      "id": "char_01",
      "name": "主角",
      "base_description": "一个年轻的冒险家",
      "variants": [
        {
          "variant_id": "char_01_v1",
          "label": "日常装",
          "description": "穿着普通休闲服的主角",
          "ai_prompt": "A young adventurer wearing casual clothes, short black hair, determined eyes, athletic build, white background"
        },
        {
          "variant_id": "char_01_v2",
          "label": "战斗装",
          "description": "穿着战斗服的主角",
          "ai_prompt": "A young adventurer in combat gear, short black hair, determined eyes, athletic build, armor and weapons, white background"
        }
      ]
    }
  ],
  "scenes": [
    {
      "id": "scene_01",
      "name": "城市街道",
      "base_description": "现代都市的繁华街道",
      "variants": [
        {
          "variant_id": "scene_01_v1",
          "label": "白天正面",
          "description": "白天的城市街道，从正面角度",
          "ai_prompt": "Modern city street, daytime, front view, tall buildings, busy traffic, clear sky, cinematic lighting"
        }
      ]
    }
  ],
  "props": [
    {
      "id": "prop_01",
      "name": "神秘宝石",
      "base_description": "发光的蓝色宝石",
      "variants": [
        {
          "variant_id": "prop_01_v1",
          "label": "完整状态",
          "description": "完整的神秘宝石",
          "ai_prompt": "Glowing blue gemstone, perfect condition, faceted surface, magical aura, white background"
        }
      ]
    }
  ]
}
```

### 步骤 4：生成参考图

```bash
python ../scripts/generate_references.py . gemini_3_pro_image
```

这会在 `references/` 目录下生成：
- `char_01_v1_ref.png` - 角色日常装参考图（四宫格）
- `char_01_v2_ref.png` - 角色战斗装参考图（四宫格）
- `scene_01_v1_ref.png` - 场景参考图
- `prop_01_v1_ref.png` - 道具参考图

### 步骤 5：创建故事板配置

创建 `storyboard.json`，定义分镜故事板。

**示例**（简化版，仅包含6个分镜）：

```json
{
  "episode_count": 1,
  "frames_per_episode": 24,
  "total_duration_seconds": 60,
  "episodes": [
    {
      "episode_number": 1,
      "title": "冒险开始",
      "duration_seconds": 60,
      "frames": [
        {
          "frame_number": 1,
          "time_start": 0.0,
          "time_end": 2.5,
          "characters": [
            {
              "variant_id": "char_01_v1",
              "name": "主角",
              "action": "站在街头，抬头仰望",
              "expression": "坚定"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": [],
          "scene_description": "主角站在繁华的城市街道上，阳光洒在他坚定的脸上",
          "camera": {
            "type": "中景",
            "movement": "固定",
            "angle": "平视"
          },
          "narration": {
            "text": "这一刻，他终于下定了决心",
            "emotion": "坚定"
          },
          "dialogue": null,
          "sfx": "城市环境音"
        },
        {
          "frame_number": 2,
          "time_start": 2.5,
          "time_end": 5.0,
          "characters": [
            {
              "variant_id": "char_01_v1",
              "name": "主角",
              "action": "快速奔跑",
              "expression": "专注"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": [],
          "scene_description": "主角在街道上快速奔跑，背景模糊",
          "camera": {
            "type": "特写",
            "movement": "跟",
            "angle": "侧面"
          },
          "narration": null,
          "dialogue": {
            "speaker": "主角",
            "text": "不能再等了！",
            "emotion": "急切"
          },
          "sfx": "脚步声"
        },
        {
          "frame_number": 3,
          "time_start": 5.0,
          "time_end": 7.5,
          "characters": [
            {
              "variant_id": "char_01_v1",
              "name": "主角",
              "action": "停下脚步，发现宝石",
              "expression": "惊讶"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": ["prop_01_v1"],
          "scene_description": "主角停下脚步，地上有一颗发光的蓝色宝石",
          "camera": {
            "type": "近景",
            "movement": "推",
            "angle": "俯视"
          },
          "narration": {
            "text": "这是……",
            "emotion": "惊讶"
          },
          "dialogue": null,
          "sfx": "宝石发光音效"
        },
        {
          "frame_number": 4,
          "time_start": 7.5,
          "time_end": 10.0,
          "characters": [
            {
              "variant_id": "char_01_v1",
              "name": "主角",
              "action": "弯腰捡起宝石",
              "expression": "好奇"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": ["prop_01_v1"],
          "scene_description": "主角手中拿着发光的宝石，仔细观察",
          "camera": {
            "type": "特写",
            "movement": "固定",
            "angle": "平视"
          },
          "narration": null,
          "dialogue": {
            "speaker": "主角",
            "text": "这是传说中的……",
            "emotion": "震惊"
          },
          "sfx": "宝石嗡鸣"
        },
        {
          "frame_number": 5,
          "time_start": 10.0,
          "time_end": 12.5,
          "characters": [
            {
              "variant_id": "char_01_v2",
              "name": "主角",
              "action": "宝石发光，身上的衣服变成战斗装",
              "expression": "惊讶转为兴奋"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": ["prop_01_v1"],
          "scene_description": "宝石释放强烈的光芒，主角的衣服变成了战斗装",
          "camera": {
            "type": "全景",
            "movement": "拉",
            "angle": "平视"
          },
          "narration": {
            "text": "力量，觉醒了",
            "emotion": "震撼"
          },
          "dialogue": null,
          "sfx": "能量爆发音效"
        },
        {
          "frame_number": 6,
          "time_start": 12.5,
          "time_end": 15.0,
          "characters": [
            {
              "variant_id": "char_01_v2",
              "name": "主角",
              "action": "握拳，摆出战斗姿态",
              "expression": "坚定自信"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": [],
          "scene_description": "主角穿着战斗装，握拳摆出战斗姿态，背景是城市街道",
          "camera": {
            "type": "中景",
            "movement": "固定",
            "angle": "仰视"
          },
          "narration": {
            "text": "冒险，从此刻开始",
            "emotion": "激昂"
          },
          "dialogue": null,
          "sfx": "英雄主题音乐渐起"
        }
      ]
    }
  ]
}
```

### 步骤 6：生成分镜图

**方式一：使用命令行参数（推荐）**
```bash
python ../scripts/generate_storyboard_image.py . "赛博朋克" gemini_3_pro_image manju my_storyboard
```

**方式二：使用项目配置文件**
```bash
# 确保项目目录下有 config.json
python ../scripts/generate_storyboard_image.py . "赛博朋克" gemini_3_pro_image
```

**方式三：使用环境变量**
```bash
export STORYBOARD_USERNAME="manju"
export STORYBOARD_PROJECT="my_storyboard"
python ../scripts/generate_storyboard_image.py . "赛博朋克" gemini_3_pro_image
```

这会：
1. 上传所有需要的参考图到 TOS
2. 生成 6 宫格分镜图
3. 保存到 `storyboards/storyboard_ep01_group01.png`

### 步骤 7：查看结果

```bash
ls -lh storyboards/
```

你应该看到生成的分镜图文件。

## 完整目录结构

完成后，项目目录结构如下：

```
my_storyboard/
├── story.txt                      # 原始故事文本
├── elements_config.json           # 元素配置
├── storyboard.json                # 故事板配置
├── references/                    # 参考图
│   ├── char_01_v1_ref.png        # 角色日常装（四宫格）
│   ├── char_01_v2_ref.png        # 角色战斗装（四宫格）
│   ├── scene_01_v1_ref.png       # 场景参考图
│   └── prop_01_v1_ref.png        # 道具参考图
└── storyboards/                   # 分镜图
    └── storyboard_ep01_group01.png  # 6宫格分镜图
```

## 进阶用法

### 使用不同模型

目前支持的模型：
- `gemini_3_pro_image`（默认，高质量）

### 自定义视觉风格

支持的风格示例：
- "cinematic"（电影质感）
- "赛博朋克"
- "暗黑悬疑"
- "温馨治愈"
- "热血动漫"

### 批量生成多集

如果你有多集内容，只需在 `storyboard.json` 中添加更多 episode：

```json
{
  "episodes": [
    { "episode_number": 1, "title": "冒险开始", "frames": [...] },
    { "episode_number": 2, "title": "初次战斗", "frames": [...] },
    { "episode_number": 3, "title": "真相揭晓", "frames": [...] }
  ]
}
```

然后运行同样的命令，脚本会自动处理所有集。

## 常见问题

### Q: 生成的角色不一致怎么办？
A:
1. 确保参考图质量高，四宫格清晰
2. 在 prompt 中强调 "maintain character consistency"
3. 使用更高质量的模型

### Q: 分镜图布局不对怎么办？
A:
1. 在 prompt 中明确说明 "6-grid layout, 3 rows x 2 columns"
2. 确保 aspect_ratio 设置为 "9:16"
3. 检查每个分镜的描述是否清晰

### Q: 如何提高生成速度？
A:
1. 减少参考图数量（只上传必需的）
2. 简化 prompt 描述
3. 使用更快的模型（如果可用）

## 下一步

1. 使用生成的分镜图进行视频制作
2. 调整 prompt 优化生成质量
3. 添加更多角色变体和场景变体
4. 创建多集系列作品
