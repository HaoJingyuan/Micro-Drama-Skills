# Generate Storyboard Skill

## 概述

分镜生成技能，用于从故事文本自动生成分镜故事板和可视化图片。

## 功能特性

1. **智能元素提取** - 自动分析故事中的人物、场景、道具及其变体
2. **快节奏拆分** - 按短剧节奏（爽点密集、反转频繁）拆分剧情
3. **6宫格可视化** - 生成9:16竖版6宫格分镜图
4. **自动质量检查** - AI驱动的质量检测，自动优化（最多3次）

## 前置要求

### 1. 配置方式

支持三种配置方式（优先级从高到低）：

#### 方式一：命令行参数（推荐）
直接在命令行传入 username 和 project_title：
```bash
python generate_storyboard_image.py ./my_project "赛博朋克" gemini_3_pro_image manju my_storyboard
```

#### 方式二：项目本地配置文件
在项目目录下创建 `config.json`：
```json
{
  "username": "your_username",
  "project_title": "your_project_name"
}
```

#### 方式三：环境变量
设置环境变量：
```bash
export STORYBOARD_USERNAME="your_username"
export STORYBOARD_PROJECT="your_project_name"
```

**API 端点**：
- 图片生成：`https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com/api/generate-image`
- 图片上传：`https://sd5hqdqdmg7k3v1e7m0ag.apigateway-cn-beijing.volceapi.com/api/tos/upload-image`

### 2. Python 依赖

```bash
pip install requests Pillow
```

### 3. 测试 API

在开始使用前，建议先测试 API 是否正常工作：

```bash
# 使用默认配置测试
python scripts/test_api.py

# 或设置环境变量后测试
export STORYBOARD_USERNAME="your_username"
export STORYBOARD_PROJECT="your_project"
python scripts/test_api.py
```

该脚本会：
- 测试图片生成接口（生成一个简单的红色方块）
- 测试图片上传接口（上传测试图片到 TOS）
- 显示详细的请求和响应信息

如果测试通过，说明 API 正常，可以开始使用。

## 使用方法

### 方式一：通过 Claude Code 调用

直接在对话中使用：
```
"根据这个故事生成分镜"
"create storyboard from story.txt"
"制作分镜故事板"
```

### 方式二：手动执行脚本

#### 步骤1：准备故事文本

将故事文本（剧本或小说）保存为文件，例如 `story.txt`

#### 步骤2：生成元素配置

首先需要手动创建 `elements_config.json`，或让 AI 帮你分析故事文本生成。

#### 步骤3：配置项目

创建项目本地配置文件 `config.json`（可选）：
```bash
cp ../project_config.example.json ./config.json
# 编辑 config.json，填入你的 username 和 project_title
```

或直接使用命令行参数，跳过配置文件。

#### 步骤4：生成参考图

```bash
cd project_output/
python ../scripts/generate_references.py . gemini_3_pro_image
```

第二个参数是模型名称，可选（默认 `gemini_3_pro_image`）。

#### 步骤5：生成故事板配置

手动创建 `storyboard.json`，或让 AI 帮你拆分剧情。

#### 步骤6：生成分镜图

**方式一：使用配置文件**
```bash
python ../scripts/generate_storyboard_image.py . "赛博朋克" gemini_3_pro_image
```

**方式二：使用命令行参数**
```bash
python ../scripts/generate_storyboard_image.py . "赛博朋克" gemini_3_pro_image manju my_storyboard
```

**参数说明**：
- 第1个参数：项目目录（必需）
- 第2个参数：视觉风格（可选，默认 "cinematic"）
- 第3个参数：模型名称（可选，默认 "gemini_3_pro_image"）
- 第4个参数：用户名（可选，从 config.json 或环境变量读取）
- 第5个参数：项目名（可选，从 config.json 或环境变量读取）

#### 步骤6：质量检查

```bash
python ../scripts/check_storyboard_quality.py . "赛博朋克"
```

## 输出文件结构

```
project_output/
├── elements_config.json          # 元素配置
├── storyboard.json                # 故事板配置
├── references/                    # 参考图
│   ├── char_01_v1_ref.png        # 角色参考图（四宫格）
│   ├── scene_01_v1_ref.png       # 场景参考图
│   └── prop_01_v1_ref.png        # 道具参考图
├── storyboards/                   # 分镜图
│   ├── storyboard_ep01_group01.png
│   └── ...
└── quality_reports/               # 质量报告
    ├── ep01_group01_check.json
    └── ...
```

## 配置说明

### elements_config.json

定义人物、场景、道具及其变体：

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
          "ai_prompt": "A young hero wearing casual clothes..."
        }
      ]
    }
  ],
  "scenes": [...],
  "props": [...]
}
```

### storyboard.json

定义分镜故事板：

```json
{
  "episodes": [
    {
      "episode_number": 1,
      "frames": [
        {
          "frame_number": 1,
          "characters": [...],
          "scene_description": "画面描述",
          "camera": {
            "type": "中景",
            "movement": "推"
          }
        }
      ]
    }
  ]
}
```

## 质量检查维度

1. **人物一致性** - 角色外貌是否与参考图一致
2. **布局正确性** - 是否为6宫格9:16布局
3. **风格匹配** - 是否符合指定的视觉风格
4. **镜头语言** - 景别变化、画面流畅度

## 优化策略

如果质量检查未通过，脚本会：
1. 分析问题原因
2. 生成优化建议
3. 修改prompt重新生成
4. 最多尝试3次

## 注意事项

1. **分镜数量**：每集建议20-30个分镜（默认24个）
2. **视觉风格**：开始前需选择或指定风格
3. **参考图质量**：角色参考图需清晰，包含三视图+特写
4. **API限流**：生成图片间隔2-3秒，避免触发限流

## 示例工作流

```bash
# 1. 创建项目目录
mkdir my_storyboard && cd my_storyboard

# 2. 准备故事文本
# 手动创建 story.txt

# 3. 让 AI 分析并生成 elements_config.json
# （通过 Claude Code 对话）

# 4. 生成参考图
python ../scripts/generate_references.py .

# 5. 让 AI 拆分剧情并生成 storyboard.json
# （通过 Claude Code 对话）

# 6. 生成分镜图
python ../scripts/generate_storyboard_image.py . "暗黑悬疑"

# 7. 质量检查
python ../scripts/check_storyboard_quality.py . "暗黑悬疑"

# 8. 查看报告
cat quality_reports/ep01_group01_check.json
```

## 故障排查

### API 调用失败
- 检查网络连接
- 确认 API 端点是否可访问
- 检查用户名和项目名配置是否正确

### 图片生成失败
- 检查 prompt 是否包含违禁内容
- 检查模型名称是否正确（如 `gemini_3_pro_image`）
- 检查参考图是否上传成功

### 图片上传失败
- 检查本地图片文件是否存在
- 检查文件格式是否为 PNG
- 确认 TOS 配置是否正确

### 图片下载失败
- 检查返回的 image_url 是否有效
- 检查网络连接
- 确认有写入权限

### 质量检查不通过
- 检查参考图质量
- 调整视觉风格描述
- 手动优化 prompt

## 相关文档

- `references/narration_style.md` - 旁白风格参考指南
- `SKILL.md` - 完整技能文档

## 更新日志

### v1.0.0 (2026-03-04)
- 初始版本
- 支持人物/场景/道具提取
- 6宫格分镜生成
- 自动质量检查
