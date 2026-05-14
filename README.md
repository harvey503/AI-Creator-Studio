# AI Creator Studio

AI Creator Studio 是一个面向跨境电商和内容运营团队的 AI 视频创作工作台。项目围绕“产品信息 -> 营销策略 -> 分镜脚本 -> 关键帧图像 -> 视频片段 -> 视频合并”的流程，帮助用户快速生成适合 TikTok、短视频广告和商品种草场景的创意素材。

## 功能特性

- 产品信息配置：录入商品标题、卖点、目标市场、创意方向，并上传产品图、模特图和参考视频。
- AI 策略分析：基于产品信息生成风险等级、文化背景、核心策略和开场钩子。
- 分镜脚本生成：自动生成多镜头脚本，包含画面、动作、运镜、中文摘要、英文图像 Prompt 和 VEO Manifest。
- 分镜编辑与重生成：支持单个分镜重新生成，方便对重点镜头迭代。
- 图片生成：支持 Flux、Google Nano Banana 等图像生成模型。
- 视频生成：支持 Mock、Runway、Kling、Google VEO 等图生视频提供商。
- 视频合并：通过 ffmpeg 将多个分镜视频片段合成为完整视频。

## 技术栈

- 前端：Vue 3、Vite、Pinia、Vue Router、Tailwind CSS、Lucide Vue
- 后端：Python、FastAPI、Pydantic、HTTPX、OpenAI SDK
- AI 服务：OpenAI、DeepSeek、Replicate/Flux、Runway、Kling、Google AI/VEO
- 本地文件：上传素材和生成结果默认保存到 `backend/uploads/`

## 项目结构

```text
AI-Creator-Studio/
├── backend/
│   ├── app/
│   │   ├── models/       # 请求与响应数据模型
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 策略、脚本、图片、视频服务
│   │   ├── utils/        # AI 客户端等工具
│   │   ├── config.py     # 环境变量配置
│   │   └── main.py       # FastAPI 入口
│   ├── .env.example      # 环境变量示例
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # 后端 API 客户端
│   │   ├── components/   # 页面组件
│   │   ├── stores/       # Pinia 状态管理
│   │   └── views/        # Step1 / Step2 页面
│   └── package.json
├── tests/                # 调试和手动测试脚本
├── PRD.md                # 产品需求文档
└── 原型.html             # 早期原型
```

## 环境要求

- Python 3.10+
- Node.js 18+
- npm
- ffmpeg，用于视频合并。可以安装到系统 PATH，或按当前代码约定放在 `backend/ffmpeg.exe`。

## 后端启动

进入后端目录：

```bash
cd backend
```

创建并激活虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量文件：

```bash
copy .env.example .env
```

按需修改 `.env`。如果只想先跑通流程，可以使用 `mock` 提供商：

```env
AI_PROVIDER=mock
VIDEO_PROVIDER=mock
```

启动 FastAPI：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后可访问：

- API 根路径：http://localhost:8000/
- Swagger 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

## 前端启动

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务器：

```bash
npm run dev
```

默认前端地址为：

```text
http://localhost:5173
```

如需指定后端地址，可以在 `frontend/.env.local` 中配置：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 常用 API

- `GET /api/v1/health`：健康检查
- `POST /api/v1/analyze/strategy`：生成营销策略分析
- `POST /api/v1/generate/storyboard`：一次性生成完整分镜脚本
- `POST /api/v1/generate/storyboard/first`：快速生成第一个分镜
- `POST /api/v1/generate/storyboard/remaining`：基于首个分镜生成剩余分镜
- `POST /api/v1/generate/shot/regenerate`：重生成单个分镜
- `POST /api/v1/upload/product`：上传产品图片
- `POST /api/v1/upload/model`：上传模特图片
- `POST /api/v1/upload/reference`：上传参考视频
- `POST /api/v1/image/generate`：生成单张关键帧图像
- `POST /api/v1/image/generate/shot`：为指定分镜生成关键帧图像
- `GET /api/v1/image/models`：查看可用图像模型
- `POST /api/v1/video/generate`：从图像生成视频
- `POST /api/v1/video/generate/shot`：为指定分镜生成视频片段
- `POST /api/v1/video/status`：查询视频任务状态
- `GET /api/v1/video/providers`：查看可用视频生成提供商
- `POST /api/v1/video/merge`：合并多个视频片段

## 环境变量说明

主要配置项位于 `backend/.env`：

| 变量 | 说明 |
| --- | --- |
| `AI_PROVIDER` | 文本生成提供商，支持 `mock`、`openai`、`deepseek` |
| `AI_MODEL` | 文本模型名称 |
| `OPENAI_API_KEY` | OpenAI API Key |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `IMAGE_MODEL` | 图片生成模型，如 `flux-schnell`、`nano-banana` |
| `REPLICATE_API_KEY` | Replicate API Key |
| `VIDEO_PROVIDER` | 视频生成提供商，支持 `mock`、`runway`、`kling`、`veo` |
| `RUNWAY_API_KEY` | Runway API Key |
| `KLING_API_KEY` | Kling API Key |
| `KLING_ACCESS_KEY` | Kling Access Key |
| `GOOGLE_API_KEY` | Google AI API Key |
| `GOOGLE_PROJECT_ID` | Google Cloud 项目 ID |
| `GOOGLE_LOCATION` | Google Cloud 区域 |
| `VEO_MODEL` | VEO 模型版本 |
| `CORS_ORIGINS` | 允许访问后端的前端地址 |

## 构建

前端生产构建：

```bash
cd frontend
npm run build
```

本地预览构建结果：

```bash
npm run preview
```

## 开发注意事项

- 不要提交 `backend/.env`，真实 API Key 只应保存在本地环境变量文件或部署平台的密钥管理中。
- 不要提交 `backend/uploads/` 下的上传素材、生成图片和生成视频。
- 不要提交 `__pycache__/`、`.pyc`、`node_modules/`、`dist/` 等生成文件。
- 如果使用真实视频合并能力，请确认本机已安装 ffmpeg。
- 当前 `tests/` 目录以调试和手动验证脚本为主，接入 CI 前建议补充自动化测试。

## 许可证

如果该项目需要开源发布，请在仓库中补充或确认 LICENSE 文件，并在此处声明对应许可证。
