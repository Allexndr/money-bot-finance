"""
Модуль для управления кнопками и сообщениями бота
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import BotMessage, BotButton
from typing import List, Optional, Dict
from navigation import create_navigation_keyboard
from default_content import DEFAULT_MESSAGES


def get_message_by_key(db: Session, page_key: str) -> Optional[BotMessage]:
    """Получить сообщение по ключу страницы"""
    return db.query(BotMessage).filter(BotMessage.page_key == page_key).first()


def get_buttons_for_message(db: Session, message_id: int) -> List[BotButton]:
    """Получить все активные кнопки для сообщения, отсортированные по row и order"""
    return db.query(BotButton).filter(
        and_(BotButton.message_id == message_id, BotButton.is_active == True)
    ).order_by(BotButton.row, BotButton.order).all()


def build_keyboard_from_db(db: Session, message_id: int, user_id: int = None, 
                          callback_prefix: str = "nav", add_back_button: bool = True) -> InlineKeyboardMarkup:
    """Построить клавиатуру из базы данных"""
    buttons = get_buttons_for_message(db, message_id)
    
    if not buttons:
        if add_back_button:
            return create_navigation_keyboard(user_id, [], callback_prefix)
        return InlineKeyboardMarkup([])
    
    # Группируем кнопки по строкам
    keyboard_rows = {}
    for button in buttons:
        row = button.row
        if row not in keyboard_rows:
            keyboard_rows[row] = []
        keyboard_rows[row].append(button)
    
    # Сортируем строки и кнопки внутри строк
    sorted_rows = sorted(keyboard_rows.keys())
    keyboard = []
    
    for row in sorted_rows:
        row_buttons = sorted(keyboard_rows[row], key=lambda b: b.order)
        inline_buttons = []
        
        for button in row_buttons:
            if button.button_type == 'callback':
                inline_buttons.append(
                    InlineKeyboardButton(button.text, callback_data=button.action_data)
                )
            elif button.button_type == 'url':
                inline_buttons.append(
                    InlineKeyboardButton(button.text, url=button.action_data)
                )
            elif button.button_type == 'message':
                # Переход на другое сообщение - используем callback с page_key
                inline_buttons.append(
                    InlineKeyboardButton(button.text, callback_data=button.action_data)
                )
        
        if inline_buttons:
            keyboard.append(inline_buttons)
    
    if add_back_button:
        return create_navigation_keyboard(user_id, keyboard, callback_prefix)
    return InlineKeyboardMarkup(keyboard)


def create_message(db: Session, page_key: str, title: str, text: str, 
                  parse_mode: str = 'HTML', is_main_menu: bool = False) -> BotMessage:
    """Создать новое сообщение"""
    message = BotMessage(
        page_key=page_key,
        title=title,
        text=text,
        parse_mode=parse_mode,
        is_main_menu=is_main_menu
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def update_message(db: Session, message_id: int, title: str = None, text: str = None, 
                  parse_mode: str = None) -> Optional[BotMessage]:
    """Обновить сообщение"""
    message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
    if not message:
        return None
    
    if title is not None:
        message.title = title
    if text is not None:
        message.text = text
    if parse_mode is not None:
        message.parse_mode = parse_mode
    
    db.commit()
    db.refresh(message)
    return message


def create_button(db: Session, message_id: int, text: str, button_type: str, 
                 action_data: str, row: int = 0, order: int = 0) -> BotButton:
    """Создать новую кнопку"""
    button = BotButton(
        message_id=message_id,
        text=text,
        button_type=button_type,
        action_data=action_data,
        row=row,
        order=order
    )
    db.add(button)
    db.commit()
    db.refresh(button)
    return button


def update_button(db: Session, button_id: int, text: str = None, button_type: str = None,
                 action_data: str = None, row: int = None, order: int = None) -> Optional[BotButton]:
    """Обновить кнопку"""
    button = db.query(BotButton).filter(BotButton.id == button_id).first()
    if not button:
        return None
    
    if text is not None:
        button.text = text
    if button_type is not None:
        button.button_type = button_type
    if action_data is not None:
        button.action_data = action_data
    if row is not None:
        button.row = row
    if order is not None:
        button.order = order
    
    db.commit()
    db.refresh(button)
    return button


def delete_button(db: Session, button_id: int) -> bool:
    """Удалить кнопку (пометить как неактивную)"""
    button = db.query(BotButton).filter(BotButton.id == button_id).first()
    if not button:
        return False
    
    button.is_active = False
    db.commit()
    return True


def get_all_messages(db: Session) -> List[BotMessage]:
    """Получить все сообщения"""
    return db.query(BotMessage).order_by(BotMessage.page_key).all()


def get_all_buttons_for_message(db: Session, message_id: int) -> List[BotButton]:
    """Получить все кнопки для сообщения (включая неактивные)"""
    return db.query(BotButton).filter(
        BotButton.message_id == message_id
    ).order_by(BotButton.row, BotButton.order).all()


def delete_message(db: Session, message_id: int) -> bool:
    """Удалить сообщение и все связанные кнопки"""
    message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
    if not message:
        return False
    
    # Удаляем все кнопки сообщения
    buttons = db.query(BotButton).filter(BotButton.message_id == message_id).all()
    for button in buttons:
        db.delete(button)
    
    # Удаляем сообщение
    db.delete(message)
    db.commit()
    return True


def update_message_main_menu(db: Session, message_id: int, is_main_menu: bool) -> Optional[BotMessage]:
    """Обновить флаг главного меню для сообщения"""
    message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
    if not message:
        return None
    
    # Если устанавливаем это сообщение как главное меню, снимаем флаг с других
    if is_main_menu:
        db.query(BotMessage).filter(BotMessage.is_main_menu == True).update({'is_main_menu': False})
    
    message.is_main_menu = is_main_menu
    db.commit()
    db.refresh(message)
    return message


def ensure_default_messages(db: Session):
    """Убедиться, что в базе есть сообщения и кнопки по умолчанию"""
    for page_key, payload in DEFAULT_MESSAGES.items():
        message = get_message_by_key(db, page_key)
        if not message:
            message = create_message(
                db,
                page_key=page_key,
                title=payload.get("title"),
                text=payload.get("text", ""),
                parse_mode=payload.get("parse_mode", "HTML"),
                is_main_menu=payload.get("is_main_menu", False)
            )

        buttons = payload.get("buttons", [])
        existing_buttons = get_all_buttons_for_message(db, message.id)
        existing_map = {(btn.text, btn.button_type, btn.action_data): btn for btn in existing_buttons if btn.is_active}

        for index, button_payload in enumerate(buttons):
            text = button_payload.get("text", "Кнопка")
            btn_type = button_payload.get("type", "callback")
            action = button_payload.get("action", "")
            signature = (text, btn_type, action)

            if signature in existing_map:
                btn = existing_map[signature]
                if btn.row != index or btn.order != 0:
                    update_button(db, btn.id, row=index, order=0)
                continue

            create_button(
                db,
                message.id,
                text,
                btn_type,
                action,
                row=index,
                order=0
            )

        db.commit()

