"""
FastAPI приложение для SmolVLM2 Web Demo.
Предоставляет API endpoints для VQA и OCR.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
import asyncio

from app.config import settings
from app.schemas import (
    VQARequest, VQAResponse, OCRRequest, OCRResponse,
    ErrorResponse, HealthResponse
)
from app.validators import validate_base64_image, validate_language, ValidationError
from app.utils import (
    generate_session_id, save_session_image, get_session_image,
    save_ocr_result, get_ocr_result, cleanup_expired_sessions,
    cleanup_expired_ocr_results
)
from app.model_manager import ModelManager

app = FastAPI(
    title="SmolVLM2 Web Demo API",
    description="API для демонстрации возможностей мультимодальной модели SmolVLM2",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = "/app/frontend"
if not os.path.exists(static_dir):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir, html=False), name="static")

model_manager = ModelManager()


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    asyncio.create_task(load_model_async())
    asyncio.create_task(periodic_cleanup())


async def load_model_async():
    """Асинхронная загрузка модели."""
    try:
        model_manager.load_model()
        print("Модель успешно загружена")
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")


async def periodic_cleanup():
    """Периодическая очистка истекших сессий и OCR результатов."""
    while True:
        await asyncio.sleep(300)
        try:
            cleanup_expired_sessions(settings.SESSION_TIMEOUT)
            cleanup_expired_ocr_results(settings.SESSION_TIMEOUT)
        except Exception as e:
            print(f"Ошибка при очистке: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Отдает frontend HTML страницу."""
    frontend_path = os.path.join(static_dir, "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Multimodal Demo</h1><p>Frontend не найден</p>"


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model_manager.is_loaded() else "loading",
        model_loaded=model_manager.is_loaded(),
        device=settings.DEVICE
    )


@app.post("/api/vqa", response_model=VQAResponse)
async def vqa(request: VQARequest):
    """
    Visual Question Answering endpoint.
    Принимает изображение и вопрос, возвращает ответ модели.
    """
    try:
        image_bytes, image = validate_base64_image(request.image)
        
        session_id = request.session_id
        if session_id:
            existing = get_session_image(session_id)
            if existing:
                image_bytes, image = existing
            else:
                save_session_image(session_id, image_bytes, image)
        else:
            session_id = generate_session_id()
            save_session_image(session_id, image_bytes, image)
        
        try:
            answer = model_manager.vqa_inference(image, request.question)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="INFERENCE_ERROR",
                    message=f"Ошибка при обработке модели: {str(e)}",
                    code="MODEL_ERROR"
                ).dict()
            )
        
        return VQAResponse(
            answer=answer,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=e.error,
                message=e.message,
                code=e.code
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message=f"Внутренняя ошибка сервера: {str(e)}",
                code="SERVER_ERROR"
            ).dict()
        )


@app.post("/api/ocr", response_model=OCRResponse)
async def ocr(request: OCRRequest):
    """
    OCR endpoint.
    Извлекает текст из изображения.
    """
    try:
        image_bytes, image = validate_base64_image(request.image)
        language = validate_language(request.language)
        
        try:
            text = model_manager.ocr_inference(image)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="OCR_ERROR",
                    message=f"Ошибка при распознавании текста: {str(e)}",
                    code="OCR_ERROR"
                ).dict()
            )
        
        task_id = save_ocr_result(text)
        download_url = f"/api/download/ocr/{task_id}"
        
        return OCRResponse(
            text=text,
            download_url=download_url,
            task_id=task_id
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=e.error,
                message=e.message,
                code=e.code
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message=f"Внутренняя ошибка сервера: {str(e)}",
                code="SERVER_ERROR"
            ).dict()
        )


@app.get("/api/download/ocr/{task_id}")
async def download_ocr(task_id: str):
    """
    Скачивание результата OCR в виде .txt файла.
    """
    text = get_ocr_result(task_id)
    
    if text is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="NOT_FOUND",
                message="Результат OCR не найден или истек",
                code="TASK_NOT_FOUND"
            ).dict()
        )
    
    from io import BytesIO
    file_content = BytesIO(text.encode("utf-8"))
    
    return Response(
        content=file_content.getvalue(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="ocr_result_{task_id}.txt"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS
    )

