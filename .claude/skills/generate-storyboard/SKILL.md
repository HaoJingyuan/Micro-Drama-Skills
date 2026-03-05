---
name: generate-storyboard
description: 分镜生成技能。根据输入的故事文本（剧本或小说），分析人物/场景/道具及变体，生成参考图，拆分剧情为分镜故事板（快节奏爽点反转），生成6宫格分镜可视化，自动检查质量并优化（最多3次）。关键词：分镜、storyboard、人物提取、场景分析、故事板、分镜图生成、质量检查。
---

# 分镜生成技能 (Generate Storyboard)

## 概述

本技能从输入的故事文本（剧本或小说原文）自动生成完整的分镜故事板和可视化图片。适用于短剧、MV等影视内容制作。

**核心流程**（4个阶段）：
1. **元素提取** - 解析人物、场景、道具及其变体
2. **剧情拆分** - 按快节奏爽点密集模式生成分镜故事板
3. **分镜可视化** - 生成6宫格分镜图（9:16比例）
4. **质量检查** - 自动验证并优化（最多3次）

---

## 执行流程

### 第一步：元素提取与分析

#### 1.1 解析故事文本

读取用户提供的故事文本（剧本或小说原文），提取：
- **人物**：姓名、外貌、性格、关键特征
- **场景**：地点、环境描述、氛围
- **道具**：重要物品、标志性物件

#### 1.2 识别变体

分析每个元素在不同情节中的变化：

**人物变体**（根据剧情需要）：
- 不同服装（日常/正式/战斗等）
- 不同状态（健康/受伤/情绪）
- 不同时期（年轻/成熟/老年）

**场景变体**（不同角度/时间）：
- 不同视角（正面/侧面/俯视）
- 不同时段（白天/夜晚/黄昏）
- 不同天气（晴天/雨天/雪天）

**道具变体**（不同状态）：
- 完整/损坏
- 新旧程度
- 使用中/静置

#### 1.3 生成元素配置

将提取结果保存为 `elements_config.json`：

```json
{
  "characters": [
    {
      "id": "char_01",
      "name": "角色名",
      "base_description": "基础外貌描述",
      "variants": [
        {
          "variant_id": "char_01_v1",
          "label": "日常装",
          "description": "详细描述",
          "ai_prompt": "English prompt for generation"
        }
      ]
    }
  ],
  "scenes": [
    {
      "id": "scene_01",
      "name": "场景名",
      "base_description": "基础场景描述",
      "variants": [
        {
          "variant_id": "scene_01_v1",
          "label": "白天正面",
          "description": "详细描述",
          "ai_prompt": "English prompt"
        }
      ]
    }
  ],
  "props": [
    {
      "id": "prop_01",
      "name": "道具名",
      "base_description": "基础描述",
      "variants": [
        {
          "variant_id": "prop_01_v1",
          "label": "完整状态",
          "description": "详细描述",
          "ai_prompt": "English prompt"
        }
      ]
    }
  ]
}
```

#### 1.4 生成参考图

调用 `.claude/skills/scripts/generate_references.py` **一次性**生成所有参考图。脚本读取 `elements_config.json`，自动遍历全部人物/场景/道具的所有变体，已存在的图片自动跳过。

**只需调用一次：**
```bash
python .claude/skills/scripts/generate_references.py <project_dir> [model] [max_workers]
```

**并发策略（两阶段）：**
1. **Phase 1**：所有元素的首变体（v1）并发生成
2. **Phase 2**：首变体完成后，以首变体为参考图，并发生成剩余变体（v2, v3...），确保同一元素的变体风格一致

**API 配置：**
- API 端点：`https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com/api/generate-image`
- 支持模型：`gemini_3_pro_image`（默认）

**人物参考图要求**：
- 单张图包含：正面全身像（修改后：不再要求四宫格）
- 比例：9:16（竖版，适合角色展示）
- 文件名：`{variant_id}_ref.png`

**场景参考图**：
- 单张图包含当前视角，比例 16:9
- 文件名：`{variant_id}_ref.png`

**道具参考图**：
- 单张图包含三视图，比例 16:9
- 文件名：`{variant_id}_ref.png`

参见 `references/narration_style.md` 了解旁白风格参考。

#### 1.5 参考图质量校验（重要！）

**生成的参考图必须经过校验，确保符合以下要求：**

