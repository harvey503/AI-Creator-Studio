from pydantic import BaseModel, Field
from typing import Optional, List
from .project import StrategyReport


class Shot(BaseModel):
    """单个分镜模型"""
    id: int = Field(..., description="分镜ID")
    title: str = Field(..., description="分镜标题")
    visual: str = Field(..., description="画面内容描述")
    action: str = Field(..., description="动作描述")
    camera: str = Field(..., description="运镜描述")
    prompt: str = Field(..., description="AI绘图提示词")
    chinese_summary: str = Field(..., description="中文大意")
    narration: Optional[str] = Field(default=None, description="配音台词(英文)")
    video_prompt: Optional[str] = Field(default=None, description="视频生成提示词(英文)")
    preview_url: Optional[str] = Field(default=None, description="预览图URL")


class StoryboardGenerateRequest(BaseModel):
    """分镜脚本生成请求"""
    market: str = Field(default="US", description="目标市场")
    product_name: str = Field(..., description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    creative_idea: Optional[str] = Field(default=None, description="创意想法")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="2K", description="分辨率")


class StoryboardResponse(BaseModel):
    """分镜脚本生成响应"""
    strategy_report: StrategyReport = Field(..., description="策略分析报告")
    shots: List[Shot] = Field(default_factory=list, description="分镜列表")


class ShotRegenerateRequest(BaseModel):
    """分镜重生成请求"""
    shot_id: int = Field(..., description="分镜ID")
    current_prompt: Optional[str] = Field(default=None, description="当前提示词")
    modification_hint: Optional[str] = Field(default=None, description="修改提示")
    product_name: Optional[str] = Field(default=None, description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    first_shot: Optional[Shot] = Field(default=None, description="第一个分镜内容（供参考）")


class FirstShotRequest(BaseModel):
    """第一个分镜生成请求 - 快速生成开场镜头"""
    market: str = Field(default="US", description="目标市场")
    product_name: str = Field(..., description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    creative_idea: Optional[str] = Field(default=None, description="创意想法")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="2K", description="分辨率")


class FirstShotResponse(BaseModel):
    """第一个分镜生成响应"""
    shot: Shot = Field(..., description="第一个分镜")


class RemainingShotsRequest(BaseModel):
    """剩余分镜生成请求 - 基于第一个分镜生成后续镜头"""
    market: str = Field(default="US", description="目标市场")
    product_name: str = Field(..., description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    creative_idea: Optional[str] = Field(default=None, description="创意想法")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="2K", description="分辨率")
    first_shot: Shot = Field(..., description="第一个分镜内容")
    first_shot_image_url: Optional[str] = Field(default=None, description="第一个分镜的关键帧图片URL（用户多模态生成）")
    shot_count: int = Field(default=5, ge=2, le=6, description="总分镜数量")


class RemainingShotsResponse(BaseModel):
    """剩余分镜生成响应"""
    shots: List[Shot] = Field(default_factory=list, description="剩余分镜列表（不包含第一个）")

