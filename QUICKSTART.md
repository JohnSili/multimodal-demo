# Быстрый запуск SmolVLM2 Web Demo

## Вариант 1: Запуск через Docker Compose (рекомендуется)

### 1. Создайте файл `.env`:

```bash
cp .env.example .env
```

При необходимости отредактируйте `.env` под свои нужды.

### 2. Запустите приложение:

```bash
docker-compose up -d
```

### 3. Откройте в браузере:

```
http://localhost:8000
```

### 4. Остановка:

```bash
docker-compose down
```

### 5. Просмотр логов:

```bash
docker-compose logs -f
```

---

## Вариант 2: Локальный запуск (для разработки)

### 1. Создайте виртуальное окружение:

```bash
cd backend
uv venv
```

### 2. Активируйте окружение:

```bash
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

### 3. Установите зависимости:

```bash
uv pip install -r requirements.txt
```

### 4. Создайте `.env` файл в корне проекта:

```bash
cd ..
cp .env.example .env
```

### 5. Запустите сервер:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Откройте в браузере:

```
http://localhost:8000
```

---

## Проверка работоспособности

### Health check:

```bash
curl http://localhost:8000/api/health
```

### Тесты:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
```

---

## Важные замечания

1. **Первая загрузка модели**: При первом запуске модель будет автоматически загружена из HuggingFace Hub. Это может занять 2-5 минут в зависимости от скорости интернета.

2. **Память**: Убедитесь, что у вас достаточно памяти:
   - CPU версия: минимум 8GB RAM
   - GPU версия: минимум 6GB VRAM

3. **GPU поддержка**: Для использования GPU:
   - Установите NVIDIA Docker
   - Раскомментируйте секцию `deploy` в `docker-compose.yml`
   - Установите `DEVICE=cuda` в `.env`

4. **Модели**: Веса моделей сохраняются в папке `./models` и не будут загружаться повторно при следующих запусках.

---

## Troubleshooting

### Проблемы с памятью:
- Уменьшите `TORCH_DTYPE` до `float16` в `.env`
- Уменьшите `MAX_IMAGE_DIMENSION`

### Медленная работа:
- Используйте GPU версию
- Уменьшите разрешение изображений

### Ошибки загрузки модели:
- Проверьте подключение к интернету
- Проверьте права доступа к папке `./models`

