import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config import BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_IDS, TAPLINK_URLS, PRIVATE_CHANNEL_ID, COURSE_CHANNEL_LINK, WHATSAPP_GROUP_LINK, TG_CHANNEL_LINK
from database import SessionLocal, User, CourseApplication, Newsletter, BotMessage, BotButton
from keyboards import (
    get_main_menu_keyboard, get_admin_application_keyboard, get_admin_menu_keyboard, 
    get_newsletter_keyboard, get_admin_panel_keyboard,
    get_back_keyboard, get_pagination_keyboard, get_info_keyboard
)
from navigation import add_to_history, go_back, Pages, clear_history, create_navigation_keyboard
from admin_handlers import (
    admin_panel, send_newsletter, handle_newsletter_title, handle_newsletter_content,
    handle_newsletter_callback, view_users, view_applications, back_to_main,
    NEWSLETTER_STATES
)
from admin_button_manager import (
    admin_button_management_callback, admin_manage_messages_callback,
    admin_manage_buttons_callback, admin_create_message_callback,
    admin_create_button_callback, admin_edit_message_callback,
    admin_edit_buttons_callback, admin_edit_button_callback,
    admin_preview_message_callback, admin_toggle_main_menu_callback,
    admin_edit_parse_mode_callback, admin_set_parse_mode_callback,
    admin_select_message_for_button_callback, admin_confirm_delete_message_callback,
    admin_delete_message_execute, admin_set_button_message_callback,
    admin_instruction_callback, admin_instruction_page_callback,
    ADMIN_BUTTON_STATES, get_back_to_button_management_keyboard
)
from button_manager import (
    get_message_by_key, build_keyboard_from_db, create_message, update_message,
    create_button, update_button, delete_button, get_all_messages, ensure_default_messages
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Очищаем историю навигации при старте
    clear_history(user.id)
    add_to_history(user.id, Pages.MAIN_MENU)
    
    # Сохраняем пользователя в базу данных
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not existing_user:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(new_user)
            db.commit()
            logger.info(f"Новый пользователь добавлен: {user.username}")
        
        # Гарантируем наличие преднастроенных сообщений и кнопок
        ensure_default_messages(db)
        
        # Проверяем, есть ли главное меню в базе данных
        main_menu_message = db.query(BotMessage).filter(BotMessage.is_main_menu == True).first()
        if main_menu_message:
            keyboard = build_keyboard_from_db(db, main_menu_message.id, user.id, "nav", add_back_button=False)
            text = main_menu_message.text
            if main_menu_message.title:
                text = f"<b>{main_menu_message.title}</b>\n\n{text}"
            parse_mode = ParseMode.HTML if main_menu_message.parse_mode == 'HTML' else (ParseMode.MARKDOWN if main_menu_message.parse_mode == 'Markdown' else None)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            return
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Если нет в БД, используем стандартное меню
    welcome_text = """
🎉 <b>Добро пожаловать в бот психолога Сауле Сайфуллиной!</b>

Я помогу вам:
• Перейти в Сообщество 5-го потока Квеста "Денежный прорыв"
• Купить запись 2-го потока квеста "Денежный прорыв"
• Записаться на консультацию
• Получить полезный контент

Выберите нужное действие:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user.id),
        parse_mode=ParseMode.HTML
    )



async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback запросов"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Обработка навигации
    if data == "nav_back":
        previous_page = go_back(user_id)
        if previous_page:
            await show_page_by_name(query, context, previous_page, user_id)
        else:
            await show_main_menu(query, context, user_id)
        return
    
    # Обработка админских заявок
    if data.startswith('approve_') or data.startswith('reject_'):
        await handle_admin_application_callback(update, context)
        return
    
    # Обработка рассылки
    if data in ['send_newsletter_all', 'edit_newsletter', 'cancel_newsletter']:
        await handle_newsletter_callback(update, context)
        return
    
    # Проверяем, есть ли сообщение в базе данных с таким page_key
    db = SessionLocal()
    try:
        message = get_message_by_key(db, data)
        if message:
            # Это переход на сообщение из базы данных
            add_to_history(user_id, data)
            await show_message_from_db(query, context, message, user_id)
            return
    finally:
        db.close()
    
    # Основные функции
    if data == "main_menu":
        clear_history(user_id)
        add_to_history(user_id, Pages.MAIN_MENU)
        await show_main_menu(query, context, user_id)
    elif data == "course_apply":
        add_to_history(user_id, Pages.COURSE_APPLY)
        await handle_course_application_callback(query, context)
    elif data == "course_apply_confirm":
        add_to_history(user_id, Pages.COURSE_APPLY_CONFIRM)
        await handle_course_apply_confirm_callback(query, context)
    elif data == "course_buy":
        add_to_history(user_id, Pages.COURSE_BUY)
        await handle_course_buy_callback(query, context)
    elif data == "buy_quest":
        add_to_history(user_id, Pages.BUY_QUEST)
        await handle_quest_recording_callback(query, context)
    elif data == "closed_club":
        add_to_history(user_id, Pages.CLOSED_CLUB)
        await handle_closed_club_callback(query, context)
    elif data == "tg_channel":
        add_to_history(user_id, Pages.TG_CHANNEL)
        await handle_tg_channel_callback(query, context)
    elif data == "quest_community":
        add_to_history(user_id, Pages.QUEST_COMMUNITY)
        await handle_quest_community_callback(query, context)
    elif data == "subscribe":
        add_to_history(user_id, Pages.SUBSCRIBE)
        await handle_subscription_callback(query, context)
    elif data == "demo_access":
        add_to_history(user_id, Pages.DEMO_ACCESS)
        await handle_demo_access_callback(query, context)
    elif data == "consultation":
        add_to_history(user_id, Pages.CONSULTATION)
        await handle_consultation_callback(query, context)
    elif data == "offer":
        add_to_history(user_id, Pages.OFFER)
        await handle_offer_callback(query, context)
    elif data == "privacy":
        add_to_history(user_id, Pages.PRIVACY)
        await handle_privacy_callback(query, context)
    elif data == "about":
        add_to_history(user_id, Pages.ABOUT)
        await handle_about_callback(query, context)
    
    # Админские функции
    elif data.startswith("admin_"):
        await handle_admin_callback(query, context, data)
    
    # Пагинация
    elif data.startswith("page_"):
        await handle_pagination_callback(query, context, data)

async def show_message_from_db(query, context, message: BotMessage, user_id: int):
    """Показать сообщение из базы данных"""
    db = SessionLocal()
    try:
        add_back_button = not message.is_main_menu
        keyboard = build_keyboard_from_db(db, message.id, user_id, "nav", add_back_button=add_back_button)
        
        text = message.text
        if message.title:
            text = f"<b>{message.title}</b>\n\n{text}"
        
        parse_mode = ParseMode.HTML if message.parse_mode == 'HTML' else (ParseMode.MARKDOWN if message.parse_mode == 'Markdown' else None)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
    finally:
        db.close()

async def show_main_menu(query, context, user_id: int):
    """Показать главное меню"""
    # Сначала проверяем, есть ли главное меню в базе данных
    db = SessionLocal()
    try:
        main_menu_messages = db.query(BotMessage).filter(BotMessage.is_main_menu == True).first()
        if main_menu_messages:
            await show_message_from_db(query, context, main_menu_messages, user_id)
            return
    finally:
        db.close()
    
    # Если нет в БД, используем стандартное меню
    welcome_text = """
🎉 <b>Добро пожаловать в бот психолога Сауле Сайфуллиной!</b>

Я помогу вам:
• Перейти в Сообщество 5-го потока Квеста "Денежный прорыв"
• Купить запись 2-го потока квеста "Денежный прорыв"
• Записаться на консультацию
• Получить полезный контент

Выберите нужное действие:
    """
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )

async def show_page_by_name(query, context, page_name: str, user_id: int):
    """Показать страницу по имени"""
    # Сначала проверяем базу данных
    db = SessionLocal()
    try:
        message = get_message_by_key(db, page_name)
        if message:
            await show_message_from_db(query, context, message, user_id)
            return
    finally:
        db.close()
    
    # Если не найдено в БД, используем стандартные обработчики
    if page_name == Pages.MAIN_MENU:
        await show_main_menu(query, context, user_id)
    elif page_name == Pages.ADMIN_PANEL:
        await show_admin_panel(query, context, user_id)
    elif page_name == Pages.DOCUMENTS:
        # Документы - можно создать через админ-панель
        await query.edit_message_text(
            "📄 <b>ДОКУМЕНТЫ</b>\n\n"
            "Документы можно настроить через админ-панель.",
            reply_markup=get_back_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
    elif page_name == Pages.ABOUT:
        await handle_about_callback(query, context)
    elif page_name == Pages.ADMIN_USERS:
        await view_users_callback(query, context)
    elif page_name == Pages.ADMIN_APPLICATIONS:
        await view_applications_callback(query, context)
    elif page_name == Pages.ADMIN_STATS:
        await admin_stats_callback(query, context)
    elif page_name == Pages.ADMIN_SETTINGS:
        await admin_settings_callback(query, context)
    elif page_name == Pages.ADMIN_NEWSLETTER:
        await send_newsletter_callback(query, context)
    elif page_name == Pages.ADMIN_BUTTON_MANAGEMENT:
        await admin_button_management_callback(query, context)
    else:
        await show_main_menu(query, context, user_id)

async def show_admin_panel(query, context, user_id: int):
    """Показать админ-панель"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав доступа к админ-панели.")
        return
    
    add_to_history(user_id, Pages.ADMIN_PANEL)
    
    admin_text = """
🔧 <b>АДМИН-ПАНЕЛЬ</b>

Выберите действие для управления ботом:
    """
    
    await query.edit_message_text(
        admin_text,
        reply_markup=get_admin_panel_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )

