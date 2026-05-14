"""
AI生成相关API路由
"""
from fastapi import APIRouter, HTTPException
from ..models import (
    StrategyAnalysisRequest,
    StrategyReport,
    StoryboardGenerateRequest,
    StoryboardResponse,
    Shot,
    ShotRegenerateRequest,
    FirstShotRequest,
    FirstShotResponse,
    RemainingShotsRequest,
    RemainingShotsResponse
)
from ..services import strategy_service, script_service

router = APIRouter(prefix="/api/v1", tags=["Generation"])


@router.post("/analyze/strategy", response_model=StrategyReport)
async def analyze_strategy(request: StrategyAnalysisRequest):
    """
    策略分析接口
    
    分析产品信息，生成营销策略报告，包括：
    - 风险等级评估
    - 文化背景备注
    - 核心策略建议
    - 视频开头钩子
    """
    try:
        result = await strategy_service.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略分析失败: {str(e)}")


@router.post("/generate/storyboard", response_model=StoryboardResponse)
async def generate_storyboard(request: StoryboardGenerateRequest):
    """
    分镜脚本生成接口（一次性生成全部）
    
    根据产品信息生成完整的分镜脚本，包括：
    - 策略分析报告
    - 多个分镜内容（画面、动作、运镜、Prompt等）
    """
    try:
        result = await script_service.generate_storyboard(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"脚本生成失败: {str(e)}")


@router.post("/generate/storyboard/first", response_model=FirstShotResponse)
async def generate_first_shot(request: FirstShotRequest):
    """
    快速生成第一个分镜（开场镜头）
    
    优化响应时间，只生成一个分镜，用于快速预览
    预计响应时间：5-8秒
    """
    try:
        result = await script_service.generate_first_shot(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"第一个分镜生成失败: {str(e)}")


@router.post("/generate/storyboard/remaining", response_model=RemainingShotsResponse)
async def generate_remaining_shots(request: RemainingShotsRequest):
    """
    基于第一个分镜生成剩余分镜
    
    用户确认第一个分镜后，调用此接口生成后续分镜
    """
    try:
        result = await script_service.generate_remaining_shots(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"剩余分镜生成失败: {str(e)}")


@router.post("/generate/shot/regenerate", response_model=Shot)
async def regenerate_shot(request: ShotRegenerateRequest):
    """
    单个分镜重生成接口
    
    根据修改提示重新生成指定的分镜内容
    """
    try:
        result = await script_service.regenerate_shot(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分镜重生成失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "AI Creator Studio API"}

