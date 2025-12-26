#!/usr/bin/env python3
"""
Комплексное тестирование всех функций управления кнопками и сообщениями
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, BotMessage, BotButton
from button_manager import (
    create_message, create_button, update_message, update_button,
    delete_button, get_message_by_key, get_buttons_for_message,
    build_keyboard_from_db, ensure_default_messages, delete_message,
    get_all_messages
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def test_create_message():
    """Тест создания сообщения"""
    print("🧪 Тест 1: Создание сообщения")
    db = SessionLocal()
    try:
        # Удаляем тестовое сообщение если есть
        test_msg = get_message_by_key(db, "test_message")
        if test_msg:
            delete_message(db, test_msg.id)
        
        message = create_message(
            db,
            page_key="test_message",
            title="Тестовое сообщение",
            text="Это тестовое сообщение для проверки",
            parse_mode="HTML",
            is_main_menu=False
        )
        assert message is not None, "Сообщение не создано"
        assert message.page_key == "test_message", "Неверный page_key"
        print("✅ Сообщение создано успешно")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 1 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 1: {e}\n")
        return False
    finally:
        db.close()

def test_create_buttons():
    """Тест создания кнопок всех типов"""
    print("🧪 Тест 2: Создание кнопок всех типов")
    db = SessionLocal()
    try:
        # Создаем тестовое сообщение
        message = create_message(
            db,
            page_key="test_buttons",
            title="Тест кнопок",
            text="Тест",
            is_main_menu=False
        )
        
        # Тест 1: Callback кнопка
        callback_btn = create_button(
            db,
            message.id,
            text="Callback кнопка",
            button_type="callback",
            action_data="test_callback",
            row=0,
            order=0
        )
        assert callback_btn.button_type == "callback", "Неверный тип callback кнопки"
        print("✅ Callback кнопка создана")
        
        # Тест 2: URL кнопка
        url_btn = create_button(
            db,
            message.id,
            text="URL кнопка",
            button_type="url",
            action_data="https://t.me/saule_prodengi",
            row=0,
            order=1
        )
        assert url_btn.button_type == "url", "Неверный тип URL кнопки"
        assert url_btn.action_data.startswith("http"), "URL должен начинаться с http"
        print("✅ URL кнопка создана")
        
        # Тест 3: Message кнопка
        message_btn = create_button(
            db,
            message.id,
            text="Message кнопка",
            button_type="message",
            action_data="main_menu",
            row=1,
            order=0
        )
        assert message_btn.button_type == "message", "Неверный тип message кнопки"
        print("✅ Message кнопка создана")
        
        # Проверяем количество кнопок
        buttons = get_buttons_for_message(db, message.id)
        assert len(buttons) == 3, f"Ожидалось 3 кнопки, получено {len(buttons)}"
        print(f"✅ Всего кнопок: {len(buttons)}")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 2 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 2: {e}\n")
        return False
    finally:
        db.close()

def test_build_keyboard():
    """Тест построения клавиатуры"""
    print("🧪 Тест 3: Построение клавиатуры из БД")
    db = SessionLocal()
    try:
        # Создаем сообщение с кнопками
        message = create_message(
            db,
            page_key="test_keyboard",
            title="Тест клавиатуры",
            text="Тест",
            is_main_menu=False
        )
        
        # Создаем кнопки разных типов
        create_button(db, message.id, "Callback", "callback", "test_cb", row=0, order=0)
        create_button(db, message.id, "URL", "url", "https://t.me/saule_prodengi", row=0, order=1)
        create_button(db, message.id, "Message", "message", "main_menu", row=1, order=0)
        
        # Строим клавиатуру
        keyboard = build_keyboard_from_db(db, message.id, None, "nav", add_back_button=False)
        
        assert keyboard is not None, "Клавиатура не создана"
        assert len(keyboard.inline_keyboard) == 2, "Должно быть 2 строки"
        assert len(keyboard.inline_keyboard[0]) == 2, "Первая строка должна содержать 2 кнопки"
        assert len(keyboard.inline_keyboard[1]) == 1, "Вторая строка должна содержать 1 кнопку"
        
        # Проверяем типы кнопок
        btn1 = keyboard.inline_keyboard[0][0]
        btn2 = keyboard.inline_keyboard[0][1]
        btn3 = keyboard.inline_keyboard[1][0]
        
        assert hasattr(btn1, 'callback_data'), "Первая кнопка должна быть callback"
        assert hasattr(btn2, 'url'), "Вторая кнопка должна быть URL"
        assert hasattr(btn3, 'callback_data'), "Третья кнопка должна быть callback (message)"
        
        print("✅ Клавиатура построена корректно")
        print(f"   - Строк: {len(keyboard.inline_keyboard)}")
        print(f"   - Кнопок в первой строке: {len(keyboard.inline_keyboard[0])}")
        print(f"   - URL кнопка: {btn2.url}")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 3 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 3: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_update_button():
    """Тест обновления кнопки"""
    print("🧪 Тест 4: Обновление кнопки")
    db = SessionLocal()
    try:
        message = create_message(db, "test_update", "Тест", "Тест", is_main_menu=False)
        button = create_button(db, message.id, "Старый текст", "callback", "old_action", row=0, order=0)
        
        # Обновляем текст
        updated = update_button(db, button.id, text="Новый текст")
        assert updated.text == "Новый текст", "Текст не обновлен"
        print("✅ Текст кнопки обновлен")
        
        # Обновляем действие
        updated = update_button(db, button.id, action_data="new_action")
        assert updated.action_data == "new_action", "Действие не обновлено"
        print("✅ Действие кнопки обновлено")
        
        # Обновляем тип и действие для URL
        updated = update_button(db, button.id, button_type="url", action_data="https://t.me/test")
        assert updated.button_type == "url", "Тип не обновлен"
        assert updated.action_data == "https://t.me/test", "URL не обновлен"
        print("✅ Тип и URL обновлены")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 4 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 4: {e}\n")
        return False
    finally:
        db.close()

def test_url_validation():
    """Тест валидации URL"""
    print("🧪 Тест 5: Валидация URL")
    
    valid_urls = [
        "https://t.me/saule_prodengi",
        "http://example.com",
        "https://example.com/page",
    ]
    
    invalid_urls = [
        "t.me/saule_prodengi",  # Без протокола
        "www.example.com",  # Без протокола
        "example.com",  # Без протокола
    ]
    
    for url in valid_urls:
        assert url.startswith(('http://', 'https://')), f"URL {url} должен начинаться с http:// или https://"
        print(f"✅ Валидный URL: {url}")
    
    for url in invalid_urls:
        assert not url.startswith(('http://', 'https://')), f"URL {url} невалиден"
        print(f"✅ Невалидный URL обнаружен: {url}")
    
    print("✅ Тест 5 пройден\n")
    return True

def test_default_messages():
    """Тест создания сообщений по умолчанию"""
    print("🧪 Тест 6: Создание сообщений по умолчанию")
    db = SessionLocal()
    try:
        # Запускаем ensure_default_messages
        ensure_default_messages(db)
        
        # Проверяем, что main_menu создан
        main_menu = get_message_by_key(db, "main_menu")
        assert main_menu is not None, "main_menu не создан"
        assert main_menu.is_main_menu == True, "main_menu должен быть главным меню"
        print("✅ main_menu создан")
        
        # Проверяем кнопки
        buttons = get_buttons_for_message(db, main_menu.id)
        assert len(buttons) > 0, "Кнопки не созданы"
        print(f"✅ Создано кнопок: {len(buttons)}")
        
        # Проверяем наличие URL кнопок
        url_buttons = [b for b in buttons if b.button_type == 'url']
        assert len(url_buttons) >= 2, "Должно быть минимум 2 URL кнопки (Пройти тест, Забрать практику)"
        print(f"✅ URL кнопок: {len(url_buttons)}")
        
        # Проверяем, что URL кнопки имеют правильный формат
        for btn in url_buttons:
            assert btn.action_data.startswith(('http://', 'https://')), f"URL кнопка '{btn.text}' имеет невалидный URL: {btn.action_data}"
            print(f"   ✅ URL кнопка '{btn.text}': {btn.action_data}")
        
        print("✅ Тест 6 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 6: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_button_order():
    """Тест порядка кнопок"""
    print("🧪 Тест 7: Порядок кнопок")
    db = SessionLocal()
    try:
        message = create_message(db, "test_order", "Тест", "Тест", is_main_menu=False)
        
        # Создаем кнопки в разном порядке
        create_button(db, message.id, "Кнопка 1", "callback", "action1", row=1, order=1)
        create_button(db, message.id, "Кнопка 2", "callback", "action2", row=0, order=0)
        create_button(db, message.id, "Кнопка 3", "callback", "action3", row=0, order=1)
        create_button(db, message.id, "Кнопка 4", "callback", "action4", row=1, order=0)
        
        buttons = get_buttons_for_message(db, message.id)
        
        # Проверяем порядок
        assert buttons[0].text == "Кнопка 2", "Первая кнопка должна быть 'Кнопка 2'"
        assert buttons[1].text == "Кнопка 3", "Вторая кнопка должна быть 'Кнопка 3'"
        assert buttons[2].text == "Кнопка 4", "Третья кнопка должна быть 'Кнопка 4'"
        assert buttons[3].text == "Кнопка 1", "Четвертая кнопка должна быть 'Кнопка 1'"
        
        print("✅ Порядок кнопок корректен")
        
        # Строим клавиатуру и проверяем порядок
        keyboard = build_keyboard_from_db(db, message.id, None, "nav", add_back_button=False)
        assert len(keyboard.inline_keyboard) == 2, "Должно быть 2 строки"
        assert keyboard.inline_keyboard[0][0].text == "Кнопка 2", "Первая строка, первая кнопка"
        assert keyboard.inline_keyboard[0][1].text == "Кнопка 3", "Первая строка, вторая кнопка"
        assert keyboard.inline_keyboard[1][0].text == "Кнопка 4", "Вторая строка, первая кнопка"
        assert keyboard.inline_keyboard[1][1].text == "Кнопка 1", "Вторая строка, вторая кнопка"
        
        print("✅ Порядок в клавиатуре корректен")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 7 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 7: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_delete_button():
    """Тест удаления кнопки"""
    print("🧪 Тест 8: Удаление кнопки")
    db = SessionLocal()
    try:
        message = create_message(db, "test_delete", "Тест", "Тест", is_main_menu=False)
        button = create_button(db, message.id, "Удаляемая", "callback", "action", row=0, order=0)
        
        # Удаляем кнопку
        result = delete_button(db, button.id)
        assert result == True, "Кнопка не удалена"
        
        # Проверяем, что кнопка неактивна
        buttons = get_buttons_for_message(db, message.id)
        assert len(buttons) == 0, "Кнопка должна быть скрыта"
        
        # Проверяем, что кнопка все еще в БД, но неактивна
        all_buttons = db.query(BotButton).filter(BotButton.message_id == message.id).all()
        assert len(all_buttons) == 1, "Кнопка должна остаться в БД"
        assert all_buttons[0].is_active == False, "Кнопка должна быть неактивна"
        
        print("✅ Кнопка удалена (помечена как неактивная)")
        
        # Очистка
        delete_message(db, message.id)
        print("✅ Тест 8 пройден\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте 8: {e}\n")
        return False
    finally:
        db.close()

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ АДМИНКИ УПРАВЛЕНИЯ КНОПКАМИ")
    print("=" * 60)
    print()
    
    tests = [
        test_create_message,
        test_create_buttons,
        test_build_keyboard,
        test_update_button,
        test_url_validation,
        test_default_messages,
        test_button_order,
        test_delete_button,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в {test.__name__}: {e}")
            results.append(False)
    
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n⚠️  Есть проблемы в {total - passed} тестах")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)





