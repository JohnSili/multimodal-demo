"""
Тесты для модуля utils.
"""
import pytest
import base64
import io
import sys
import os
from datetime import datetime, timedelta
from PIL import Image

# Добавляем путь к app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils import (
    generate_session_id,
    save_session_image,
    get_session_image,
    cleanup_expired_sessions,
    image_to_base64,
    save_ocr_result,
    get_ocr_result,
    cleanup_expired_ocr_results,
    sessions,
    ocr_results
)


class TestSessionManagement:
    """Тесты для управления сессиями."""
    
    def setup_method(self):
        """Очистка перед каждым тестом."""
        sessions.clear()
    
    def test_generate_session_id(self):
        """Тест генерации session_id."""
        session_id = generate_session_id()
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        # UUID должен быть уникальным
        session_id2 = generate_session_id()
        assert session_id != session_id2
    
    def test_save_and_get_session_image(self, sample_image_png):
        """Тест сохранения и получения изображения из сессии."""
        session_id = generate_session_id()
        image = Image.open(io.BytesIO(sample_image_png))
        
        save_session_image(session_id, sample_image_png, image)
        
        result = get_session_image(session_id)
        assert result is not None
        image_bytes, retrieved_image = result
        assert image_bytes == sample_image_png
        assert isinstance(retrieved_image, Image.Image)
    
    def test_get_nonexistent_session(self):
        """Тест получения несуществующей сессии."""
        result = get_session_image("nonexistent-session-id")
        assert result is None
    
    def test_session_last_accessed_updated(self, sample_image_png):
        """Тест обновления last_accessed при получении сессии."""
        session_id = generate_session_id()
        image = Image.open(io.BytesIO(sample_image_png))
        
        save_session_image(session_id, sample_image_png, image)
        initial_time = sessions[session_id]["last_accessed"]
        
        # Ждем немного
        import time
        time.sleep(0.1)
        
        get_session_image(session_id)
        updated_time = sessions[session_id]["last_accessed"]
        
        assert updated_time > initial_time
    
    def test_cleanup_expired_sessions(self, sample_image_png):
        """Тест очистки истекших сессий."""
        session_id1 = generate_session_id()
        session_id2 = generate_session_id()
        image = Image.open(io.BytesIO(sample_image_png))
        
        # Сохраняем две сессии
        save_session_image(session_id1, sample_image_png, image)
        save_session_image(session_id2, sample_image_png, image)
        
        # Делаем одну сессию истекшей
        sessions[session_id1]["last_accessed"] = datetime.now() - timedelta(seconds=3700)
        
        # Очищаем с таймаутом 3600 секунд
        cleanup_expired_sessions(3600)
        
        # Первая сессия должна быть удалена, вторая - нет
        assert session_id1 not in sessions
        assert session_id2 in sessions


class TestImageToBase64:
    """Тесты для конвертации изображения в base64."""
    
    def test_image_to_base64_png(self, sample_image_png):
        """Тест конвертации PNG в base64."""
        image = Image.open(io.BytesIO(sample_image_png))
        base64_str = image_to_base64(image, format="PNG")
        
        assert isinstance(base64_str, str)
        # Декодируем обратно и проверяем
        decoded = base64.b64decode(base64_str)
        assert len(decoded) > 0
    
    def test_image_to_base64_jpeg(self, sample_image_jpeg):
        """Тест конвертации JPEG в base64."""
        image = Image.open(io.BytesIO(sample_image_jpeg))
        base64_str = image_to_base64(image, format="JPEG")
        
        assert isinstance(base64_str, str)
        decoded = base64.b64decode(base64_str)
        assert len(decoded) > 0


class TestOCRResults:
    """Тесты для управления результатами OCR."""
    
    def setup_method(self):
        """Очистка перед каждым тестом."""
        ocr_results.clear()
    
    def test_save_ocr_result(self):
        """Тест сохранения результата OCR."""
        text = "Sample OCR text"
        task_id = save_ocr_result(text)
        
        assert isinstance(task_id, str)
        assert len(task_id) > 0
        assert task_id in ocr_results
        assert ocr_results[task_id]["text"] == text
        assert "created_at" in ocr_results[task_id]
    
    def test_get_ocr_result(self):
        """Тест получения результата OCR."""
        text = "Sample OCR text"
        task_id = save_ocr_result(text)
        
        result = get_ocr_result(task_id)
        assert result == text
    
    def test_get_nonexistent_ocr_result(self):
        """Тест получения несуществующего результата OCR."""
        result = get_ocr_result("nonexistent-task-id")
        assert result is None
    
    def test_cleanup_expired_ocr_results(self):
        """Тест очистки истекших результатов OCR."""
        task_id1 = save_ocr_result("Text 1")
        task_id2 = save_ocr_result("Text 2")
        
        # Делаем один результат истекшим
        ocr_results[task_id1]["created_at"] = datetime.now() - timedelta(seconds=3700)
        
        # Очищаем с таймаутом 3600 секунд
        cleanup_expired_ocr_results(3600)
        
        # Первый результат должен быть удален, второй - нет
        assert task_id1 not in ocr_results
        assert task_id2 in ocr_results

