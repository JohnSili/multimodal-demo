# Настройка модели SmolVLM2

## Проблема с именем модели

Если вы получаете ошибку о том, что модель не найдена, это означает, что имя модели в `.env` файле неверное.

## Как найти правильное имя модели

1. Перейдите на https://huggingface.co/models
2. Поищите "SmolVLM2" или "SmolVLM"
3. Найдите правильное имя модели (формат: `organization/model-name`)

## Возможные варианты имени модели

Попробуйте следующие варианты в файле `.env`:

```bash
# Вариант 1
MODEL_NAME=microsoft/SmolVLM2-Instruct

# Вариант 2 (если первый не работает)
MODEL_NAME=SmolVLM2-Instruct

# Вариант 3
MODEL_NAME=HuggingFaceTB/SmolVLM2-Instruct

# Вариант 4 (альтернативная модель для тестирования)
MODEL_NAME=Salesforce/blip-image-captioning-base
```

## Обновление конфигурации

После изменения `.env` файла:

1. Перезапустите сервер:
```bash
pkill -f uvicorn
cd /home/danil/Documents/ProjectPTAI/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. Проверьте логи на наличие ошибок загрузки модели

## Альтернативные модели для тестирования

Если SmolVLM2 недоступна, можно использовать другие vision-language модели:

- `Salesforce/blip-image-captioning-base` - для image captioning
- `Salesforce/blip-vqa-base` - для VQA
- `microsoft/git-base` - для image captioning

**Важно:** При смене модели может потребоваться изменить код в `model_manager.py` для работы с другой архитектурой.

