import asyncio
import httpx
import os
import sys
from pathlib import Path

# Load .env manually to ensure we get the key
root_dir = Path(__file__).parent.parent / "backend"
env_file = root_dir / ".env"

api_key = None
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GOOGLE_API_KEY="):
                api_key = line.strip().split("=")[1]
                break

if not api_key:
    print("Error: Could not find GOOGLE_API_KEY in .env")
    sys.exit(1)

async def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Available Models:")
            for model in data.get("models", []):
                print(f"- {model['name']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(list_models())