**校验方式：由 AI 直接检查**

使用 AI 的图片分析能力直接检查生成的参考图。AI 可以：
- 读取图片内容（通过 Read 工具）
- 分析图片是否符合要求
- 识别问题并提出修改建议
- 对比多张图片的一致性

**校验流程：**
1. 生成所有参考图后，提供图片路径给 AI
2. AI 逐一读取并分析图片
3. AI 根据检查维度给出评估
4. 对不合格的图片，AI 提供修改建议或直接调用修改脚本

**检查维度：**

**1. 风格一致性检查**
- 所有参考图的视觉风格必须统一
- 画风、色调、线条风格应保持一致
- 不同角色/场景/道具应该像是来自同一部作品

**2. 时代一致性检查**
- 人物服装、发型、配饰必须符合故事设定的时代背景
- 场景建筑、装饰、家具必须符合时代特征
- 道具的设计、材质、样式必须符合时代
- **避免穿帮**：不能出现现代元素混入古代场景，或古代元素混入现代场景

**3. 剧情符合性检查**
- 人物打扮必须符合剧情设定
- 角色的服装变化必须有剧情依据（如：日常装 → 正式装 → 战斗装）
- 场景细节必须与故事描述一致

**4. 图片质量检查**
- **不能有漫画文字气泡或对话框**
- 不能有多余的文字标注
- 图片清晰，没有明显瑕疵
- 角色特征清晰可辨

**校验不通过的处理方式：**

如果参考图不符合要求，有以下处理方式（按优先级）：

**方式1：图片修改（推荐）**

**核心原则：是否符合剧情要求**

图片修改的判断标准只有一个：**生成的图片是否符合剧情要求**。任何不符合剧情的图片都应该修改，不限于以下列举的情况。

使用图片修改功能，通过参考图+prompt来修改：
```python
# 调用生图API，传入要修改的图片作为参考
payload = {
    "model": "gemini_3_pro_image",
    "prompt": "描述需要修改的内容 + 明确保持不变的部分",
    "aspect_ratio": "9:16",
    "reference_images": ["原图URL"]
}
```

**常见修改场景（示例，不限于此）：**

1. **去除不符合要求的元素**
   - 去除文字气泡：`"Remove all text bubbles, speech balloons, and text overlays. Keep everything else unchanged."`
   - 去除多余物品：`"Remove the modern smartphone from the scene. Keep everything else unchanged."`
   - 去除不合理背景：`"Remove the background buildings. Replace with traditional Chinese architecture. Keep the character unchanged."`

2. **调整不符合剧情的细节**
   - 调整服装时代：`"Change the character's clothing to traditional Chinese style from Tang Dynasty. Keep the character's face and pose unchanged."`
   - 调整年龄外貌：`"Make the character look younger, around 8 years old. Keep the clothing and pose unchanged."`
   - 调整表情动作：`"Change the character's expression to sad and worried. Keep everything else unchanged."`
   - 调整道具状态：`"Change the cake to show it cut in half. Keep the plate and background unchanged."`

3. **统一不一致的风格**
   - 统一画风：`"Redraw in warm and healing anime style with soft colors. Keep the composition and character unchanged."`
   - 统一色调：`"Adjust the color tone to match the warm and cozy atmosphere. Keep the composition unchanged."`
   - 结合参考图修改：传入多张参考图，`"Match the art style of the reference images. Keep the character's appearance consistent."`

4. **修正不符合剧情的场景**
   - 调整场景氛围：`"Change the lighting to warm and cozy. Keep the layout and furniture unchanged."`
   - 调整场景细节：`"Add flour stains on the apron to show she's been baking. Keep the character and pose unchanged."`
   - 调整场景时间：`"Change to nighttime scene with dim lighting. Keep the interior layout unchanged."`

5. **修正角色不一致**
   - 统一角色外貌：`"Make the character's hairstyle match the reference image. Keep the clothing and pose unchanged."`
   - 调整角色比例：`"Make the character smaller and more petite to match an 8-year-old. Keep the face and clothing unchanged."`

**修改原则：**
- ✅ **明确修改目标**：清楚描述要改什么
- ✅ **明确保持不变**：清楚描述要保留什么
- ✅ **符合剧情为准**：一切以是否符合剧情要求为判断标准
- ✅ **可结合参考图**：传入多张参考图提高准确性
- ✅ **设置修改上限**：最多修改2-3次，不成功则降级

