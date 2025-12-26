#!/usr/bin/env python3
"""
Основной файл для запуска Telegram бота психолога
"""

import sys
import os
import logging

# Добавляем текущую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import main

if __name__ == "__main__":
    try:
        print("🤖 Запуск бота психолога...")
        print("📋 Функции бота:")
        print("  • Главное меню с кнопками")
        print("  • Система заявок на курс")
        print("  • Интеграция с Taplink")
        print("  • Админ-панель и рассылки")
        print("  • База данных пользователей")
        print("\n⚡ Бот запущен! Нажмите Ctrl+C для остановки.\n")
        
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Ошибка запуска бота: {e}")
        
        if "Unauthorized" in error_msg or "token" in error_msg.lower() or "401" in error_msg:
            print("\n⚠️  ПРОБЛЕМА С ТОКЕНОМ БОТА!")
            print("Токен бота неверный или истек.")
            print("\n📝 Как исправить:")
            print("1. Откройте Telegram и найдите @BotFather")
            print("2. Отправьте команду /mybots")
            print("3. Выберите вашего бота")
            print("4. Выберите 'API Token' и скопируйте новый токен")
            print("5. Создайте файл .env в папке проекта:")
            print("   BOT_TOKEN=ваш_новый_токен_здесь")
            print("6. Или обновите токен в config.py")
        
        logging.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)





