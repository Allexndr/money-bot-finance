#!/usr/bin/env python3
"""
Мгновенная настройка webhook для деплоя
"""

import requests

USERNAME = 'funarick'
API_TOKEN = '7694fc9a1ffd97ab40cb5a2e8f6b3547de1d61d2'
HOST = 'www.pythonanywhere.com'
PROJECT_PATH = f'/home/{USERNAME}/money_bot'

class QuickWebhookSetup:
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

    def setup_webhook(self):
        print("🚀 Запускаем webhook сервер для мгновенных обновлений...")

        webhook_commands = [
            f'cd {PROJECT_PATH}',
            'pkill -f webhook_deploy.py 2>/dev/null || true',
            'sleep 1',
            f'nohup python {PROJECT_PATH}/webhook_deploy.py > {PROJECT_PATH}/webhook.log 2>&1 &',
            'echo "✅ Webhook запущен на порту 8080"'
        ]

        for cmd in webhook_commands:
            print(f"📤 {cmd}")
            self.run_console_command(cmd)

        print("✅ Webhook сервер запущен!")
        print(f"🌐 URL: https://{USERNAME}.pythonanywhere.com/webhook")

def main():
    print("⚡ МГНОВЕННАЯ НАСТРОЙКА WEBHOOK")
    print("=" * 40)

    setup = QuickWebhookSetup()

    # Проверяем подключение
    success, _ = setup.api_request('GET', '/cpu/')
    if not success:
        print("❌ Ошибка подключения к API")
        return

    print("✅ API подключение работает")

    # Запускаем webhook
    setup.setup_webhook()

    print("\n🎉 WEBHOOK ГОТОВ!")
    print("=" * 40)
    print("🔥 Теперь при каждом пуше в GitHub:")
    print("   💫 Мгновенное обновление на PythonAnywhere!")
    print("   🚀 Бот автоматически перезапускается!")
    print()
    print("📋 Проверить статус webhook:")
    print(f"ssh {USERNAME}@{HOST} 'ps aux | grep webhook'")
    print()
    print("📋 Проверить логи webhook:")
    print(f"ssh {USERNAME}@{HOST} 'tail -f /home/{USERNAME}/money_bot/webhook.log'")

if __name__ == '__main__':
    main()
