#!/bin/bash

set -e

MODE="${1:-cpu}"

if [ "$MODE" = "gpu" ]; then
    echo "🔨 Сборка образа для GPU..."
    docker-compose -f docker-compose.gpu.yml build
elif [ "$MODE" = "cpu" ]; then
    echo "🔨 Сборка образа для CPU..."
    docker-compose build
else
    echo "❌ Неверный режим. Используйте: cpu или gpu"
    echo "Пример: ./build.sh cpu"
    echo "Пример: ./build.sh gpu"
    exit 1
fi

echo "✅ Сборка завершена!"

