
import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.video_service import VIDEO_DIR

async def debug_merge():
    print(f"Video Directory: {VIDEO_DIR}")
    if not VIDEO_DIR.exists():
        print("Directory does not exist!")
        return

    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        print("ffmpeg is available.")
    except FileNotFoundError:
        print("Error: ffmpeg not found in PATH.")
        return
    except Exception as e:
        print(f"Error checking ffmpeg: {e}")

    # 查找视频文件
    video_files = list(VIDEO_DIR.glob("*.mp4"))
    source_videos = [f for f in video_files if not f.name.startswith("merged_") and not f.name.startswith("temp_") and not f.name.startswith("test_") and not f.name.startswith("debug_")]
    
    if len(source_videos) < 2:
        print("Not enough videos for testing.")
        print(f"Found videos: {[f.name for f in video_files]}")
        return

    test_videos = source_videos[:2]
    print(f"Testing with: {[f.name for f in test_videos]}")
    
    output_path = VIDEO_DIR / "debug_merge_output.mp4"
    
    # 构建 ffmpeg concat filter 命令
    # ffmpeg -i v1.mp4 -i v2.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" output.mp4
    
    inputs = []
    filter_complex = ""
    for i in range(len(test_videos)):
        inputs.extend(["-i", str(test_videos[i])])
        filter_complex += f"[{i}:v][{i}:a]"
        
    filter_complex += f"concat=n={len(test_videos)}:v=1:a=1[v][a]"
    
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(output_path)
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Merge successful!")
            print(f"Output: {output_path}")
        else:
            print("Merge failed!")
            print(result.stderr)
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_merge())
