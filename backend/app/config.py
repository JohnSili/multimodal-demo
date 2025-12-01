"""
Конфигурация приложения через environment variables.
Использует pydantic-settings для загрузки и валидации.
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения из environment variables."""
    
    MODEL_NAME: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"
    MODEL_SIZE: Literal["instruct", "base"] = "instruct"
    DEVICE: Literal["cuda", "cpu"] = "cpu"
    TORCH_DTYPE: Literal["float16", "bfloat16", "float32"] = "float32"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    HF_HOME: str = str(Path(__file__).parent.parent.parent / "models")
    TRANSFORMERS_CACHE: str = str(Path(__file__).parent.parent.parent / "models")
    HF_DATASETS_CACHE: str = str(Path(__file__).parent.parent.parent / "models")
    
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024
    MAX_IMAGE_DIMENSION: int = 4096
    SESSION_TIMEOUT: int = 3600
    
    OCR_LANGUAGES: list[str] = ["en", "ru"]
    OCR_DEFAULT_LANGUAGE: str = "en"
    
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

os.environ["HF_HOME"] = settings.HF_HOME
os.environ["TRANSFORMERS_CACHE"] = settings.TRANSFORMERS_CACHE
os.environ["HF_DATASETS_CACHE"] = settings.HF_DATASETS_CACHE

