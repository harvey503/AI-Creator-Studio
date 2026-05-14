from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # API Keys
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    google_api_key: str = ""
    replicate_api_key: str = ""
    runway_api_key: str = ""
    kling_api_key: str = ""
    kling_access_key: str = ""
    
    # AI Model Configuration
    ai_provider: str = "deepseek"  # mock, openai, deepseek
    ai_model: str = "deepseek-chat"
    
    # Image Generation
    image_model: str = "nano-banana"  # flux-schnell, nano-banana
    
    # Video Generation
    video_provider: str = "veo"  # mock, runway, kling, veo
    veo_model: str = "veo-3.1-fast-generate-001"
    google_project_id: str = "gen-lang-client-0181028886"
    google_location: str = "us-central1"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略未定义的环境变量


@lru_cache()
def get_settings() -> Settings:
    return Settings()
