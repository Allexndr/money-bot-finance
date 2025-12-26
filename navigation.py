"""
Система навигации с историей переходов
"""
from typing import Dict, List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Глобальная история навигации для каждого пользователя
USER_NAVIGATION_HISTORY: Dict[int, List[str]] = {}

def get_navigation_history(user_id: int) -> List[str]:
    """Получить историю навигации пользователя"""
    return USER_NAVIGATION_HISTORY.get(user_id, [])

def add_to_history(user_id: int, page: str):
    """Добавить страницу в историю навигации"""
    if user_id not in USER_NAVIGATION_HISTORY:
        USER_NAVIGATION_HISTORY[user_id] = []
    
    # Не добавляем дубликаты подряд
    if not USER_NAVIGATION_HISTORY[user_id] or USER_NAVIGATION_HISTORY[user_id][-1] != page:
        USER_NAVIGATION_HISTORY[user_id].append(page)
    
    # Ограничиваем историю до 10 страниц
    if len(USER_NAVIGATION_HISTORY[user_id]) > 10:
        USER_NAVIGATION_HISTORY[user_id] = USER_NAVIGATION_HISTORY[user_id][-10:]

def get_previous_page(user_id: int) -> Optional[str]:
    """Получить предыдущую страницу из истории"""
    history = get_navigation_history(user_id)
    if len(history) >= 2:
        return history[-2]  # Предыдущая страница
    return None

def go_back(user_id: int) -> Optional[str]:
    """Перейти назад в истории навигации"""
    history = get_navigation_history(user_id)
    if len(history) >= 2:
        # Удаляем текущую страницу
        USER_NAVIGATION_HISTORY[user_id] = history[:-1]
        # Возвращаем предыдущую
        return USER_NAVIGATION_HISTORY[user_id][-1]
    return None

def clear_history(user_id: int):
    """Очистить историю навигации пользователя"""
    if user_id in USER_NAVIGATION_HISTORY:
        USER_NAVIGATION_HISTORY[user_id] = []

def get_back_button(user_id: int, callback_prefix: str = "nav") -> List[InlineKeyboardButton]:
    """Получить кнопку 'Назад' с правильным callback"""
    previous_page = get_previous_page(user_id)
    
    if previous_page:
        return [InlineKeyboardButton("🔙 Назад", callback_data=f"{callback_prefix}_back")]
    else:
        return [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]

def create_navigation_keyboard(user_id: int, buttons: List[List[InlineKeyboardButton]], 
                              callback_prefix: str = "nav") -> InlineKeyboardMarkup:
    """Создать клавиатуру с правильной навигацией"""
    keyboard = buttons.copy()
    
    # Добавляем кнопку назад в конец
    keyboard.append(get_back_button(user_id, callback_prefix))
    
    return InlineKeyboardMarkup(keyboard)

# Константы для страниц
class Pages:
    MAIN_MENU = "main_menu"
    ADMIN_PANEL = "admin_panel"
    ADMIN_USERS = "admin_users"
    ADMIN_APPLICATIONS = "admin_applications"
    ADMIN_STATS = "admin_stats"
    ADMIN_SETTINGS = "admin_settings"
    ADMIN_NEWSLETTER = "admin_newsletter"
    ADMIN_BUTTON_MANAGEMENT = "admin_button_management"
    DOCUMENTS = "documents"
    ABOUT = "about"
    COURSE_APPLY = "course_apply"
    COURSE_APPLY_CONFIRM = "course_apply_confirm"
    BUY_QUEST = "buy_quest"
    SUBSCRIBE = "subscribe"
    FREE_QUEST = "free_quest"
    CONSULTATION = "consultation"
    COURSE_BUY = "course_buy"
    OFFER = "offer"
    PRIVACY = "privacy"
    QUEST_COMMUNITY = "quest_community"
    TG_CHANNEL = "tg_channel"
    CLOSED_CLUB = "closed_club"
    DEMO_ACCESS = "demo_access"

