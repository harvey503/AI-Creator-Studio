"""
AI Creator Studio - 后端API服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .routers import generation_router, upload_router, image_router, video_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    settings = get_settings()
    print("AI Creator Studio API starting...")
    print(f"AI Provider: {settings.ai_provider}")
    print(f"Debug Mode: {settings.debug}")
    yield
    # 关闭时执行
    print("AI Creator Studio API shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title="AI Creator Studio API",
    description="爆款视频创作系统后端API - 提供策略分析和分镜脚本生成服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(generation_router)
app.include_router(upload_router)
app.include_router(image_router)
app.include_router(video_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI Creator Studio API",
        "version": "1.0.0",
        "description": "爆款视频创作系统后端API",
        "docs": "/docs"
    }
