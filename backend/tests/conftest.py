"""
Pytest конфигурация и фикстуры.
"""
import pytest
import base64
import io
from PIL import Image
import os
import sys

# Добавляем путь к app в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def sample_image_png():
    """Создает тестовое PNG изображение."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image_jpeg():
    """Создает тестовое JPEG изображение."""
    img = Image.new('RGB', (100, 100), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image_base64(sample_image_png):
    """Создает base64 строку из PNG изображения."""
    return base64.b64encode(sample_image_png).decode('utf-8')


@pytest.fixture
def sample_image_base64_with_prefix(sample_image_png):
    """Создает base64 строку с префиксом data:image."""
    base64_str = base64.b64encode(sample_image_png).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"


@pytest.fixture
def large_image_base64():
    """Создает base64 строку большого изображения (для тестов размера)."""
    # Создаем большое изображение
    img = Image.new('RGB', (5000, 5000), color='green')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@pytest.fixture
def mock_settings(monkeypatch):
    """Мокирует настройки для тестов."""
    import json
    import importlib
    
    monkeypatch.setenv("MAX_IMAGE_SIZE", "10485760")  # 10MB
    monkeypatch.setenv("MAX_IMAGE_DIMENSION", "4096")
    # pydantic-settings для списков ожидает JSON формат
    monkeypatch.setenv("OCR_LANGUAGES", json.dumps(["en", "ru"]))
    monkeypatch.setenv("OCR_DEFAULT_LANGUAGE", "en")
    monkeypatch.setenv("SESSION_TIMEOUT", "3600")
    
    # Перезагружаем модуль config чтобы применить новые env переменные
    import app.config
    importlib.reload(app.config)
    
    # Возвращаем новый экземпляр settings
    return app.config.settings

