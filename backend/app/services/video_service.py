"""
视频生成服务
集成Runway/Kling API生成视频片段
"""
import os
import uuid
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
from ..config import get_settings


# 生成的视频存储目录
VIDEO_DIR = Path(__file__).parent.parent.parent / "uploads" / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


class VideoProvider(str, Enum):
    """视频生成提供商"""
    MOCK = "mock"
    RUNWAY = "runway"
    KLING = "kling"
    VEO = "veo"


class VideoGenerationService:
    """视频生成服务"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: int = 5,
        provider: Optional[str] = None,
        aspect_ratio: str = "9:16",
        manifest: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从图像生成视频
        
        Args:
            image_url: 起始帧图像URL
            prompt: 视频生成提示词（描述运动）
            duration: 视频时长（秒）
            provider: 视频生成提供商 (runway/kling)
            aspect_ratio: 画面比例
            
        Returns:
            {
                "video_url": "生成的视频URL",
                "local_path": "本地保存路径",
                "duration": "视频时长",
                "status": "生成状态"
            }
        """
        provider = provider or self.settings.video_provider
        
        if provider == "mock":
            return await self._mock_generate(image_url, prompt, duration)
        elif provider == "runway":
            return await self._runway_generate(image_url, prompt, duration, aspect_ratio)
        elif provider == "kling":
            return await self._kling_generate(image_url, prompt, duration, aspect_ratio)
        elif provider == "veo":
            return await self._veo_generate(image_url, prompt, duration, aspect_ratio, manifest)
        else:
            return await self._mock_generate(image_url, prompt, duration)
    
    async def _mock_generate(
        self, 
        image_url: str, 
        prompt: str, 
        duration: int
    ) -> Dict[str, Any]:
        """模拟视频生成"""
        # 模拟生成延迟
        await asyncio.sleep(1)
        
        # 使用示例视频URL
        mock_videos = [
            "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "https://www.w3schools.com/html/mov_bbb.mp4",
        ]
        
        seed = hash(prompt) % len(mock_videos)
        
        return {
            "video_url": mock_videos[seed],
            "local_path": None,
            "duration": duration,
            "prompt": prompt,
            "provider": "mock",
            "status": "completed",
            "task_id": f"mock_{uuid.uuid4().hex[:8]}"
        }
    
    async def _runway_generate(
        self,
        image_url: str,
        prompt: str,
        duration: int,
        aspect_ratio: str
    ) -> Dict[str, Any]:
        """
        使用Runway Gen-3 API生成视频
        
        需要在.env中配置 RUNWAY_API_KEY
        文档: https://docs.runwayml.com/
        """
        api_key = os.getenv("RUNWAY_API_KEY", "")
        
        if not api_key:
            print("警告: RUNWAY_API_KEY未配置，使用mock模式")
            return await self._mock_generate(image_url, prompt, duration)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"
        }
        
        # Runway Gen-3 Alpha Turbo 图生视频
        payload = {
            "promptImage": image_url,
            "promptText": prompt,
            "model": "gen3a_turbo",
            "duration": min(duration, 10),  # Runway最长10秒
            "ratio": "16:9" if aspect_ratio == "16:9" else "9:16",
            "watermark": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                # 创建生成任务
                response = await client.post(
                    "https://api.runwayml.com/v1/image_to_video",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                task_data = response.json()
                task_id = task_data.get("id")
                
                # 轮询等待完成
                for _ in range(120):  # 最多等待2分钟
                    status_response = await client.get(
                        f"https://api.runwayml.com/v1/tasks/{task_id}",
                        headers=headers
                    )
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "SUCCEEDED":
                        video_url = status_data.get("output", [None])[0]
                        
                        # 下载并保存视频
                        local_path = None
                        if video_url:
                            local_path = await self._download_video(video_url)
                        
                        return {
                            "video_url": video_url,
                            "local_path": local_path,
                            "duration": duration,
                            "prompt": prompt,
                            "provider": "runway",
                            "status": "completed",
                            "task_id": task_id
                        }
                    elif status == "FAILED":
                        error = status_data.get("failure", "Unknown error")
                        raise Exception(f"Runway视频生成失败: {error}")
                    
                    await asyncio.sleep(2)
                
                raise Exception("Runway视频生成超时")
                
        except httpx.HTTPError as e:
            print(f"Runway API错误: {e}")
            return await self._mock_generate(image_url, prompt, duration)
        except Exception as e:
            print(f"视频生成错误: {e}")
            return await self._mock_generate(image_url, prompt, duration)
    
    async def _kling_generate(
        self,
        image_url: str,
        prompt: str,
        duration: int,
        aspect_ratio: str
    ) -> Dict[str, Any]:
        """
        使用Kling API生成视频
        
        需要在.env中配置 KLING_API_KEY 和 KLING_ACCESS_KEY
        """
        api_key = os.getenv("KLING_API_KEY", "")
        access_key = os.getenv("KLING_ACCESS_KEY", "")
        
        if not api_key or not access_key:
            print("警告: KLING_API_KEY未配置，使用mock模式")
            return await self._mock_generate(image_url, prompt, duration)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Kling图生视频参数
        payload = {
            "model_name": "kling-v1",  # 或 kling-v1-5
            "image": image_url,
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted",
            "cfg_scale": 0.5,
            "mode": "std",  # std 或 pro
            "duration": str(min(duration, 10))  # 5 或 10 秒
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                # 提交任务
                response = await client.post(
                    "https://api.klingai.com/v1/videos/image2video",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                task_data = response.json()
                
                if task_data.get("code") != 0:
                    raise Exception(f"Kling错误: {task_data.get('message')}")
                
                task_id = task_data.get("data", {}).get("task_id")
                
                # 轮询等待完成
                for _ in range(180):  # 最多等待3分钟
                    status_response = await client.get(
                        f"https://api.klingai.com/v1/videos/image2video/{task_id}",
                        headers=headers
                    )
                    status_data = status_response.json()
                    
                    if status_data.get("code") != 0:
                        raise Exception(f"Kling查询错误: {status_data.get('message')}")
                    
                    task_status = status_data.get("data", {}).get("task_status")
                    
                    if task_status == "succeed":
                        videos = status_data.get("data", {}).get("task_result", {}).get("videos", [])
                        video_url = videos[0].get("url") if videos else None
                        
                        # 下载并保存视频
                        local_path = None
                        if video_url:
                            local_path = await self._download_video(video_url)
                        
                        return {
                            "video_url": video_url,
                            "local_path": local_path,
                            "duration": duration,
                            "prompt": prompt,
                            "provider": "kling",
                            "status": "completed",
                            "task_id": task_id
                        }
                    elif task_status == "failed":
                        error = status_data.get("data", {}).get("task_status_msg", "Unknown error")
                        raise Exception(f"Kling视频生成失败: {error}")
                    
                    await asyncio.sleep(2)
                
                raise Exception("Kling视频生成超时")
                
        except httpx.HTTPError as e:
            print(f"Kling API错误: {e}")
            return await self._mock_generate(image_url, prompt, duration)
        except Exception as e:
            print(f"Kling视频生成错误: {e}")
            return await self._mock_generate(image_url, prompt, duration)
    
    async def _download_video(self, url: str) -> Optional[str]:
        """下载视频到本地"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # 生成唯一文件名
                ext = ".mp4"
                if "webm" in url.lower():
                    ext = ".webm"
                
                filename = f"{uuid.uuid4().hex[:12]}{ext}"
                file_path = VIDEO_DIR / filename
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                return f"/api/v1/upload/files/videos/{filename}"
        except Exception as e:
            print(f"下载视频失败: {e}")
            return None
    
    async def _veo_generate(
        self,
        image_url: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        manifest: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用Google VEO API生成视频
        
        支持 VEO 2 和 VEO 3 模型
        需要在.env中配置 GOOGLE_API_KEY
        文档: https://ai.google.dev/gemini-api/docs/video
        """
        # 优先从Settings读取
        api_key = self.settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")
        
        if not api_key:
            print("警告: GOOGLE_API_KEY未配置，使用mock模式")
            return await self._mock_generate(image_url, prompt, duration)
        
        # 直接使用 Gemini API 的 VEO 模型
        # Vertex AI 需要 Service Account，API Key 只能用 Gemini API
        print("[VEO] 使用 Gemini API 调用 VEO 模型...")
        return await self._veo_gemini_generate(image_url, prompt, duration, aspect_ratio, api_key, manifest)
        

    
    async def _veo_gemini_generate(
        self,
        image_url: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        api_key: str,
        manifest: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用Gemini API的VEO视频生成
        
        参考: https://ai.google.dev/gemini-api/docs/video
        模型: veo-3.1-generate-preview
        """
        import base64
        
        # 使用正确的VEO模型名称
        # 注意: veo-3.1-generate-preview 是正确的模型名
        veo_model = "veo-3.1-fast-generate-preview"
        
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base_url}/models/{veo_model}:predictLongRunning"
        
        print(f"[VEO] 使用模型: {veo_model}")
        # print(f"[VEO] Prompt: {prompt}")
        
        # 使用 x-goog-api-key header 进行认证
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # 解析Manifest
        final_prompt = prompt
        parameters = {}
        
        if manifest and "veo_production_manifest" in manifest:
            m = manifest["veo_production_manifest"]
            if "shot_summary" in m:
                final_prompt = m["shot_summary"]
                print(f"[VEO] Using Manifest Prompt: {final_prompt[:50]}...")
            
            # 提取 Global Settings -> Output Specifications
            try:
                specs = m.get("global_settings", {}).get("output_specifications", {})
                
                # 1. 合并 inner 'parameters' dict (如 aspectRatio)
                if "parameters" in specs and isinstance(specs["parameters"], dict):
                    manifest_params = specs["parameters"]
                    print(f"[VEO] Merging Manifest Parameters: {manifest_params}")
                    parameters.update(manifest_params)
                
                # 2. 检查 resolution 并添加到 parameters
                if "resolution" in specs:
                    parameters["resolution"] = specs["resolution"]
                    print(f"[VEO] Adding Manifest Resolution: {specs['resolution']}")
                    
            except Exception as e:
                print(f"[VEO] Error parsing manifest settings: {e}")
        
        # 确保 aspectRatio 存在 (如果Manifest未提供，使用参数默认值)
        if "aspectRatio" not in parameters and aspect_ratio:
            parameters["aspectRatio"] = aspect_ratio
            
        # 强制在Prompt中添加宽高比描述 (Double Insurance)
        target_ar = parameters.get("aspectRatio", aspect_ratio)
        if target_ar:
            if target_ar == "9:16":
                final_prompt += ", vertical 9:16 aspect ratio, portrait mode"
            elif target_ar == "16:9":
                final_prompt += ", cinematic 16:9 aspect ratio, wide screen"
            else:
                final_prompt += f", {target_ar} aspect ratio"
        
        # 构建实例
        instances = [{"prompt": final_prompt}]
        print(f"[VEO] Instances: {instances}")

        # 3. 处理图像 (添加到 instance 中)
        if image_url:
            image_base64, mime_type = await self._fetch_image_base64_with_mime(image_url)
            if image_base64:
                print(f"[VEO] 包含参考图像，MIME: {mime_type}, 大小: {len(image_base64)} bytes")
                instances[0]["image"] = {
                    "bytesBase64Encoded": image_base64,
                    "mimeType": mime_type
                }
        
        payload = {
            "instances": instances,
            "parameters": parameters
        }
        
        print(f"[VEO] 发送请求到: {url}")
        #打印parameters
        print(f"[VEO] Parameters: {parameters}")    
        
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                # 发送生成请求
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                
                print(f"[VEO] 响应状态: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[VEO] 错误响应: {response.text}")
                    raise Exception(f"VEO API错误: {response.status_code} - {response.text}")
                
                result = response.json()
                operation_name = result.get("name")
                print(f"[VEO] Operation: {operation_name}")
                
                if not operation_name:
                    raise Exception("VEO未返回operation name")
                
                # 轮询等待视频生成完成
                # 视频生成可能需要较长时间（1-5分钟）
                max_attempts = 60  # 最多等待10分钟 (60 * 10秒)
                
                for attempt in range(max_attempts):
                    print(f"[VEO] 轮询状态... (尝试 {attempt + 1}/{max_attempts})")
                    
                    status_resp = await client.get(
                        f"{base_url}/{operation_name}",
                        headers=headers
                    )
                    
                    status_data = status_resp.json()
                    is_done = status_data.get("done", False)
                    
                    if is_done:
                        print(f"[VEO] 生成完成!")
                        
                        # 检查错误
                        if "error" in status_data:
                            raise Exception(f"VEO生成错误: {status_data['error']}")
                        
                        # 解析响应 - 根据官方格式
                        # response.generateVideoResponse.generatedSamples[0].video.uri
                        response_data = status_data.get("response", {})
                        generate_video_response = response_data.get("generateVideoResponse", {})
                        generated_samples = generate_video_response.get("generatedSamples", [])
                        
                        if generated_samples:
                            video_info = generated_samples[0].get("video", {})
                            video_uri = video_info.get("uri")
                            
                            if video_uri:
                                print(f"[VEO] 视频URI: {video_uri}")
                                
                                # 下载视频
                                video_response = await client.get(
                                    video_uri,
                                    headers=headers,
                                    follow_redirects=True
                                )
                                
                                if video_response.status_code == 200:
                                    # 保存视频到本地
                                    filename = f"{uuid.uuid4().hex[:12]}.mp4"
                                    file_path = VIDEO_DIR / filename
                                    
                                    with open(file_path, "wb") as f:
                                        f.write(video_response.content)
                                    
                                    print(f"[VEO] 视频已保存: {file_path}")
                                    
                                    # 构建返回URL
                                    host = self.settings.host
                                    port = self.settings.port
                                    if host == "0.0.0.0":
                                        host = "localhost"
                                    
                                    local_path = f"/api/v1/upload/files/videos/{filename}"
                                    full_url = f"http://{host}:{port}{local_path}"
                                    
                                    return {
                                        "video_url": full_url,
                                        "local_path": local_path,
                                        "duration": duration,
                                        "prompt": prompt,
                                        "provider": "veo",
                                        "status": "completed",
                                        "task_id": operation_name
                                    }
                                else:
                                    print(f"[VEO] 下载视频失败: {video_response.status_code}")
                        
                        # 如果没有找到视频URI，打印完整响应以便调试
                        print(f"[VEO] 完整响应: {status_data}")
                        raise Exception("VEO响应中未找到视频URI")
                    
                    # 等待10秒后再次轮询
                    await asyncio.sleep(10)
                
                raise Exception("VEO视频生成超时（等待时间过长）")
                
        except Exception as e:
            print(f"[VEO] Gemini VEO错误: {e}")
            return await self._mock_generate(image_url, prompt, duration)

    
    async def _fetch_image_base64(self, url: str) -> str:
        """获取图像并转换为base64"""
        import base64
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            print(f"获取图像失败: {e}")
            return ""
    
    async def _fetch_image_base64_with_mime(self, url: str) -> tuple:
        """获取图像并转换为base64，同时返回MIME类型"""
        import base64
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # 从Content-Type header获取MIME类型
                content_type = response.headers.get("content-type", "image/png")
                # 清理可能的charset等附加信息
                mime_type = content_type.split(";")[0].strip()
                
                # 如果无法确定，根据URL扩展名推断
                if mime_type == "application/octet-stream" or not mime_type.startswith("image/"):
                    if url.lower().endswith(".png"):
                        mime_type = "image/png"
                    elif url.lower().endswith(".jpg") or url.lower().endswith(".jpeg"):
                        mime_type = "image/jpeg"
                    elif url.lower().endswith(".webp"):
                        mime_type = "image/webp"
                    elif url.lower().endswith(".gif"):
                        mime_type = "image/gif"
                    else:
                        mime_type = "image/png"  # 默认
                
                image_base64 = base64.b64encode(response.content).decode("utf-8")
                return image_base64, mime_type
        except Exception as e:
            print(f"获取图像失败: {e}")
            return "", "image/png"
    
    async def get_task_status(
        self, 
        task_id: str, 
        provider: str = "runway"
    ) -> Dict[str, Any]:
        """
        查询视频生成任务状态
        
        Args:
            task_id: 任务ID
            provider: 提供商
            
        Returns:
            任务状态信息
        """
        if provider == "mock":
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100
            }
        
        # TODO: 实现真实的状态查询
        return {
            "task_id": task_id,
            "status": "unknown",
            "progress": 0
        }
    
    async def merge_videos(
        self,
        video_urls: List[str],
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合并多个视频为一个完整视频
        
        Args:
            video_urls: 视频URL列表（按顺序）
            aspect_ratio: 画面比例
            resolution: 目标分辨率
            output_filename: 输出文件名（可选）
            
        Returns:
            {
                "video_url": "合并后视频的URL",
                "local_path": "本地保存路径",
                "duration": 总时长,
                "status": "completed"
            }
        """
        import subprocess
        import tempfile
        
        if not video_urls:
            raise ValueError("视频列表不能为空")
        
        print(f"[VideoMerge] 开始合并 {len(video_urls)} 个视频, 目标比例: {aspect_ratio}, 分辨率: {resolution}")
        
        # 生成输出文件名
        if not output_filename:
            output_filename = f"merged_{uuid.uuid4().hex[:12]}.mp4"
        
        output_path = VIDEO_DIR / output_filename
        
        try:
            # 下载所有视频到临时目录
            temp_files = []
            async with httpx.AsyncClient(timeout=60.0) as client:
                for i, url in enumerate(video_urls):
                    print(f"[VideoMerge] 下载视频 {i+1}/{len(video_urls)}: {url}")
                    
                    # 处理相对URL
                    if url.startswith("/"):
                        # 本地文件
                        local_path = Path(__file__).parent.parent.parent / url.lstrip("/")
                        if local_path.exists():
                            temp_files.append(str(local_path))
                            continue
                    
                    # 远程URL，下载到临时文件
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    temp_file = VIDEO_DIR / f"temp_{i}_{uuid.uuid4().hex[:8]}.mp4"
                    with open(temp_file, "wb") as f:
                        f.write(response.content)
                    temp_files.append(str(temp_file))
            
            print(f"[VideoMerge] 已下载 {len(temp_files)} 个视频文件")
            
            # 检查ffmpeg是否可用并获取路径
            ffmpeg_path = "ffmpeg"
            ffmpeg_available = False
            
            # 尝试查找位置列表
            possible_paths = [
                "ffmpeg",  # 系统环境变量
                str(Path(os.getcwd()) / "ffmpeg.exe"), # 当前工作目录
                str(Path(os.getcwd()) / "bin" / "ffmpeg.exe"), # 当前目录bin下
                str(Path(__file__).parent.parent.parent / "ffmpeg.exe"), # backend根目录
                str(Path(__file__).parent.parent.parent.parent / "ffmpeg.exe"), # 项目根目录
                str(Path(__file__).parent.parent.parent.parent / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"), # 常见工具目录
            ]
            
            for path in possible_paths:
                try:
                    subprocess.run(
                        [path, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    ffmpeg_path = path
                    ffmpeg_available = True
                    print(f"[VideoMerge] Found ffmpeg at: {path}")
                    break
                except Exception:
                    continue
            
            if not ffmpeg_available:
                print("[VideoMerge] ffmpeg 未找到，无法合并视频")
            
            if ffmpeg_available and len(temp_files) >= 1:
                # 解析分辨率
                # 默认 1080p -> 1080x1920 (9:16) 或 1920x1080 (16:9)
                target_w = 1080
                target_h = 1920
                
                if aspect_ratio == "16:9":
                    target_w = 1920
                    target_h = 1080
                    if resolution == "2K":
                        target_w, target_h = 2560, 1440
                    elif resolution == "4K":
                        target_w, target_h = 3840, 2160
                else: # 9:16
                    target_w = 1080
                    target_h = 1920
                    if resolution == "2K":
                        target_w, target_h = 1440, 2560
                    elif resolution == "4K":
                        target_w, target_h = 2160, 3840

                print(f"[VideoMerge] 最终目标尺寸: {target_w}x{target_h}")
                
                # 构建复杂的ffmpeg命令，对每个视频进行缩放和补边
                # 使用 filter_complex 处理多个输入
                filter_complex = ""
                for i in range(len(temp_files)):
                    # 缩放并保持比例，不足部分补黑边 (pad)
                    # force_original_aspect_ratio=decrease 确保视频不被拉伸
                    filter_complex += f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];"
                    # 音频处理（如果存在）
                    filter_complex += f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];"
                
                concat_inputs = "".join([f"[v{i}][a{i}]" for i in range(len(temp_files))])
                filter_complex += f"{concat_inputs}concat=n={len(temp_files)}:v=1:a=1[v][a]"
                
                cmd = [ffmpeg_path, "-y"]
                for f in temp_files:
                    cmd.extend(["-i", f])
                
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[v]",
                    "-map", "[a]",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    str(output_path)
                ])
                
                print(f"[VideoMerge] 执行合并命令: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600 # 合并可能较慢
                )
                
                if result.returncode != 0:
                    print(f"[VideoMerge] ffmpeg合并失败: {result.stderr}")
                    # 回退尝试最简合并（如果复杂滤镜失败）
                    raise Exception(f"ffmpeg合并失败: {result.stderr}")
                
                print(f"[VideoMerge] 合并成功: {output_path}")
                
            elif len(temp_files) == 1:
                # 只有一个视频，直接复制
                import shutil
                shutil.copy(temp_files[0], output_path)
                print(f"[VideoMerge] 单个视频，直接复制: {output_path}")
            else:
                # ffmpeg不可用，返回第一个视频
                print("[VideoMerge] ffmpeg不可用或无视频，返回第一个视频")
                if temp_files:
                    import shutil
                    shutil.copy(temp_files[0], output_path)
            
            # 清理临时下载的文件
            for temp_file in temp_files:
                temp_path = Path(temp_file)
                # 只清理临时生成的文件，不清理原始上传的视频
                if "temp_" in temp_path.name:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except Exception as e:
                        print(f"清理临时文件失败: {e}")
            
            # 计算总时长（估算）
            total_duration = len(video_urls) * 5  # 假设每个视频5秒
            
            # 构建相对路径URL
            # 注意：这里需要返回前端可以访问的URL
            relative_path = f"/api/v1/upload/files/videos/{output_filename}"
            
            return {
                "video_url": relative_path,
                "local_path": str(output_path),
                "duration": total_duration,
                "status": "completed",
                "video_count": len(video_urls)
            }
            
        except Exception as e:
            print(f"[VideoMerge] 合并失败: {e}")
            raise Exception(f"视频合并失败: {str(e)}")


# 单例服务实例
video_service = VideoGenerationService()

