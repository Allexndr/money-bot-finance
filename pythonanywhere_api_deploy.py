#!/usr/bin/env python3
"""
Скрипт для автоматизации деплоя на PythonAnywhere через API
"""

import requests
import json
import time
import os
from datetime import datetime

# Настройки - замените на свои данные
USERNAME = 'your-username'  # Ваш username на PythonAnywhere
API_TOKEN = os.getenv('API_TOKEN', 'your-api-token')  # API токен из Account → API Token
HOST = 'www.pythonanywhere.com'  # или 'eu.pythonanywhere.com' для EU сервера

# Настройки проекта
PROJECT_PATH = f'/home/{USERNAME}/money_bot'  # Путь к проекту
BOT_COMMAND = f'cd {PROJECT_PATH} && python main.py'  # Команда запуска бота

class PythonAnywhereAPI:
    def __init__(self, username, token, host='www.pythonanywhere.com'):
        self.username = username
        self.token = token
        self.host = host
        self.base_url = f'https://{host}/api/v0/user/{username}'
        self.headers = {'Authorization': f'Token {token}'}

    def _make_request(self, method, endpoint, data=None):
        """Выполнить запрос к API"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data)

        if response.status_code >= 400:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None

        return response.json()

    def list_scheduled_tasks(self):
        """Получить список запланированных задач"""
        return self._make_request('GET', '/schedule/')

    def create_scheduled_task(self, command, description="Auto-deploy", interval="daily", hour=2, minute=0):
        """Создать запланированную задачу"""
        data = {
            "command": command,
            "description": description,
            "enabled": True,
            "interval": interval,
            "hour": hour,
            "minute": minute
        }
        return self._make_request('POST', '/schedule/', data)

    def delete_scheduled_task(self, task_id):
        """Удалить запланированную задачу"""
        return self._make_request('DELETE', f'/schedule/{task_id}/')

    def list_consoles(self):
        """Получить список консолей"""
        return self._make_request('GET', '/consoles/')

    def create_console(self, executable='bash', arguments='', working_directory=None):
        """Создать новую консоль"""
        data = {
            "executable": executable,
            "arguments": arguments,
            "working_directory": working_directory or f'/home/{self.username}'
        }
        return self._make_request('POST', '/consoles/', data)

    def send_console_input(self, console_id, input_text):
        """Отправить команду в консоль"""
        data = {"input": input_text}
        return self._make_request('POST', f'/consoles/{console_id}/send_input/', data)

    def kill_console(self, console_id):
        """Завершить консоль"""
        return self._make_request('DELETE', f'/consoles/{console_id}/')

    def list_always_on_tasks(self):
        """Получить список always-on задач"""
        return self._make_request('GET', '/always_on/')

    def create_always_on_task(self, command, description="Bot"):
        """Создать always-on задачу"""
        data = {
            "command": command,
            "description": description,
            "enabled": True
        }
        return self._make_request('POST', '/always_on/', data)

    def restart_always_on_task(self, task_id):
        """Перезапустить always-on задачу"""
        return self._make_request('POST', f'/always_on/{task_id}/restart/')

    def delete_always_on_task(self, task_id):
        """Удалить always-on задачу"""
        return self._make_request('DELETE', f'/always_on/{task_id}/')

    def reload_webapp(self, domain_name):
        """Перезагрузить веб-приложение"""
        return self._make_request('POST', f'/webapps/{domain_name}/reload/')

def setup_auto_deploy(api):
    """Настроить автоматический деплой"""

    print("🚀 Настройка автоматического деплоя...")

    # 1. Создать скрипт деплоя на PythonAnywhere
    deploy_script = f'''#!/bin/bash
echo "$(date): Начинаем деплой..."

# Переход в директорию проекта
cd {PROJECT_PATH}

# Получение обновлений
echo "📥 Git pull..."
git pull origin python-version

# Обновление зависимостей
echo "📦 Обновление зависимостей..."
pip install -r requirements.txt --quiet

# Перезапуск бота
echo "🔄 Перезапуск бота..."
pkill -f "python.*main.py"
sleep 2
nohup python main.py > bot.log 2>&1 &

echo "✅ Деплой завершен!"
'''

    # 2. Создать cron job для автоматического деплоя
    print("📅 Создание cron job...")
    cron_command = f'bash -c \'{deploy_script}\''
    result = api.create_scheduled_task(
        command=cron_command,
        description="Auto-deploy bot every hour",
        interval="hourly",
        hour=None,
        minute=0
    )

    if result:
        print(f"✅ Cron job создан: {result}")
    else:
        print("❌ Не удалось создать cron job")

def deploy_now(api):
    """Выполнить деплой прямо сейчас через API"""

    print("🚀 Выполняем деплой через API...")

    # Создать консоль и выполнить команды
    console = api.create_console()

    if not console:
        print("❌ Не удалось создать консоль")
        return

    console_id = console['id']
    print(f"📺 Создана консоль: {console_id}")

    # Выполнить команды деплоя
    commands = [
        f'cd {PROJECT_PATH}',
        'echo "📥 Git pull..."',
        'git pull origin python-version',
        'echo "📦 Installing dependencies..."',
        'pip install -r requirements.txt --quiet',
        'echo "🔄 Restarting bot..."',
        'pkill -f "python.*main.py"',
        'sleep 2',
        'nohup python main.py > bot.log 2>&1 &',
        'echo "✅ Deploy completed!"',
        f'rm /tmp/console-{console_id}.log'  # Очистка
    ]

    for cmd in commands:
        print(f"📤 Выполняем: {cmd}")
        api.send_console_input(console_id, cmd + '\n')
        time.sleep(1)  # Небольшая задержка между командами

    # Ждем завершения
    time.sleep(5)

    # Убиваем консоль
    api.kill_console(console_id)
    print("🗑️ Консоль закрыта")

def main():
    print("🤖 PythonAnywhere Bot Deploy via API")
    print("=" * 50)

    # Инициализация API
    api = PythonAnywhereAPI(USERNAME, API_TOKEN, HOST)

    # Тест подключения
    print("🔗 Тестируем подключение...")
    tasks = api.list_scheduled_tasks()
    if tasks is not None:
        print(f"✅ API работает! Найдено {len(tasks)} запланированных задач")
    else:
        print("❌ Ошибка подключения к API")
        return

    while True:
        print("\nВыберите действие:")
        print("1. 🚀 Выполнить деплой сейчас")
        print("2. 📅 Настроить автоматический деплой (cron)")
        print("3. 📋 Показать запланированные задачи")
        print("4. 🔄 Перезапустить always-on задачу")
        print("5. ❌ Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == '1':
            deploy_now(api)
        elif choice == '2':
            setup_auto_deploy(api)
        elif choice == '3':
            tasks = api.list_scheduled_tasks()
            if tasks:
                print(f"\n📅 Запланированные задачи ({len(tasks)}):")
                for task in tasks:
                    print(f"  ID: {task['id']}, Command: {task['command'][:50]}...")
            else:
                print("📅 Нет запланированных задач")
        elif choice == '4':
            always_on = api.list_always_on_tasks()
            if always_on:
                print(f"\n🔄 Always-on задачи ({len(always_on)}):")
                for task in always_on:
                    print(f"  ID: {task['id']}, Command: {task['command']}")
                    if input("Перезапустить эту задачу? (y/n): ").lower() == 'y':
                        api.restart_always_on_task(task['id'])
                        print("✅ Задача перезапущена")
            else:
                print("🔄 Нет always-on задач")
        elif choice == '5':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")

if __name__ == '__main__':
    main()
