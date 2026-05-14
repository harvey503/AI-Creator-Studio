"""
视频生成相关API路由
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.video_service import video_service

router = APIRouter(prefix="/api/v1/video", tags=["Video Generation"])


class VideoGenerateRequest(BaseModel):
    """视频生成请求"""
    image_url: str = Field(..., description="起始帧图像URL")
    prompt: str = Field(..., description="视频生成提示词（描述运动）")
    duration: int = Field(default=5, ge=1, le=10, description="视频时长（秒）")
    provider: Optional[str] = Field(default=None, description="提供商 (runway/kling)")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="1080p", description="分辨率")


class VideoGenerateResponse(BaseModel):
    """视频生成响应"""
    video_url: Optional[str] = Field(None, description="视频URL")
    local_path: Optional[str] = Field(None, description="本地保存路径")
    duration: int = Field(default=5, description="视频时长")
    prompt: str = Field(..., description="使用的提示词")
    provider: str = Field(default="mock", description="使用的提供商")
    status: str = Field(default="completed", description="生成状态")
    task_id: Optional[str] = Field(None, description="任务ID")


class ShotVideoRequest(BaseModel):
    """分镜视频生成请求"""
    shot_id: int = Field(..., description="分镜ID")
    image_url: str = Field(..., description="分镜关键帧图像URL")
    prompt: str = Field(..., description="动作描述提示词")
    duration: int = Field(default=5, ge=1, le=10, description="视频时长")
    provider: Optional[str] = Field(default=None, description="提供商")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="1080p", description="分辨率")
    veo_manifest: Optional[dict] = Field(default=None, description="VEO视频生成Manifest JSON")


class TaskStatusRequest(BaseModel):
    """任务状态查询请求"""
    task_id: str = Field(..., description="任务ID")
    provider: str = Field(default="runway", description="提供商")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: int = Field(default=0, description="进度百分比")
    video_url: Optional[str] = None


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    从图像生成视频
    
    使用Runway或Kling API将静态图像转换为视频
    """
    try:
        result = await video_service.generate_video(
            image_url=request.image_url,
            prompt=request.prompt,
            duration=request.duration,
            provider=request.provider,
            aspect_ratio=request.aspect_ratio
        )
        return VideoGenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")


@router.post("/generate/shot", response_model=VideoGenerateResponse)
async def generate_shot_video(request: ShotVideoRequest):
    """
    为分镜生成视频片段
    
    根据分镜的关键帧图像和动作描述生成视频
    """
    try:
        result = await video_service.generate_video(
            image_url=request.image_url,
            prompt=request.prompt,
            duration=request.duration,
            provider=request.provider,
            aspect_ratio=request.aspect_ratio,
            manifest=request.veo_manifest
        )
        
        return VideoGenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分镜视频生成失败: {str(e)}")


@router.post("/status", response_model=TaskStatusResponse)
async def get_task_status(request: TaskStatusRequest):
    """
    查询视频生成任务状态
    """
    try:
        result = await video_service.get_task_status(
            task_id=request.task_id,
            provider=request.provider
        )
        return TaskStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/providers")
async def list_providers():
    """
    获取可用的视频生成提供商列表
    """
    return {
        "providers": [
            {
                "id": "mock",
                "name": "Mock",
                "description": "模拟生成，返回示例视频",
                "max_duration": 10,
                "requires_key": False
            },
            {
                "id": "runway",
                "name": "Runway Gen-3",
                "description": "Runway Gen-3 Alpha Turbo，高质量图生视频",
                "max_duration": 10,
                "requires_key": True,
                "env_key": "RUNWAY_API_KEY"
            },
            {
                "id": "kling",
                "name": "Kling AI",
                "description": "快手可灵AI，支持5-10秒视频生成",
                "max_duration": 10,
                "requires_key": True,
                "env_key": "KLING_API_KEY"
            },
            {
                "id": "veo",
                "name": "Google VEO",
                "description": "Google VEO 2/3，4K高质量视频生成",
                "max_duration": 8,
                "requires_key": True,
                "env_key": "GOOGLE_API_KEY"
            }
        ]
    }


class MergeVideosRequest(BaseModel):
    """视频合并请求"""
    video_urls: list = Field(..., description="视频URL列表（按顺序）")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="1080p", description="分辨率")
    output_filename: Optional[str] = Field(None, description="输出文件名（可选）")


class MergeVideosResponse(BaseModel):
    """视频合并响应"""
    video_url: str = Field(..., description="合并后视频的URL")
    local_path: str = Field(..., description="本地保存路径")
    duration: int = Field(..., description="总时长（秒）")
    status: str = Field(default="completed", description="状态")
    video_count: int = Field(..., description="合并的视频数量")


@router.post("/merge", response_model=MergeVideosResponse)
async def merge_videos(request: MergeVideosRequest):
    """
    合并多个视频为一个完整视频
    
    将多个分镜视频按顺序合并为一个完整的视频文件
    需要系统安装ffmpeg
    """
    try:
        result = await video_service.merge_videos(
            video_urls=request.video_urls,
            output_filename=request.output_filename
        )
        return MergeVideosResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频合并失败: {str(e)}")


