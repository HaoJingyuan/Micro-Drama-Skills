# 分镜生成技能改进经验总结

## 项目信息
- 项目名称：小满的蛋糕店（xiaoqie）
- 生成日期：2026-03-05
- 故事时长：1分30秒
- 分镜数量：24个

---

## 遇到的问题

### 1. 角色参考图生成失败（422错误）✅ 已解决

**问题描述：**
- 所有角色（char_01, char_02, char_03）的参考图生成都失败
- API 返回 422 Unprocessable Entity 错误
- 场景和道具的参考图生成成功

**失败的角色：**
- char_01_v1, char_01_v2, char_01_v3（林小满）
- char_02_v1, char_02_v2（张婶）
- char_03_v1, char_03_v2（神秘老人）

**成功的元素：**
- 所有场景参考图（scene_01_v1, scene_01_v2, scene_01_v3, scene_02_v1）
- 所有道具参考图（prop_01_v1, prop_01_v2, prop_02_v1, prop_03_v1）

**尝试的解决方案：**
1. 简化 prompt 长度 - 无效
2. 移除复杂描述词 - 无效
3. **修改 prompt 构建策略和比例 - 成功！✅**

**根本原因：**
- API 不支持 2x2 grid layout 的复杂布局要求
- 1:1 比例对角色生成不友好
- "Create a character reference sheet in 2x2 grid layout" 这类指令导致 422 错误

**成功的解决方案：**
修改 `generate_references.py` 中的 `_build_character_prompt` 函数：

```python
def _build_character_prompt(vi):
    # Simplified approach: single front view instead of grid layout
    prompt = f"""
    {vi['ai_prompt']}

    Full body character portrait, front view, standing pose.
    Clean white background, high quality, detailed.
    Character design, anime style.
    """
    return prompt, "9:16"  # Changed from 1:1 to 9:16
```

**关键改变：**
1. 移除 2x2 grid layout 要求
2. 改用单一正面视角
3. 比例从 1:1 改为 9:16（竖版）
4. 简化 prompt 结构

**最终结果：**
- ✅ 所有角色参考图生成成功（7/7）
- ✅ 成功率：100%（第二次尝试后）
- ✅ 平均生成时间：26.6秒/图
- ⚠️ 只有1个超时（char_03_v2），重试后成功

---

### 2. Prompt 构建策略需要优化

**当前问题：**
- 角色 prompt 要求生成 2x2 grid layout（四宫格）
- 这种复杂布局可能超出 API 能力范围

**改进建议：**
```python
def _build_character_prompt(vi):
    # 方案1：单一视角
    prompt = f\"\"\"{vi['ai_prompt']}

    Full body character portrait, standing pose.
    Clean white background, high quality, detailed.
    Anime style, character design.
    \"\"\"
    return prompt, \"9:16\"  # 改用竖版比例

    # 方案2：分步生成
    # 第一步：生成主视图
    # 第二步：使用主视图作为参考，生成侧视图
    # 第三步：使用主视图作为参考，生成背视图
```

---

### 3. 元素配置 JSON 的 prompt 设计

**经验教训：**
- 简洁的 prompt 更可靠
- 避免过多的描述性词汇
- 关键信息优先：外貌 > 服装 > 表情 > 动作

**优化前的 prompt（失败）：**
```
"An 8-year-old Chinese girl named Lin Xiaoman, twin ponytails tied with pink hair bands, wearing a light blue apron with flour stains, white short-sleeved t-shirt, dark pants, flour on hands, focused and determined eyes, petite figure, fair skin, slightly chubby cheeks, cute appearance, standing pose, character design sheet with front view, side view, back view and close-up face, 2x2 grid layout, 1:1 ratio, clean white background, anime style, high quality"
```

**优化后的 prompt（仍失败，但更简洁）：**
```
"8-year-old Chinese girl, twin ponytails with pink hair bands, light blue apron with flour stains, white t-shirt, dark pants, cute face, petite, anime style"
```

**建议的最佳实践：**
- 控制在 20-30 个单词以内
- 使用逗号分隔关键特征
- 避免复杂的句子结构
- 不在 ai_prompt 中指定布局要求（由脚本处理）

---

## 成功的部分

