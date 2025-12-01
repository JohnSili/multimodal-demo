"""
Тесты для модуля config.
"""
import pytest
import os
import sys

# Добавляем путь к app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import Settings


class TestSettings:
    """Тесты для настроек."""
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        settings = Settings()
        
        assert settings.MODEL_NAME == "HuggingFaceTB/SmolVLM2-Instruct"
        assert settings.MODEL_SIZE == "instruct"
        assert settings.DEVICE == "cpu"
        assert settings.TORCH_DTYPE == "float32"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.WORKERS == 1
        assert settings.MAX_IMAGE_SIZE == 10 * 1024 * 1024
        assert settings.MAX_IMAGE_DIMENSION == 4096
        assert settings.SESSION_TIMEOUT == 3600
        assert settings.OCR_DEFAULT_LANGUAGE == "en"
        assert "en" in settings.OCR_LANGUAGES
        assert "ru" in settings.OCR_LANGUAGES
    
    def test_environment_variables(self, monkeypatch):
        """Тест загрузки из environment variables."""
        monkeypatch.setenv("MODEL_NAME", "test-model")
        monkeypatch.setenv("DEVICE", "cuda")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("MAX_IMAGE_SIZE", "5242880")  # 5MB
        
        # Перезагружаем settings
        settings = Settings()
        
        assert settings.MODEL_NAME == "test-model"
        assert settings.DEVICE == "cuda"
        assert settings.PORT == 9000
        assert settings.MAX_IMAGE_SIZE == 5242880
    
    def test_model_size_validation(self, monkeypatch):
        """Тест валидации MODEL_SIZE."""
        monkeypatch.setenv("MODEL_SIZE", "base")
        settings = Settings()
        assert settings.MODEL_SIZE == "base"
        
        # Невалидное значение должно вызвать ошибку
        monkeypatch.setenv("MODEL_SIZE", "invalid")
        with pytest.raises(Exception):  # Pydantic validation error
            Settings()
    
    def test_device_validation(self, monkeypatch):
        """Тест валидации DEVICE."""
        monkeypatch.setenv("DEVICE", "cuda")
        settings = Settings()
        assert settings.DEVICE == "cuda"
        
        monkeypatch.setenv("DEVICE", "invalid")
        with pytest.raises(Exception):  # Pydantic validation error
            Settings()
    
    def test_torch_dtype_validation(self, monkeypatch):
        """Тест валидации TORCH_DTYPE."""
        monkeypatch.setenv("TORCH_DTYPE", "float16")
        settings = Settings()
        assert settings.TORCH_DTYPE == "float16"
        
        monkeypatch.setenv("TORCH_DTYPE", "invalid")
        with pytest.raises(Exception):  # Pydantic validation error
            Settings()

