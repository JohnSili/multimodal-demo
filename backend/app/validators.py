"""
Валидация входных данных: изображений, форматов, размеров.
"""
import base64
import io
from PIL import Image
from typing import Tuple, Optional
from app.config import settings


class ValidationError(Exception):
    """Исключение для ошибок валидации."""
    def __init__(self, error: str, message: str, code: str):
        self.error = error
        self.message = message
        self.code = code
        super().__init__(message)


def validate_base64_image(base64_string: str) -> Tuple[bytes, Image.Image]:
    """
    Валидирует base64 строку и декодирует изображение.
    
    Args:
        base64_string: Base64-encoded строка изображения
        
    Returns:
        Tuple[bytes, Image.Image]: Декодированные байты и PIL Image
        
    Raises:
        ValidationError: Если валидация не прошла
    """
    if not base64_string or not base64_string.strip():
        raise ValidationError(
            error="INVALID_IMAGE",
            message="Изображение не предоставлено",
            code="EMPTY_IMAGE"
        )
    
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    if len(base64_string) > settings.MAX_IMAGE_SIZE:
        raise ValidationError(
            error="IMAGE_TOO_LARGE",
            message=f"Размер изображения превышает {settings.MAX_IMAGE_SIZE / (1024*1024):.1f}MB",
            code="SIZE_EXCEEDED"
        )
    
    try:
        image_bytes = base64.b64decode(base64_string, validate=True)
    except Exception as e:
        raise ValidationError(
            error="INVALID_BASE64",
            message="Некорректная base64 строка",
            code="DECODE_ERROR"
        )
    
    if len(image_bytes) > settings.MAX_IMAGE_SIZE:
        raise ValidationError(
            error="IMAGE_TOO_LARGE",
            message=f"Размер изображения превышает {settings.MAX_IMAGE_SIZE / (1024*1024):.1f}MB",
            code="SIZE_EXCEEDED"
        )
    
    valid_formats = {
        b'\xff\xd8\xff': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'RIFF': 'WEBP'
    }
    
    image_format = None
    for magic, fmt in valid_formats.items():
        if image_bytes.startswith(magic):
            image_format = fmt
            break
    
    if image_format is None:
        if image_bytes[8:12] == b'WEBP':
            image_format = 'WEBP'
        else:
            raise ValidationError(
                error="INVALID_FORMAT",
                message="Неподдерживаемый формат изображения. Разрешены: JPEG, PNG, WebP",
                code="FORMAT_ERROR"
            )
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as e:
        raise ValidationError(
            error="INVALID_IMAGE",
            message=f"Ошибка при обработке изображения: {str(e)}",
            code="IMAGE_ERROR"
        )
    
    width, height = image.size
    if width > settings.MAX_IMAGE_DIMENSION or height > settings.MAX_IMAGE_DIMENSION:
        raise ValidationError(
            error="IMAGE_TOO_LARGE",
            message=f"Разрешение изображения превышает {settings.MAX_IMAGE_DIMENSION}x{settings.MAX_IMAGE_DIMENSION} пикселей",
            code="DIMENSION_EXCEEDED"
        )
    
    return image_bytes, image


def validate_language(language: Optional[str]) -> str:
    """
    Валидирует язык для OCR.
    
    Args:
        language: Код языка
        
    Returns:
        str: Валидный код языка
        
    Raises:
        ValidationError: Если язык не поддерживается
    """
    if language is None:
        return settings.OCR_DEFAULT_LANGUAGE
    
    if language not in settings.OCR_LANGUAGES:
        raise ValidationError(
            error="INVALID_LANGUAGE",
            message=f"Неподдерживаемый язык. Доступны: {', '.join(settings.OCR_LANGUAGES)}",
            code="LANGUAGE_ERROR"
        )
    
    return language


def validate_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Валидирует session_id.
    
    Args:
        session_id: ID сессии
        
    Returns:
        Optional[str]: Валидный session_id или None
    """
    if session_id is None or not session_id.strip():
        return None
    return session_id.strip()