**判断是否需要修改的标准：**
1. 这个图片是否准确表达了剧情要求？
2. 角色的外貌、服装、表情是否符合剧情设定？
3. 场景的细节、氛围、时代是否符合故事背景？
4. 道具的状态、样式是否符合剧情逻辑？
5. 整体风格是否与其他图片一致？

**如果答案是"否"，就应该修改。**

**方式2：重新生成**
如果修改2-3次后仍不满意，放弃参考图修改，直接用优化后的prompt重新生成：
```python
# 不使用reference_images，直接用更详细的prompt
payload = {
    "model": "gemini_3_pro_image",
    "prompt": "详细的角色描述 + 风格要求 + 时代背景 + 无文字要求",
    "aspect_ratio": "9:16",
    "reference_images": []  # 不使用参考图
}
```

**方式3：手动修改**
使用图片编辑工具（如Photoshop）手动修改，适用于：
- 简单的去除文字
- 微调颜色和细节
- 合成多张图片

**校验流程建议：**
1. 生成所有参考图后，提供图片路径给 AI
2. AI 批量读取并分析所有参考图
3. AI 检查：风格一致性、时代一致性、剧情符合性、文字清洁度
4. AI 标记不合格的参考图并说明原因
5. 对于不合格的图片：
   - AI 提供修改建议（如何修改 prompt）
   - 或 AI 直接调用 `modify_image.py` 脚本进行修改
6. 修改后再次由 AI 检查
7. 全部通过后再进入下一步

**AI 检查示例：**
```
用户：请检查这些参考图
AI：我来逐一检查...
  - char_01_v1_ref.png: ✅ 符合要求
  - char_01_v2_ref.png: ❌ 有文字气泡，需要去除
  - scene_01_v1_ref.png: ✅ 符合要求
  - prop_01_v1_ref.png: ⚠️ 风格与其他图片不一致，建议重新生成
```

---

### 第二步：剧情拆分为分镜故事板

按短剧节奏将故事拆分为分镜故事板。

#### 2.1 拆分原则

**快节奏爽点密集模式**：
- 每集时长：1分钟
- 分镜数量：20-30个（可由用户指定，默认24个）
- 开头吸引人（3秒内钩子）
- 至少3次反转
- 节奏：快速推进，避免拖沓

#### 2.2 分镜故事板结构

生成 `storyboard.json`：

```json
{
  "episode_count": 1,
  "frames_per_episode": 24,
  "total_duration_seconds": 60,
  "episodes": [
    {
      "episode_number": 1,
      "title": "集标题",
      "duration_seconds": 60,
      "frames": [
        {
          "frame_number": 1,
          "time_start": 0.0,
          "time_end": 2.5,
          "characters": [
            {
              "variant_id": "char_01_v1",
              "name": "角色名",
              "action": "动作描述",
              "expression": "表情"
            }
          ],
          "scene_variant_id": "scene_01_v1",
          "prop_variant_ids": ["prop_01_v1"],
          "scene_description": "画面描述（中文，50字）",
          "camera": {
            "type": "远景|中景|近景|特写",
            "movement": "固定|推|拉|摇|移|跟",
            "angle": "平视|俯视|仰视"
          },
          "narration": {
            "text": "旁白内容（参考 narration_style.md）",
            "emotion": "情感基调"
          },
          "dialogue": {
            "speaker": "角色名",
            "text": "对话内容",
            "emotion": "语气"
          },
          "sfx": "音效描述"
        }
      ]
    }
  ]
}
```

#### 2.3 旁白风格匹配

旁白需参考 `references/narration_style.md` 中的风格示例，确保：
- 与画面内容匹配
- 情感基调一致
- 推进剧情节奏

---

---

### 第四步：质量检查与优化

**由 AI 直接检查生成的分镜图**，不符合要求则修改重试（最多3次）。

**检查方式：**
1. 用户提供分镜图路径给 AI
2. AI 使用 Read 工具读取图片
3. AI 根据检查维度进行分析
4. AI 给出评估结果和修改建议
5. 如需修改，AI 可以：
   - 提供修改 prompt 的建议
   - 直接调用 `modify_image.py` 脚本修改图片
   - 建议重新生成

