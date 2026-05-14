# 产品需求文档 (PRD): AI Creator Studio (爆款视频创作系统)

| **版本** | **日期**   | **修改人**   | **备注**                                  |
| -------- | ---------- | ------------ | ----------------------------------------- |
| v1.0     | 2026-02-04 | AI Assistant | 基于 Vue3 原型代码逆向生成的 MVP 需求文档 |

## 1. 项目背景与目标

**产品定位**：面向跨境电商（特别是 TikTok Shop）和营销人员的 AI 全流程视频创作 SaaS 平台。

**核心价值**：通过“输入产品 -> 策略分析 -> 分镜脚本 -> 批量生成”的 Agentic Workflow（代理工作流），将原本需要专业团队耗时数天的视频制作过程缩短至几分钟。

**目标用户**：电商卖家、内容运营、MCN 机构。

------

## 2. 核心业务流程 (User Flow)

1. **配置阶段**：用户输入产品信息、目标市场，上传素材。
2. **分析阶段 (AI Agent 1)**：系统分析产品卖点，结合平台（TikTok）合规政策和流行趋势，生成营销策略。
3. **脚本阶段 (AI Agent 2)**：将策略转化为分镜脚本，自动生成对应的英文绘画提示词 (Prompt)。
4. **生成阶段 (AI Agent 3)**：
   - Step A: 调用文生图模型 (T2I) 生成分镜关键帧。
   - Step B: 调用图生视频模型 (I2V) 将关键帧转化为 4K 视频素材。
5. **交付阶段**：用户预览、微调 Prompt 重绘，导出最终视频或 JSON Manifest。

------

## 3. 功能模块详解

### 3.1 模块一：产品配置 (Product Settings)

**对应页面**：Step 1

**功能目标**：收集生成视频所需的上下文信息 (Context)。

#### 功能需求：

1. **市场与语言选择**：
   - 支持选择目标市场（如 US/UK），系统需根据市场调整生成的文案风格（如美式英语 vs 英式英语）。
2. **产品元数据录入**：
   - **产品标题**：必填。
   - **产品描述/卖点**：支持粘贴亚马逊/Shopify 的五点描述或用户评论（用于 RAG 检索痛点）。
   - **创意想法 (User Intent)**：用户可输入自然语言指令（如：“逐帧复刻，换个模特”）。
3. **技术参数配置**：
   - 画面比例：默认 9:16（竖屏）。
   - 分辨率：支持 1080P/2K/4K 选项。
4. **素材资产管理 (Assets Upload)**：
   - **指定产品图**：支持上传 1-4 张。系统需调用 Vision Model (如 GPT-4o-vision) 提取产品特征 (Trigger Word/LoRA 训练数据)。
   - **指定模特**：支持上传特定模特参考图（用于保持角色一致性）。
   - **参考视频**：支持上传视频，提取其分镜结构。

### 3.2 模块二：AI 策略分析引擎 (Strategy Intelligence)

**对应页面**：Step 2 左侧边栏

**功能目标**：利用 LLM 模拟“营销专家”和“合规专员”。

#### 功能需求：

1. **合规性检查 (Compliance Check)**：
   - 输入：生成的脚本内容。
   - 逻辑：检索 TikTok 广告政策库。
   - 输出：风险等级 (Safe/Warning)、违规词高亮。
2. **文化背景备注 (Culture Notes)**：
   - 逻辑：分析目标市场流行趋势 (Trend Analysis)。
   - 示例输出：“使用 'Clean Girl Aesthetic' 风格，强调自然感。”
3. **核心策略 (Core Strategy)**：
   - 逻辑：提炼营销打法（如：痛点反差、价格锚点、从众心理）。
4. **黄金钩子 (Hook Generation)**：
   - 输出：视频前 3 秒的抓人话术。

### 3.3 模块三：分镜脚本编辑器 (Storyboard Editor)

**对应页面**：Step 2 主视图

**功能目标**：结构化展示视频内容，支持“所见即所得”的修改。

#### 数据结构 (Shot Object)：

每个分镜 (Shot) 需包含以下字段：

- **Index**: 序号。
- **Title**: 简短标题。
- **Visual (画面)**: 详细的视觉描述（供人看）。
- **Action (动作)**: 模特或物体的运动逻辑。
- **Camera (运镜)**: 镜头语言（如 Zoom in, Pan right, Macro）。
- **Prompt (AI 指令)**: **核心字段**。由 LLM 自动翻译并优化的英文提示词，用于传给 Stable Diffusion/Flux/Midjourney。
- **Chinese Summary**: 中文大意。
- **Manifest (JSON)**: 针对视频生成模型的底层参数配置。

#### 交互需求：