async def handle_admin_application_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback'ов от админа для заявок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    application_id = int(data.split('_')[1])
    
    db = SessionLocal()
    try:
        application = db.query(CourseApplication).filter(CourseApplication.id == application_id).first()
        if not application:
            await query.edit_message_text("Заявка не найдена.")
            return
        
        if data.startswith('approve'):
            # Одобряем заявку
            application.status = 'approved'
            application.processed_at = datetime.utcnow()
            application.processed_by = 'admin'
            db.commit()
            
            # Отправляем приветственное сообщение пользователю
            welcome_message = f"""
🎉 Поздравляем, {application.first_name}!

Ваша заявка на курс одобрена! 

🔗 Ссылка для входа в закрытый канал:
https://t.me/{PRIVATE_CHANNEL_ID}

Добро пожаловать в наше сообщество!
            """
            
            await context.bot.send_message(
                chat_id=application.user_telegram_id,
                text=welcome_message
            )
            
            await query.edit_message_text(
                f"✅ Заявка от {application.first_name} (@{application.username}) одобрена!"
            )
            
        elif data.startswith('reject'):
            # Отклоняем заявку
            application.status = 'rejected'
            application.processed_at = datetime.utcnow()
            application.processed_by = 'admin'
            db.commit()
            
            await query.edit_message_text(
                f"❌ Заявка от {application.first_name} (@{application.username}) отклонена."
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обработке заявки: {e}")
        await query.edit_message_text("Произошла ошибка при обработке заявки.")
        db.rollback()
    finally:
        db.close()

# Новые callback функции для инлайн кнопок
async def handle_course_application_callback(query, context):
    """Обработчик заявки на курс через callback"""
    # Показываем текст согласия с кнопками
    buttons = [
        [InlineKeyboardButton("🎓 Перейти к курсу", callback_data="course_apply_confirm")],
        [
            InlineKeyboardButton("📋 Договор публичной оферты", callback_data="offer"),
            InlineKeyboardButton("🔒 Политика конфиденциальности", callback_data="privacy")
        ]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "⚠️ <b>Согласие на обработку данных</b>\n\n"
        "<i>Нажимая на кнопку \"Перейти к курсу 'Деньги в радости'\", вы соглашаетесь на обработку персональных данных и с договором публичной оферты. С этими документами вы можете ознакомиться ниже.</i>\n\n"
        "Для продолжения нажмите кнопку ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_course_apply_confirm_callback(query, context):
    """Обработчик подтверждения заявки на курс"""
    user = query.from_user
    
    # Создаем заявку в базе данных
    db = SessionLocal()
    try:
        application = CourseApplication(
            user_id=user.id,
            user_telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            status='pending'
        )
        db.add(application)
        db.commit()
        
        # Отправляем сообщение пользователю
        await query.edit_message_text(
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Спасибо за ваш интерес! Я отправил(а) вашу заявку на рассмотрение администратору. "
            "После одобрения вы получите ссылку для входа в канал.",
            reply_markup=get_back_keyboard(query.from_user.id),
            parse_mode=ParseMode.HTML
        )
        
        # Отправляем уведомление админу
        admin_message = f"""
🔔 <b>Новая заявка на курс!</b>

👤 <b>Пользователь:</b>
• Имя: {user.first_name} {user.last_name or ''}
• Username: @{user.username or 'не указан'}
• ID: {user.id}

📅 Дата подачи: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        # Отправляем уведомление всем админам, кроме того кто подает заявку
        for admin_id in ADMIN_IDS:
            if admin_id != user.id:  # Не отправляем уведомление тому, кто подает заявку
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        reply_markup=get_admin_application_keyboard(application.id),
                        parse_mode=ParseMode.HTML
                    )
                    logger.info(f"Уведомление отправлено админу {admin_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")
        
        logger.info(f"Заявка на курс от пользователя {user.username} (ID: {user.id})")
        
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        db.rollback()
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке заявки. Попробуйте позже.",
            reply_markup=get_back_keyboard()
        )
    finally:
        db.close()

async def handle_course_buy_callback(query, context):
    """Обработчик покупки курса через callback"""
    buttons = [
        [InlineKeyboardButton("💰 Купить курс", url=TAPLINK_URLS['course_buy'])],
        [
            InlineKeyboardButton("📋 Договор публичной оферты", callback_data="offer"),
            InlineKeyboardButton("🔒 Политика конфиденциальности", callback_data="privacy")
        ]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "⚠️ <b>Согласие на обработку данных</b>\n\n"
        "<i>Нажимая на кнопку \"Купить Курс 'Деньги в радости'\", вы соглашаетесь на обработку персональных данных и с договором публичной оферты. С этими документами вы можете ознакомиться ниже.</i>\n\n"
        "Для покупки курса нажмите кнопку ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_offer_callback(query, context):
    """Обработчик договора публичной оферты"""
    buttons = [
        [InlineKeyboardButton("📋 Читать оферту", url=TAPLINK_URLS['offer'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "📋 <b>Договор публичной оферты</b>\n\n"
        "Ознакомьтесь с условиями договора публичной оферты:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_privacy_callback(query, context):
    """Обработчик политики конфиденциальности"""
    buttons = [
        [InlineKeyboardButton("🔒 Читать политику", url=TAPLINK_URLS['privacy'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🔒 <b>Политика конфиденциальности</b>\n\n"
        "Ознакомьтесь с политикой конфиденциальности:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_quest_recording_callback(query, context):
    """Обработчик покупки записи квеста через callback"""
    buttons = [
        [InlineKeyboardButton("💳 Оплатить запись", url=TAPLINK_URLS['quest_recording'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🎬 <b>Покупка записи 2-го потока Квеста</b>\n\n"
        "Для покупки записи 2-го потока квеста перейдите по ссылке ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_closed_club_callback(query, context):
    """Обработчик доступа в закрытый клуб через callback"""
    buttons = [
        [InlineKeyboardButton("💳 Оплатить доступ", url=TAPLINK_URLS['closed_club'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🚀 <b>Доступ в клуб «Квантовый скачок»</b>\n\n"
        "Оформите доступ на месяц по ссылке ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_subscription_callback(query, context):
    """Обработчик оплаты подписки через callback"""
    buttons = [
        [InlineKeyboardButton("💳 Оплатить подписку", url=TAPLINK_URLS['subscription'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🔒 <b>Подписка на закрытый канал</b>\n\n"
        "Для оплаты подписки в закрытый канал перейдите по ссылке ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_free_quest_callback(query, context):
    """Обработчик бесплатного квеста через callback"""
    buttons = [
        [InlineKeyboardButton("🎯 Записаться на квест", url=TAPLINK_URLS['free_quest'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🎯 <b>Квест 'Денежный прорыв'</b>\n\n"
        "Для участия в квесте перейдите по ссылке ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_tg_channel_callback(query, context):
    """Обработчик Telegram канала Про деньги через callback"""
    buttons = [
        [InlineKeyboardButton("📢 Перейти в канал", url=TG_CHANNEL_LINK)]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "📢 <b>ТГ Канал Про деньги</b>\n\n"
        "Подписывайтесь на мой канал, где я делюсь полезной информацией о психологии денег:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_quest_community_callback(query, context):
    """Обработчик сообщества 5-го потока квеста через callback"""
    buttons = [
        [InlineKeyboardButton("👥 Перейти в сообщество", url="https://chat.whatsapp.com/J9EEPPE4y6t0WeGsq6gLsH")]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "🎯 <b>Бесплатный Квест 'Денежный прорыв'</b>\n\n"
        "Начало: 6 октября\n\n"
        "Присоединяйтесь к бесплатному квесту 'Денежный прорыв':",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_demo_access_callback(query, context):
    """Обработчик демо-доступа через callback"""
    if PRIVATE_CHANNEL_ID:
        buttons = [
            [InlineKeyboardButton("🔗 Получить демо-доступ", url=f"https://t.me/{PRIVATE_CHANNEL_ID}")]
        ]
        reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
        
        await query.edit_message_text(
            "🎁 <b>3-х дневный демо-доступ</b>\n\n"
            "Вот ваша ссылка для получения демо-доступа к курсу:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await query.edit_message_text(
            "🎁 <b>Демо-доступ</b>\n\n"
            "Демо-доступ временно недоступен. "
            "Обратитесь к администратору для получения доступа.",
            reply_markup=get_back_keyboard(query.from_user.id),
            parse_mode=ParseMode.HTML
        )

async def handle_consultation_callback(query, context):
    """Обработчик записи на консультацию через callback"""
    buttons = [
        [InlineKeyboardButton("📅 Записаться на консультацию", url=TAPLINK_URLS['consultation'])]
    ]
    reply_markup = create_navigation_keyboard(query.from_user.id, buttons, "nav")
    
    await query.edit_message_text(
        "💬 <b>Запись на консультацию</b>\n\n"
        "Для записи на консультацию перейдите по ссылке ниже:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_about_callback(query, context):
    """Обработчик информации о боте через callback"""
    await query.edit_message_text(
        "ℹ️ <b>О боте</b>\n\n"
        "Этот бот создан для автоматизации работы психолога:\n\n"
        "🎓 <b>Курсы</b> - доступ к обучающим материалам\n"
        "🎬 <b>Квесты</b> - интерактивные задания\n"
        "💬 <b>Консультации</b> - персональные сессии\n"
        "📧 <b>Рассылки</b> - полезный контент\n\n"
        "Все функции доступны через главное меню!",
        reply_markup=get_info_keyboard(query.from_user.id),
        parse_mode=ParseMode.HTML
    )

async def handle_admin_callback(query, context, data):
    """Обработчик админских callback'ов"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав доступа.", reply_markup=get_back_keyboard(user_id))
        return
    
    if data == "admin_send_newsletter":
        add_to_history(user_id, Pages.ADMIN_NEWSLETTER)
        await send_newsletter_callback(query, context)
    elif data == "admin_view_users":
        add_to_history(user_id, Pages.ADMIN_USERS)
        await view_users_callback(query, context)
    elif data == "admin_view_applications":
        add_to_history(user_id, Pages.ADMIN_APPLICATIONS)
        await view_applications_callback(query, context)
    elif data == "admin_stats":
        add_to_history(user_id, Pages.ADMIN_STATS)
        await admin_stats_callback(query, context)
    elif data == "admin_settings":
        add_to_history(user_id, Pages.ADMIN_SETTINGS)
        await admin_settings_callback(query, context)
    elif data == "admin_button_management":
        add_to_history(user_id, Pages.ADMIN_BUTTON_MANAGEMENT)
        await admin_button_management_callback(query, context)
    elif data == "admin_manage_messages":
        await admin_manage_messages_callback(query, context)
    elif data == "admin_manage_buttons":
        await admin_manage_buttons_callback(query, context)
    elif data == "admin_instruction":
        await admin_instruction_callback(query, context)
    elif data.startswith("admin_instruction_section_"):
        section = data[len("admin_instruction_section_"):]
        await admin_instruction_callback(query, context, section)
    elif data.startswith("admin_instruction_page_"):
        try:
            index = int(data[len("admin_instruction_page_"):])
        except ValueError:
            await query.answer("Некорректный номер страницы")
            return
        await admin_instruction_page_callback(query, context, index)
    elif data == "admin_create_message":
        await admin_create_message_callback(query, context)
    elif data == "admin_create_button":
        await admin_create_button_callback(query, context)
    elif data.startswith("admin_edit_message_"):
        message_id = int(data.split("_")[-1])
        await admin_edit_message_callback(query, context, message_id)
    elif data.startswith("admin_edit_buttons_"):
        message_id = int(data.split("_")[-1])
        await admin_edit_buttons_callback(query, context, message_id)
    elif data.startswith("admin_edit_button_"):
        button_id = int(data.split("_")[-1])
        await admin_edit_button_callback(query, context, button_id)
    elif data.startswith("admin_quick_edit_button_"):
        button_id = int(data.split("_")[-1])
        await admin_edit_button_callback(query, context, button_id)
    elif data.startswith("admin_create_button_msg_"):
        message_id = int(data.split("_")[-1])
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'create_button',
            'step': 'text',
            'message_id': message_id
        }
        await query.edit_message_text(
            "➕ <b>СОЗДАНИЕ КНОПКИ</b>\n\n"
            "Шаг 1/5: Введите текст кнопки:",
            reply_markup=get_back_to_button_management_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
    elif data.startswith("admin_edit_msg_text_"):
        message_id = int(data.split("_")[-1])
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'edit_message_text',
            'message_id': message_id
        }
        await query.edit_message_text(
            "✏️ <b>РЕДАКТИРОВАНИЕ ТЕКСТА СООБЩЕНИЯ</b>\n\n"
            "Введите новый текст сообщения:",
            reply_markup=get_back_to_button_management_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
    elif data.startswith("admin_edit_msg_title_"):
        message_id = int(data.split("_")[-1])
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'edit_message_title',
            'message_id': message_id
        }
        await query.edit_message_text(
            "✏️ <b>РЕДАКТИРОВАНИЕ ЗАГОЛОВКА СООБЩЕНИЯ</b>\n\n"
            "Введите новый заголовок (или отправьте '-' для удаления):",
            reply_markup=get_back_to_button_management_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
    elif data.startswith("admin_edit_msg_parse_mode_"):
        message_id = int(data.split("_")[-1])
        await admin_edit_parse_mode_callback(query, context, message_id)
    elif data.startswith("admin_set_parse_mode_"):
        # Формат: admin_set_parse_mode_{message_id}_{parse_mode}
        parts = data.split("_")
        message_id = int(parts[-2])
        parse_mode = parts[-1]
        await admin_set_parse_mode_callback(query, context, message_id, parse_mode)
    elif data.startswith("admin_toggle_main_menu_"):
        message_id = int(data.split("_")[-1])
        await admin_toggle_main_menu_callback(query, context, message_id)
    elif data.startswith("admin_preview_message_"):
        message_id = int(data.split("_")[-1])
        await admin_preview_message_callback(query, context, message_id)
    elif data.startswith("admin_delete_message_yes_"):
        message_id = int(data.split("_")[-1])
        await admin_delete_message_execute(query, context, message_id)
    elif data.startswith("admin_delete_message_"):
        message_id = int(data.split("_")[-1])
        await admin_confirm_delete_message_callback(query, context, message_id)
    elif data.startswith("admin_edit_btn_text_"):
        button_id = int(data.split("_")[-1])
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'edit_button_text',
            'button_id': button_id
        }
        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if button:
                await query.edit_message_text(
                    "✏️ <b>РЕДАКТИРОВАНИЕ ТЕКСТА КНОПКИ</b>\n\n"
                    f"<b>Текущий текст:</b> {button.text}\n\n"
                    "<i>Просто напишите новый текст кнопки и отправьте сообщение. Например: \"Купить курс\" или \"📚 Перейти в канал\"</i>",
                    reply_markup=get_back_to_button_management_keyboard(user_id),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text("❌ Кнопка не найдена.")
        finally:
            db.close()
    elif data.startswith("admin_edit_btn_type_"):
        button_id = int(data.split("_")[-1])
        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if not button:
                await query.edit_message_text("❌ Кнопка не найдена.")
                return
            
            buttons = [
                [
                    InlineKeyboardButton("🔄 Callback (внутренний переход)", callback_data=f"admin_set_btn_type_{button_id}_callback")
                ],
                [
                    InlineKeyboardButton("🔗 URL (ссылка)", callback_data=f"admin_set_btn_type_{button_id}_url")
                ],
                [
                    InlineKeyboardButton("➡️ Message (переход на сообщение)", callback_data=f"admin_set_btn_type_{button_id}_message")
                ],
                [
                    InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")
                ]
            ]
            
            await query.edit_message_text(
                "🔄 <b>ВЫБЕРИТЕ ТИП КНОПКИ</b>\n\n"
                "• <b>Callback</b> - внутренний переход (callback_data)\n"
                "• <b>URL</b> - внешняя ссылка\n"
                "• <b>Message</b> - переход на другое сообщение",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        finally:
            db.close()
    elif data.startswith("admin_set_btn_type_"):
        parts = data.split("_")
        button_id = int(parts[-2])
        button_type = parts[-1]
        
        db = SessionLocal()
        try:
            button = update_button(db, button_id, button_type=button_type)
            if button:
                await query.answer("✅ Тип кнопки изменен!")
                if button_type == "message":
                    await admin_select_message_for_button_callback(query, context, button_id)
                else:
                    await admin_edit_button_callback(query, context, button_id)
            else:
                await query.answer("❌ Ошибка при изменении типа")
        finally:
            db.close()
    elif data.startswith("admin_edit_btn_action_"):
        button_id = int(data.split("_")[-1])
        user_id = query.from_user.id

        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if not button:
                await query.edit_message_text("❌ Кнопка не найдена.")
                return

            # Показываем выбор типа действия через кнопки
            action_buttons = [
                [InlineKeyboardButton("🔄 Внутренний переход", callback_data=f"admin_set_btn_action_type_{button_id}_callback")],
                [InlineKeyboardButton("🔗 Ссылка", callback_data=f"admin_set_btn_action_type_{button_id}_url")],
                [InlineKeyboardButton("➡️ Переход на сообщение", callback_data=f"admin_set_btn_action_type_{button_id}_message")]
            ]

            action_buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")])

            type_descriptions = {
                'callback': 'Внутренний переход в боте',
                'url': 'Ссылка на внешний сайт/канал',
                'message': 'Переход к другому сообщению'
            }

            await query.edit_message_text(
                f"📋 <b>ВЫБОР ТИПА ДЕЙСТВИЯ</b>\n\n"
                f"<b>Текущий тип:</b> {type_descriptions.get(button.button_type, button.button_type)}\n"
                f"<b>Текущее действие:</b> {button.action_data}\n\n"
                "<i>Выберите новый тип действия для кнопки:</i>",
                reply_markup=InlineKeyboardMarkup(action_buttons),
                parse_mode=ParseMode.HTML
            )
        finally:
            db.close()
    elif data.startswith("admin_set_btn_action_type_"):
        parts = data.split("_")
        button_id = int(parts[-2])
        action_type = parts[-1]
        user_id = query.from_user.id

        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if not button:
                await query.answer("❌ Кнопка не найдена")
                return

            # Меняем тип кнопки если нужно
            if button.button_type != action_type:
                update_button(db, button_id, button_type=action_type)

            # Устанавливаем состояние для ввода действия
            ADMIN_BUTTON_STATES[user_id] = {
                'action': 'edit_button_action',
                'button_id': button_id
            }

            type_hints = {
                'callback': 'Напишите имя страницы для перехода (например: main_menu, course_info)',
                'url': 'Напишите ссылку с https:// (например: https://t.me/channel)',
                'message': 'Выберите сообщение из списка'
            }

            if action_type == 'message':
                await admin_select_message_for_button_callback(query, context, button_id)
            else:
                await query.edit_message_text(
                    f"📋 <b>ВВОД ДЕЙСТВИЯ</b>\n\n"
                    f"<b>Тип:</b> {action_type}\n\n"
                    f"<i>{type_hints.get(action_type, 'Введите действие')}</i>",
                    reply_markup=get_back_to_button_management_keyboard(user_id),
                    parse_mode=ParseMode.HTML
                )
        finally:
            db.close()
    elif data.startswith("admin_edit_btn_pos_"):
        button_id = int(data.split("_")[-1])
        user_id = query.from_user.id

        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if not button:
                await query.edit_message_text("❌ Кнопка не найдена.")
                return

            # Показываем текущую позицию и предлагаем варианты
            position_buttons = []

            # Кнопки для выбора строки (0-4)
            row_buttons = []
            for row in range(5):
                row_buttons.append(
                    InlineKeyboardButton(
                        f"Строка {row}" + (" ✓" if button.row == row else ""),
                        callback_data=f"admin_set_btn_row_{button_id}_{row}"
                    )
                )
            position_buttons.append(row_buttons)

            # Кнопки для выбора порядка (0-4)
            order_buttons = []
            for order in range(5):
                order_buttons.append(
                    InlineKeyboardButton(
                        f"Порядок {order}" + (" ✓" if button.order == order else ""),
                        callback_data=f"admin_set_btn_order_{button_id}_{order}"
                    )
                )
            position_buttons.append(order_buttons)

            position_buttons.append([
                InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")
            ])

            await query.edit_message_text(
                f"📐 <b>ИЗМЕНЕНИЕ ПОЗИЦИИ КНОПКИ</b>\n\n"
                f"<b>Текущая позиция:</b> Строка {button.row}, Порядок {button.order}\n\n"
                "<i>Сначала выберите строку (горизонтальный ряд), затем порядок в строке (позиция слева направо).</i>",
                reply_markup=InlineKeyboardMarkup(position_buttons),
                parse_mode=ParseMode.HTML
            )
        finally:
            db.close()
    elif data.startswith("admin_set_btn_row_"):
        parts = data.split("_")
        button_id = int(parts[-2])
        new_row = int(parts[-1])

        db = SessionLocal()
        try:
            button = update_button(db, button_id, row=new_row)
            if button:
                await query.answer(f"Строка изменена на {new_row}")
                # Обновляем сообщение с новой позицией
                await query.edit_message_text(
                    f"📐 <b>ИЗМЕНЕНИЕ ПОЗИЦИИ КНОПКИ</b>\n\n"
                    f"<b>Текущая позиция:</b> Строка {new_row}, Порядок {button.order}\n\n"
                    "<i>Сначала выберите строку (горизонтальный ряд), затем порядок в строке (позиция слева направо).</i>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"Строка {r}" + (" ✓" if r == new_row else ""), callback_data=f"admin_set_btn_row_{button_id}_{r}") for r in range(5)],
                        [InlineKeyboardButton(f"Порядок {o}" + (" ✓" if o == button.order else ""), callback_data=f"admin_set_btn_order_{button_id}_{o}") for o in range(5)],
                        [InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.answer("❌ Ошибка")
        finally:
            db.close()
    elif data.startswith("admin_set_btn_order_"):
        parts = data.split("_")
        button_id = int(parts[-2])
        new_order = int(parts[-1])

        db = SessionLocal()
        try:
            button = update_button(db, button_id, order=new_order)
            if button:
                await query.answer(f"Порядок изменен на {new_order}")
                # Обновляем сообщение с новой позицией
                await query.edit_message_text(
                    f"📐 <b>ИЗМЕНЕНИЕ ПОЗИЦИИ КНОПКИ</b>\n\n"
                    f"<b>Текущая позиция:</b> Строка {new_row}, Порядок {button.order}\n\n"
                    "<i>Сначала выберите строку (горизонтальный ряд), затем порядок в строке (позиция слева направо).</i>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"Строка {r}" + (" ✓" if r == new_row else ""), callback_data=f"admin_set_btn_row_{button_id}_{r}") for r in range(5)],
                        [InlineKeyboardButton(f"Порядок {o}" + (" ✓" if o == button.order else ""), callback_data=f"admin_set_btn_order_{button_id}_{o}") for o in range(5)],
                        [InlineKeyboardButton("🔙 Назад", callback_data=f"admin_edit_button_{button_id}")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.answer("❌ Ошибка")
        finally:
            db.close()
    elif data.startswith("admin_edit_message_text_"):
        message_id = int(data.split("_")[-1])
        user_id = query.from_user.id
        ADMIN_BUTTON_STATES[user_id] = {
            'action': 'edit_message_text',
            'message_id': message_id
        }

        db = SessionLocal()
        try:
            message = db.query(BotMessage).filter(BotMessage.id == message_id).first()
            if message:
                await query.edit_message_text(
                    "✏️ <b>РЕДАКТИРОВАНИЕ ТЕКСТА СООБЩЕНИЯ</b>\n\n"
                    f"<b>Текущий текст:</b>\n{message.text}\n\n"
                    "<i>Просто напишите новый текст сообщения и отправьте. Поддерживается форматирование HTML (жирный, курсив, ссылки).</i>",
                    reply_markup=get_back_to_button_management_keyboard(user_id),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text("❌ Сообщение не найдено.")
        finally:
            db.close()
    elif data.startswith("admin_set_btn_message_"):
        payload = data[len("admin_set_btn_message_"):]
        if "_" not in payload:
            await query.answer("❌ Некорректные данные")
            return
        button_id_str, page_key = payload.split("_", 1)
        try:
            button_id = int(button_id_str)
        except ValueError:
            await query.answer("❌ Некорректный идентификатор кнопки")
            return
        await admin_set_button_message_callback(query, context, button_id, page_key)
    elif data.startswith("admin_select_btn_message_"):
        button_id = int(data.split("_")[-1])
        await admin_select_message_for_button_callback(query, context, button_id)
    elif data.startswith("admin_delete_button_"):
        button_id = int(data.split("_")[-1])
        db = SessionLocal()
        try:
            button = db.query(BotButton).filter(BotButton.id == button_id).first()
            if button:
                message_id = button.message_id
                if delete_button(db, button_id):
                    await query.answer("✅ Кнопка удалена!")
                    await admin_edit_buttons_callback(query, context, message_id)
                else:
                    await query.answer("❌ Ошибка при удалении")
            else:
                await query.answer("❌ Кнопка не найдена")
        finally:
            db.close()
    elif data.startswith("admin_set_main_menu_"):
        is_main_menu = data.split("_")[-1] == "1"
        user_id = query.from_user.id
        
        if user_id in ADMIN_BUTTON_STATES:
            state = ADMIN_BUTTON_STATES[user_id]
            if state.get('action') == 'create_message':
                db = SessionLocal()
                try:
                    message = create_message(
                        db,
                        state['page_key'],
                        state.get('title'),
                        state['text'],
                        is_main_menu=is_main_menu
                    )
                    del ADMIN_BUTTON_STATES[user_id]
                    await query.edit_message_text(
                        f"✅ Сообщение '{message.page_key}' успешно создано!\n\n"
                        "<i>Теперь вы можете добавить к нему кнопки — выберите раздел «Управление кнопками» или вернитесь к списку сообщений.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                finally:
                    db.close()
    elif data.startswith("admin_btn_type_"):
        parts = data.split("_")
        button_type = parts[-2]  # callback, url, message
        message_id = int(parts[-1])
        
        user_id = query.from_user.id
        if user_id in ADMIN_BUTTON_STATES:
            state = ADMIN_BUTTON_STATES[user_id]
            if state.get('action') == 'create_button' and state.get('message_id') == message_id:
                state['button_type'] = button_type
                state['step'] = 'action'
                
                type_hint = {
                    'callback': 'callback_data (например: main_menu, course_info)',
                    'url': 'URL ссылка (например: https://example.com)',
                    'message': 'page_key сообщения (например: main_menu, course_info)'
                }.get(button_type, 'действие')
                
                example_text = ""
                if button_type == 'url':
                    example_text = "\n\n<i>Пример: https://t.me/saule_prodengi\nВажно: URL должен начинаться с http:// или https://</i>"
                elif button_type == 'callback':
                    example_text = "\n\n<i>Пример: main_menu, course_info, tg_channel</i>"
                elif button_type == 'message':
                    example_text = "\n\n<i>Пример: main_menu, course_info\n(ключ страницы, на которую будет переход)</i>"
                
                await query.edit_message_text(
                    f"✅ Тип кнопки сохранен!\n\n"
                    f"Шаг 3/5: Введите действие ({type_hint}):{example_text}",
                    reply_markup=get_back_to_button_management_keyboard(user_id),
                    parse_mode=ParseMode.HTML
                )

async def send_newsletter_callback(query, context):
    """Callback для создания рассылки"""
    NEWSLETTER_STATES[query.from_user.id] = {'step': 'title'}
    
    await query.edit_message_text(
        "📧 <b>СОЗДАНИЕ РАССЫЛКИ</b>\n\n"
        "Введите заголовок рассылки:",
        reply_markup=get_back_keyboard(query.from_user.id),
        parse_mode=ParseMode.HTML
    )

async def view_users_callback(query, context):
    """Callback для просмотра пользователей"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        total_users = len(users)
        subscribed_users = len([u for u in users if u.is_subscribed])
        
        stats_text = f"""
👥 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ</b>

📊 Общее количество: {total_users}
✅ Подписанных: {subscribed_users}
❌ Отписанных: {total_users - subscribed_users}

📋 <b>Последние 5 пользователей:</b>
        """
        
        for user in users[-5:]:
            status = "✅" if user.is_subscribed else "❌"
            username = f"@{user.username}" if user.username else "не указан"
            stats_text += f"\n{status} {user.first_name} {username} (ID: {user.telegram_id})"
        
        await query.edit_message_text(
            stats_text,
            reply_markup=get_back_keyboard(query.from_user.id),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        await query.edit_message_text("❌ Ошибка при получении данных.", reply_markup=get_back_keyboard(query.from_user.id))
    finally:
        db.close()

async def view_applications_callback(query, context):
    """Callback для просмотра заявок"""
    db = SessionLocal()
    try:
        applications = db.query(CourseApplication).order_by(CourseApplication.created_at.desc()).all()
        
        if not applications:
            await query.edit_message_text("📋 Заявок на курс пока нет.", reply_markup=get_back_keyboard(query.from_user.id))
            return
        
        apps_text = f"📋 <b>ЗАЯВКИ НА КУРС ({len(applications)})</b>\n\n"
        
        for app in applications[:5]:  # Показываем последние 5
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(app.status, '❓')
            
            username = f"@{app.username}" if app.username else "не указан"
            apps_text += f"{status_emoji} {app.first_name} {username}\n"
            apps_text += f"   ID: {app.user_telegram_id} | {app.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        if len(applications) > 5:
            apps_text += f"... и еще {len(applications) - 5} заявок"
        
        await query.edit_message_text(
            apps_text,
            reply_markup=get_back_keyboard(query.from_user.id),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {e}")
        await query.edit_message_text("❌ Ошибка при получении данных.", reply_markup=get_back_keyboard(query.from_user.id))
    finally:
        db.close()

async def admin_stats_callback(query, context):
    """Callback для статистики"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        applications = db.query(CourseApplication).all()
        newsletters = db.query(Newsletter).all()
        
        stats_text = f"""
📊 <b>СТАТИСТИКА БОТА</b>

👥 <b>Пользователи:</b>
• Всего: {len(users)}
• Подписанных: {len([u for u in users if u.is_subscribed])}

📋 <b>Заявки на курс:</b>
• Всего: {len(applications)}
• Ожидают: {len([a for a in applications if a.status == 'pending'])}
• Одобрены: {len([a for a in applications if a.status == 'approved'])}
• Отклонены: {len([a for a in applications if a.status == 'rejected'])}

📧 <b>Рассылки:</b>
• Всего отправлено: {len(newsletters)}
        """
        
        await query.edit_message_text(
            stats_text,
            reply_markup=get_back_keyboard(query.from_user.id),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await query.edit_message_text("❌ Ошибка при получении данных.", reply_markup=get_back_keyboard(query.from_user.id))
    finally:
        db.close()

async def admin_settings_callback(query, context):
    """Callback для настроек"""
    await query.edit_message_text(
        "⚙️ <b>НАСТРОЙКИ</b>\n\n"
        "В данный момент настройки недоступны.\n"
        "Все конфигурации задаются в файле config.py",
        reply_markup=get_back_keyboard(query.from_user.id),
        parse_mode=ParseMode.HTML
    )

async def handle_pagination_callback(query, context, data):
    """Обработчик пагинации"""
    # Здесь можно добавить логику для пагинации списков
    await query.answer("Пагинация в разработке")

async def handle_newsletter_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода текста для рассылки и управления кнопками"""
    user_id = update.effective_user.id
    
    # Сначала проверяем состояния управления кнопками
    if user_id in ADMIN_BUTTON_STATES:
        state = ADMIN_BUTTON_STATES[user_id]
        action = state.get('action')
        
        db = SessionLocal()
        try:
            if action == 'create_message':
                step = state.get('step')
                if step == 'page_key':
                    page_key = update.message.text.strip()
                    # Проверка на валидность ключа
                    if not page_key.replace('_', '').replace('-', '').isalnum():
                        await update.message.reply_text(
                            "❌ Ключ должен содержать только латинские буквы, цифры, подчеркивания и дефисы.\n"
                            "Попробуйте еще раз:\n\n"
                            "<i>Например: main_menu, promo_start, faq_step1.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                        return
                    
                    # Проверка на уникальность
                    existing = get_message_by_key(db, page_key)
                    if existing:
                        await update.message.reply_text(
                            f"❌ Сообщение с ключом '{page_key}' уже существует.\n"
                            "Введите другой ключ:\n\n"
                            "<i>Добавьте приставку, например: promo_main, promo_main_v2.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                        return
                    
                    state['page_key'] = page_key
                    state['step'] = 'title'
                    await update.message.reply_text(
                        "✅ Ключ сохранен!\n\n"
                        "Шаг 2/4: Введите заголовок сообщения (или отправьте '-' для пропуска):\n\n"
                        "<i>Заголовок увидит пользователь над текстом. Можно пропустить, отправив символ '-'.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                elif step == 'title':
                    title = update.message.text.strip()
                    if title == '-':
                        title = None
                    state['title'] = title
                    state['step'] = 'text'
                    await update.message.reply_text(
                        "✅ Заголовок сохранен!\n\n"
                        "Шаг 3/4: Введите текст сообщения:\n\n"
                        "<i>Напишите основной текст экрана — можно использовать переносы строк и эмодзи.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                elif step == 'text':
                    text = update.message.text
                    state['text'] = text
                    state['step'] = 'is_main_menu'
                    
                    buttons = [
                        [
                            InlineKeyboardButton("✅ Да", callback_data="admin_set_main_menu_1"),
                            InlineKeyboardButton("❌ Нет", callback_data="admin_set_main_menu_0")
                        ],
                        [
                            InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")
                        ]
                    ]
                    
                    await update.message.reply_text(
                        "✅ Текст сохранен!\n\n"
                        "Шаг 4/4: Это главное меню?\n\n"
                        "<i>Выберите «Да», если это стартовый экран. «Нет» — для внутренних страниц.</i>",
                        reply_markup=InlineKeyboardMarkup(buttons),
                        parse_mode=ParseMode.HTML
                    )
                return
            
            elif action == 'create_button':
                step = state.get('step')
                message_id = state.get('message_id')
                
                if step == 'text':
                    state['text'] = update.message.text
                    state['step'] = 'type'
                    
                    buttons = [
                        [
                            InlineKeyboardButton("🔄 Callback", callback_data=f"admin_btn_type_callback_{message_id}"),
                            InlineKeyboardButton("🔗 URL", callback_data=f"admin_btn_type_url_{message_id}")
                        ],
                        [
                            InlineKeyboardButton("➡️ Message", callback_data=f"admin_btn_type_message_{message_id}")
                        ],
                        [
                            InlineKeyboardButton("🔙 Назад", callback_data="admin_button_management")
                        ]
                    ]
                    
                    await update.message.reply_text(
                        "✅ Текст кнопки сохранен!\n\n"
                        "Шаг 2/5: Выберите тип кнопки:\n\n"
                        "<i>Callback — внутренний переход, URL — внешняя ссылка, Message — переход на другое сообщение.</i>",
                        reply_markup=InlineKeyboardMarkup(buttons),
                        parse_mode=ParseMode.HTML
                    )
                elif step == 'action':
                    action_data = update.message.text.strip()
                    
                    # Валидация URL
                    if state.get('button_type') == 'url':
                        if not action_data.startswith(('http://', 'https://')):
                            await update.message.reply_text(
                                "❌ URL должен начинаться с http:// или https://\n\n"
                                "<i>Пример: https://t.me/saule_prodengi</i>\n"
                                "Попробуйте еще раз:",
                                reply_markup=get_back_to_button_management_keyboard(user_id),
                                parse_mode=ParseMode.HTML
                            )
                            return
                    
                    state['action_data'] = action_data
                    state['step'] = 'row'
                    await update.message.reply_text(
                        "✅ Действие сохранено!\n\n"
                        "Шаг 4/5: Введите номер строки (начиная с 0):\n\n"
                        "<i>Строки нумеруются сверху вниз: 0 — первая, 1 — вторая и т.д.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                elif step == 'row':
                    try:
                        row = int(update.message.text.strip())
                        state['row'] = row
                        state['step'] = 'order'
                        await update.message.reply_text(
                            "✅ Строка сохранена!\n\n"
                            "Шаг 5/5: Введите порядок в строке (начиная с 0):\n\n"
                            "<i>0 — крайняя левая позиция, 1 — следующая справа и так далее.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                    except ValueError:
                        await update.message.reply_text(
                            "❌ Введите число! Попробуйте еще раз:\n\n"
                            "<i>Используйте только цифры, например 0 или 1.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                elif step == 'order':
                    try:
                        order = int(update.message.text.strip())
                        # Создаем кнопку
                        button = create_button(
                            db,
                            state['message_id'],
                            state['text'],
                            state['button_type'],
                            state['action_data'],
                            state['row'],
                            order
                        )
                        del ADMIN_BUTTON_STATES[user_id]
                        await update.message.reply_text(
                            f"✅ Кнопка '{button.text}' успешно создана!\n\n"
                            "<i>Вернитесь к списку кнопок, чтобы проверить расположение или добавить новые.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                    except ValueError:
                        await update.message.reply_text(
                            "❌ Введите число! Попробуйте еще раз:\n\n"
                            "<i>Используйте только цифры, например 0 или 1.</i>",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                return
            
            elif action == 'edit_message_text':
                message_id = state.get('message_id')
                new_text = update.message.text
                message = update_message(db, message_id, text=new_text)
                if message:
                    del ADMIN_BUTTON_STATES[user_id]
                    await update.message.reply_text(
                        "✅ Текст сообщения обновлен!\n\n"
                        "<i>Откройте превью или раздел кнопок, чтобы убедиться в результате.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                return
            
            elif action == 'edit_message_title':
                message_id = state.get('message_id')
                new_title = update.message.text.strip()
                if new_title == '-':
                    new_title = None
                message = update_message(db, message_id, title=new_title)
                if message:
                    del ADMIN_BUTTON_STATES[user_id]
                    await update.message.reply_text(
                        "✅ Заголовок сообщения обновлен!\n\n"
                        "<i>Если заголовок не нужен, отправьте '-' и он будет скрыт.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                return
            
            elif action == 'edit_button_text':
                button_id = state.get('button_id')
                new_text = update.message.text
                button = update_button(db, button_id, text=new_text)
                if button:
                    del ADMIN_BUTTON_STATES[user_id]
                    await update.message.reply_text(
                        "✅ Текст кнопки обновлен!\n\n"
                        "<i>Проверьте итоговый вид через список кнопок.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                return
            
            elif action == 'edit_message_text':
                message_id = state.get('message_id')
                new_text = update.message.text.strip()

                if not new_text:
                    await update.message.reply_text(
                        "❌ Текст не может быть пустым!\n\n"
                        "<i>Напишите новый текст сообщения.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                    return

                message = update_message(db, message_id, text=new_text)
                if message:
                    del ADMIN_BUTTON_STATES[user_id]
                    await update.message.reply_text(
                        "✅ Текст сообщения обновлен!\n\n"
                        "<i>Вернитесь к списку кнопок для проверки.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при обновлении текста сообщения.",
                        reply_markup=get_back_to_button_management_keyboard(user_id)
                    )
                return

            elif action == 'edit_button_action':
                button_id = state.get('button_id')
                new_action = update.message.text.strip()
                
                # Проверяем тип кнопки и валидируем URL
                button = db.query(BotButton).filter(BotButton.id == button_id).first()
                if button and button.button_type == 'url':
                    if not new_action.startswith(('http://', 'https://')):
                        await update.message.reply_text(
                            "❌ URL должен начинаться с http:// или https://\n\n"
                            "<i>Пример правильного URL: https://t.me/saule_prodengi</i>\n"
                            "Попробуйте еще раз:",
                            reply_markup=get_back_to_button_management_keyboard(user_id),
                            parse_mode=ParseMode.HTML
                        )
                        return
                
                button = update_button(db, button_id, action_data=new_action)
                if button:
                    del ADMIN_BUTTON_STATES[user_id]
                    await update.message.reply_text(
                        "✅ Действие кнопки обновлено!\n\n"
                        "<i>Проверьте работу кнопки через превью сообщения.</i>",
                        reply_markup=get_back_to_button_management_keyboard(user_id),
                        parse_mode=ParseMode.HTML
                    )
                return
            
        finally:
            db.close()
    
    # Обработка ввода для рассылки
    if user_id not in NEWSLETTER_STATES:
        # Если пользователь не в процессе создания рассылки, показываем главное меню
        await update.message.reply_text(
            "Выберите действие из меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Обработка ввода для рассылки
    if NEWSLETTER_STATES[user_id]['step'] == 'title':
        NEWSLETTER_STATES[user_id]['title'] = update.message.text
        NEWSLETTER_STATES[user_id]['step'] = 'content'
        
        await update.message.reply_text(
            "✅ Заголовок сохранен!\n\nТеперь введите текст рассылки:",
            reply_markup=get_back_keyboard(user_id)
        )
    elif NEWSLETTER_STATES[user_id]['step'] == 'content':
        NEWSLETTER_STATES[user_id]['content'] = update.message.text
        NEWSLETTER_STATES[user_id]['step'] = 'preview'
        
        # Показываем превью рассылки
        preview_text = f"""
📧 <b>ПРЕВЬЮ РАССЫЛКИ</b>

📌 <b>Заголовок:</b> {NEWSLETTER_STATES[user_id]['title']}

📝 <b>Текст:</b>
{NEWSLETTER_STATES[user_id]['content']}

---
Отправить эту рассылку всем подписчикам?
        """
        
        await update.message.reply_text(
            preview_text,
            reply_markup=get_newsletter_keyboard(),
            parse_mode=ParseMode.HTML
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа к админ-панели.")
        return
    
    # Очищаем историю и добавляем админ-панель
    clear_history(user_id)
    add_to_history(user_id, Pages.ADMIN_PANEL)
    
    admin_text = """
🔧 <b>АДМИН-ПАНЕЛЬ</b>

Выберите действие для управления ботом:
    """
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_panel_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Обработчик текстовых сообщений для рассылки
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_newsletter_input))
    
    # Основной обработчик callback'ов
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
