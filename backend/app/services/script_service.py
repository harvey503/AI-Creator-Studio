"""
脚本生成服务
负责调用AI模型生成分镜脚本
"""
import json
from typing import List, Optional
from ..models import (
    StoryboardGenerateRequest, 
    StoryboardResponse, 
    Shot,
    ShotRegenerateRequest,
    FirstShotRequest,
    FirstShotResponse,
    RemainingShotsRequest,
    RemainingShotsResponse
)
from ..config import get_settings
from .strategy_service import strategy_service
from ..utils.ai_client import ai_client


# 分镜脚本生成的系统提示词
STORYBOARD_SYSTEM_PROMPT = """你是一位专业的TikTok短视频导演和脚本策划师。你的任务是将产品信息转化为具体的分镜脚本，用于AI视频生成。

每个分镜需要包含以下内容：
1. **title**: 分镜标题（中文，简短描述这个镜头的核心内容）
2. **visual**: 画面内容描述（中文，详细描述画面中看到的所有元素）
3. **action**: 动作描述（描述模特或物体的运动）
4. **camera**: 运镜描述（如固定镜头、推拉、平移、微距等）
5. **prompt**: AI绘图提示词（**必须是英文**，用于Stable Diffusion/Midjourney，包含画面构图、光线、风格等细节，8k质量）
6. **video_prompt**: 视频生成提示词（**必须是英文**，用于VEO/Sora视频生成，包含详细的画面、动作、运镜描述，将作为Manifest中的shot_summary）
7. **chinese_summary**: 中文大意（这个镜头对应的口播文案或旁白）
8. **narration**: 英文配音台词（English Dubbing Lines）

你需要生成4-6个分镜，构成一个完整的TikTok短视频脚本。遵循以下结构：
- 镜头1：开场钩子，吸引注意力
- 镜头2-3：产品展示和细节特写
- 镜头4-5：使用效果展示
- 镜头6：结尾号召行动

你必须以JSON格式返回结果，格式如下：
{
    "shots": [
        {
            "id": 1,
            "title": "分镜标题",
            "visual": "画面描述",
            "action": "动作描述",
            "camera": "运镜描述",
            "prompt": "English prompt for AI image generation, 8k, photorealistic...",
            "video_prompt": "English video description for VEO manifest...",
            "chinese_summary": "中文大意/口播文案",
            "narration": "English dubbing line..."
        }
    ]
}
"""

# 分镜重生成的系统提示词
REGENERATE_SYSTEM_PROMPT = """你是一位专业的TikTok短视频导演。你的任务是根据用户的修改提示，重新生成一个分镜内容。

分镜需要包含：
- title: 分镜标题（中文）
- visual: 画面内容描述（中文）
- action: 动作描述
- camera: 运镜描述
- prompt: AI绘图提示词（必须是英文，用于Stable Diffusion，8k质量）
- video_prompt: 视频生成提示词（必须是英文）
- chinese_summary: 中文大意
- narration: 英文配音台词

返回单个JSON对象，不要包含id字段，不要返回列表。
"""


