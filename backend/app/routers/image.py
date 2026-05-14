"""
图像生成相关API路由
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.image_service import image_service

router = APIRouter(prefix="/api/v1/image", tags=["Image Generation"])


class ImageGenerateRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像生成提示词")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="1080p", description="分辨率 (如 1080p, 2K, 4K)")
    model: Optional[str] = Field(default=None, description="模型名称，默认使用配置值")
    reference_image_url: Optional[str] = Field(default=None, description="参考图URL")


class ImageGenerateResponse(BaseModel):
    """图像生成响应"""
    url: str = Field(..., description="图像展示URL")
    local_path: Optional[str] = Field(None, description="本地存储路径")
    prompt: str = Field(..., description="使用的提示词")
    model: str = Field(..., description="使用的模型名称")
    status: str = Field(default="completed", description="生成状态")

# ... (BatchGenerateRequest unchanged)

class ShotImageRequest(BaseModel):
    """分镜图像生成请求"""
    shot_id: int = Field(..., description="分镜ID")
    prompt: str = Field(..., description="图像生成提示词")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="1080p", description="分辨率 (如 1080p, 2K, 4K)")
    model: Optional[str] = Field(default=None, description="模型名称，默认使用配置值")
    reference_image_url: Optional[str] = Field(default=None, description="参考图URL")


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    生成单张图像
    
    使用Flux模型根据提示词生成图像
    """
    try:
        result = await image_service.generate_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            model=request.model,
            reference_image_url=request.reference_image_url
        )
        return ImageGenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


# ... (BatchGenerateRequest unchanged)

@router.post("/generate/shot", response_model=ImageGenerateResponse)
async def generate_shot_image(request: ShotImageRequest):
    """
    为分镜生成关键帧图像
    
    根据分镜的prompt生成对应的关键帧图像
    """
    try:
        result = await image_service.generate_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            model=request.model,
            reference_image_url=request.reference_image_url
        )
        
        # 返回结果中包含shot_id
        response = ImageGenerateResponse(**result)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分镜图像生成失败: {str(e)}")


@router.get("/models")
async def list_models():
    """
    获取可用的图像生成模型列表
    """
    return {
        "models": [
            {
                "id": "flux-schnell",
                "name": "Flux Schnell",
                "description": "快速生成模型，速度快但质量稍低",
                "speed": "fast",
                "quality": "good"
            },
            {
                "id": "flux-dev",
                "name": "Flux Dev",
                "description": "开发版模型，平衡速度和质量",
                "speed": "medium",
                "quality": "high"
            },
            {
                "id": "flux-pro",
                "name": "Flux Pro",
                "description": "专业版模型，最高质量",
                "speed": "slow",
                "quality": "best"
            },
            {
                "id": "nano-banana",
                "name": "Nano Banana (Gemini Flash)",
                "description": "Google Gemini 2.0 Flash 图像生成，快速高质量",
                "speed": "fast",
                "quality": "high",
                "env_key": "GOOGLE_API_KEY"
            },
            {
                "id": "nano-banana-pro",
                "name": "Nano Banana Pro",
                "description": "Google Gemini Pro 图像生成，最高质量",
                "speed": "medium",
                "quality": "best",
                "env_key": "GOOGLE_API_KEY"
            }
        ]
    }