### 1. 场景参考图生成

**成功率：** 100%（4/4）

**有效的 prompt 特点：**
- 直接描述场景内容
- 明确的视角和光线
- 简洁的环境描述

**示例：**
```
"Interior of a small cake shop in old neighborhood, glass display counter with cakes, warm yellow lighting, slightly worn walls, wooden tables and chairs, oven in corner, natural light from window, cozy but simple atmosphere, 16:9 ratio, anime style background, high quality"
```

### 2. 道具参考图生成

**成功率：** 100%（4/4）

**有效的 prompt 特点：**
- 物品的核心特征
- 颜色和质感
- 视觉效果描述

**示例：**
```
"Handmade lemon small cake, golden yellow surface, round shape, soft and fluffy appearance, lemon aroma visual effect with sparkles, three views (front, side, top), 16:9 ratio, anime style, high quality, detailed texture"
```

### 3. 分镜故事板配置生成

**成功完成：**
- 24个分镜，覆盖90秒时长
- 每个分镜平均3.75秒
- 包含完整的镜头语言（景别、运动、角度）
- 旁白和对话分配合理
- 至少3次反转（张婶闹事 → 老人出现 → 真相揭露 → 获得宝典）

**分镜节奏：**
- 开篇（0-18秒）：介绍主角和环境
- 发展（18-42秒）：危机出现，主角应对
- 反转（42-73秒）：老人出现，真相揭露
- 结尾（73-90秒）：获得宝典，立下决心

---

## 改进建议

### 短期改进（立即可行）

1. **修改角色参考图生成策略** ✅ 已完成
   - 改用单一视角生成
   - 使用 9:16 比例而不是 1:1
   - 移除 grid layout 要求

2. **添加参考图质量校验（新增）**
   - 风格一致性检查：所有参考图的画风、色调必须统一
   - 时代一致性检查：人物服装、道具、场景必须符合故事时代背景
   - 剧情符合性检查：人物打扮必须符合剧情设定
   - 文字清洁度检查：不能有漫画文字气泡或对话框

3. **添加图片修改功能（新增）**
   - 使用生图API的参考图功能进行图片修改
   - 适用场景：去除文字、调整时代风格、统一画风
   - 修改失败则降级为重新生成
   - 最多修改2-3次

4. **添加重试机制** ✅ 已有
   - 对失败的生成自动尝试不同的 prompt 变体
   - 记录哪种 prompt 格式成功率更高

5. **提供手动上传选项**
   - 如果 API 生成失败，允许用户手动上传角色参考图
   - 脚本自动检测并使用手动上传的图片

### 中期改进（需要开发）

1. **智能 Prompt 优化器**
   - 根据历史成功率自动调整 prompt
   - 对不同类型的元素使用不同的 prompt 模板

2. **参考图自动校验工具（新增）**
   - 自动检测风格一致性
   - 自动检测时代穿帮
   - 自动检测文字气泡
   - 生成校验报告

3. **图片自动修改工具（新增）**
   - 自动去除文字气泡
   - 自动调整画风统一
   - 自动修正时代错误
   - 支持批量处理

4. **分步生成角色参考**
   - 第一步：生成正面全身图
   - 第二步：使用正面图作为参考，生成侧面图
   - 第三步：使用正面图作为参考，生成背面图
   - 第四步：使用正面图作为参考，生成脸部特写
   - 最后：合成为四宫格（可选）

5. **质量预检查**
   - 在大批量生成前，先测试一个角色
   - 如果失败，自动切换到备用策略

6. **时代背景数据库（新增）**
   - 建立不同时代的服装、道具、场景特征库
   - 自动匹配故事时代背景
   - 生成时自动添加时代特征描述

### 长期改进（架构优化）

1. **多 API 支持**
   - 支持多个图片生成 API
   - 如果一个 API 失败，自动切换到备用 API

2. **本地缓存和复用**
   - 缓存成功的 prompt 模板
   - 对相似角色复用成功的生成策略

3. **交互式调整**
   - 生成失败时，提示用户调整描述
   - 提供可视化的 prompt 编辑器

---

## 下一步行动

### 当前项目（xiaoqie）

由于角色参考图生成失败，有以下选项：

