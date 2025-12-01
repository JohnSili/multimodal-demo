"""
Вспомогательные функции для работы с изображениями, сессиями и файлами.
"""
import uuid
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional
from PIL import Image
import io


sessions: Dict[str, Dict] = {}


def generate_session_id() -> str:
    """Генерирует уникальный session_id."""
    return str(uuid.uuid4())


def save_session_image(session_id: str, image_bytes: bytes, image: Image.Image) -> None:
    """
    Сохраняет изображение в сессии.
    
    Args:
        session_id: ID сессии
        image_bytes: Байты изображения
        image: PIL Image объект
    """
    sessions[session_id] = {
        "image_bytes": image_bytes,
        "image": image,
        "created_at": datetime.now(),
        "last_accessed": datetime.now()
    }


def get_session_image(session_id: str) -> Optional[tuple[bytes, Image.Image]]:
    """
    Получает изображение из сессии.
    
    Args:
        session_id: ID сессии
        
    Returns:
        Optional[tuple[bytes, Image.Image]]: Байты и PIL Image или None
    """
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    session["last_accessed"] = datetime.now()
    return session["image_bytes"], session["image"]


def cleanup_expired_sessions(timeout_seconds: int) -> None:
    """
    Удаляет истекшие сессии.
    
    Args:
        timeout_seconds: Таймаут сессии в секундах
    """
    now = datetime.now()
    expired = [
        sid for sid, session in sessions.items()
        if (now - session["last_accessed"]).total_seconds() > timeout_seconds
    ]
    for sid in expired:
        del sessions[sid]


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """
    Конвертирует PIL Image в base64 строку.
    
    Args:
        image: PIL Image объект
        format: Формат изображения
        
    Returns:
        str: Base64-encoded строка
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode("utf-8")


ocr_results: Dict[str, Dict] = {}


def save_ocr_result(text: str) -> str:
    """
    Сохраняет результат OCR и возвращает task_id.
    
    Args:
        text: Распознанный текст
        
    Returns:
        str: task_id для скачивания
    """
    task_id = str(uuid.uuid4())
    ocr_results[task_id] = {
        "text": text,
        "created_at": datetime.now()
    }
    return task_id


def get_ocr_result(task_id: str) -> Optional[str]:
    """
    Получает результат OCR по task_id.
    
    Args:
        task_id: ID задачи
        
    Returns:
        Optional[str]: Текст или None
    """
    if task_id not in ocr_results:
        return None
    return ocr_results[task_id]["text"]


def cleanup_expired_ocr_results(timeout_seconds: int = 3600) -> None:
    """
    Удаляет истекшие результаты OCR.
    
    Args:
        timeout_seconds: Таймаут в секундах
    """
    now = datetime.now()
    expired = [
        tid for tid, result in ocr_results.items()
        if (now - result["created_at"]).total_seconds() > timeout_seconds
    ]
    for tid in expired:
        del ocr_results[tid]