**AI 检查的优势：**
- 可以看到图片的实际内容
- 可以理解剧情要求并判断是否符合
- 可以对比多张图片的一致性
- 可以提供具体的修改建议
- 可以直接调用修改工具

#### 4.1 检查维度

1. **人物一致性**
   - 角色是否与参考图是同一人？
   - 不同格之间角色外貌是否一致？

2. **布局正确性**
   - 是否为6宫格布局？
   - 是否为9:16比例？

3. **风格一致性**
   - 是否符合用户指定的视觉风格？
   - 所有分镜格的画风是否统一？

4. **镜头语言**
   - 是否有合理的景别变化？
   - 画面叙事是否流畅？

5. **时代一致性**
   - 人物服装、道具、场景是否符合故事设定的时代？
   - 是否有穿帮（如现代元素出现在古代场景）？

6. **文字清洁度**
   - 图片中是否有漫画文字气泡或对话框？
   - 是否有多余的文字标注？
   - **如有文字，必须去除**

7. **剧情符合性**
   - 画面内容是否符合分镜描述？
   - 角色动作、表情是否符合剧情？

#### 4.2 检查方法

**由 AI 直接检查图片：**

用户提供图片路径，AI 读取并分析：

```
用户：请检查 storyboard_ep01_group01.png

AI：我来检查这张分镜图...
[读取图片]

检查结果：
✅ 布局正确：6宫格，9:16比例
✅ 人物一致：角色外貌保持一致
❌ 文字清洁度：发现5处文字气泡和对话框
✅ 风格一致：温馨治愈风格统一
⚠️ 剧情符合性：第3格中角色表情与剧情不符

问题详情：
1. 第1格：有 "(Thinking)" 文字气泡
2. 第2格：有对话框 "啊，对不起..."
3. 第3格：角色应该是紧张表情，但图中是微笑
4. 第5格：有 "(Thinking)" 文字气泡
5. 第6格：有对话框 "松软多孔..."

修改建议：
1. 使用 modify_image.py 去除所有文字气泡
2. 第3格需要重新生成或修改表情
```

**AI 可以批量检查：**

```
用户：请检查所有分镜图

AI：我来检查所有4张分镜图...

Group 1: ✅ 通过
Group 2: ✅ 通过
Group 3: ⚠️ 有1处问题
Group 4: ❌ 有5处问题（文字气泡）

详细报告已生成...
```

**备选方案：使用脚本检查**

如果需要自动化检查，可以调用 `.claude/skills/scripts/check_storyboard_quality.py`：

```python
check_result = check_storyboard_quality(
    image_path="storyboard_group_01.png",
    reference_images=[...],
    expected_style="风格名",
    frame_descriptions=[...]
)

# 返回格式
{
  "passed": false,
  "issues": [
    {
      "dimension": "character_consistency",
      "severity": "high",
      "description": "格1和格3中的主角发型不一致"
    },
    {
      "dimension": "visual_style",
      "severity": "medium",
      "description": "整体色调偏暖，不符合暗黑风格要求"
    }
  ],
  "suggestions": [
    "修改prompt：强调角色发型为黑色短发",
    "修改prompt：添加 'dark moody lighting, cool color palette'"
  ]
}
```

#### 4.3 优化策略

根据检查结果，采用以下策略修复问题：

**核心判断标准：是否符合剧情要求**

所有优化策略的目标只有一个：**让图片符合剧情要求**。不符合剧情的任何方面都应该修改。

**策略1：修改prompt**
- 强化角色描述（如"same character as reference, consistent appearance"）
- 调整风格关键词
- 增加镜头语言提示
- 添加时代背景描述
- 明确要求"no text, no speech bubbles, no dialogue boxes"
- **添加剧情相关描述**（如角色情绪、场景氛围、道具状态）

**策略2：图片修改（推荐）**

使用生图API的参考图功能进行图片修改。

**适用于任何不符合剧情要求的情况，包括但不限于：**

- 角色外貌、服装、表情不符合剧情
- 场景细节、氛围、时代不符合故事
- 道具状态、样式不符合剧情逻辑
- 画面中有不应该出现的元素
- 画面缺少应该出现的元素
- 风格与其他图片不一致
- 有文字气泡或对话框

