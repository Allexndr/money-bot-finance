#!/usr/bin/env python3
"""
Тестовый скрипт для проверки PythonAnywhere API
"""

import requests

# Настройки
USERNAME = 'funarick'
API_TOKEN = '7694fc9a1ffd97ab40cb5a2e8f6b3547de1d61d2'
HOST = 'www.pythonanywhere.com'

def test_api():
    """Простой тест API"""
    base_url = f'https://{HOST}/api/v0/user/{USERNAME}'
    headers = {'Authorization': f'Token {API_TOKEN}'}

    print("🔗 Тестируем PythonAnywhere API...")
    print(f"👤 Пользователь: {USERNAME}")
    print(f"🏠 Хост: {HOST}")
    print()

    try:
        # Тест CPU
        print("📊 Проверяем CPU...")
        response = requests.get(f"{base_url}/cpu/", headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ CPU API работает!")
            print(f"   Дневной лимит: {data.get('daily_cpu_limit_seconds', 'N/A')} сек")
            print(f"   Использовано: {data.get('daily_cpu_total_usage_seconds', 'N/A')} сек")
        else:
            print(f"❌ Ошибка CPU API: {response.status_code} - {response.text}")
            return False

        # Тест консолей
        print("\n📺 Проверяем консоли...")
        response = requests.get(f"{base_url}/consoles/", headers=headers, timeout=10)

        if response.status_code == 200:
            consoles = response.json()
            print("✅ API консолей работает!")
            print(f"   Активных консолей: {len(consoles)}")
        else:
            print(f"❌ Ошибка API консолей: {response.status_code} - {response.text}")
            return False

        print("\n🎉 Все тесты пройдены! API работает корректно.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        return False

if __name__ == '__main__':
    success = test_api()
    exit(0 if success else 1)
