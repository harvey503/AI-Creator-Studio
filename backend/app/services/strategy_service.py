"""
策略分析服务
负责调用AI模型生成营销策略分析报告
"""
import json
from typing import Optional
from ..models import StrategyAnalysisRequest, StrategyReport
from ..config import get_settings
from ..utils.ai_client import ai_client


# 策略分析的系统提示词
STRATEGY_SYSTEM_PROMPT = """你是一位专业的TikTok跨境电商营销专家和内容策略师。你的任务是分析产品信息，生成针对TikTok短视频的营销策略报告。

你需要分析以下几个方面：
1. **合规性检查**：评估内容是否符合TikTok广告政策，检查是否有夸大功效、品牌侵权等风险
2. **文化背景**：根据目标市场（美国/英国等）的文化特点，给出本土化建议
3. **核心策略**：提炼最有效的营销打法（如痛点反差、价格锚点、从众心理等）
4. **视频钩子**：设计视频前3秒的抓人话术，必须简短有力

你必须以JSON格式返回结果，格式如下：
{
    "risk_level": "safe" 或 "warning",
    "culture_notes": "文化背景分析和本土化建议",
    "core_strategy": "核心营销策略描述",
    "hook": "视频开头钩子话术（中文，简短有力）"
}
"""


class StrategyService:
    """策略分析服务"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def analyze(self, request: StrategyAnalysisRequest) -> StrategyReport:
        """
        分析产品并生成策略报告
        """
        if self.settings.ai_provider == "mock":
            return await self._mock_analyze(request)
        elif self.settings.ai_provider == "openai":
            return await self._openai_analyze(request)
        elif self.settings.ai_provider == "deepseek":
            return await self._deepseek_analyze(request)
        else:
            return await self._mock_analyze(request)
    
    def _build_user_prompt(self, request: StrategyAnalysisRequest) -> str:
        """构建用户提示词"""
        prompt = f"""请分析以下产品并生成TikTok营销策略报告：

**目标市场**: {request.market}
**产品名称**: {request.product_name}
"""
        if request.product_desc:
            prompt += f"**产品描述/卖点**: {request.product_desc}\n"
        if request.creative_idea:
            prompt += f"**创意想法**: {request.creative_idea}\n"
        
        prompt += "\n请以JSON格式返回策略分析报告。"
        return prompt
    
    async def _openai_analyze(self, request: StrategyAnalysisRequest) -> StrategyReport:
        """使用OpenAI进行策略分析"""
        try:
            messages = [
                {"role": "system", "content": STRATEGY_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(request)}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            
            return StrategyReport(
                risk_level=data.get("risk_level", "safe"),
                culture_notes=data.get("culture_notes", ""),
                core_strategy=data.get("core_strategy", ""),
                hook=data.get("hook", "")
            )
        except Exception as e:
            print(f"OpenAI策略分析失败: {e}")
            # 失败时回退到mock
            return await self._mock_analyze(request)
    
    async def _deepseek_analyze(self, request: StrategyAnalysisRequest) -> StrategyReport:
        """使用DeepSeek进行策略分析"""
        try:
            messages = [
                {"role": "system", "content": STRATEGY_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(request)}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider="deepseek",
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            
            return StrategyReport(
                risk_level=data.get("risk_level", "safe"),
                culture_notes=data.get("culture_notes", ""),
                core_strategy=data.get("core_strategy", ""),
                hook=data.get("hook", "")
            )
        except Exception as e:
            print(f"DeepSeek策略分析失败: {e}")
            # 失败时回退到mock
            return await self._mock_analyze(request)
    
    async def _mock_analyze(self, request: StrategyAnalysisRequest) -> StrategyReport:
        """模拟策略分析"""
        # 根据市场生成不同的文化备注
        culture_notes = self._get_culture_notes(request.market)
        
        # 根据产品名称生成核心策略
        core_strategy = self._get_core_strategy(request.product_name, request.product_desc)
        
        # 生成钩子
        hook = self._get_hook(request.product_name, request.creative_idea)
        
        return StrategyReport(
            risk_level="safe",
            culture_notes=culture_notes,
            core_strategy=core_strategy,
            hook=hook
        )
    
    def _get_culture_notes(self, market: str) -> str:
        """根据市场生成文化备注"""
        notes = {
            "US": '使用了美国 "Clean Girl Aesthetic" (干净女孩美学) 风格，强调自然妆容和保湿效果。口语表达地道，使用 "Game changer", "Obsessed" 等词汇。',
            "UK": '采用英式低调奢华风格，强调产品的精致工艺和持久效果。使用 "Absolutely brilliant", "Lovely" 等英式表达。',
        }
        return notes.get(market, notes["US"])
    
    def _get_core_strategy(self, product_name: str, product_desc: Optional[str]) -> str:
        """生成核心策略"""
        base_strategy = f'利用"讲解+展示"形式，突出{product_name}的独特卖点。'
        
        if product_desc:
            base_strategy += f' 通过对比展示产品的核心优势，结合用户痛点引发共鸣。'
        else:
            base_strategy += ' 通过视觉冲击力和真实使用效果打动观众。'
        
        return base_strategy
    
    def _get_hook(self, product_name: str, creative_idea: Optional[str]) -> str:
        """生成强钩子"""
        hooks = [
            f"你绝对想不到这个{product_name}有多神奇！",
            f"所有人都在找的{product_name}，终于被我找到了！",
            f"这不是普通的{product_name}，看完你会被种草！",
        ]
        return hooks[0]


# 单例服务实例
strategy_service = StrategyService()