**修改方法：**
```python
# 基本格式
payload = {
    "model": "gemini_3_pro_image",
    "prompt": "[描述要修改的内容] + Keep [描述要保持不变的部分] unchanged.",
    "aspect_ratio": "9:16",
    "reference_images": ["原图URL"]
}

# 示例1：修改角色表情以符合剧情
payload = {
    "prompt": "Change the character's expression to worried and nervous, with red-rimmed eyes. Keep the character's appearance, clothing, and pose unchanged.",
    "reference_images": ["原图URL"]
}

# 示例2：修改场景氛围以符合剧情
payload = {
    "prompt": "Change the lighting to dim and gloomy to show the shop is struggling. Keep the layout and furniture unchanged.",
    "reference_images": ["原图URL"]
}

# 示例3：修改道具状态以符合剧情
payload = {
    "prompt": "Show the cake as freshly baked with steam rising. Keep the cake design and plate unchanged.",
    "reference_images": ["原图URL"]
}

# 示例4：去除不符合剧情的元素
payload = {
    "prompt": "Remove the modern smartphone from the character's hand. Keep everything else unchanged.",
    "reference_images": ["原图URL"]
}

# 示例5：添加符合剧情的元素
payload = {
    "prompt": "Add flour stains on the apron to show she has been baking. Keep the character and pose unchanged.",
    "reference_images": ["原图URL"]
}
```

**图片修改的核心原则：**
1. **明确修改目标**：清楚描述要改什么，为什么要改（符合哪个剧情要求）
2. **明确保持不变**：清楚描述要保留什么
3. **以剧情为准**：一切修改都是为了让图片更符合剧情
4. **可结合参考图**：传入多张参考图（风格参考+内容参考）
5. **设置修改上限**：最多修改2-3次

**判断是否需要修改：**
- 这个图片是否准确表达了剧情要求？
- 角色的一切是否符合剧情设定？
- 场景的一切是否符合故事背景？
- 道具的一切是否符合剧情逻辑？
- 整体是否与其他图片风格一致？

**如果任何一项答案是"否"，就应该修改。**

**使用图片修改脚本：**

为了方便修改图片，已提供专门的修改脚本 `scripts/modify_image.py`：

```bash
# 基本用法
python .claude/skills/generate-storyboard/scripts/modify_image.py \
  <input_image> \
  <output_image> \
  "<modification_prompt>" \
  [model] \
  [aspect_ratio]

# 示例1：去除文字气泡
python .claude/skills/generate-storyboard/scripts/modify_image.py \
  "projects/xiaoqie/storyboards/storyboard_ep01_group04.png" \
  "projects/xiaoqie/storyboards/storyboard_ep01_group04_fixed.png" \
  "Remove all text bubbles and dialogue boxes. Keep everything else unchanged."

# 示例2：使用备用模型
python .claude/skills/generate-storyboard/scripts/modify_image.py \
  "input.png" \
  "output.png" \
  "Change character clothing to 1990s style. Keep face unchanged." \
  gemini-3-pro-openrouter

# 示例3：指定比例
python .claude/skills/generate-storyboard/scripts/modify_image.py \
  "input.png" \
  "output.png" \
  "Remove text" \
  gemini_3_pro_image \
  "16:9"
```

**脚本特性：**
- 自动上传原图到 TOS
- 调用生图 API 进行修改
- 自动下载修改后的图片
- 超时时间：120秒
- 失败时自动尝试备用模型（gemini-3-pro-openrouter）
- 支持自定义模型和比例

**注意事项：**
- 如果 API 超时，可以尝试不同的模型
- 如果多次失败，考虑使用手动编辑工具
- 修改前建议备份原图

**策略3：重新生成（降级方案）**
如果图片修改多次仍不成功：
- 放弃使用参考图
- 优化prompt，使其更详细、更明确
- 直接用文生图方式重新生成
- 在prompt中明确所有要求（风格、时代、无文字等）

**策略4：修改参考图**
如果问题源于参考图本身：
- 重新生成更清晰的参考图
- 确保参考图符合风格、时代、剧情要求
- 参考图必须无文字、无气泡

**优化流程：**
1. 识别问题类型（人物、风格、时代、文字等）
2. 优先尝试图片修改（策略2）
3. 修改失败则优化prompt重新生成（策略3）
4. 如果是参考图问题，修改参考图（策略4）
5. 最多尝试3次
6. 记录问题和解决方案