**选项1：手动创建角色参考图**
- 使用其他工具（如 Midjourney, Stable Diffusion）生成
- 按照命名规范保存到 references/ 目录
- 继续执行分镜图生成

**选项2：修改脚本后重试**
- 修改 `_build_character_prompt` 函数
- 使用单一视角生成
- 重新运行生成脚本

**选项3：跳过角色参考图**
- 直接生成分镜图，不使用角色参考
- 可能导致角色一致性问题
- 适合快速原型验证

### 推荐方案

**立即执行：**
1. 修改 `generate_references.py` 中的角色 prompt 构建逻辑
2. 改用 9:16 比例，单一正面视角
3. 重新生成角色参考图

**如果仍失败：**
1. 使用其他工具手动生成角色参考图
2. 保存到 references/ 目录
3. 继续执行后续步骤

---

## 技术细节记录

### API 配置
- 端点：`https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com/api/generate-image`
- 模型：`gemini_3_pro_image`
- 并发数：4 workers
- 超时：120秒

### 生成统计
**第一次尝试（使用 2x2 grid layout）：**
- Phase 1 成功：5/8（场景和道具）
- Phase 1 失败：3/8（所有角色首变体）
- Phase 2 成功：3/7（场景变体和道具变体）
- Phase 2 失败：4/7（所有角色变体）
- 总成功率：53%（8/15）
- 平均生成时间：27.9秒/图

**第二次尝试（修改后，使用 9:16 单一视角）：**
- Phase 1 成功：3/3（所有角色首变体）✅
- Phase 2 成功：3/4（角色变体）
- Phase 2 失败：1/4（超时，非422错误）
- 总成功率：86%（6/7）
- 平均生成时间：26.6秒/图

**第三次尝试（重试失败项）：**
- 成功：1/1（char_03_v2）✅
- 总成功率：100%

**最终统计：**
- ✅ 所有参考图生成成功：15/15
- ✅ 角色参考图：7/7
- ✅ 场景参考图：4/4
- ✅ 道具参考图：4/4

### 文件输出
```
projects/xiaoqie/
├── story.txt                      # 原始故事文本
├── elements_config.json           # 元素配置（已生成）
├── storyboard.json                # 分镜故事板（已生成）
├── improvement_notes.md           # 改进经验总结（本文件）
├── references/                    # 参考图目录（15个）
│   ├── scene_01_v1_ref.png       ✅ 成功
│   ├── scene_01_v2_ref.png       ✅ 成功
│   ├── scene_01_v3_ref.png       ✅ 成功
│   ├── scene_02_v1_ref.png       ✅ 成功
│   ├── prop_01_v1_ref.png        ✅ 成功
│   ├── prop_01_v2_ref.png        ✅ 成功
│   ├── prop_02_v1_ref.png        ✅ 成功
│   ├── prop_03_v1_ref.png        ✅ 成功
│   ├── char_01_v1_ref.png        ✅ 成功（修改后）
│   ├── char_01_v2_ref.png        ✅ 成功（修改后）
│   ├── char_01_v3_ref.png        ✅ 成功（修改后）
│   ├── char_02_v1_ref.png        ✅ 成功（修改后）
│   ├── char_02_v2_ref.png        ✅ 成功（修改后）
│   ├── char_03_v1_ref.png        ✅ 成功（修改后）
│   └── char_03_v2_ref.png        ✅ 成功（修改后）
├── storyboards/                   # 分镜图（4个6宫格）
│   ├── storyboard_ep01_group01.png  ✅ 第1-6格
│   ├── storyboard_ep01_group02.png  ✅ 第7-12格
│   ├── storyboard_ep01_group03.png  ✅ 第13-18格
│   └── storyboard_ep01_group04.png  ✅ 第19-24格
└── quality_reports/               # 质量报告（可选）
```

---

## 总结

本次分镜生成过程中，最初遇到了角色参考图生成失败的问题，但通过修改 prompt 构建策略成功解决。

