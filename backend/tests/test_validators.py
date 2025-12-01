"""
Тесты для модуля validators.
"""
import pytest
import base64
import io
import sys
import os
from PIL import Image

# Добавляем путь к app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.validators import (
    validate_base64_image,
    validate_language,
    validate_session_id,
    ValidationError
)


class TestValidateBase64Image:
    """Тесты для validate_base64_image."""
    
    def test_valid_png_image(self, sample_image_base64):
        """Тест валидного PNG изображения."""
        image_bytes, image = validate_base64_image(sample_image_base64)
        assert isinstance(image_bytes, bytes)
        assert isinstance(image, Image.Image)
        assert image.format == 'PNG'
    
    def test_valid_png_with_prefix(self, sample_image_base64_with_prefix):
        """Тест PNG изображения с префиксом data:image."""
        image_bytes, image = validate_base64_image(sample_image_base64_with_prefix)
        assert isinstance(image_bytes, bytes)
        assert isinstance(image, Image.Image)
    
    def test_valid_jpeg_image(self, sample_image_jpeg):
        """Тест валидного JPEG изображения."""
        base64_str = base64.b64encode(sample_image_jpeg).decode('utf-8')
        image_bytes, image = validate_base64_image(base64_str)
        assert isinstance(image_bytes, bytes)
        assert isinstance(image, Image.Image)
        assert image.format == 'JPEG'
    
    def test_empty_string(self):
        """Тест пустой строки."""
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image("")
        assert exc_info.value.code == "EMPTY_IMAGE"
        assert exc_info.value.error == "INVALID_IMAGE"
    
    def test_none_string(self):
        """Тест None строки."""
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image(None)
        assert exc_info.value.code == "EMPTY_IMAGE"
    
    def test_whitespace_string(self):
        """Тест строки с пробелами."""
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image("   ")
        assert exc_info.value.code == "EMPTY_IMAGE"
    
    def test_invalid_base64(self):
        """Тест некорректной base64 строки."""
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image("not_valid_base64!!!")
        assert exc_info.value.code == "DECODE_ERROR"
        assert exc_info.value.error == "INVALID_BASE64"
    
    def test_too_large_image(self, mock_settings):
        """Тест слишком большого изображения."""
        # Создаем строку больше MAX_IMAGE_SIZE
        large_string = "A" * (mock_settings.MAX_IMAGE_SIZE + 1)
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image(base64.b64encode(large_string.encode()).decode())
        assert exc_info.value.code == "SIZE_EXCEEDED"
    
    def test_invalid_format(self):
        """Тест неподдерживаемого формата."""
        # Создаем валидную base64 строку, но не изображение
        invalid_data = base64.b64encode(b"not an image").decode('utf-8')
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image(invalid_data)
        assert exc_info.value.code == "FORMAT_ERROR"
        assert "JPEG, PNG, WebP" in exc_info.value.message
    
    def test_too_large_dimension(self, mock_settings):
        """Тест слишком большого разрешения."""
        # Создаем изображение больше MAX_IMAGE_DIMENSION
        large_img = Image.new('RGB', (5000, 5000), color='red')
        buffer = io.BytesIO()
        large_img.save(buffer, format='PNG')
        buffer.seek(0)
        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        with pytest.raises(ValidationError) as exc_info:
            validate_base64_image(base64_str)
        assert exc_info.value.code == "DIMENSION_EXCEEDED"
        assert "4096" in exc_info.value.message


class TestValidateLanguage:
    """Тесты для validate_language."""
    
    def test_default_language(self, mock_settings):
        """Тест языка по умолчанию."""
        result = validate_language(None)
        assert result == mock_settings.OCR_DEFAULT_LANGUAGE
    
    def test_valid_language_en(self, mock_settings):
        """Тест валидного языка английский."""
        result = validate_language("en")
        assert result == "en"
    
    def test_valid_language_ru(self, mock_settings):
        """Тест валидного языка русский."""
        result = validate_language("ru")
        assert result == "ru"
    
    def test_invalid_language(self, mock_settings):
        """Тест неподдерживаемого языка."""
        with pytest.raises(ValidationError) as exc_info:
            validate_language("fr")
        assert exc_info.value.code == "LANGUAGE_ERROR"
        assert exc_info.value.error == "INVALID_LANGUAGE"
        assert "en" in exc_info.value.message or "ru" in exc_info.value.message


class TestValidateSessionId:
    """Тесты для validate_session_id."""
    
    def test_none_session_id(self):
        """Тест None session_id."""
        result = validate_session_id(None)
        assert result is None
    
    def test_empty_string(self):
        """Тест пустой строки."""
        result = validate_session_id("")
        assert result is None
    
    def test_whitespace_string(self):
        """Тест строки с пробелами."""
        result = validate_session_id("   ")
        assert result is None
    
    def test_valid_session_id(self):
        """Тест валидного session_id."""
        session_id = "test-session-123"
        result = validate_session_id(session_id)
        assert result == session_id
    
    def test_session_id_with_spaces(self):
        """Тест session_id с пробелами (должен обрезаться)."""
        session_id = "  test-session-123  "
        result = validate_session_id(session_id)
        assert result == "test-session-123"

