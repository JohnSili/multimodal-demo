"""
Pydantic схемы для валидации входных и выходных данных API.
"""
from pydantic import BaseModel, Field
from typing import Optional


class VQARequest(BaseModel):
    """Схема запроса для Visual Question Answering."""
    image: str = Field(..., description="Base64-encoded изображение")
    question: Optional[str] = Field(None, description="Вопрос об изображении (опционально)")
    session_id: Optional[str] = Field(None, description="ID сессии для сохранения изображения")


class VQAResponse(BaseModel):
    """Схема ответа для Visual Question Answering."""
    answer: str = Field(..., description="Ответ модели")
    session_id: str = Field(..., description="ID сессии")
    timestamp: str = Field(..., description="Временная метка ответа")


class OCRRequest(BaseModel):
    """Схема запроса для OCR."""
    image: str = Field(..., description="Base64-encoded изображение")
    language: Optional[str] = Field("en", description="Язык распознавания (en, ru)")


class OCRResponse(BaseModel):
    """Схема ответа для OCR."""
    text: str = Field(..., description="Извлеченный текст")
    download_url: str = Field(..., description="URL для скачивания результата")
    task_id: str = Field(..., description="ID задачи для скачивания")


class ErrorResponse(BaseModel):
    """Схема ответа об ошибке."""
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Понятное описание ошибки на русском")
    code: str = Field(..., description="Код ошибки для программной обработки")


class HealthResponse(BaseModel):
    """Схема ответа health check."""
    status: str = Field(..., description="Статус сервиса")
    model_loaded: bool = Field(..., description="Загружена ли модель")
    device: str = Field(..., description="Устройство (CPU/CUDA)")