**关键经验：**
1. ✅ **Grid layout 是失败的根本原因** - API 不支持复杂的多视图布局要求
2. ✅ **9:16 比例更适合角色生成** - 竖版比例比 1:1 方形更适合全身角色展示
3. ✅ **简化 prompt 结构很重要** - 单一明确的指令比复杂的布局描述更可靠
4. ✅ **重试机制有效** - 偶尔的超时错误可以通过重试解决
5. ✅ **分阶段生成策略成功** - Phase 1 生成首变体，Phase 2 使用参考图生成其他变体

**成功的关键改变：**
- 从 "2x2 grid layout with 4 views" 改为 "single front view"
- 从 1:1 比例改为 9:16 比例
- 移除复杂的布局指令，只保留核心描述

**最终成果：**
- ✅ 所有15个参考图生成成功
- ✅ 24个分镜故事板配置完成
- ✅ 4个6宫格分镜图生成成功（共24格）
- ✅ 完整的改进经验文档
- ✅ 分镜生成流程全部完成

**分镜图生成统计：**
- 上传参考图：14/14 ✅
- 生成分镜组：4/4 ✅
- 总耗时：183.6秒（约3分钟）
- 平均每组：45.9秒
- 并发数：4 workers

**下一步：**
分镜生成已完成。可以进行质量检查，或直接使用这些分镜图进行视频制作。

**质量检查发现的问题：**
- ✅ 已创建图片修改脚本 `modify_image.py`
- ⚠️ 分镜图中有文字气泡和对话框（需要去除）
- ⚠️ API 修改功能存在超时问题（120秒超时）
- 📝 已测试两个模型：`gemini_3_pro_image` 和 `gemini-3-pro-openrouter`，均超时

**图片修改脚本使用方法：**
```bash
# 基本用法
python .claude/skills/generate-storyboard/scripts/modify_image.py <input> <output> <prompt>

# 指定模型
python .claude/skills/generate-storyboard/scripts/modify_image.py <input> <output> <prompt> <model>

# 示例：去除文字气泡
python .claude/skills/generate-storyboard/scripts/modify_image.py \
  "projects/xiaoqie/storyboards/storyboard_ep01_group04.png" \
  "projects/xiaoqie/storyboards/storyboard_ep01_group04_fixed.png" \
  "Remove all text bubbles and dialogue boxes. Keep everything else unchanged." \
  gemini-3-pro-openrouter
```

**备选方案：**
1. 增加超时时间（如180秒或更长）
2. 使用其他图片编辑工具手动去除文字
3. 在生成分镜图时就明确要求无文字（在 prompt 中强调）

---

## 用户观察和经验（重要！）

以下是在实际使用中发现的关键问题和经验，已融入到 SKILL.md 中：

### 1. 风格一致性是基础要求

**问题：**
不同参考图的画风、色调、线条风格不统一，导致最终分镜图看起来像是来自不同作品。

**解决方案：**
- 在 `elements_config.json` 中，所有元素的 `ai_prompt` 都应包含相同的风格关键词
- 例如："warm and healing anime style, soft colors, cozy atmosphere"
- 生成后批量预览所有参考图，确认风格统一
- 使用 Phase 2 的参考图机制，确保同一元素的变体风格一致

### 2. 时代一致性避免穿帮

**问题：**
人物服装、道具、场景可能出现时代错乱，如：
- 古代故事中出现现代服装
- 现代故事中出现古代建筑
- 不同时代的元素混杂

**解决方案：**
- 在故事分析阶段明确时代背景
- 在所有 `ai_prompt` 中添加时代描述
  - 例如："1990s Chinese style"
  - 例如："Tang Dynasty traditional clothing"
  - 例如："modern urban setting"
- 生成后检查所有元素是否符合时代设定
- 特别注意：
  - 人物服装、发型、配饰
  - 场景建筑、装饰、家具
  - 道具的设计、材质、样式

### 3. 剧情符合性确保合理性

**问题：**
即使文字描述正确，生成的图片可能不符合剧情逻辑：
- 人物打扮与剧情设定不符
- 场景细节与故事描述不一致
- 道具状态变化没有依据

**解决方案：**
- 人物变体必须有剧情依据
  - 例如：char_01_v1（日常装）→ char_01_v2（正式装）→ char_01_v3（战斗装）
  - 每个变体的 `description` 中说明为什么需要这个变体
- 场景变体必须符合故事需要
  - 例如：scene_01_v1（白天）→ scene_01_v2（夜晚）
