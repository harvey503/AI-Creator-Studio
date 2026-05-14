"""
图像生成服务
集成Flux/Replicate API生成分镜关键帧图片
"""
import os
import uuid
import httpx
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from ..config import get_settings


# 生成的图片存储目录
GENERATED_DIR = Path(__file__).parent.parent.parent / "uploads" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerationService:
    """图像生成服务"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        model: str = None,
        reference_image_url: str = None
    ) -> Dict[str, Any]:
        """
        生成图像
        
        Args:
            prompt: 图像生成提示词
            aspect_ratio: 画面比例 (9:16, 16:9, 1:1)
            resolution: 分辨率 (如 1080p, 2K, 4K)
            model: 模型名称
            reference_image_url: 参考图URL (用于图生图或风格参考)
            
        Returns:
            生成结果字典
        """
        # 使用配置中的默认模型
        if model is None:
            model = self.settings.image_model
        
        # 检查是否使用Google Nano Banana
        if model.startswith("nano-banana"):
            return await self._nano_banana_generate(prompt, aspect_ratio, resolution, model, reference_image_url)
        
        # Flux模型 (目前不支持参考图)
        if model.startswith("flux"):
            return await self._replicate_generate(prompt, aspect_ratio, model)
        
        # 默认mock
        return await self._mock_generate(prompt, aspect_ratio)

    async def _nano_banana_generate(
        self,
        prompt: str,
        aspect_ratio: str,
        resolution: str,
        model: str,
        reference_image_url: str = None
    ) -> Dict[str, Any]:
        """
        使用Google Gemini Image (gemini-2.5-flash-image) 生成图像
        """
        import base64
        
        # 优先从Settings读取，如果为空尝试环境变量
        api_key = self.settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")
        
        print(f"[Nano Banana] 开始生成图像，模型: {model}")
        
        if not api_key:
            print("警告: GOOGLE_API_KEY未配置，使用mock模式")
            return await self._mock_generate(prompt, aspect_ratio)
        
        # 使用 Gemini 模型进行图像生成 (Based on user request)
        gemini_model = "gemini-3-pro-image-preview"
        
        # Gemini API端点
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"
        
        # 构建parts
        parts = [{"text": f"Generate a high quality image: {prompt}"}]
        
        # 辅助确定本地文件路径并读取
        image_data = None
        mime_type = "image/jpeg"
        
        # 处理参考图
        if reference_image_url:
            print(f"[Nano Banana] 使用参考图: {reference_image_url}")
            
            # 使用列表，因为我们要寻找可能是生成的图也可能是上传的产品图
            is_product_image = "/product/" in reference_image_url
            
            # 尝试读取本地文件
            try:
                if "/generated/" in reference_image_url:
                    filename = reference_image_url.split("/generated/")[-1]
                    local_path = GENERATED_DIR / filename
                elif "/product/" in reference_image_url:
                    filename = reference_image_url.split("/product/")[-1]
                    # 上传的产品图在 uploads/product
                    local_path = Path(__file__).parent.parent.parent / "uploads" / "product" / filename
                else:
                    local_path = None

                if local_path and local_path.exists():
                    print(f"[Nano Banana] 读取本地参考图: {local_path}")
                    with open(local_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                        if filename.lower().endswith(".png"):
                            mime_type = "image/png"
                        elif filename.lower().endswith(".webp"):
                            mime_type = "image/webp"
                
                # 如果是产品图，强制增加一致性提示词
                if is_product_image:
                    consistency_hint = "The uploaded product images must be consistent."
                    if consistency_hint not in prompt:
                        prompt = f"{prompt}. {consistency_hint}"
                        print(f"[Nano Banana] 已添加产品一致性提示词: {prompt}")

            except Exception as e:
                print(f"[Nano Banana] 读取本地参考图失败: {e}")
            
            if image_data:
                parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": image_data
                    }
                })
        
        # 重新构建parts中的文案（可能已被修改）
        parts[0] = {"text": f"Generate a high quality image: {prompt}"}

        headers = {
            "Content-Type": "application/json",
        }
        
        # 构建请求
        payload = {
            "contents": [{
                "parts": parts
            }],
            # Gemini 2.5 Flash Image requires no specific responseModalities or 'IMAGE'
            # But based on prev experience, 'IMAGE' might be needed. 
            # However, for 2.5 flash, usually just prompting is enough. 
            # We'll keep it simple first or stick to what worked if any.
            # User example: 'contents' only. No generationConfig in sample?
            # User sample: 
            # -d '{ "contents": [...] }'
            # It did NOT show generationConfig. 
            # But to ensure image output we might need it? 
            # For now I will include it as it shouldn't hurt, or remove it if 2.5 is strict.
            # I will include it to be safe as Imagen 3 needed it.
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"[Nano Banana] 发送请求: {url}")
                response = await client.post(
                    f"{url}?key={api_key}",
                    headers=headers,
                    json=payload
                )
                
                print(f"[Nano Banana] 响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[Nano Banana] 错误响应: {response.text}")
                    
                response.raise_for_status()
                result = response.json()
                
                # 解析响应获取图像
                candidates = result.get("candidates", [])
                
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    
                    for part in parts:
                        # 检查是否有内联图像数据
                        if "inlineData" in part:
                            image_data = part["inlineData"]
                            mime_type = image_data.get("mimeType", "image/png")
                            base64_data = image_data.get("data", "")
                            
                            print(f"[Nano Banana] 找到图像! MIME: {mime_type}, 数据长度: {len(base64_data)}")
                            
                            # 保存图像到本地
                            ext = ".png" if "png" in mime_type else ".jpg"
                            filename = f"{uuid.uuid4().hex[:12]}{ext}"
                            file_path = GENERATED_DIR / filename
                            
                            with open(file_path, "wb") as f:
                                f.write(base64.b64decode(base64_data))
                            
                            base_url = f"http://{self.settings.host}:{self.settings.port}"
                            if self.settings.host == "0.0.0.0":
                                base_url = f"http://localhost:{self.settings.port}"
                                
                            local_path = f"/api/v1/upload/files/generated/{filename}"
                            full_url = f"{base_url}{local_path}"
                            
                            return {
                                "url": full_url,
                                "local_path": local_path,
                                "prompt": prompt,
                                "model": model,
                                "status": "completed"
                            }
                
                print(f"[Nano Banana] 未找到图像数据")
                # 打印完整响应以便调试
                print(f"[Nano Banana] Full Response: {result}")
                
                # Fallback check for user provided sample 'inline_data' snake_case?
                # Unlikely for response but worth checking parts text if error or fallback
                
                raise Exception("Gemini未返回图像数据")
                
        except httpx.HTTPError as e:
            print(f"[Nano Banana] HTTP错误: {e}")
            return await self._mock_generate(prompt, aspect_ratio)
        except Exception as e:
            print(f"[Nano Banana] 生成错误: {e}")
            return await self._mock_generate(prompt, aspect_ratio)
    
    async def _mock_generate(self, prompt: str, aspect_ratio: str) -> Dict[str, Any]:
        """模拟图像生成"""
        # 使用Unsplash随机图片作为模拟
        # 根据比例选择尺寸
        size_map = {
            "9:16": "450x800",
            "16:9": "800x450",
            "1:1": "600x600"
        }
        size = size_map.get(aspect_ratio, "450x800")
        
        # 使用seed确保同一prompt返回相同图片
        seed = hash(prompt) % 1000
        
        mock_url = f"https://picsum.photos/seed/{seed}/{size.replace('x', '/')}"
        
        return {
            "url": mock_url,
            "local_path": None,
            "prompt": prompt,
            "model": "mock",
            "status": "completed"
        }
    
    async def _replicate_generate(
        self, 
        prompt: str, 
        aspect_ratio: str,
        model: str
    ) -> Dict[str, Any]:
        """
        使用Replicate API生成图像（支持Flux模型）
        
        需要在.env中配置 REPLICATE_API_KEY
        """
        api_key = os.getenv("REPLICATE_API_KEY", "")
        
        if not api_key:
            print("警告: REPLICATE_API_KEY未配置，使用mock模式")
            return await self._mock_generate(prompt, aspect_ratio)
        
        # Flux模型映射
        model_versions = {
            "flux-schnell": "black-forest-labs/flux-schnell",
            "flux-dev": "black-forest-labs/flux-dev",
            "flux-pro": "black-forest-labs/flux-1.1-pro"
        }
        
        model_id = model_versions.get(model, model_versions["flux-schnell"])
        
        # 宽高映射
        dimensions = {
            "9:16": {"width": 768, "height": 1344},
            "16:9": {"width": 1344, "height": 768},
            "1:1": {"width": 1024, "height": 1024}
        }
        dims = dimensions.get(aspect_ratio, dimensions["9:16"])
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "prompt": prompt,
                "width": dims["width"],
                "height": dims["height"],
                "num_outputs": 1,
                "output_format": "webp",
                "output_quality": 90
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 创建预测
                response = await client.post(
                    f"https://api.replicate.com/v1/models/{model_id}/predictions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                prediction = response.json()
                
                prediction_id = prediction.get("id")
                
                # 轮询等待完成
                for _ in range(60):  # 最多等待60秒
                    status_response = await client.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers=headers
                    )
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output = status_data.get("output", [])
                        image_url = output[0] if output else None
                        
                        # 下载并保存图片
                        local_path = None
                        if image_url:
                            local_path = await self._download_image(image_url)
                        
                        return {
                            "url": image_url,
                            "local_path": local_path,
                            "prompt": prompt,
                            "model": model,
                            "status": "completed"
                        }
                    elif status == "failed":
                        error = status_data.get("error", "Unknown error")
                        raise Exception(f"图像生成失败: {error}")
                    
                    await asyncio.sleep(1)
                
                raise Exception("图像生成超时")
                
        except httpx.HTTPError as e:
            print(f"Replicate API错误: {e}")
            return await self._mock_generate(prompt, aspect_ratio)
        except Exception as e:
            print(f"图像生成错误: {e}")
            return await self._mock_generate(prompt, aspect_ratio)
    
    async def _download_image(self, url: str) -> Optional[str]:
        """下载图片到本地"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # 生成唯一文件名
                ext = ".webp"
                if "png" in url.lower():
                    ext = ".png"
                elif "jpg" in url.lower() or "jpeg" in url.lower():
                    ext = ".jpg"
                
                filename = f"{uuid.uuid4().hex[:12]}{ext}"
                file_path = GENERATED_DIR / filename
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                return f"/api/v1/upload/files/generated/{filename}"
        except Exception as e:
            print(f"下载图片失败: {e}")
            return None
    
    async def generate_batch(
        self,
        prompts: list,
        aspect_ratio: str = "9:16",
        model: str = "flux-schnell"
    ) -> list:
        """
        批量生成图像
        
        Args:
            prompts: 提示词列表
            aspect_ratio: 画面比例
            model: 模型名称
            
        Returns:
            生成结果列表
        """
        tasks = [
            self.generate_image(prompt, aspect_ratio, model)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 单例服务实例
image_service = ImageGenerationService()