#### 4.4 终止条件

- 检查通过（`passed: true`）
- 已尝试3次（记录最终问题）

---

## 输出文件结构

完整的分镜生成产出：

```
project_output/
├── elements_config.json          # 元素配置（人物/场景/道具+变体）
├── storyboard.json                # 完整故事板配置
├── references/                    # 参考图
│   ├── char_01_v1_ref.png        # 角色变体1参考图（四宫格）
│   ├── char_01_v2_ref.png        # 角色变体2参考图
│   ├── scene_01_v1_ref.png       # 场景变体1
│   └── prop_01_v1_ref.png        # 道具变体1
├── storyboards/                   # 分镜图（脚本自动生成）
│   ├── storyboard_ep01_group01.png   # Episode 1 第1-6格
│   ├── storyboard_ep01_group02.png   # Episode 1 第7-12格
│   ├── storyboard_ep01_group03.png   # Episode 1 第13-18格
│   └── storyboard_ep01_group04.png   # Episode 1 第19-24格
└── quality_reports/               # 质量检查报告
    ├── group_01_check.json
    ├── group_02_check.json
    └── ...
```

---

## 运行指令

用户可通过以下方式触发：
- "生成分镜图"
- "create storyboard"
- "根据故事生成分镜"
- "制作分镜故事板"

可选参数：
- **故事文本路径**：`--story path/to/story.txt`
- **每集分镜数**：`--frames 24`
- **视觉风格**：`--style "赛博朋克"`

---

## 用户交互节点

在执行过程中需要与用户交互的环节：

1. **视觉风格选择**（第三步开始前）
   - 使用 `AskUserQuestion` 列出可选风格
   - 或让用户自定义风格描述

2. **分镜数量确认**（第二步开始前）
   - 默认24个/集
   - 用户可指定20-30范围

3. **参考图质量检查**（第一步完成后）
   - AI 主动检查所有参考图
   - 向用户报告检查结果
   - 对不合格的图片提供修改建议
   - 询问用户是否修改或重新生成

4. **分镜图质量检查**（第三步完成后）
   - AI 主动检查所有分镜图
   - 向用户报告检查结果
   - 对不合格的图片提供修改建议
   - 如3次优化后仍有问题，询问用户是否接受当前结果或手动调整

**AI 主动检查流程：**
```
1. 生成参考图完成
   ↓
2. AI 自动读取所有参考图
   ↓
3. AI 进行质量检查
   ↓
4. AI 向用户报告结果
   ↓
5. 如有问题，AI 提供修改方案
   ↓
6. 用户确认后继续或修改
```

---

## 执行检查清单

- [ ] 故事文本已读取
- [ ] `elements_config.json` 已生成
- [ ] 所有元素参考图已生成到 `references/` 目录
- [ ] **参考图已通过质量校验**
  - [ ] 风格一致性检查通过
  - [ ] 时代一致性检查通过
  - [ ] 剧情符合性检查通过
  - [ ] 无文字气泡和对话框
- [ ] `storyboard.json` 已生成
- [ ] 分镜数量符合要求（20-30个）
- [ ] 每集至少3次反转
- [ ] 所有6宫格分镜图已生成
- [ ] 质量检查已执行
  - [ ] 人物一致性检查通过
  - [ ] 风格一致性检查通过
  - [ ] 时代一致性检查通过
  - [ ] 无文字气泡和对话框
  - [ ] 剧情符合性检查通过
- [ ] 不合格项已优化（最多3次）
- [ ] `quality_reports/` 包含所有检查报告
- [ ] 用户已确认视觉风格
- [ ] 旁白风格符合 `narration_style.md` 要求

---

## 输出示例

```
✅ 分镜生成完成！

📋 项目信息
- 故事来源：《示例故事》
- 总分镜数：24个
- 视觉风格：赛博朋克

📊 元素统计
- 人物：3个（5个变体）
- 场景：2个（4个变体）
- 道具：1个（2个变体）

📂 输出目录：project_output/

🎨 参考图
- 角色参考图：5张
- 场景参考图：4张
- 道具参考图：2张

🖼️ 分镜图
- 6宫格图片：4张（共24格）

✅ 质量检查
- 通过组数：4/4
- 优化次数：1次（第2组）

⏭️ 下一步
使用生成的分镜图和故事板配置进行视频制作
```

