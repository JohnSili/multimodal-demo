# Настройка GPU для SmolVLM2

## Требования

- NVIDIA GPU с поддержкой CUDA
- NVIDIA Docker runtime установлен
- Docker Compose v2

## Проверка установки NVIDIA Docker

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

Если команда выполняется успешно, NVIDIA Docker установлен правильно.

## Запуск на GPU

### Способ 1: Использование docker-compose.gpu.yml

1. Создайте файл `.env`:
   ```bash
   DEVICE=cuda
   TORCH_DTYPE=bfloat16
   MODEL_NAME=HuggingFaceTB/SmolVLM2-2.2B-Instruct
   ```

2. Запустите с GPU compose файлом:
   ```bash
   docker-compose -f docker-compose.gpu.yml up -d
   ```

### Способ 2: Использование переменной окружения

1. Создайте файл `.env`:
   ```bash
   DEVICE=cuda
   TORCH_DTYPE=bfloat16
   ```

2. Запустите с указанием Dockerfile:
   ```bash
   DOCKERFILE=Dockerfile.gpu docker-compose up -d --build
   ```

## Рекомендуемые настройки для GPU

В файле `.env` установите:

```bash
DEVICE=cuda
TORCH_DTYPE=bfloat16  # или float16 для экономии памяти
```

Для моделей с большим количеством VRAM можно использовать `float32`, но это не рекомендуется.

## Проверка работы GPU

После запуска проверьте логи:

```bash
docker-compose logs -f smolvlm2-backend
```

Вы должны увидеть:
```
Модель загружена на cuda с dtype torch.bfloat16
```

Также можно проверить использование GPU:

```bash
nvidia-smi
```

## Устранение проблем

### Ошибка: "NVIDIA Docker runtime not found" или "libnvidia-ml.so.1: cannot open shared object file"

Установите NVIDIA Container Toolkit:

**Для Ubuntu/Debian (современный способ):**
```bash
# Добавление репозитория NVIDIA
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Установка
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Настройка Docker для использования NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Перезапуск Docker
sudo systemctl restart docker
```

**Проверка установки:**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

Если команда выполняется успешно, установка прошла правильно.

### Ошибка: "CUDA out of memory"

Уменьшите `TORCH_DTYPE` до `float16` или используйте меньшую модель.

### Модель не использует GPU

Проверьте:
1. `DEVICE=cuda` в `.env`
2. Используется правильный Dockerfile (Dockerfile.gpu)
3. NVIDIA Docker runtime установлен и работает

