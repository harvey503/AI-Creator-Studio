"""
AI模型客户端
统一管理OpenAI、DeepSeek和Gemini API调用
"""
import json
import httpx
import base64
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from ..config import get_settings


class AIClient:
    """AI模型客户端"""
    
    def __init__(self):
        self.settings = get_settings()
        # 定义上传目录路径
        self.upload_dir = Path(__file__).parent.parent.parent / "uploads"
    
    async def chat_completion(
        self, 
        messages: list, 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        调用AI聊天补全接口
        
        Args:
            messages: 消息列表
            provider: AI提供商 (openai/deepseek/gemini)，默认使用配置
            model: 模型名称，默认使用配置
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            
        Returns:
            AI生成的文本内容
        """
        provider = provider or self.settings.ai_provider
        
        if provider == "openai":
            return await self._openai_chat(messages, model, temperature, max_tokens, response_format)
        elif provider == "deepseek":
            return await self._deepseek_chat(messages, model, temperature, max_tokens, response_format)
        elif provider == "gemini":
            return await self._gemini_chat(messages, model, temperature, max_tokens, response_format)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    async def _openai_chat(
        self,
        messages: list,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]]
    ) -> str:
        """调用OpenAI API"""
        model = model or self.settings.ai_model or "gpt-4o"
        
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _deepseek_chat(
        self,
        messages: list,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]]
    ) -> str:
        """调用DeepSeek API（兼容OpenAI格式）"""
        model = model or "deepseek-chat"
        
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _gemini_chat(
        self,
        messages: list,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]]
    ) -> str:
        """调用Google Gemini API (支持多模态)"""
        model = model or self.settings.ai_model or "gemini-1.5-flash"
        api_key = self.settings.google_api_key
        
        if not api_key:
             raise ValueError("Google API Key is missing")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # 转换 OpenAI messages 为 Gemini contents
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            parts = []
            if isinstance(content, str):
                parts.append({"text": content})
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        parts.append({"text": item["text"]})
                    elif item.get("type") == "image_url":
                        image_url = item["image_url"]["url"]
                        mime_type = "image/jpeg" # Default fallback
                        image_data = None
                        
                        # 检查是否为本地生成的图片
                        if "/generated/" in image_url:
                            try:
                                # 从URL中提取文件名
                                filename = image_url.split("/generated/")[-1]
                                local_path = self.upload_dir / "generated" / filename
                                
                                if local_path.exists():
                                    print(f"Reading local image: {local_path}")
                                    with open(local_path, "rb") as f:
                                        file_content = f.read()
                                        image_data = base64.b64encode(file_content).decode("utf-8")
                                        # 确定 Mime 类型
                                        if filename.lower().endswith(".png"):
                                            mime_type = "image/png"
                                        elif filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
                                            mime_type = "image/jpeg"
                                        elif filename.lower().endswith(".webp"):
                                            mime_type = "image/webp"
                            except Exception as e:
                                print(f"Failed to read local image {image_url}: {e}")

                        if not image_data:
                            if image_url.startswith("data:"):
                                # 处理 base64 data URI
                                try:
                                    header, encoded = image_url.split(",", 1)
                                    mime_type = header.split(";")[0].split(":")[1]
                                    image_data = encoded
                                except: pass
                            else:
                                # 处理 HTTP URL - 下载它
                                try:
                                    async with httpx.AsyncClient() as dl_client:
                                        img_resp = await dl_client.get(image_url)
                                        img_resp.raise_for_status()
                                        mime_type = img_resp.headers.get("content-type", "image/jpeg")
                                        image_data = base64.b64encode(img_resp.content).decode("utf-8")
                                except Exception as e:
                                    print(f"Failed to download image from {image_url}: {e}")
                                    continue
                                
                        if image_data:
                            parts.append({
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": image_data
                                }
                            })

            if not parts:
                continue

            if role == "system":
                system_instruction = {"parts": parts} 
            elif role == "user":
                contents.append({"role": "user", "parts": parts})
            elif role == "assistant":
                contents.append({"role": "model", "parts": parts})
                
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        if response_format and response_format.get("type") == "json_object":
             payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                print(f"Gemini Response Error: {data}")
                raise ValueError(f"Unexpected Gemini response format")
    
    def parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        解析AI返回的JSON响应
        处理可能的markdown代码块包裹
        """
        # 移除可能的markdown代码块标记
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content.strip())


# 单例客户端实例
ai_client = AIClient()
