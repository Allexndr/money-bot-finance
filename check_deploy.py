#!/usr/bin/env python3
"""
Проверка статуса деплоя на PythonAnywhere
"""

import subprocess
import sys

def run_ssh_command(command):
    """Выполнить команду через SSH"""
    ssh_cmd = f"ssh funarick@www.pythonanywhere.com '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def check_deploy_status():
    """Проверить статус деплоя"""
    print("🔍 Проверяем статус деплоя на PythonAnywhere...")
    print()

    # Проверяем, существует ли проект
    success, output, error = run_ssh_command("ls -la /home/funarick/money_bot")
    if not success:
        print("❌ Ошибка подключения или проект не найден")
        print(f"Ошибка: {error}")
        return

    print("📁 Содержимое проекта:")
    print(output)
    print()

    # Проверяем git статус
    success, output, error = run_ssh_command("cd /home/funarick/money_bot && git status --porcelain")
    if success:
        if output.strip():
            print("📊 Git статус: Есть изменения")
            print(output)
        else:
            print("✅ Git: Репозиторий синхронизирован")
    else:
        print("❌ Ошибка проверки git статуса")

    # Проверяем логи бота
    success, output, error = run_ssh_command("cd /home/funarick/money_bot && tail -5 bot.log 2>/dev/null || echo 'Лог не найден'")
    print(f"\n📋 Последние строки лога бота:\n{output}")

    # Проверяем процессы
    success, output, error = run_ssh_command("ps aux | grep python | grep -v grep")
    print(f"\n🔄 Активные Python процессы:\n{output}")

if __name__ == '__main__':
    check_deploy_status()