class ScriptService:
    """脚本生成服务"""
    
    # 默认预览图列表
    PREVIEW_IMAGES = [
        "https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?auto=format&fit=crop&q=80&w=600",
        "https://images.unsplash.com/photo-1522337660859-02fbefca4702?auto=format&fit=crop&q=80&w=600",
        "https://images.unsplash.com/photo-1596462502278-27bfdd403348?auto=format&fit=crop&q=80&w=600",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=600",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=600",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&q=80&w=600",
    ]
    
    def __init__(self):
        self.settings = get_settings()
    
    async def generate_storyboard(self, request: StoryboardGenerateRequest) -> StoryboardResponse:
        """
        生成完整的分镜脚本
        """
        # 先生成策略报告
        from ..models import StrategyAnalysisRequest
        strategy_request = StrategyAnalysisRequest(
            market=request.market,
            product_name=request.product_name,
            product_desc=request.product_desc,
            creative_idea=request.creative_idea
        )
        strategy_report = await strategy_service.analyze(strategy_request)
        # 打印ai_provider
        print(f"AI Provider: {self.settings.ai_provider}")
        # 生成分镜列表
        if self.settings.ai_provider == "mock":
            shots = await self._mock_generate_shots(request)
        elif self.settings.ai_provider == "openai":
            shots = await self._openai_generate_shots(request)
        elif self.settings.ai_provider == "deepseek":
            shots = await self._deepseek_generate_shots(request)
        else:
            shots = await self._mock_generate_shots(request)
        
        return StoryboardResponse(
            strategy_report=strategy_report,
            shots=shots
        )
    
    async def regenerate_shot(self, request: ShotRegenerateRequest) -> Shot:
        """
        重新生成单个分镜
        """
        if self.settings.ai_provider == "mock":
            return await self._mock_regenerate_shot(request)
        elif self.settings.ai_provider in ["openai", "deepseek", "gemini"]:
            return await self._ai_regenerate_shot(request)
        else:
            return await self._mock_regenerate_shot(request)
    
    async def generate_first_shot(self, request: FirstShotRequest) -> FirstShotResponse:
        """
        快速生成第一个分镜（开场镜头）
        优化响应时间，只生成一个分镜
        """
        print(f"[FirstShot] AI Provider: {self.settings.ai_provider}")
        
        if self.settings.ai_provider == "mock":
            shot = await self._mock_generate_first_shot(request)
        elif self.settings.ai_provider in ["openai", "deepseek"]:
            shot = await self._ai_generate_first_shot(request)
        else:
            shot = await self._mock_generate_first_shot(request)
        
        return FirstShotResponse(shot=shot)
    
    async def generate_remaining_shots(self, request: RemainingShotsRequest) -> RemainingShotsResponse:
        """
        基于第一个分镜生成剩余分镜
        """
        print(f"[RemainingShots] AI Provider: {self.settings.ai_provider}")
        
        if self.settings.ai_provider == "mock":
            shots = await self._mock_generate_remaining_shots(request)
        elif self.settings.ai_provider in ["openai", "deepseek"]:
            shots = await self._ai_generate_remaining_shots(request)
        else:
            shots = await self._mock_generate_remaining_shots(request)
        
        return RemainingShotsResponse(shots=shots)
    
    def _build_storyboard_prompt(self, request: StoryboardGenerateRequest) -> str:
        """构建分镜生成的用户提示词"""
        prompt = f"""请为以下产品生成TikTok短视频分镜脚本：

**目标市场**: {request.market}
**产品名称**: {request.product_name}
"""
        if request.product_desc:
            prompt += f"**产品描述/卖点**: {request.product_desc}\n"
        if request.creative_idea:
            prompt += f"**创意想法**: {request.creative_idea}\n"
        
        prompt += f"""
**视频参数**: 
- 画面比例: {request.aspect_ratio}
- 分辨率: {request.resolution}

请生成4-6个分镜，构成一个完整的TikTok爆款视频脚本。确保prompt字段是英文，适合AI图像生成。
以JSON格式返回。
"""
        return prompt
    
    def _build_regenerate_prompt(self, request: ShotRegenerateRequest) -> str:
        """构建分镜重生成的用户提示词"""
        prompt = f"请根据修改要求，重新为分镜{request.shot_id}生成内容。\n\n"
        
        # 添加产品信息上下文
        if request.product_name:
            prompt += f"**产品名称**: {request.product_name}\n"
        if request.product_desc:
            prompt += f"**产品关键词/卖点**: {request.product_desc}\n"
            
        # 添加第一个分镜上下文（如果当前不是分镜1且有第一个分镜数据）
        if request.shot_id > 1 and request.first_shot:
            prompt += "--- \n"
            prompt += "**参考分镜 1 (开场分镜)**:\n"
            prompt += f"- 画面描述: {request.first_shot.visual}\n"
            prompt += f"- 角色/动作: {request.first_shot.action}\n"
            prompt += f"- AI绘图提示词: {request.first_shot.prompt}\n"
            prompt += f"**核心要求**: 分镜 {request.shot_id} 必须在视觉元素上与分镜 1 保持严格一致。人物的长相、发型、服装，以及产品的包装、颜色、Logo 必须与分镜 1 完全相同。新分镜是视频的后续，故事必须连贯。\n"
            prompt += "--- \n\n"

        if request.current_prompt:
            prompt += f"**当前分镜提示词**: {request.current_prompt}\n"
        if request.modification_hint:
            prompt += f"**修改要求**: {request.modification_hint}\n"
        
        prompt += "\n请以单个JSON对象格式返回新的分镜内容。"
        return prompt
    
    async def _openai_generate_shots(self, request: StoryboardGenerateRequest) -> List[Shot]:
        """使用OpenAI生成分镜"""
        try:
            messages = [
                {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_storyboard_prompt(request)}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.8,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            shots_data = data.get("shots", [])
            
            # 转换为Shot对象并添加预览图
            shots = []
            for i, shot_data in enumerate(shots_data):
                shot = Shot(
                    id=shot_data.get("id", i + 1),
                    title=shot_data.get("title", ""),
                    visual=shot_data.get("visual", ""),
                    action=shot_data.get("action", ""),
                    camera=shot_data.get("camera", ""),
                    prompt=shot_data.get("prompt", ""),
                    chinese_summary=shot_data.get("chinese_summary", ""),
                    narration=shot_data.get("narration", ""),
                    video_prompt=shot_data.get("video_prompt", ""),
                    preview_url=self.PREVIEW_IMAGES[i % len(self.PREVIEW_IMAGES)]
                )
                shots.append(shot)
            
            return shots
        except Exception as e:
            print(f"OpenAI分镜生成失败: {e}")
            return await self._mock_generate_shots(request)
    
    async def _deepseek_generate_shots(self, request: StoryboardGenerateRequest) -> List[Shot]:
        """使用DeepSeek生成分镜"""
        try:
            messages = [
                {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_storyboard_prompt(request)}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider="deepseek",
                temperature=0.8,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            shots_data = data.get("shots", [])
            
            # 转换为Shot对象并添加预览图
            shots = []
            for i, shot_data in enumerate(shots_data):
                shot = Shot(
                    id=shot_data.get("id", i + 1),
                    title=shot_data.get("title", ""),
                    visual=shot_data.get("visual", ""),
                    action=shot_data.get("action", ""),
                    camera=shot_data.get("camera", ""),
                    prompt=shot_data.get("prompt", ""),
                    chinese_summary=shot_data.get("chinese_summary", ""),
                    narration=shot_data.get("narration", ""),
                    video_prompt=shot_data.get("video_prompt", ""),
                    preview_url=self.PREVIEW_IMAGES[i % len(self.PREVIEW_IMAGES)]
                )
                shots.append(shot)
            
            return shots
        except Exception as e:
            print(f"DeepSeek分镜生成失败: {e}")
            return await self._mock_generate_shots(request)
    
    async def _ai_regenerate_shot(self, request: ShotRegenerateRequest) -> Shot:
        """使用AI重新生成分镜 (通用)"""
        try:
            prompt = self._build_regenerate_prompt(request)
            print(f"[Regenerate] Constructed Prompt for Shot {request.shot_id}:\n{prompt}")
            
            messages = [
                {"role": "system", "content": REGENERATE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider=self.settings.ai_provider,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            
            # 兼容处理：如果AI返回了列表，取第一个元素
            if isinstance(data, list):
                if len(data) > 0:
                    data = data[0]
                else:
                    raise ValueError("AI returned an empty list")
            
            return Shot(
                id=request.shot_id,
                title=data.get("title", "重新生成的分镜"),
                visual=data.get("visual", ""),
                action=data.get("action", ""),
                camera=data.get("camera", ""),
                prompt=data.get("prompt", ""),
                chinese_summary=data.get("chinese_summary", ""),
                narration=data.get("narration", ""),
                video_prompt=data.get("video_prompt", ""),
                preview_url=self.PREVIEW_IMAGES[request.shot_id % len(self.PREVIEW_IMAGES)]
            )
        except Exception as e:
            print(f"AI分镜重生成失败 ({self.settings.ai_provider}): {e}")
            return await self._mock_regenerate_shot(request)
    
    async def _deepseek_regenerate_shot(self, request: ShotRegenerateRequest) -> Shot:
        """使用DeepSeek重新生成分镜"""
        try:
            messages = [
                {"role": "system", "content": REGENERATE_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_regenerate_prompt(request)}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider="deepseek",
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            
            return Shot(
                id=request.shot_id,
                title=data.get("title", "重新生成的分镜"),
                visual=data.get("visual", ""),
                action=data.get("action", ""),
                camera=data.get("camera", ""),
                prompt=data.get("prompt", ""),
                chinese_summary=data.get("chinese_summary", ""),
                narration=data.get("narration", ""),
                video_prompt=data.get("video_prompt", ""),
                preview_url=self.PREVIEW_IMAGES[request.shot_id % len(self.PREVIEW_IMAGES)]
            )
        except Exception as e:
            print(f"DeepSeek分镜重生成失败: {e}")
            return await self._mock_regenerate_shot(request)
    
    async def _mock_generate_shots(self, request: StoryboardGenerateRequest) -> List[Shot]:
        """模拟生成分镜列表"""
        product_name = request.product_name
        
        shots_template = [
            {
                "id": 1,
                "title": f"高清特写，展示{product_name}的第一印象",
                "visual": f"中景镜头。一位年轻漂亮的女性，妆容自然精致，手持{product_name}，表情惊喜。背景是现代简约的化妆台。",
                "action": "模特展示产品，眼睛瞪大表示震惊，然后指着产品，语气夸张地介绍。",
                "camera": "固定镜头，焦点在模特面部和手中的产品。",
                "prompt": f"Medium shot of a beautiful young woman with natural makeup, holding {product_name}, looking surprised and excited. Modern minimalist makeup vanity background. High quality, 4k, TikTok influencer style.",
                "video_prompt": f"Medium shot of a beautiful young woman with natural makeup, holding {product_name}, looking surprised and excited.",
                "chinese_summary": f"你看到这个{product_name}了吗？太不可思议了！",
                "narration": f"Have you seen this {product_name}? It's incredible!",
                "preview_url": self.PREVIEW_IMAGES[0]
            },
            {
                "id": 2,
                "title": f"手部特写，展示{product_name}的质感",
                "visual": f"模特快速展示{product_name}，突出其高级质感和设计细节。",
                "action": "Focus on the hand texture and the product details.",
                "camera": "微距镜头，浅景深。",
                "prompt": f"Close up shot of woman's hands holding {product_name}, elegant design, blurred luxury background, cinematic lighting.",
                "video_prompt": f"Close up shot of woman's hands holding {product_name}, elegant design, blurred luxury background.",
                "chinese_summary": "质感完全不输大牌，手感超级棒！",
                "narration": "The texture rivals big brands, and it feels amazing in hand!",
                "preview_url": self.PREVIEW_IMAGES[1]
            },
            {
                "id": 3,
                "title": f"使用过程特写，展示{product_name}的效果",
                "visual": f"展示{product_name}的实际使用过程，突出产品效果。",
                "action": "Slow motion demonstration of product usage.",
                "camera": "Extreme close-up macro shot.",
                "prompt": f"Macro shot of {product_name} being used, showing texture and effect details, soft lighting, 8k resolution.",
                "video_prompt": f"Macro shot of {product_name} being used, showing texture and effect details, soft lighting.",
                "chinese_summary": "效果太惊艳了，一用就爱上！",
                "narration": "The effect is stunning, you'll fall in love with it instantly!",
                "preview_url": self.PREVIEW_IMAGES[2]
            },
            {
                "id": 4,
                "title": "最终效果展示，模特自信微笑",
                "visual": "模特自信地微笑，展示使用产品后的完美效果。",
                "action": "Model smiling and turning head slightly.",
                "camera": "Portrait shot, soft ring light.",
                "prompt": "Portrait of a confident girl showing the perfect result, smiling, studio lighting, glowing skin, beauty commercial style.",
                "video_prompt": "Portrait of a confident girl showing the perfect result, smiling, studio lighting.",
                "chinese_summary": "看看这个效果，太完美了！",
                "narration": "Just look at this result, it's absolutely perfect!",
                "preview_url": self.PREVIEW_IMAGES[3]
            }
        ]
        
        return [Shot(**shot) for shot in shots_template]
    
    async def _mock_regenerate_shot(self, request: ShotRegenerateRequest) -> Shot:
        """模拟重新生成单个分镜"""
        return Shot(
            id=request.shot_id,
            title="重新生成的分镜",
            visual="这是重新生成的画面描述，根据您的修改提示进行了调整。",
            action="Updated action based on modification.",
            camera="Dynamic camera movement.",
            prompt=f"Regenerated prompt based on: {request.modification_hint or 'default style'}",
            video_prompt="Regenerated video prompt.",
            chinese_summary="这是重新生成的中文大意。",
            narration="This is the regenerated narration line.",
            preview_url=self.PREVIEW_IMAGES[request.shot_id % len(self.PREVIEW_IMAGES)]
        )
    
    # ============ 分步生成方法 ============
    
    async def _mock_generate_first_shot(self, request: FirstShotRequest) -> Shot:
        """Mock生成第一个分镜"""
        product_name = request.product_name
        return Shot(
            id=1,
            title=f"开场句子: 惊艳亮相",
            visual=f"中心镜头。一位年轻女性手持{product_name}，表情惊喜。背景简约干净。",
            action="模特展示产品，眼神惊喜，嘴角微微上扬。",
            camera="固定镜头，焦点在模特面部和产品。",
            prompt=f"Medium shot of a beautiful young woman with natural makeup, holding {product_name}, looking surprised and excited, clean background, high quality, 8k, photorealistic, cinematic lighting.",
            video_prompt=f"Medium shot of a beautiful young woman with natural makeup, holding {product_name}, looking surprised and excited.",
            chinese_summary=f"你看到这个{product_name}了吗？太不可思议了！",
            narration=f"Have you seen this {product_name}? It's incredible!",
            preview_url=self.PREVIEW_IMAGES[0]
        )
    
    async def _mock_generate_remaining_shots(self, request: RemainingShotsRequest) -> List[Shot]:
        """Mock生成剩余分镜"""
        product_name = request.product_name
        
        remaining_shots = [
            Shot(
                id=2,
                title="手部特写，展示产品质感",
                visual=f"特写镜头展示手持{product_name}，突出产品细节和质感。",
                action="手轻轻转动产品展示各个角度。",
                camera="微距镜头，浅景深。",
                prompt=f"Close up of elegant hands holding {product_name}, showing product details, cinematic lighting, 8k.",
                video_prompt=f"Close up of elegant hands holding {product_name}, showing product details.",
                chinese_summary="质感完全不输大牌！",
                narration="The quality rivals big brands!",
                preview_url=self.PREVIEW_IMAGES[1]
            )
        ]
        
        return remaining_shots
    
    async def _ai_generate_first_shot(self, request: FirstShotRequest) -> Shot:
        """使用AI生成第一个分镜"""
        first_shot_prompt = f"""你是一位专业的TikTok短视频导演。请只生成第一个开场分镜（钩子镜头）。

产品信息：
- 目标市场: {request.market}
- 产品名称: {request.product_name}
- 产品描述: {request.product_desc or '无'}
- 创意想法: {request.creative_idea or '无'}

要求：
1. 这是开场镜头，需要在3秒内抓住观众注意力
2. 必须有强烈的视觉冲击或情感共鸣

返回JSON格式：
{{
    "title": "分镜标题",
    "visual": "画面描述",
    "action": "动作描述",
    "camera": "运镜描述",
    "prompt": "English AI image prompt, 8k, photorealistic...",
    "video_prompt": "English video description...",
    "chinese_summary": "中文大意/口播文案",
    "narration": "English dubbing line..."
}}"""

        try:
            messages = [
                {"role": "system", "content": "你是专业的TikTok短视频导演，擅长创作吸引人的开场镜头。"},
                {"role": "user", "content": first_shot_prompt}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider=self.settings.ai_provider,
                temperature=0.8,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            
            return Shot(
                id=1,
                title=data.get("title", "开场镜头"),
                visual=data.get("visual", ""),
                action=data.get("action", ""),
                camera=data.get("camera", ""),
                prompt=data.get("prompt", ""),
                chinese_summary=data.get("chinese_summary", ""),
                narration=data.get("narration", ""),
                video_prompt=data.get("video_prompt", ""),
                preview_url=self.PREVIEW_IMAGES[0]
            )
        except Exception as e:
            print(f"AI生成第一个分镜失败: {e}")
            return await self._mock_generate_first_shot(request)
    
    async def _ai_generate_remaining_shots(self, request: RemainingShotsRequest) -> List[Shot]:
        """使用AI基于第一个分镜生成剩余分镜"""
        first_shot = request.first_shot
        
        remaining_count = request.shot_count - 1
        if remaining_count < 1:
            remaining_count = 1

        remaining_prompt = f"""你是一位专业的TikTok短视频导演。基于已有的第一个分镜，生成后续 {remaining_count} 个分镜（ID从2开始），使总分镜数为 {request.shot_count}，完成整个视频脚本。

产品信息：
- 目标市场: {request.market}
- 产品名称: {request.product_name}
- 产品描述: {request.product_desc or '无'}
- 创意想法: {request.creative_idea or '无'}

第一个分镜（已确定）：
- 标题: {first_shot.title}
- 画面: {first_shot.visual}
- 动作: {first_shot.action}
- 运镜: {first_shot.camera}
- 中文大意: {first_shot.chinese_summary}
- AI绘图提示词: {first_shot.prompt}

任务：
1. **视觉一致性（至关重要）**：
   - 仔细观察第一张分镜的图片（如果有）和提示词。
   - 提取产品的核心视觉特征（包装颜色、形状、Logo位置、材质等）。
   - 提取人物特征（发型、妆容、服装）。
   - **在后续每个分镜的 `prompt` 字段中，必须显式包含这些特征描述，确保画面连续。**
   
2. 保持风格一致，创作后续的镜头。
3. 确保故事连贯，有高潮和结尾。

返回JSON格式：
{{
    "shots": [
        {{
            "id": 2,
            "title": "分镜标题",
            "visual": "画面描述",
            "action": "动作描述",
            "camera": "运镜描述",
            "prompt": "English AI image prompt, 8k... [MUST include consistent product/character details]",
            "video_prompt": "English video description...",
            "chinese_summary": "中文大意",
            "narration": "English dubbing line..."
        }},
        ...
    ]
}}"""

        try:
            user_content = remaining_prompt
            
            # 如果有第一张分镜的图片，作为多模态输入
            if request.first_shot_image_url:
                print(f"[RemainingShots] Using first shot image: {request.first_shot_image_url}")
                user_content = [
                    {"type": "text", "text": remaining_prompt},
                    {
                        "type": "image_url", 
                        "image_url": {"url": request.first_shot_image_url}
                    }
                ]
            
            messages = [
                {"role": "system", "content": "你是专业的TikTok短视频导演，擅长创作连贯的分镜脚本。"},
                {"role": "user", "content": user_content}
            ]
            
            response = await ai_client.chat_completion(
                messages=messages,
                provider=self.settings.ai_provider,
                temperature=0.8,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            data = ai_client.parse_json_response(response)
            shots_data = data.get("shots", [])
            
            shots = []
            for i, shot_data in enumerate(shots_data):
                shot = Shot(
                    id=shot_data.get("id", i + 2),
                    title=shot_data.get("title", ""),
                    visual=shot_data.get("visual", ""),
                    action=shot_data.get("action", ""),
                    camera=shot_data.get("camera", ""),
                    prompt=shot_data.get("prompt", ""),
                    chinese_summary=shot_data.get("chinese_summary", ""),
                    narration=shot_data.get("narration", ""),
                    video_prompt=shot_data.get("video_prompt", ""),
                    preview_url=self.PREVIEW_IMAGES[(i + 1) % len(self.PREVIEW_IMAGES)]
                )
                shots.append(shot)
            
            return shots
        except Exception as e:
            print(f"AI生成剩余分镜失败: {e}")
            return await self._mock_generate_remaining_shots(request)


# 单例服务实例
script_service = ScriptService()

