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

调用 `scripts/generate_references.py` **一次性**生成所有参考图。脚本读取 `elements_config.json`，自动遍历全部人物/场景/道具的所有变体，已存在的图片自动跳过。

**只需调用一次：**
```bash
python scripts/generate_references.py <project_dir> [model] [max_workers]
```

**并发策略（两阶段）：**
1. **Phase 1**：所有元素的首变体（v1）并发生成
2. **Phase 2**：首变体完成后，以首变体为参考图，并发生成剩余变体（v2, v3...），确保同一元素的变体风格一致

**API 配置：**
- API 端点：`https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com/api/generate-image`
- 支持模型：`gemini_3_pro_image`（默认）

**人物参考图要求**：
- 单张图包含：三视图（正面/侧面/背面）+ 脸部特写
- 四宫格布局（2×2），比例 1:1
- 文件名：`{variant_id}_ref.png`

**场景参考图**：
- 单张图包含当前视角，比例 16:9
- 文件名：`{variant_id}_ref.png`

**道具参考图**：
- 单张图包含三视图，比例 16:9
- 文件名：`{variant_id}_ref.png`

参见 `references/narration_style.md` 了解旁白风格参考。

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

### 第三步：分镜可视化

将故事板转化为6宫格分镜图。

#### 3.1 脚本调用方式

**只需调用一次** `scripts/generate_storyboard_image.py`，脚本会自动：
- 读取 `storyboard.json` 中所有 episode 的所有 frame
- 每6个 frame 自动分为一组（group）
- 已存在的图片自动跳过
- 所有 group 并发生成

```bash
python scripts/generate_storyboard_image.py <project_dir> [visual_style] [model] [max_workers] [--retry SPEC]
```

**参数说明：**
| 参数 | 默认值 | 说明 |
|------|--------|------|
| project_dir | (必填) | 项目目录，需包含 storyboard.json 和 references/ |
| visual_style | "cinematic" | 视觉风格描述 |
| model | "gemini_3_pro_image" | 生成模型 |
| max_workers | 4 | 最大并发数 |
| --retry SPEC | (无) | 重试指定 group，见下方说明 |

**配置**：username 和 project_title 从 `project_dir/config.json` 读取。

#### 3.2 并发策略

每个 episode 内部三阶段执行：

1. **收集去重**：遍历所有 group，合并参考图路径并去重
2. **并发上传**：将去重后的参考图并发上传到 TOS（同一张图只上传一次）
3. **并发生成**：所有 group 并发调用生成 API，共享上传结果

```
Episode 1:
  收集 → 去重参考图 {char_01_v1, char_02_v1, scene_01_v1}
  并发上传 3 张参考图
  并发生成 Group1, Group2, Group3, Group4
```

#### 3.3 重试机制

脚本默认跳过已存在的输出文件。如需重试失败的 group，使用 `--retry` 参数：

```bash
# 重试 Episode 1 的 Group 2 和 Group 5
python scripts/generate_storyboard_image.py ./project_dir "风格" --retry 1-2,1-5

# 重试 Episode 1 的所有 group
python scripts/generate_storyboard_image.py ./project_dir "风格" --retry 1

# 强制全部重新生成
python scripts/generate_storyboard_image.py ./project_dir "风格" --retry all
```

匹配到的 group 会删除旧文件并重新生成，不匹配的保持跳过。

#### 3.4 生成要求

- **比例**：9:16（竖版）
- **布局**：6宫格（3行2列）
- **风格**：用户指定（在开始时通过 AskUserQuestion 询问）
- **一致性**：角色外貌参考 reference_images
- **模型**：gemini_3_pro_image（默认）
- **输出命名**：`storyboard_ep{NN}_group{NN}.png`

---

### 第四步：质量检查与优化

自动检查生成的分镜图，不符合要求则修改重试（最多3次）。

#### 4.1 检查维度

1. **人物一致性**
   - 角色是否与参考图是同一人？
   - 不同格之间角色外貌是否一致？

2. **布局正确性**
   - 是否为6宫格布局？
   - 是否为9:16比例？

3. **风格匹配**
   - 是否符合用户指定的视觉风格？

4. **镜头语言**
   - 是否有合理的景别变化？
   - 画面叙事是否流畅？

#### 4.2 检查方法

调用 `scripts/check_storyboard_quality.py`：

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

根据检查结果：

**修改prompt**：
- 强化角色描述（如"same character as reference, consistent appearance"）
- 调整风格关键词
- 增加镜头语言提示

**修改参考图**：
- 如角色参考图本身不清晰，重新生成更清晰的参考图

**重新生成**：
- 应用修改后的prompt或参考图
- 重复检查流程
- 最多尝试3次

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

在执行过程中需要询问用户的信息：

1. **视觉风格选择**（第三步开始前）
   - 使用 `AskUserQuestion` 列出可选风格
   - 或让用户自定义风格描述

2. **分镜数量确认**（第二步开始前）
   - 默认24个/集
   - 用户可指定20-30范围

3. **质量检查失败时**（第四步）
   - 如3次优化后仍有问题，询问用户是否接受当前结果或手动调整

---

## 执行检查清单

- [ ] 故事文本已读取
- [ ] `elements_config.json` 已生成
- [ ] 所有元素参考图已生成到 `references/` 目录
- [ ] `storyboard.json` 已生成
- [ ] 分镜数量符合要求（20-30个）
- [ ] 每集至少3次反转
- [ ] 所有6宫格分镜图已生成
- [ ] 质量检查已执行
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
