from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "ID SHIELD"
    app_version: str = "1.0.0-MVP"
    debug: bool = False
    
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/idshield"
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    upload_dir: str = "/tmp/idshield/uploads"
    reports_dir: str = "/tmp/idshield/reports"
    max_file_size_mb: int = 500
    
    allowed_image_types: list = ["image/jpeg", "image/png", "image/tiff", "image/bmp"]
    allowed_video_types: list = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/avi"]
    allowed_audio_types: list = ["audio/mpeg", "audio/wav", "audio/x-wav"]
    
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
