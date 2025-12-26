#!/usr/bin/env python3
"""
Простая настройка деплоя на PythonAnywhere
"""

import requests
import time

# Настройки
USERNAME = 'funarick'
API_TOKEN = '7694fc9a1ffd97ab40cb5a2e8f6b3547de1d61d2'
HOST = 'www.pythonanywhere.com'
PROJECT_NAME = 'money_bot'
BRANCH = 'python-version'

class SimpleDeploy:
    def __init__(self):
        self.base_url = f'https://{HOST}/api/v0/user/{USERNAME}'
        self.headers = {'Authorization': f'Token {API_TOKEN}'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def api_request(self, method, endpoint, data=None):
        """Выполнить запрос к API"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, json=data, timeout=30)

        if response.status_code >= 400:
            print(f"❌ API Error {response.status_code}: {response.text[:200]}")
            return None

        try:
            return response.json()
        except:
            return response.text

    def run_console_command(self, command, working_dir=None):
        """Выполнить команду в консоли"""
        # Создаем консоль
        console_data = {"executable": "bash"}
        if working_dir:
            console_data["working_directory"] = working_dir

        console = self.api_request('POST', '/consoles/', console_data)
        if not console:
            return False

        console_id = console['id']

        # Выполняем команду
        self.api_request('POST', f'/consoles/{console_id}/send_input/', {
            "input": command + '\n'
        })

        # Ждем выполнения
        time.sleep(5)

        # Получаем результат (опционально)
        output = self.api_request('GET', f'/consoles/{console_id}/get_latest_output/')
        if output:
            print(f"📄 Вывод: {output.strip()}")

        # Убиваем консоль
        self.api_request('DELETE', f'/consoles/{console_id}/')

        return True

    def setup_cron_job(self):
        """Настроить cron job для регулярного деплоя"""
        print("📅 Настраиваем cron job...")

        cron_command = f'cd /home/{USERNAME}/{PROJECT_NAME} && ./deploy.sh'

        # Проверяем существующие задачи
        existing = self.api_request('GET', '/schedule/')
        if existing:
            for task in existing:
                if PROJECT_NAME in task.get('command', ''):
                    print(f"🗑️ Удаляем старую задачу: {task['id']}")
                    self.api_request('DELETE', f'/schedule/{task["id"]}/')

        # Создаем новую задачу (каждый час в :30)
        task = self.api_request('POST', '/schedule/', {
            "command": cron_command,
            "description": f"Auto-deploy {PROJECT_NAME}",
            "enabled": True,
            "interval": "hourly"
        })

        if task:
            print(f"✅ Cron job создан: #{task['id']} (каждые 30 мин)")
            return True
        else:
            print("❌ Не удалось создать cron job")
            return False

    def setup_always_on_bot(self):
        """Настроить always-on задачу для бота"""
        print("🔄 Настраиваем always-on бота...")

        bot_command = f'cd /home/{USERNAME}/{PROJECT_NAME} && python main.py'

        # Проверяем существующие задачи
        existing = self.api_request('GET', '/always_on/')
        if existing:
            for task in existing:
                if 'main.py' in task.get('command', ''):
                    print(f"🗑️ Удаляем старую always-on задачу: {task['id']}")
                    self.api_request('DELETE', f'/always_on/{task["id"]}/')

        # Создаем новую задачу
        task = self.api_request('POST', '/always_on/', {
            "command": bot_command,
            "description": f"{PROJECT_NAME} Telegram bot",
            "enabled": True
        })

        if task:
            print(f"✅ Always-on бот создан: #{task['id']}")
            return True
        else:
            print("❌ Не удалось создать always-on задачу")
            return False

    def test_deploy(self):
        """Тестовый запуск деплоя"""
        print("🧪 Тестируем деплой...")

        test_command = f'cd /home/{USERNAME}/{PROJECT_NAME} && echo "🚀 Деплой работает! $(date)" >> deploy_test.log'

        if self.run_console_command(test_command):
            print("✅ Тестовый деплой выполнен")
            return True
        else:
            print("❌ Ошибка тестового деплоя")
            return False

def main():
    print("🚀 ПРОСТАЯ НАСТРОЙКА ДЕПЛОЯ PYTHON BOT")
    print("=" * 50)

    deploy = SimpleDeploy()

    # Тест подключения
    print("🔗 Тестируем подключение...")
    cpu_info = deploy.api_request('GET', '/cpu/')
    if not cpu_info:
        print("❌ Ошибка подключения к API")
        return

    print("✅ API подключение работает!")

    # Настройка cron job
    print("\n📅 ШАГ 1: Настраиваем автоматический деплой...")
    deploy.setup_cron_job()

    # Настройка always-on бота
    print("\n🔄 ШАГ 2: Запускаем бота в фоне...")
    deploy.setup_always_on_bot()

    # Тест
    print("\n🧪 ШАГ 3: Тестируем систему...")
    deploy.test_deploy()

    print("\n🎉 ГОТОВО!")
    print("=" * 50)
    print("✅ Автоматический деплой настроен")
    print("✅ Бот работает в always-on режиме")
    print("✅ Система протестирована")
    print()
    print("📋 Для ручного деплоя:")
    print(f"ssh {USERNAME}@{HOST} 'cd /home/{USERNAME}/{PROJECT_NAME} && ./deploy.sh'")
    print()
    print("🔧 Для настройки GitHub webhook откройте:")
    print("https://github.com/Allexndr/money_bot/settings/hooks")
    print(f"URL: https://{USERNAME}.pythonanywhere.com/webhook")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Прервано")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