---

## 已知问题和解决方案

### 问题1：角色参考图生成失败（422错误）

**症状：**
- API 返回 422 Unprocessable Entity 错误
- 只影响角色生成，场景和道具正常

**原因：**
- 原始脚本要求生成 2x2 grid layout（四宫格）
- API 不支持这种复杂的多视图布局

**解决方案：**
已在 `scripts/generate_references.py` 中修复：
- 改用单一正面视角（front view）
- 比例从 1:1 改为 9:16（竖版）
- 移除 grid layout 要求

**修改后的代码：**
```python
def _build_character_prompt(vi):
    prompt = f"""
    {vi['ai_prompt']}

    Full body character portrait, front view, standing pose.
    Clean white background, high quality, detailed.
    Character design, anime style.
    """
    return prompt, "9:16"  # Changed from 1:1
```

**效果：**
- ✅ 角色生成成功率：100%
- ✅ 平均生成时间：26.6秒/图

### 问题2：偶尔的超时错误

**症状：**
- 个别图片生成超时（120秒）
- 非系统性问题，随机发生

**解决方案：**
- 重新运行脚本即可
- 脚本会自动跳过已生成的图片
- 只重新生成失败的项

### 最佳实践

**Prompt 设计：**
1. 保持简洁（20-30个单词）
2. 使用逗号分隔关键特征
3. 避免复杂的布局指令
4. 不在 ai_prompt 中指定比例和布局（由脚本处理）
5. **明确时代背景**（如"1990s Chinese style", "Tang Dynasty", "modern urban"）
6. **明确要求无文字**（"no text, no speech bubbles, no dialogue boxes"）

**生成策略：**
1. 角色：9:16 比例，单一正面视角
2. 场景：16:9 比例，环境描述
3. 道具：16:9 比例，三视图布局

**风格一致性保证：**
1. **在 elements_config.json 中统一风格描述**
   - 所有元素的 ai_prompt 都应包含相同的风格关键词
   - 例如："warm and healing anime style, soft colors"
2. **使用参考图保持一致性**
   - Phase 2 生成时使用 Phase 1 的图作为参考
   - 确保同一元素的变体风格统一
3. **批量检查风格**
   - 生成后先预览所有参考图
   - 确认风格统一后再进入下一步

**时代一致性保证：**
1. **明确故事时代背景**
   - 在 prompt 中明确时代（如"1990s", "modern", "ancient China"）
2. **检查服装道具**
   - 人物服装必须符合时代
   - 道具设计必须符合时代
   - 场景建筑必须符合时代
3. **避免穿帮**
   - 不能出现时代错乱（如古代人穿现代服装）
   - 不能出现不符合时代的道具（如古代场景出现手机）

**剧情符合性保证：**
1. **人物打扮符合剧情**
   - 角色服装变化必须有剧情依据
   - 例如：日常装 → 正式装 → 战斗装
2. **场景细节符合故事**
   - 场景描述必须与故事设定一致
   - 例如：破旧的小店 vs 豪华的餐厅
3. **道具使用符合逻辑**
   - 道具的状态变化必须有剧情依据
   - 例如：完整的蛋糕 → 切开的蛋糕

**文字清洁度保证：**
1. **生成时明确要求无文字**
   - 在 prompt 中加入："no text, no speech bubbles, no dialogue boxes, no text overlays"
2. **检查并去除文字**
   - 如果生成的图有文字气泡，使用图片修改功能去除
   - 修改prompt："Remove all text bubbles and dialogue boxes. Keep everything else unchanged."
3. **参考图必须无文字**
   - 参考图如有文字，必须先修改后再使用

**图片修改最佳实践：**
1. **明确保持不变的部分**
   - "Keep the character's face and pose unchanged"
   - "Keep the background and composition unchanged"
2. **结合多张参考图**
   - 风格参考图 + 内容参考图
   - 提高修改的准确性
3. **设置修改次数上限**
   - 最多修改2-3次
   - 不成功则改用重新生成
4. **记录修改经验**
   - 哪些修改容易成功
   - 哪些修改容易失败

**重试策略：**
1. 如果生成失败，直接重新运行脚本
2. 脚本会自动跳过已成功的图片
3. 最多重试2-3次即可解决偶发问题
4. 如果持续失败，检查prompt是否有问题