- 道具变体必须有状态变化依据
  - 例如：prop_01_v1（完整）→ prop_01_v2（损坏）

### 4. 参考图必须校验

**问题：**
生成的参考图可能不符合要求，但如果不检查就直接使用，会导致后续所有分镜图都有问题。

**解决方案：**
- 生成所有参考图后，**必须进行人工或自动校验**
- 检查项：
  - ✅ 风格一致性
  - ✅ 时代一致性
  - ✅ 剧情符合性
  - ✅ 无文字气泡
- 不合格的参考图必须修改或重新生成
- 全部通过后才能进入下一步

### 5. 文字气泡必须去除

**问题：**
生成的图片中可能出现漫画风格的文字气泡、对话框或文字标注，这些在分镜图中是不需要的。

**解决方案：**
- 在生成时明确要求无文字
  - 在 prompt 中添加："no text, no speech bubbles, no dialogue boxes, no text overlays"
- 如果生成的图有文字，使用图片修改功能去除
  - 修改 prompt："Remove all text bubbles, speech balloons, and text overlays. Keep the character, background, and composition unchanged."
- 参考图如有文字，必须先修改后再使用

### 6. 图片修改功能的使用

**核心原则：是否符合剧情要求**

图片修改的判断标准只有一个：**生成的图片是否符合剧情要求**。

任何不符合剧情的图片都应该修改，不限于以下列举的情况。

**新增功能：**
使用生图API的参考图功能进行图片修改，而不是重新生成。

**适用于任何不符合剧情要求的情况：**
- 角色外貌、服装、表情不符合剧情
- 场景细节、氛围、时代不符合故事
- 道具状态、样式不符合剧情逻辑
- 画面中有不应该出现的元素
- 画面缺少应该出现的元素
- 风格与其他图片不一致
- 有文字气泡或对话框

**常见修改场景示例（不限于此）：**

1. **去除不符合要求的元素**
   ```python
   payload = {
       "prompt": "Remove all text bubbles and dialogue boxes. Keep everything else unchanged.",
       "reference_images": ["原图URL"]
   }
   ```

2. **调整不符合剧情的细节**
   ```python
   payload = {
       "prompt": "Change the character's clothing to 1990s Chinese style. Keep the character's face and pose unchanged.",
       "reference_images": ["原图URL"]
   }
   ```

3. **修改角色状态以符合剧情**
   ```python
   payload = {
       "prompt": "Change the character's expression to worried and nervous. Keep the character's appearance and clothing unchanged.",
       "reference_images": ["原图URL"]
   }
   ```

4. **修改场景氛围以符合剧情**
   ```python
   payload = {
       "prompt": "Change the lighting to warm and cozy. Keep the layout unchanged.",
       "reference_images": ["原图URL"]
   }
   ```

5. **统一画风**
   ```python
   payload = {
       "prompt": "Redraw in warm and healing anime style with soft colors. Keep the composition and character unchanged.",
       "reference_images": ["风格参考图URL", "要修改的图片URL"]
   }
   ```

**判断是否需要修改的标准：**
1. 这个图片是否准确表达了剧情要求？
2. 角色的外貌、服装、表情是否符合剧情设定？
3. 场景的细节、氛围、时代是否符合故事背景？
4. 道具的状态、样式是否符合剧情逻辑？
5. 整体风格是否与其他图片一致？

**如果任何一项答案是"否"，就应该修改。**

**注意事项：**
- 明确指出"保持不变"的部分
- 可以结合多张参考图（风格参考+内容参考）
- 如果修改2-3次后仍不理想，放弃修改，改用重新生成

### 7. 降级策略

**原则：**
如果图片修改多次仍不成功，不要继续尝试，应该降级为重新生成。

**降级流程：**
1. 尝试图片修改（最多2-3次）
2. 如果仍不满意，放弃参考图
3. 优化 prompt，使其更详细、更明确
4. 直接用文生图方式重新生成
5. 在 prompt 中明确所有要求（风格、时代、无文字等）

**何时降级：**
- 修改2-3次后仍有明显问题
- 修改后的图片质量下降
- 修改方向不明确，不知道如何改进

---
