from pydantic import BaseModel, Field
from typing import Optional, Literal


class ProjectConfig(BaseModel):
    """项目配置模型"""
    market: str = Field(default="US", description="目标市场")
    product_name: str = Field(..., description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    creative_idea: Optional[str] = Field(default=None, description="创意想法")
    aspect_ratio: str = Field(default="9:16", description="画面比例")
    resolution: str = Field(default="2K", description="分辨率")


class StrategyAnalysisRequest(BaseModel):
    """策略分析请求"""
    market: str = Field(default="US", description="目标市场")
    product_name: str = Field(..., description="产品名称")
    product_desc: Optional[str] = Field(default=None, description="产品描述")
    creative_idea: Optional[str] = Field(default=None, description="创意想法")


class StrategyReport(BaseModel):
    """策略分析报告"""
    risk_level: Literal["safe", "warning"] = Field(default="safe", description="风险等级")
    culture_notes: str = Field(..., description="文化背景备注")
    core_strategy: str = Field(..., description="核心策略")
    hook: str = Field(..., description="强钩子")