1. **折叠/展开**：支持查看摘要或详细信息。
2. **Prompt 编辑与复制**：用户可手动修改英文 Prompt，支持一键复制。
3. **VEO Manifest 生成**：
   - 根据当前分镜参数，实时生成对应的 JSON 配置代码（如 `veo_production_manifest`）。
4. **预览与重绘**：
   - 显示当前生成的关键帧图片。
   - 提供“重生成 (Regenerate)”按钮，点击后重新调用绘图 API。

------

## 4. 技术架构建议 (Technology Stack)

作为资深开发，建议采用以下架构以支撑高并发和复杂的 AI 流：

### 4.1 前端 (Frontend)

- **框架**: Vue 3 (Composition API) + Vite。
- **UI 库**: Tailwind CSS (样式), Lucide-Vue (图标), Shadcn-Vue (组件)。
- **状态管理**: Pinia (用于管理庞大的 Script List 和 Project Config 状态)。
- **流式响应**: 使用 EventSource 或 WebSocket 处理 AI 的流式文本输出。

### 4.2 后端 (Backend)

- **语言**: Python (FastAPI)。Python 是 AI 原生语言，方便处理 LangChain/LlamaIndex。
- **数据库**: MySQL (存储用户及脚本数据) + Redis (任务队列)。
- **对象存储**: 腾讯 OSS (存储生成的大量图片和视频文件)。

### 4.3 AI 模型编排 (Model Orchestration)

这是系统的核心大脑，建议采用 **CoT (Chain of Thought)** 链式调用：

1. **文本/逻辑层 (LLM)**:
   - 模型：**DeepSeek-V3** (性价比高，逻辑强) 或 **GPT-4o**。
   - 任务：策略分析、脚本拆解、Prompt Rewriting (将中文意图转译为 SD/Flux 专业的英文 Prompt)。
2. **图像生成层 (T2I)**:
   - 模型：**Flux.1 [Dev]** (目前文字理解能力和画质最佳的开源模型) 或 **Midjourney API** (通过代理调用)。
   - 任务：生成分镜的“首帧”。
3. **视频生成层 (I2V)**:
   - 模型：
     - **Google Veo** (文中提到的，若有内测资格)。
     - **Runway Gen-3 Alpha** (商业化成熟)。
     - **Kling (可灵) / Hailuo (海螺)** (国内模型，API 开放且效果好)。
   - 任务：Image-to-Video，输入首帧 + Prompt，生成 5s 视频。

------

## 5. 核心数据结构设计 (JSON Schema)

这是前后端交互的关键协议，参考了你提供的 HTML 代码中的结构：

JSON

```
// 视频项目完整结构
{
  "project_id": "proj_123456",
  "config": {
    "market": "US",
    "product_name": "Glossy Lipstick",
    "aspect_ratio": "9:16"
  },
  "strategy_report": {
    "risk_level": "safe",
    "culture_notes": "Clean Girl Aesthetic...",
    "core_strategy": "Contrast visual texture"
  },
  "storyboard": [
    {
      "shot_id": 1,
      "type": "master_shot",
      "content": {
        "title": "高清特写",
        "visual_desc": "中景镜头，年轻亚裔女性...",
        "action_desc": "模特震惊，抿嘴唇...",
        "camera_movement": "Static, focus on face",
        "chinese_summary": "e.l.f. 你看到这个了吗？"
      },
      "ai_params": {
        // T2I 提示词
        "image_prompt": "Medium shot of a beautiful young Asian woman..., 8k, photorealistic",
        // I2V 提示词
        "video_prompt": "The woman opens her mouth in shock, slight zoom in",
        "negative_prompt": "deformed hands, blur, bad quality"
      },
      "assets": {
        "preview_image_url": "https://oss.../img_01.jpg",
        "video_url": "https://oss.../vid_01.mp4"
      },
      // 对应代码中的 manifest
      "veo_manifest": {
        "version": "4.0",
        "input_assets": { "reference_image": "Start Frame" },
        "dynamic_range": "HDR"
      }
    }
  ]
}
```

## 6. 开发优先级 (Roadmap)

1. **P0 (MVP 核心)**:
   - 完成 Step 1 表单与 Step 2 静态布局。
   - 接入 LLM (如 DeepSeek/GPT) 实现“一键生成文本脚本”功能。
   - 接入 Flux API 实现“脚本转图片”功能。
2. **P1 (增强体验)**:
   - 分镜编辑功能（修改 Prompt 后重绘）。
   - 图片上传与一致性控制 (通过 IP-Adapter 保持模特/产品一致)。
3. **P2 (完整闭环)**:
   - 接入图生视频 API (Runway/Kling)。
   - 视频拼接与配音 (TTS) 合成。

