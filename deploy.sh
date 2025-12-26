#!/bin/bash

# Скрипт для автоматизации деплоя на PythonAnywhere
echo "🚀 Начинаем деплой Python бота..."

# Переходим в директорию проекта (измените на свой путь)
cd /home/your-username/your-project || exit 1

# Получаем последние изменения
echo "📥 Получаем обновления из Git..."
git pull origin main

# Обновляем зависимости (если нужно)
echo "📦 Обновляем зависимости..."
pip install -r requirements.txt --quiet

# Перезапускаем бота
echo "🔄 Перезапускаем бота..."

# Убиваем старый процесс бота
pkill -f "python.*main.py" || echo "Старый процесс не найден"

# Ждем немного
sleep 2

# Запускаем нового бота
nohup python main.py > bot.log 2>&1 &

echo "✅ Деплой завершен! Бот перезапущен."
echo "📊 Проверьте логи: tail -f bot.log"
