#!/usr/bin/env python3
"""
Автоматический деплой через GitHub API проверку
Запускается на PythonAnywhere как always-on задача
"""

import requests
import time
import subprocess
import os
from datetime import datetime

# Настройки
GITHUB_REPO = 'Allexndr/money_bot'
BRANCH = 'python-version'
CHECK_INTERVAL = 60  # Проверять каждые 60 секунд

# Файл для хранения последнего проверенного коммита
LAST_COMMIT_FILE = '/home/funarick/money_bot/.last_commit'

def get_latest_commit():
    """Получить последний коммит из GitHub"""
    url = f'https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['sha'], data['commit']['message']
        else:
            print(f"❌ Ошибка GitHub API: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Ошибка подключения к GitHub: {e}")
        return None, None

def get_last_checked_commit():
    """Получить последний проверенный коммит"""
    try:
        with open(LAST_COMMIT_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_commit(commit_sha):
    """Сохранить последний проверенный коммит"""
    with open(LAST_COMMIT_FILE, 'w') as f:
        f.write(commit_sha)

def run_deploy():
    """Выполнить деплой"""
    print(f"🚀 [{datetime.now()}] Выполняем деплой...")

    try:
        # Переход в директорию проекта
        os.chdir('/home/funarick/money_bot')

        # Git pull
        print("📥 Git pull...")
        result = subprocess.run(['git', 'pull', 'origin', BRANCH],
                              capture_output=True, text=True, timeout=60)
        print(f"Git: {result.stdout.strip()}")

        # Обновление зависимостей
        print("📦 Обновление зависимостей...")
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt', '--quiet'],
                              capture_output=True, text=True, timeout=120)

        # Перезапуск бота
        print("🔄 Перезапуск бота...")
        subprocess.run(['pkill', '-f', 'python.*main.py'], timeout=10)

        # Небольшая задержка
        time.sleep(2)

        # Запуск нового бота
        subprocess.Popen(['python', 'main.py'],
                        stdout=open('bot.log', 'a'),
                        stderr=subprocess.STDOUT)

        print("✅ Деплой завершен успешно!")

    except Exception as e:
        print(f"❌ Ошибка деплоя: {e}")

def main():
    print(f"🤖 GitHub Auto Deploy запущен для {GITHUB_REPO}:{BRANCH}")
    print(f"📊 Проверка каждые {CHECK_INTERVAL} секунд")
    print("=" * 50)

    last_commit = get_last_checked_commit()
    if last_commit:
        print(f"📝 Последний проверенный коммит: {last_commit[:8]}")
    else:
        print("📝 Первый запуск - проверим все коммиты")

    while True:
        try:
            # Получаем последний коммит
            latest_commit, commit_message = get_latest_commit()

            if latest_commit:
                if last_commit != latest_commit:
                    print(f"🔄 [{datetime.now()}] Найден новый коммит: {latest_commit[:8]}")
                    print(f"📝 {commit_message}")

                    # Выполняем деплой
                    run_deploy()

                    # Сохраняем новый коммит
                    save_last_commit(latest_commit)
                    last_commit = latest_commit

                    print(f"✅ Обновлено до коммита: {latest_commit[:8]}")
                else:
                    print(f"✅ [{datetime.now()}] Коммит {latest_commit[:8]} уже проверен")

            # Ждем следующей проверки
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Остановлено пользователем")
            break
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
