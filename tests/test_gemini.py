import asyncio
import sys
import os
from pathlib import Path

# 添加 backend 目录到 sys.path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.utils.ai_client import ai_client
from app.config import get_settings

async def test_gemini():
    settings = get_settings()
    print(f"Current AI Provider: {settings.ai_provider}")
    print(f"Google API Key Configured: {'Yes' if settings.google_api_key else 'No'}")
    
    if not settings.google_api_key:
        print("Error: GOOGLE_API_KEY is not set.")
        return

    # 强制使用 gemini (或者测试是否能通过 provider 参数覆盖)
    try:
        print("Testing Gemini API...")
        # Note: model name might need to be 'models/gemini-2.0-flash' or just 'gemini-2.0-flash' depending on client implementation
        # Our client prepends 'models/' to the URL path segment? 
        # No, client uses f".../models/{model}:generateContent..."
        # So passing "gemini-2.0-flash" results in ".../models/gemini-2.0-flash:generateContent"
        # This matches the API docs.
        
        response = await ai_client.chat_completion(
            messages=[{"role": "user", "content": "Hello, explain quantum physics in 10 words."}],
            provider="gemini",
            model="gemini-2.0-flash"
        )
        print("\nGemini Response:")
        print(response)
        
        print("\nTesting JSON mode...")
        response_json = await ai_client.chat_completion(
            messages=[{"role": "user", "content": "List 3 fruits in JSON format with keys 'name' and 'color'."}],
            provider="gemini",
            model="gemini-2.0-flash",
            response_format={"type": "json_object"}
        )
        print("\nGemini JSON Response:")
        print(response_json)
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
