"""
Тесты для API endpoints.
"""
import pytest
import base64
import io
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем путь к app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.utils import sessions, ocr_results


@pytest.fixture
def client():
    """Создает тестовый клиент FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Создает base64 строку тестового изображения."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@pytest.fixture(autouse=True)
def mock_model_manager(monkeypatch):
    """Мокирует ModelManager для всех тестов."""
    mock_manager = MagicMock()
    mock_manager.is_loaded.return_value = True
    mock_manager.vqa_inference.return_value = "This is a test image."
    mock_manager.ocr_inference.return_value = "Sample OCR text"
    
    # Мокируем model_manager в app.main
    import app.main
    monkeypatch.setattr(app.main, "model_manager", mock_manager)
    
    yield mock_manager


class TestHealthEndpoint:
    """Тесты для /api/health."""
    
    def test_health_check(self, client, mock_model_manager):
        """Тест health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "device" in data
        assert data["model_loaded"] is True


class TestVQAEndpoint:
    """Тесты для /api/vqa."""
    
    def setup_method(self):
        """Очистка перед каждым тестом."""
        sessions.clear()
    
    def test_vqa_with_question(self, client, sample_image_base64, mock_model_manager):
        """Тест VQA с вопросом."""
        response = client.post(
            "/api/vqa",
            json={
                "image": sample_image_base64,
                "question": "What is in this image?"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
        assert "timestamp" in data
        assert data["answer"] == "This is a test image."
        assert len(data["session_id"]) > 0
    
    def test_vqa_without_question(self, client, sample_image_base64, mock_model_manager):
        """Тест VQA без вопроса (image captioning)."""
        response = client.post(
            "/api/vqa",
            json={
                "image": sample_image_base64
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
    
    def test_vqa_with_session_id(self, client, sample_image_base64, mock_model_manager):
        """Тест VQA с существующей сессией."""
        # Первый запрос
        response1 = client.post(
            "/api/vqa",
            json={
                "image": sample_image_base64,
                "question": "First question"
            }
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Второй запрос с тем же session_id
        response2 = client.post(
            "/api/vqa",
            json={
                "image": sample_image_base64,  # Можно даже не отправлять, но для теста отправим
                "question": "Second question",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
    
    def test_vqa_invalid_image(self, client):
        """Тест VQA с невалидным изображением."""
        response = client.post(
            "/api/vqa",
            json={
                "image": "invalid_base64",
                "question": "Test question"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_vqa_empty_image(self, client):
        """Тест VQA с пустым изображением."""
        response = client.post(
            "/api/vqa",
            json={
                "image": "",
                "question": "Test question"
            }
        )
        assert response.status_code == 400
    
    def test_vqa_missing_image(self, client):
        """Тест VQA без изображения."""
        response = client.post(
            "/api/vqa",
            json={
                "question": "Test question"
            }
        )
        assert response.status_code == 422  # Validation error


class TestOCREndpoint:
    """Тесты для /api/ocr."""
    
    def setup_method(self):
        """Очистка перед каждым тестом."""
        ocr_results.clear()
    
    def test_ocr_success(self, client, sample_image_base64, mock_model_manager):
        """Тест успешного OCR."""
        response = client.post(
            "/api/ocr",
            json={
                "image": sample_image_base64,
                "language": "en"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "download_url" in data
        assert "task_id" in data
        assert data["text"] == "Sample OCR text"
        assert len(data["task_id"]) > 0
    
    def test_ocr_default_language(self, client, sample_image_base64, mock_model_manager):
        """Тест OCR с языком по умолчанию."""
        response = client.post(
            "/api/ocr",
            json={
                "image": sample_image_base64
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
    
    def test_ocr_invalid_image(self, client):
        """Тест OCR с невалидным изображением."""
        response = client.post(
            "/api/ocr",
            json={
                "image": "invalid_base64"
            }
        )
        assert response.status_code == 400
    
    def test_ocr_invalid_language(self, client, sample_image_base64):
        """Тест OCR с невалидным языком."""
        response = client.post(
            "/api/ocr",
            json={
                "image": sample_image_base64,
                "language": "fr"
            }
        )
        assert response.status_code == 400


class TestDownloadOCREndpoint:
    """Тесты для /api/download/ocr/{task_id}."""
    
    def setup_method(self):
        """Очистка перед каждым тестом."""
        ocr_results.clear()
    
    def test_download_ocr_success(self, client, sample_image_base64, mock_model_manager):
        """Тест успешного скачивания OCR результата."""
        # Сначала создаем OCR результат
        ocr_response = client.post(
            "/api/ocr",
            json={
                "image": sample_image_base64
            }
        )
        task_id = ocr_response.json()["task_id"]
        
        # Скачиваем результат
        response = client.get(f"/api/download/ocr/{task_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert task_id in response.headers["content-disposition"]
        assert response.text == "Sample OCR text"
    
    def test_download_nonexistent_task(self, client):
        """Тест скачивания несуществующего результата."""
        response = client.get("/api/download/ocr/nonexistent-task-id")
        assert response.status_code == 404


class TestRootEndpoint:
    """Тесты для корневого endpoint."""
    
    def test_root_endpoint(self, client):
        """Тест корневого endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

