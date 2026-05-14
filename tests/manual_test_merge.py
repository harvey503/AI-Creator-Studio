
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.video_service import video_service, VIDEO_DIR

async def test_merge():
    # 确保视频目录存在
    if not VIDEO_DIR.exists():
        print(f"Video directory not found: {VIDEO_DIR}")
        return

    # 获取目录下的所有mp4文件
    video_files = list(VIDEO_DIR.glob("*.mp4"))
    
    # 过滤掉以 "merged_" 或 "temp_" 开头的文件，以此模拟测试
    source_videos = [f for f in video_files if not f.name.startswith("merged_") and not f.name.startswith("temp_")]
    
    if len(source_videos) < 2:
        print(f"Not enough source videos found in {VIDEO_DIR}. Need at least 2.")
        print(f"Available videos: {[f.name for f in source_videos]}")
        
        # 如果没有足够的视频，您可以手动复制一些视频到该目录，
        # 或者在这里修改代码指向特定的文件。
        # 例如:
        # source_videos = [
        #     VIDEO_DIR / "video1.mp4",
        #     VIDEO_DIR / "video2.mp4"
        # ]
        return

    # 取前两个视频进行合并测试
    test_videos = source_videos[:2]
    print(f"Testing merge with: {[f.name for f in test_videos]}")
    
    # 构建相对路径URL (模拟前端传入的URL)
    # 注意：video_service.merge_videos 能够处理以 / 开头的相对路径
    video_urls = [f"/uploads/videos/{f.name}" for f in test_videos]
    
    try:
        result = await video_service.merge_videos(
            video_urls=video_urls,
            output_filename=f"test_merge_{int(asyncio.get_event_loop().time())}.mp4"
        )
        print("\nMerge Successful!")
        print(f"Result: {result}")
        print(f"Merged video path: {result['local_path']}")
        
    except Exception as e:
        print(f"\nMerge Failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_merge())
