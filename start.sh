#!/bin/bash

set -e

MODE="${1:-cpu}"

if [ "$MODE" = "gpu" ]; then
    echo "🚀 Запуск в режиме GPU..."
    docker-compose -f docker-compose.gpu.yml up -d --build
elif [ "$MODE" = "cpu" ]; then
    echo "🚀 Запуск в режиме CPU..."
    docker-compose up -d --build
else
    echo "❌ Неверный режим. Используйте: cpu или gpu"
    echo "Пример: ./start.sh cpu"
    echo "Пример: ./start.sh gpu"
    exit 1
fi

echo "✅ Приложение запущено!"
echo "🌐 Откройте в браузере: http://localhost:8000"
