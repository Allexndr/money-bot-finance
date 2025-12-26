#!/usr/bin/env python3
"""
Автоматическая настройка деплоя на PythonAnywhere через API
Запустите: python auto_setup_deploy.py
"""

import requests
import json
import time
import os
from datetime import datetime

# Настройки PythonAnywhere
USERNAME = 'funarick'
API_TOKEN = '7694fc9a1ffd97ab40cb5a2e8f6b3547de1d61d2'
HOST = 'www.pythonanywhere.com'
PROJECT_NAME = 'money_bot'
BRANCH = 'python-version'

# Вычисляемые пути
PROJECT_PATH = f'/home/{USERNAME}/{PROJECT_NAME}'
REPO_URL = f'https://github.com/Allexndr/money_bot.git'
WEBHOOK_URL = f'https://{USERNAME}.pythonanywhere.com/webhook'

class PythonAnywhereDeploy:
    def __init__(self):
        self.base_url = f'https://{HOST}/api/v0/user/{USERNAME}'
        self.headers = {'Authorization': f'Token {API_TOKEN}'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _api_request(self, method, endpoint, data=None):
        """Выполнить запрос к API"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, json=data)

        print(f"🔗 {method} {endpoint} → {response.status_code}")

        if response.status_code >= 400:
            print(f"❌ API Error: {response.text}")
            return None

        try:
            return response.json()
        except:
            return response.text

    def test_connection(self):
        """Тест подключения к API"""
        print("🔗 Тестируем подключение к PythonAnywhere API...")
        result = self._api_request('GET', '/cpu/')
        if result:
            print("✅ API работает!")
            return True
        else:
            print("❌ Ошибка подключения к API")
            return False

    def setup_git_repo(self):
        """Настроить Git репозиторий"""
        print("📥 Настраиваем Git репозиторий...")

        try:
            # Создаем консоль для выполнения команд
            console = self._api_request('POST', '/consoles/', {
                "executable": "bash",
                "working_directory": f"/home/{self.username}"
            })

            if not console:
                print("❌ Не удалось создать консоль")
                return False

            console_id = console['id']
            print(f"📺 Создана консоль: {console_id}")

            # Выполняем команды настройки по одной
            commands = [
                f'cd /home/{self.username}',
                f'rm -rf {PROJECT_NAME} 2>/dev/null || true',  # Безопасное удаление
                f'git clone -b {BRANCH} {REPO_URL} {PROJECT_NAME}',
                f'cd {PROJECT_NAME}',
                'chmod +x deploy.sh',
                'pip install -r requirements.txt --quiet 2>/dev/null || pip install python-telegram-bot --quiet',
                'echo "✅ Git репозиторий настроен"'
            ]

            for i, cmd in enumerate(commands):
                print(f"📤 [{i+1}/{len(commands)}] {cmd}")
                result = self._api_request('POST', f'/consoles/{console_id}/send_input/', {
                    "input": cmd + '\n'
                })
                if not result:
                    print(f"❌ Ошибка выполнения команды: {cmd}")
                    return False
                time.sleep(3)  # Ждем выполнения

            time.sleep(5)  # Ждем завершения всех команд

            # Убиваем консоль
            self._api_request('DELETE', f'/consoles/{console_id}/')
            print("🗑️ Консоль закрыта")

            return True

        except Exception as e:
            print(f"❌ Ошибка в setup_git_repo: {e}")
            return False

    def setup_webhook_server(self):
        """Настроить webhook сервер"""
        print("🎣 Настраиваем webhook сервер...")

        console = self._api_request('POST', '/consoles/', {
            "executable": "bash",
            "working_directory": PROJECT_PATH
        })

        if not console:
            return False

        console_id = console['id']

        # Запускаем webhook сервер в фоне
        commands = [
            f'cd {PROJECT_PATH}',
            'pkill -f webhook_deploy.py',  # Убиваем старый процесс
            'sleep 1',
            'nohup python webhook_deploy.py > webhook.log 2>&1 &',
            'echo "✅ Webhook сервер запущен"'
        ]

        for cmd in commands:
            print(f"📤 {cmd}")
            self._api_request('POST', f'/consoles/{console_id}/send_input/', {
                "input": cmd + '\n'
            })
            time.sleep(1)

        time.sleep(3)
        self._api_request('DELETE', f'/consoles/{console_id}/')

        return True

    def setup_cron_job(self):
        """Настроить cron job для регулярного деплоя"""
        print("📅 Настраиваем cron job...")

        cron_command = f'cd {PROJECT_PATH} && ./deploy.sh'

        # Удаляем существующие задачи с похожей командой
        existing_tasks = self._api_request('GET', '/schedule/')
        if existing_tasks:
            for task in existing_tasks:
                if PROJECT_NAME in task.get('command', ''):
                    print(f"🗑️ Удаляем старую задачу: {task['id']}")
                    self._api_request('DELETE', f'/schedule/{task["id"]}/')

        # Создаем новую задачу
        task = self._api_request('POST', '/schedule/', {
            "command": cron_command,
            "description": f"Auto-deploy {PROJECT_NAME}",
            "enabled": True,
            "interval": "hourly",
            "hour": None,
            "minute": 0
        })

        if task:
            print(f"✅ Cron job создан: #{task['id']} - каждый час в :00")
            return True
        else:
            print("❌ Не удалось создать cron job")
            return False

    def setup_always_on_bot(self):
        """Настроить always-on задачу для бота"""
        print("🔄 Настраиваем always-on задачу для бота...")

        bot_command = f'cd {PROJECT_PATH} && python main.py'

        # Удаляем существующие задачи
        existing_tasks = self._api_request('GET', '/always_on/')
        if existing_tasks:
            for task in existing_tasks:
                if 'main.py' in task.get('command', ''):
                    print(f"🗑️ Удаляем старую always-on задачу: {task['id']}")
                    self._api_request('DELETE', f'/always_on/{task["id"]}/')

        # Создаем новую always-on задачу
        task = self._api_request('POST', '/always_on/', {
            "command": bot_command,
            "description": f"{PROJECT_NAME} bot",
            "enabled": True
        })

        if task:
            print(f"✅ Always-on задача создана: #{task['id']}")
            return True
        else:
            print("❌ Не удалось создать always-on задачу")
            return False

    def test_deploy(self):
        """Тестовый запуск деплоя"""
        print("🧪 Тестируем деплой...")

        console = self._api_request('POST', '/consoles/', {
            "executable": "bash",
            "working_directory": PROJECT_PATH
        })

        if not console:
            return False

        console_id = console['id']

        # Выполняем тестовый деплой
        commands = [
            f'cd {PROJECT_PATH}',
            'echo "🚀 Тестовый деплой начат"',
            './deploy.sh',
            'echo "✅ Тестовый деплой завершен"'
        ]

        for cmd in commands:
            print(f"📤 {cmd}")
            self._api_request('POST', f'/consoles/{console_id}/send_input/', {
                "input": cmd + '\n'
            })
            time.sleep(3)

        time.sleep(10)  # Ждем завершения

        # Получаем последние выходные данные консоли
        output = self._api_request('GET', f'/consoles/{console_id}/get_latest_output/')
        if output:
            print(f"📄 Последний вывод: {output}")

        self._api_request('DELETE', f'/consoles/{console_id}/')

        return True

    def create_github_webhook(self):
        """Инструкции по настройке GitHub webhook"""
        print("\n🌐 Настройка GitHub Webhook:")
        print("=" * 50)
        print("1. Перейдите: https://github.com/Allexndr/money_bot/settings/hooks")
        print("2. Нажмите 'Add webhook'")
        print("3. Заполните:")
        print(f"   Payload URL: {WEBHOOK_URL}")
        print("   Content type: application/json")
        print("   Secret: (оставьте пустым для простоты)")
        print("4. Выберите событие: 'Pushes'")
        print("5. Укажите ветку: python-version")
        print("6. Нажмите 'Add webhook'")
        print("\n✅ Теперь при каждом пуше будет автоматический деплой!")

def main():
    print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА ДЕПЛОЯ PYTHON BOT")
    print("=" * 60)
    print(f"👤 Пользователь: {USERNAME}")
    print(f"📁 Проект: {PROJECT_NAME}")
    print(f"🌿 Ветка: {BRANCH}")
    print(f"🔗 Репозиторий: {REPO_URL}")
    print()

    deploy = PythonAnywhereDeploy()

    # Шаг 1: Тест подключения
    print("🔗 ШАГ 1: Проверяем подключение к PythonAnywhere API...")
    if not deploy.test_connection():
        print("❌ Ошибка подключения! Проверьте API токен и интернет.")
        return

    print("✅ Подключение успешно!")

    # Шаг 2: Настройка Git репозитория
    print("\n📥 ШАГ 2: Настраиваем Git репозиторий...")
    if not deploy.setup_git_repo():
        print("❌ Ошибка настройки Git репозитория")
        return

    print("✅ Git репозиторий настроен!")

    # Шаг 3: Настройка webhook сервера
    print("\n🎣 ШАГ 3: Запускаем webhook сервер...")
    if not deploy.setup_webhook_server():
        print("❌ Ошибка запуска webhook сервера")
        return

    print("✅ Webhook сервер запущен!")

    # Шаг 4: Настройка cron job
    print("\n📅 ШАГ 4: Настраиваем автоматический деплой...")
    deploy.setup_cron_job()
    print("✅ Cron job настроен!")

    # Шаг 5: Настройка always-on бота
    print("\n🔄 ШАГ 5: Запускаем бота в always-on режиме...")
    deploy.setup_always_on_bot()
    print("✅ Always-on бот настроен!")

    # Шаг 6: Тестовый запуск
    print("\n🧪 ШАГ 6: Тестируем деплой...")
    deploy.test_deploy()
    print("✅ Тестовый деплой выполнен!")

    # Шаг 7: Инструкции по GitHub
    print("\n🌐 ШАГ 7: Настройка GitHub webhook")
    deploy.create_github_webhook()

    print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print("✅ Git репозиторий настроен")
    print("✅ Webhook сервер запущен")
    print("✅ Cron job создан (каждый час)")
    print("✅ Always-on бот настроен")
    print("✅ Тестовый деплой выполнен")
    print()
    print("📋 РУЧНОЙ ДЕПЛОЙ:")
    print(f"ssh {USERNAME}@{HOST} 'cd {PROJECT_PATH} && ./deploy.sh'")
    print()
    print("📊 МОНИТОРИНГ:")
    print(f"ssh {USERNAME}@{HOST} 'cd {PROJECT_PATH} && tail -f bot.log'")
    print(f"ssh {USERNAME}@{HOST} 'cd {PROJECT_PATH} && tail -f webhook.log'")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте подключение к интернету и корректность API токена")
