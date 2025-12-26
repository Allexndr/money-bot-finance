from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from navigation import create_navigation_keyboard, Pages

def get_main_menu_keyboard(user_id: int = None):
    """Главное меню бота с инлайн кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("📢 Открытый канал «Про деньги»", callback_data="tg_channel")
        ],
        [
            InlineKeyboardButton("🎯 Бесплатный Квест 'Денежный прорыв'", callback_data="quest_community")
        ],
        [
            InlineKeyboardButton("🚀 Доступ в клуб «Квантовый скачок»", callback_data="closed_club")
        ],
        [
            InlineKeyboardButton("💰 Купить Курс 'Деньги в радости'", callback_data="course_buy")
        ],
        [
            InlineKeyboardButton("🎬 Купить запись 2-го потока Квеста", callback_data="buy_quest")
        ],
        [
            InlineKeyboardButton("💬 Консультация", callback_data="consultation")
        ],
        [
            InlineKeyboardButton("🎁 Демо-доступ", callback_data="demo_access")
        ],
        [
            InlineKeyboardButton("ℹ️ О боте", callback_data="about")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_application_keyboard(application_id):
    """Клавиатура для админа при рассмотрении заявки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{application_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{application_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu_keyboard():
    """Админское меню"""
    keyboard = [
        [KeyboardButton("/admin_panel")],
        [KeyboardButton("/send_newsletter")],
        [KeyboardButton("/view_users")],
        [KeyboardButton("/view_applications")],
        [KeyboardButton("/back_to_main")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_newsletter_keyboard():
    """Клавиатура для рассылки"""
    keyboard = [
        [InlineKeyboardButton("📤 Отправить всем", callback_data="send_newsletter_all")],
        [InlineKeyboardButton("📝 Редактировать", callback_data="edit_newsletter")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_newsletter")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(user_id: int = None):
    """Простая клавиатура с кнопкой Назад"""
    buttons = []
    return create_navigation_keyboard(user_id, buttons, "nav")

def get_info_keyboard(user_id: int = None):
    """Клавиатура для информационных страниц"""
    buttons = []
    return create_navigation_keyboard(user_id, buttons, "nav")

def get_admin_panel_keyboard(user_id: int = None):
    """Клавиатура админ-панели"""
    buttons = [
        [
            InlineKeyboardButton("📧 Создать рассылку", callback_data="admin_send_newsletter"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_view_users")
        ],
        [
            InlineKeyboardButton("📋 Заявки на курс", callback_data="admin_view_applications"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🔘 Управление кнопками", callback_data="admin_button_management")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
        ]
    ]
    return create_navigation_keyboard(user_id, buttons, "admin")

def get_pagination_keyboard(page=1, total_pages=1, callback_prefix="page"):
    """Клавиатура с пагинацией"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)
