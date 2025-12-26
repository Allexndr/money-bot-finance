"""
Админ-панель для управления кнопками и сообщениями
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import SessionLocal, BotMessage, BotButton
from button_manager import (
    get_message_by_key, get_buttons_for_message, get_all_messages,
    create_message, update_message, create_button, update_button, delete_button,
    get_all_buttons_for_message, build_keyboard_from_db, delete_message,
    update_message_main_menu, ensure_default_messages
)
from navigation import create_navigation_keyboard, Pages, add_to_history
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Состояния для админ-панели управления кнопками
ADMIN_BUTTON_STATES: Dict[int, Dict] = {}


def build_admin_button_grid(buttons: list, message_id: int) -> InlineKeyboardMarkup:
    """Построить клавиатуру, повторяющую пользовательскую, но с переходом к редактированию"""
    rows: Dict[int, list] = {}
    for btn in buttons:
        rows.setdefault(btn.row, []).append(btn)

    keyboard = []
    for row_index in sorted(rows.keys()):
        row_buttons = sorted(rows[row_index], key=lambda b: b.order)
        keyboard.append([
            InlineKeyboardButton(button.text, callback_data=f"admin_quick_edit_button_{button.id}")
            for button in row_buttons
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Добавить кнопку", callback_data=f"admin_create_button_msg_{message_id}")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_message_{message_id}")
    ])
    return InlineKeyboardMarkup(keyboard)


def get_admin_button_management_keyboard(user_id: int = None):
    """Клавиатура админ-панели для контента"""
    buttons = [
        [InlineKeyboardButton("📄 Открыть список страниц", callback_data="admin_manage_messages")],
        [InlineKeyboardButton("📘 Инструкция", callback_data="admin_instruction")],
        [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)


async def admin_button_management_callback(query, context):
    """Главное меню управления контентом"""
    add_to_history(query.from_user.id, Pages.ADMIN_BUTTON_MANAGEMENT)
    await admin_manage_messages_callback(query, context, intro=True)


INSTRUCTION_SECTIONS = {
    "overview": {
        "title": "🚀 Быстрый старт",
        "text": (
            "<b>ШАГ 1. Вход в админку</b>\n"
            "• Отправьте /admin\n"
            "• Нажмите «Управление кнопками»\n\n"
            "<b>ШАГ 2. Страница</b>\n"
            "• «Создать страницу» → придумайте короткое имя латиницей\n"
            "• Добавьте заголовок и текст\n"
            "• Укажите: это главное меню или обычная страница\n\n"
            "<b>ШАГ 3. Кнопки</b>\n"
            "• Откройте страницу → «Управление кнопками» → «Добавить кнопку»\n"
            "• Введите текст, выберите действие (ссылка/страница)\n"
            "• Укажите строку (0 – верх) и место в строке (0 – слева)\n\n"
            "<b>ШАГ 4. Проверка</b>\n"
            "• На странице нажмите «Превью» — увидите, как выглядит для людей"
        )
    },
    "pages": {
        "title": "📄 Страницы (сообщения)",
        "text": (
            "<b>Создание</b>\n"
            "1. «Создать страницу»\n"
            "2. Имя латиницей без пробелов (пример: about_course)\n"
            "3. Заголовок (или «-», если не нужен)\n"
            "4. Текст любыми блоками и смайлами\n"
            "5. Выберите: главное меню или нет\n\n"
            "<b>Редактирование</b>\n"
            "• «Изменить текст» — обновляет основной текст\n"
            "• «Изменить заголовок» — новый текст или «-» чтобы убрать\n"
            "• «Главное меню» — делаем страницу стартовой\n"
            "• «Превью» — проверка результата\n"
            "• «Удалить» — убирает страницу и все её кнопки\n\n"
            "<b>Важно</b>\n"
            "• Имя страницы уникально и только латиницей\n"
            "• Главное меню может быть одно"
        )
    },
    "buttons": {
        "title": "🔘 Кнопки",
        "text": (
            "<b>Создание (5 шагов)</b>\n"
            "1. Текст кнопки (то, что увидит человек)\n"
            "2. Тип:\n"
            "   • «Ссылка» — открыть сайт/канал (начинается с https://)\n"
            "   • «Переход на страницу» — показать другую страницу бота\n"
            "   • «Действие» — спец. кнопка (используем только если нужно)\n"
            "3. Действие:\n"
            "   • Для ссылки — полный адрес с https://\n"
            "   • Для перехода — выбрать страницу из списка\n"
            "4. Строка: 0 – верхняя, 1 – ниже и т.д.\n"
            "5. Место в строке: 0 – слева, 1 – справа и т.д.\n\n"
            "<b>Редактирование</b>\n"
            "• «Изменить текст» — отправьте новый текст\n"
            "• «Изменить действие» — новая ссылка или другая страница\n"
            "• «Изменить тип» — ссылка ↔ переход\n"
            "• «Изменить позицию» — новое место\n"
            "• «Удалить» — убирает кнопку (можно создать заново)\n\n"
            "<b>Советы</b>\n"
            "• Важные кнопки ставьте в строку 0\n"
            "• «Назад» обычно в последней строке\n"
            "• Используйте эмодзи, чтобы кнопки было легче читать"
        )
    },
    "faq": {
        "title": "❓ Частые вопросы",
        "text": (
            "<b>Кнопка со ссылкой не работает?</b>\n"
            "→ Добавьте https:// в начале (пример: https://t.me/username)\n\n"
            "<b>Страница не создаётся?</b>\n"
            "→ Имя только латиницей без пробелов и не занято\n\n"
            "<b>Кнопка не видна?</b>\n"
            "→ Проверьте строку/позицию и нажмите «Превью»\n\n"
            "<b>Как сделать «Назад»?</b>\n"
            "→ Тип «Переход на страницу», действие main_menu, поставьте в последнюю строку\n\n"
            "<b>Сколько кнопок можно?</b>\n"
            "→ Технически много, но удобнее до 8–10 на страницу"
        )
    },
    "tips": {
        "title": "💡 Полезные советы",
        "text": (
            "• Делайте одну страницу = одна тема\n"
            "• Короткие тексты + эмодзи → быстрее читают\n"
            "• Группируйте похожие кнопки в одну строку\n"
            "• Используйте «Превью» после каждого изменения\n"
            "• Если что-то «сломалось», нажмите «Назад» и откройте заново\n"
            "• Держите главное меню максимально простым"
        )
    }
}

INSTRUCTION_PAGES: List[Dict[str, str]] = [
    {
        "title": "📘 Полная инструкция — Страница 1 из 6",
        "text": (
            "<b>Что такое страница и кнопка?</b>\n"
            "• Страница — любое сообщение в боте (например, главное меню)\n"
            "• Кнопки — зелёные кнопки под сообщением\n\n"
            "<b>Как устроена админка</b>\n"
            "1. Нажмите /admin\n"
            "2. Выберите «Управление кнопками»\n"
            "3. В списке увидите все страницы\n\n"
            "<b>Когда создавать новую страницу?</b>\n"
            "• Нужен отдельный экран (например, «О курсе», «FAQ»)\n"
            "• Нужно другое сообщение для кнопки «Переход на страницу»\n"
            "• Хотите разделить контент на темы\n\n"
            "<b>Советы</b>\n"
            "• Одна страница = одна тема\n"
            "• Главное меню должно быть простым и понятным\n"
            "• Используйте эмодзи, чтобы текст читали охотнее"
        )
    },
    {
        "title": "📘 Полная инструкция — Страница 2 из 6",
        "text": (
            "<b>Как создать страницу</b>\n"
            "1. «➕ Создать страницу»\n"
            "2. <b>Имя страницы</b> — только латиница, цифры и _ (пример: about_course)\n"
            "3. <b>Заголовок</b> — жирный текст сверху (или «-», чтобы скрыть)\n"
            "4. <b>Текст</b> — любой текст, списки, эмодзи\n"
            "5. <b>Главное меню?</b> — выберите «Да», если это стартовый экран\n\n"
            "<b>Как изменять страницу</b>\n"
            "• «Изменить текст» — обновите содержание\n"
            "• «Изменить заголовок» — новый текст или «-»\n"
            "• «Главное меню» — делает страницу стартовой\n"
            "• «Превью» — смотрите, как увидит пользователь\n"
            "• «Удалить» — убирает страницу и её кнопки\n\n"
            "<b>Важно</b>\n"
            "• Имя страницы уникально, переиспользовать нельзя\n"
            "• Главное меню всегда одно"
        )
    },
    {
        "title": "📘 Полная инструкция — Страница 3 из 6",
        "text": (
            "<b>Добавление кнопок (5 шагов)</b>\n"
            "1. «Управление кнопками» → «➕ Добавить кнопку»\n"
            "2. <b>Текст</b> — что увидит человек (пример: «Купить курс»)\n"
            "3. <b>Тип</b>:\n"
            "   • «Ссылка» — открывает сайт/канал (https://...)\n"
            "   • «Переход на страницу» — показывает другую страницу бота\n"
            "   • «Действие» — спец. кнопка (только при необходимости)\n"
            "4. <b>Действие</b>:\n"
            "   • Ссылка — полный адрес с https://\n"
            "   • Переход — выберите страницу из списка\n"
            "5. <b>Расположение</b>:\n"
            "   • Строка 0 — верхняя, 1 — ниже и т.д.\n"
            "   • Порядок 0 — слева, 1 — справа, 2 — еще правее\n\n"
            "<b>Пример</b>\n"
            "Строка 0, порядок 0 → верхняя строка, крайняя левая кнопка"
        )
    },
    {
        "title": "📘 Полная инструкция — Страница 4 из 6",
        "text": (
            "<b>Редактирование кнопок</b>\n"
            "• Нажмите на кнопку в макете или в списке\n"
            "• Доступны действия:\n"
            "   📝 Изменить текст — отправьте новый текст\n"
            "   📋 Изменить действие — новая ссылка или другая страница\n"
            "   🔄 Изменить тип — ссылка ↔ переход\n"
            "   📐 Изменить позицию — новое место (строка/порядок)\n"
            "   🗑️ Удалить — убирает кнопку (создать снова можно в любой момент)\n\n"
            "<b>Хороший макет</b>\n"
            "• Важные кнопки держите в строке 0\n"
            "• Похожие действия ставьте рядом\n"
            "• Кнопка «Назад» обычно в последней строке\n"
            "• Не делайте больше 8–10 кнопок на страницу — так удобнее"
        )
    },
    {
        "title": "📘 Полная инструкция — Страница 5 из 6",
        "text": (
            "<b>Частые вопросы</b>\n"
            "• <b>Ссылка не работает?</b>\n"
            "  Добавьте https:// в начале (пример: https://t.me/username)\n\n"
            "• <b>Страница не создаётся?</b>\n"
            "  Имя занято или содержит русские буквы/пробелы\n\n"
            "• <b>Кнопка не появляется?</b>\n"
            "  Проверьте строку/порядок и обновите «Превью»\n\n"
            "• <b>Как сделать «Назад»?</b>\n"
            "  Тип «Переход на страницу», действие main_menu, поставьте в последнюю строку\n\n"
            "• <b>Можно ли вернуться после удаления?</b>\n"
            "  Страницу — нет. Кнопку — создать заново"
        )
    },
    {
        "title": "📘 Полная инструкция — Страница 6 из 6",
        "text": (
            "<b>Полезные советы</b>\n"
            "• Делайте короткие тексты, добавляйте эмодзи\n"
            "• Группируйте кнопки по смыслу\n"
            "• Проверяйте каждое изменение через «Превью»\n"
            "• Если что-то «зависло», нажмите «Назад» и откройте экран снова\n"
            "• Всегда держите под рукой ссылку на главное меню (кнопка «Назад»)\n"
            "• Важные действия располагайте выше и левее"
        )
    }
]


def get_instruction_keyboard(section: Optional[str] = None):
    """Построить клавиатуру для разделов инструкции"""
    buttons = []
    if section:
        buttons.append([InlineKeyboardButton("📚 Все разделы", callback_data="admin_instruction")])
        buttons.append([InlineKeyboardButton("📖 Полная инструкция", callback_data="admin_instruction_page_0")])
    else:
        buttons.extend([
            [
                InlineKeyboardButton("🚀 Быстрый старт", callback_data="admin_instruction_section_overview")
            ],
            [
                InlineKeyboardButton("📄 Страницы", callback_data="admin_instruction_section_pages"),
                InlineKeyboardButton("🔘 Кнопки", callback_data="admin_instruction_section_buttons")
            ],
            [
                InlineKeyboardButton("❓ Вопросы", callback_data="admin_instruction_section_faq"),
                InlineKeyboardButton("💡 Советы", callback_data="admin_instruction_section_tips")
            ]
        ])
        buttons.append([
            InlineKeyboardButton("📖 Полная инструкция", callback_data="admin_instruction_page_0")
        ])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")])
    return InlineKeyboardMarkup(buttons)


async def admin_instruction_callback(query, context, section: Optional[str] = None):
    """Показать инструкцию внутри админки со страницами"""
    if section:
        section_data = INSTRUCTION_SECTIONS.get(section)
        if not section_data:
            await query.answer("Раздел не найден")
            return
        text = f"{section_data['title']}\n\n{section_data['text']}"
    else:
        text = (
            "📘 <b>ИНСТРУКЦИЯ ПО АДМИНКЕ</b>\n\n"
            "Выберите раздел ниже, чтобы быстро вспомнить нужный шаг.\n"
            "Разделы можно открывать в любом порядке, а потом возвращаться назад."
        )
    await query.edit_message_text(
        text,
        reply_markup=get_instruction_keyboard(section),
        parse_mode=ParseMode.HTML
    )


def get_instruction_page_keyboard(index: int) -> InlineKeyboardMarkup:
    buttons = []
    navigation = []
    if index > 0:
        navigation.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_instruction_page_{index - 1}"))
    if index < len(INSTRUCTION_PAGES) - 1:
        navigation.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"admin_instruction_page_{index + 1}"))
    if navigation:
        buttons.append(navigation)
    buttons.append([
        InlineKeyboardButton("📚 Разделы", callback_data="admin_instruction"),
        InlineKeyboardButton("🔙 В меню", callback_data="admin_button_management")
    ])
    return InlineKeyboardMarkup(buttons)


async def admin_instruction_page_callback(query, context, index: int):
    """Постраничное руководство"""
    if index < 0 or index >= len(INSTRUCTION_PAGES):
        await query.answer("Страница не найдена")
        return
    page = INSTRUCTION_PAGES[index]
    text = f"{page['title']}\n\n{page['text']}"
    await query.edit_message_text(
        text,
        reply_markup=get_instruction_page_keyboard(index),
        parse_mode=ParseMode.HTML
    )


async def admin_manage_messages_callback(query, context, intro: bool = False):
    """Список всех сообщений для управления"""
    db = SessionLocal()
    try:
        ensure_default_messages(db)
        messages = get_all_messages(db)
        
        if not messages:
            await query.edit_message_text(
                "📝 <b>СООБЩЕНИЯ</b>\n\n"
                "Сообщений пока нет.\n\n"
                "<i>Нажмите «Создать страницу», чтобы добавить первый экран. После создания вернитесь сюда для управления.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать страницу", callback_data="admin_create_message")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")]
                ]),
                parse_mode=ParseMode.HTML
            )
            return
        
        text = "📝 <b>СПИСОК СООБЩЕНИЙ</b>\n\n"
        if intro:
            text += "<i>Выберите страницу, чтобы редактировать текст или её кнопки. Внизу можно добавить новую страницу.</i>\n\n"
        
        buttons_layout = []
        for msg in messages:
            main_menu_mark = "🏠 " if msg.is_main_menu else ""
            text += f"{main_menu_mark}<b>{msg.page_key}</b> — {msg.title or 'Без заголовка'}\n"
            buttons_layout.append([
                InlineKeyboardButton(
                    f"✏️ {msg.page_key}",
                    callback_data=f"admin_edit_message_{msg.id}"
                )
            ])
        text += "\n"
        
        buttons_layout.append([InlineKeyboardButton("➕ Создать страницу", callback_data="admin_create_message")])
        buttons_layout.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons_layout),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_manage_buttons_callback(query, context):
    """Выбор сообщения для управления кнопками"""
    db = SessionLocal()
    try:
        ensure_default_messages(db)
        messages = get_all_messages(db)
        
        if not messages:
            await query.edit_message_text(
                "🔘 <b>УПРАВЛЕНИЕ КНОПКАМИ</b>\n\n"
                "Сначала создайте сообщение!\n\n"
                "<i>Вернитесь назад, выберите «Создать сообщение», а затем снова откройте этот раздел.</i>",
                reply_markup=get_back_to_button_management_keyboard(query.from_user.id),
                parse_mode=ParseMode.HTML
            )
            return
        
        text = "🔘 <b>ВЫБЕРИТЕ СООБЩЕНИЕ ДЛЯ УПРАВЛЕНИЯ КНОПКАМИ</b>\n\n"
        buttons = []
        
        for msg in messages:
            buttons_count = len(get_buttons_for_message(db, msg.id))
            text += f"<b>{msg.page_key}</b> - {buttons_count} кнопок\n"
            
            buttons.append([
                InlineKeyboardButton(
                    f"🔘 {msg.page_key} ({buttons_count})",
                    callback_data=f"admin_edit_buttons_{msg.id}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")
        ])
        
        text += "<i>Выберите сообщение из списка, чтобы увидеть и настроить его кнопки.</i>"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_create_message_callback(query, context):
    """Начать создание нового сообщения"""
    user_id = query.from_user.id
    ADMIN_BUTTON_STATES[user_id] = {
        'action': 'create_message',
        'step': 'page_key'
    }
    
    await query.edit_message_text(
        "➕ <b>СОЗДАНИЕ НОВОГО СООБЩЕНИЯ</b>\n\n"
        "Шаг 1/4: Введите уникальный ключ страницы (например: main_menu, course_info)\n\n"
        "<i>Используйте латиницу, цифры и нижнее подчеркивание. Этот ключ будет использоваться для переходов между экранами.</i>",
        reply_markup=get_back_to_button_management_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )


async def admin_create_button_callback(query, context):
    """Начать создание новой кнопки"""
    db = SessionLocal()
    try:
        messages = get_all_messages(db)
        
        if not messages:
            await query.edit_message_text(
                "➕ <b>СОЗДАНИЕ КНОПКИ</b>\n\n"
                "Сначала создайте сообщение!",
                reply_markup=get_back_to_button_management_keyboard(query.from_user.id),
                parse_mode=ParseMode.HTML
            )
            return
        
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'create_button',
            'step': 'select_message'
        }
        
        text = "➕ <b>СОЗДАНИЕ НОВОЙ КНОПКИ</b>\n\n"
        text += "Выберите сообщение, к которому добавить кнопку:\n\n"
        text += "<i>Сначала определите экран, затем настроите текст и действие будущей кнопки.</i>\n\n"
        
        buttons = []
        for msg in messages:
            buttons.append([
                InlineKeyboardButton(
                    f"📝 {msg.page_key}",
                    callback_data=f"admin_create_button_msg_{msg.id}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_edit_message_callback(query, context, message_id: int):
    """Редактирование сообщения"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.edit_message_text("❌ Сообщение не найдено.")
            return
        
        buttons = get_buttons_for_message(db, message_id)
        
        parse_mode_names = {
            'HTML': 'HTML',
            'Markdown': 'Markdown',
            None: 'Без форматирования'
        }
        
        text = f"✏️ <b>РЕДАКТИРОВАНИЕ СООБЩЕНИЯ</b>\n\n"
        text += f"<b>Ключ:</b> {message.page_key}\n"
        text += f"<b>Заголовок:</b> {message.title or 'Не задан'}\n"
        text += f"<b>Текст:</b>\n{message.text[:200]}{'...' if len(message.text) > 200 else ''}\n\n"
        text += f"<b>Формат:</b> {parse_mode_names.get(message.parse_mode, message.parse_mode or 'Без форматирования')}\n"
        text += f"<b>Кнопок:</b> {len(buttons)}\n"
        text += f"<b>Главное меню:</b> {'✅ Да' if message.is_main_menu else '❌ Нет'}\n\n"
        text += "<i>Выберите действие ниже: сначала обновите текст и формат, затем переходите к управлению кнопками или превью.</i>"
        
        keyboard_buttons = [
            [
                InlineKeyboardButton("📝 Изменить текст", callback_data=f"admin_edit_msg_text_{message_id}"),
                InlineKeyboardButton("📌 Изменить заголовок", callback_data=f"admin_edit_msg_title_{message_id}")
            ],
            [
                InlineKeyboardButton("🎨 Изменить формат", callback_data=f"admin_edit_msg_parse_mode_{message_id}")
            ],
            [
                InlineKeyboardButton("🏠 Главное меню", callback_data=f"admin_toggle_main_menu_{message_id}")
            ],
            [
                InlineKeyboardButton("🔘 Управление кнопками", callback_data=f"admin_edit_buttons_{message_id}")
            ],
            [
                InlineKeyboardButton("👁️ Превью", callback_data=f"admin_preview_message_{message_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"admin_delete_message_{message_id}"),
                InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_messages")
            ]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard_buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_edit_buttons_callback(query, context, message_id: int):
    """Управление кнопками сообщения"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.edit_message_text("❌ Сообщение не найдено.")
            return
        
        buttons = get_all_buttons_for_message(db, message_id)
        active_buttons = [b for b in buttons if b.is_active]
        
        text = f"🔘 <b>УПРАВЛЕНИЕ КНОПКАМИ</b>\n\n"
        text += f"<b>Сообщение:</b> {message.page_key}\n\n"
        text += "<i>Нажмите на кнопку в макете ниже для редактирования. Дополнительно можно воспользоваться списком характеристик выше.</i>\n\n"
        
        if not active_buttons:
            text += "Кнопок пока нет.\n"
        else:
            text += "<b>Текущие кнопки:</b>\n"
            for btn in active_buttons:
                type_emoji = {'callback': '🔄', 'url': '🔗', 'message': '➡️'}.get(btn.button_type, '❓')
                text += f"{type_emoji} <b>{btn.text}</b> (строка {btn.row}, порядок {btn.order})\n"
        
        text += "\n<i>Используйте макет ниже для быстрого редактирования или кнопки списка справа.</i>"
        
        admin_keyboard = build_admin_button_grid(active_buttons, message_id)
        
        await query.edit_message_text(
            text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_edit_button_callback(query, context, button_id: int):
    """Редактирование конкретной кнопки"""
    db = SessionLocal()
    try:
        button = db.query(BotButton).filter(BotButton.id == button_id).first()
        if not button:
            await query.edit_message_text("❌ Кнопка не найдена.")
            return
        
        message = db.query(BotMessage).filter(BotMessage.id == button.message_id).first()
        
        type_names = {
            'callback': 'Callback (внутренний переход)',
            'url': 'URL (ссылка)',
            'message': 'Message (переход на сообщение)'
        }
        
        text = f"✏️ <b>РЕДАКТИРОВАНИЕ КНОПКИ</b>\n\n"
        text += f"<b>Текст:</b> {button.text}\n"
        text += f"<b>Тип:</b> {type_names.get(button.button_type, button.button_type)}\n"
        text += f"<b>Действие:</b> {button.action_data}\n"
        text += f"<b>Строка:</b> {button.row}\n"
        text += f"<b>Порядок:</b> {button.order}\n"
        text += f"<b>Сообщение:</b> {message.page_key if message else 'Не найдено'}\n\n"
        text += "<i>Используйте кнопки ниже, чтобы изменить текст, тип, действие или позицию. После изменений вернитесь назад для проверки списка.</i>"
        
        keyboard_buttons = [
            [
                InlineKeyboardButton("📝 Изменить текст", callback_data=f"admin_edit_btn_text_{button_id}"),
                InlineKeyboardButton("🔄 Изменить тип", callback_data=f"admin_edit_btn_type_{button_id}")
            ],
            [
                InlineKeyboardButton("📋 Изменить действие", callback_data=f"admin_edit_btn_action_{button_id}"),
                InlineKeyboardButton("📐 Изменить позицию", callback_data=f"admin_edit_btn_pos_{button_id}")
            ]
        ]
        
        # Проверяем, ведет ли кнопка к сообщению из базы данных
        target_message = None
        if button.button_type == 'callback':
            # Для callback типа проверяем, есть ли сообщение с таким page_key
            target_message = db.query(BotMessage).filter(BotMessage.page_key == button.action_data).first()
        elif button.button_type == 'message':
            # Для message типа получаем связанное сообщение
            target_message = db.query(BotMessage).filter(BotMessage.page_key == button.action_data).first()

        if target_message:
            keyboard_buttons.append([
                InlineKeyboardButton("📝 Изменить текст сообщения", callback_data=f"admin_edit_message_text_{target_message.id}")
            ])

        if button.button_type == 'message':
            keyboard_buttons.append([
                InlineKeyboardButton("➡️ Выбрать сообщение", callback_data=f"admin_select_btn_message_{button_id}")
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"admin_delete_button_{button_id}"),
            InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_buttons_{button.message_id}")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard_buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


def get_back_to_button_management_keyboard(user_id: int = None):
    """Клавиатура с кнопкой назад в управление кнопками"""
    buttons = [
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")]
    ]
    return InlineKeyboardMarkup(buttons)


async def admin_preview_message_callback(query, context, message_id: int):
    """Превью сообщения с кнопками"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.edit_message_text("❌ Сообщение не найдено.")
            return
        
        keyboard = build_keyboard_from_db(db, message_id, query.from_user.id, "nav", add_back_button=False)
        
        text = message.text
        if message.title:
            text = f"<b>{message.title}</b>\n\n{text}"
        
        parse_mode = ParseMode.HTML if message.parse_mode == 'HTML' else (ParseMode.MARKDOWN if message.parse_mode == 'Markdown' else None)
        
        buttons = [
            [InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_message_{message_id}")]
        ]
        admin_keyboard = InlineKeyboardMarkup(buttons)
        
        # Объединяем клавиатуры: сначала пользовательские кнопки, потом админская
        if keyboard and keyboard.inline_keyboard:
            combined_keyboard = keyboard.inline_keyboard + buttons
        else:
            combined_keyboard = buttons
        
        await query.edit_message_text(
            f"👁️ <b>ПРЕВЬЮ СООБЩЕНИЯ</b>\n\n{text}\n\n<i>Это то, как видят сообщение пользователи. Внизу кнопка «Назад» для возврата к редактированию.</i>",
            reply_markup=InlineKeyboardMarkup(combined_keyboard),
            parse_mode=parse_mode
        )
    finally:
        db.close()


async def admin_toggle_main_menu_callback(query, context, message_id: int):
    """Переключить флаг главного меню"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.answer("❌ Сообщение не найдено")
            return
        
        new_value = not message.is_main_menu
        updated = update_message_main_menu(db, message_id, new_value)
        if updated:
            status = "установлено" if new_value else "снято"
            await query.answer(f"✅ Главное меню {status}!")
            await admin_edit_message_callback(query, context, message_id)
        else:
            await query.answer("❌ Ошибка при обновлении")
    finally:
        db.close()


async def admin_edit_parse_mode_callback(query, context, message_id: int):
    """Выбор формата сообщения"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.edit_message_text("❌ Сообщение не найдено.")
            return
        
        buttons = [
            [
                InlineKeyboardButton("HTML", callback_data=f"admin_set_parse_mode_{message_id}_HTML"),
                InlineKeyboardButton("Markdown", callback_data=f"admin_set_parse_mode_{message_id}_Markdown")
            ],
            [
                InlineKeyboardButton("Без форматирования", callback_data=f"admin_set_parse_mode_{message_id}_None")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_message_{message_id}")
            ]
        ]
        
        await query.edit_message_text(
            "🎨 <b>ВЫБЕРИТЕ ФОРМАТ СООБЩЕНИЯ</b>\n\n"
            "• <b>HTML</b> - поддержка HTML тегов\n"
            "• <b>Markdown</b> - поддержка Markdown разметки\n"
            "• <b>Без форматирования</b> - обычный текст",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_set_parse_mode_callback(query, context, message_id: int, parse_mode: str):
    """Установить формат сообщения"""
    db = SessionLocal()
    try:
        parse_mode_value = None if parse_mode == "None" else parse_mode
        message = update_message(db, message_id, parse_mode=parse_mode_value)
        if message:
            await query.answer("✅ Формат обновлен!")
            await admin_edit_message_callback(query, context, message_id)
        else:
            await query.answer("❌ Ошибка при обновлении")
    finally:
        db.close()


async def admin_select_message_for_button_callback(query, context, button_id: int):
    """Выбор сообщения для кнопки типа message"""
    db = SessionLocal()
    try:
        button = db.query(BotButton).filter(BotButton.id == button_id).first()
        if not button:
            await query.edit_message_text("❌ Кнопка не найдена.")
            return
        
        messages = get_all_messages(db)
        # Исключаем текущее сообщение, к которому относится кнопка
        messages = [m for m in messages if m.id != button.message_id]
        
        if not messages:
            await query.edit_message_text(
                "❌ Нет доступных сообщений для перехода.",
                reply_markup=get_back_to_button_management_keyboard(query.from_user.id)
            )
            return
        
        text = "➡️ <b>ВЫБЕРИТЕ СООБЩЕНИЕ ДЛЯ ПЕРЕХОДА</b>\n\n"
        buttons = []
        
        for msg in messages:
            buttons.append([
                InlineKeyboardButton(
                    f"📝 {msg.page_key}",
                    callback_data=f"admin_set_btn_message_{button_id}_{msg.page_key}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_confirm_delete_message_callback(query, context, message_id: int):
    """Подтверждение удаления сообщения"""
    db = SessionLocal()
    try:
        message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
        if not message:
            await query.edit_message_text("❌ Сообщение не найдено.")
            return
        
        buttons_count = len(get_buttons_for_message(db, message_id))
        text = (
            "🗑️ <b>УДАЛЕНИЕ СООБЩЕНИЯ</b>\n\n"
            f"<b>Ключ:</b> {message.page_key}\n"
            f"<b>Заголовок:</b> {message.title or 'Не задан'}\n"
            f"<b>Кнопок привязано:</b> {buttons_count}\n\n"
            "<i>Удаление необратимо. Все связанные кнопки также будут удалены.</i>"
        )
        
        buttons = [
            [
                InlineKeyboardButton("✅ Удалить", callback_data=f"admin_delete_message_yes_{message_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"admin_edit_message_{message_id}")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_messages")
            ]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()


async def admin_delete_message_execute(query, context, message_id: int):
    """Удалить сообщение и вернуться к списку"""
    db = SessionLocal()
    try:
        if delete_message(db, message_id):
            await query.edit_message_text(
                "🗑️ Сообщение удалено!\n\n"
                "<i>Чтобы создать новое сообщение, вернитесь в раздел и выберите «Создать сообщение».</i>",
                reply_markup=get_back_to_button_management_keyboard(query.from_user.id),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                "❌ Не удалось удалить сообщение.",
                reply_markup=get_back_to_button_management_keyboard(query.from_user.id)
            )
    finally:
        db.close()


async def admin_set_button_message_callback(query, context, button_id: int, page_key: str):
    """Привязать кнопку типа message к выбранному сообщению"""
    db = SessionLocal()
    try:
        target_message = get_message_by_key(db, page_key)
        if not target_message:
            await query.answer("❌ Сообщение не найдено")
            return
        
        button = update_button(db, button_id, action_data=page_key)
        if button:
            await query.answer("✅ Переход обновлен!")
            await admin_edit_button_callback(query, context, button_id)
        else:
            await query.answer("❌ Не удалось обновить кнопку")
    finally:
        db.close()

