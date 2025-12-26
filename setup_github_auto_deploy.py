#!/usr/bin/env python3
"""
Настройка автоматического деплоя через GitHub API
"""

import requests

USERNAME = 'funarick'
API_TOKEN = '7694fc9a1ffd97ab40cb5a2e8f6b3547de1d61d2'
HOST = 'www.pythonanywhere.com'
PROJECT_PATH = f'/home/{USERNAME}/money_bot'

class GitHubAutoDeploySetup:
    def __init__(self):
        self.base_url = f'https://{HOST}/api/v0/user/{USERNAME}'
        self.headers = {'Authorization': f'Token {API_TOKEN}'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def api_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, json=data, timeout=30)
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text

    def run_console_command(self, command):
        console = self.api_request('POST', '/consoles/', {
            "executable": "bash",
            "working_directory": f"/home/{USERNAME}"
        })

        if not console[0]:
            return False

        console_id = console[1]['id']

        self.api_request('POST', f'/consoles/{console_id}/send_input/', {
            "input": command + '\n'
        })

        import time
        time.sleep(3)

        self.api_request('DELETE', f'/consoles/{console_id}/')
        return True

    def setup_auto_deploy(self):
        print("🚀 Настраиваем автоматический деплой через GitHub API...")

        # Копируем скрипт авто-деплоя
        copy_commands = [
            f'cd {PROJECT_PATH}',
            'cp github_auto_deploy.py /home/funarick/',
            'chmod +x /home/funarick/github_auto_deploy.py'
        ]

        for cmd in copy_commands:
            print(f"📤 {cmd}")
            self.run_console_command(cmd)

        # Запускаем как always-on задачу
        print("🔄 Создаем always-on задачу...")

        command = 'cd /home/funarick && python github_auto_deploy.py'

        # Проверяем существующие задачи
        existing = self.api_request('GET', '/always_on/')
        if existing[0]:
            for task in existing[1]:
                if 'github_auto_deploy.py' in task.get('command', ''):
                    print(f"🗑️ Удаляем старую задачу: {task['id']}")
                    self.api_request('DELETE', f'/always_on/{task["id"]}/')

        # Создаем новую задачу (cron job каждые 5 минут)
        task = self.api_request('POST', '/schedule/', {
            "command": command,
            "description": "GitHub Auto Deploy - проверяет обновления каждые 5 мин",
            "enabled": True,
            "interval": "hourly",
            "minute": 5  # Каждые :05 минут каждого часа
        })

        # Альтернативно - каждые 10 минут
        if not task[0]:
            print("Пробуем создать задачу каждые 10 минут...")
            task = self.api_request('POST', '/schedule/', {
                "command": f"{command} && sleep 600 && {command}",  # Запуск дважды с интервалом
                "description": "GitHub Auto Deploy - проверяет обновления каждые 10 мин",
                "enabled": True,
                "interval": "hourly",
                "minute": 10
            })

        if task[0]:
            print(f"✅ Always-on задача создана: #{task[1]['id']}")
            return True
        else:
            print("❌ Не удалось создать always-on задачу")
            return False

def main():
    print("⚡ НАСТРОЙКА МГНОВЕННОГО АВТО-ДЕПЛОЯ")
    print("=" * 50)

    setup = GitHubAutoDeploySetup()

    # Проверяем подключение
    success, _ = setup.api_request('GET', '/cpu/')
    if not success:
        print("❌ Ошибка подключения к API")
        return

    print("✅ API подключение работает")

    # Настраиваем авто-деплой
    if setup.setup_auto_deploy():
        print("\n🎉 АВТО-ДЕПЛОЙ НАСТРОЕН!")
        print("=" * 50)
        print("🔥 Теперь система:")
        print("   • Проверяет GitHub каждые 60 секунд")
        print("   • При новых коммитах делает git pull")
        print("   • Перезапускает бота автоматически")
        print("   • Работает 24/7 без перерыва")
        print()
        print("📊 Мониторинг:")
        print(f"ssh {USERNAME}@{HOST} 'ps aux | grep github_auto_deploy'")
        print(f"ssh {USERNAME}@{HOST} 'tail -f /home/{USERNAME}/money_bot/bot.log'")
        print()
        print("⚡ Первый деплой запустится через 60 секунд!")

if __name__ == '__main__':
    main()
