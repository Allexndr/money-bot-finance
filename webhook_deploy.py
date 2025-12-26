#!/usr/bin/env python3
"""
Webhook endpoint для автоматического деплоя от GitHub
Запустите: python webhook_deploy.py
"""

import json
import hmac
import hashlib
from flask import Flask, request, jsonify
import subprocess
import os
from datetime import datetime

app = Flask(__name__)

# Настройки
GITHUB_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-webhook-secret')  # Секрет из GitHub
PROJECT_PATH = '/home/your-username/money_bot'  # Путь к проекту

def verify_signature(payload, signature):
    """Проверка подписи GitHub webhook"""
    if not GITHUB_SECRET:
        return True  # Для тестирования без секрета

    expected_signature = hmac.new(
        GITHUB_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected_signature}', signature)

def run_deploy():
    """Выполнить деплой"""
    print(f"🚀 [{datetime.now()}] Начинаем деплой...")

    try:
        # Переход в директорию проекта
        os.chdir(PROJECT_PATH)

        # Git pull
        print("📥 Git pull...")
        result = subprocess.run(['git', 'pull', 'origin', 'python-version'],
                              capture_output=True, text=True, timeout=60)
        print(f"Git: {result.stdout.strip()}")

        # Обновление зависимостей
        print("📦 Обновление зависимостей...")
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt', '--quiet'],
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ Ошибка установки зависимостей: {result.stderr}")

        # Перезапуск бота
        print("🔄 Перезапуск бота...")
        subprocess.run(['pkill', '-f', 'python.*main.py'], timeout=10)

        # Небольшая задержка
        import time
        time.sleep(2)

        # Запуск нового бота
        subprocess.Popen(['python', 'main.py'],
                        stdout=open('bot.log', 'a'),
                        stderr=subprocess.STDOUT)

        print("✅ Деплой завершен успешно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка деплоя: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Обработчик GitHub webhook"""

    # Получение данных
    payload = request.get_data()
    signature = request.headers.get('X-Hub-Signature-256')

    # Проверка подписи (опционально)
    if not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    # Парсинг JSON
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Проверка типа события
    event_type = request.headers.get('X-GitHub-Event')
    if event_type != 'push':
        return jsonify({'message': f'Ignored {event_type} event'}), 200

    # Проверка ветки
    ref = data.get('ref')
    if ref != 'refs/heads/python-version':
        return jsonify({'message': f'Ignored push to {ref}'}), 200

    # Выполнение деплоя
    success = run_deploy()

    if success:
        return jsonify({'message': 'Deploy completed successfully'}), 200
    else:
        return jsonify({'error': 'Deploy failed'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'project': PROJECT_PATH
    })

if __name__ == '__main__':
    print("🎣 Запуск webhook сервера...")
    print(f"📁 Проект: {PROJECT_PATH}")
    print("🌐 Слушаем на http://0.0.0.0:8080")
    print("📡 Webhook endpoint: POST /webhook")
    print("💚 Health check: GET /health")

    app.run(host='0.0.0.0', port=8080, debug=False)
