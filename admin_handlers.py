import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import SessionLocal, User, Newsletter, CourseApplication
from keyboards import get_admin_menu_keyboard, get_newsletter_keyboard
from config import ADMIN_CHAT_ID, ADMIN_IDS

logger = logging.getLogger(__name__)

# Состояния для рассылки
NEWSLETTER_STATES = {}

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа к админ-панели.")
        return
    
    admin_text = """
🔧 АДМИН-ПАНЕЛЬ

Доступные команды:
• /send_newsletter - Отправить рассылку
• /view_users - Просмотр базы пользователей  
• /view_applications - Просмотр заявок на курс
• /stats - Статистика бота

Выберите действие:
    """
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_menu_keyboard()
    )

async def send_newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание рассылки"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа.")
        return
    
    NEWSLETTER_STATES[user_id] = {'step': 'title'}
    
    await update.message.reply_text(
        "📧 СОЗДАНИЕ РАССЫЛКИ\n\n"
        "Введите заголовок рассылки:"
    )

async def handle_newsletter_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка заголовка рассылки"""
    user_id = update.effective_user.id
    
    if user_id not in NEWSLETTER_STATES:
        return
    
    if NEWSLETTER_STATES[user_id]['step'] == 'title':
        NEWSLETTER_STATES[user_id]['title'] = update.message.text
        NEWSLETTER_STATES[user_id]['step'] = 'content'
        
        await update.message.reply_text(
            "✅ Заголовок сохранен!\n\n"
            "Теперь введите текст рассылки:"
        )

async def handle_newsletter_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка содержания рассылки"""
    user_id = update.effective_user.id
    
    if user_id not in NEWSLETTER_STATES or NEWSLETTER_STATES[user_id]['step'] != 'content':
        return
    
    NEWSLETTER_STATES[user_id]['content'] = update.message.text
    NEWSLETTER_STATES[user_id]['step'] = 'preview'
    
    # Показываем превью рассылки
    preview_text = f"""
📧 ПРЕВЬЮ РАССЫЛКИ

📌 Заголовок: {NEWSLETTER_STATES[user_id]['title']}

📝 Текст:
{NEWSLETTER_STATES[user_id]['content']}

---
Отправить эту рассылку всем подписчикам?
    """
    
    await update.message.reply_text(
        preview_text,
        reply_markup=get_newsletter_keyboard()
    )

async def handle_newsletter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов рассылки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав доступа.")
        return
    
    if query.data == "send_newsletter_all":
        await send_newsletter_to_all(query, context, user_id)
    elif query.data == "edit_newsletter":
        await edit_newsletter(query, user_id)
    elif query.data == "cancel_newsletter":
        await cancel_newsletter(query, user_id)

async def send_newsletter_to_all(query, context, user_id):
    """Отправка рассылки всем пользователям"""
    if user_id not in NEWSLETTER_STATES:
        await query.edit_message_text("❌ Рассылка не найдена.")
        return
    
    newsletter_data = NEWSLETTER_STATES[user_id]
    
    # Сохраняем рассылку в базу данных
    db = SessionLocal()
    try:
        newsletter = Newsletter(
            title=newsletter_data['title'],
            content=newsletter_data['content'],
            sent_at=datetime.utcnow(),
            is_sent=True
        )
        db.add(newsletter)
        db.commit()
        
        # Получаем всех подписчиков
        subscribers = db.query(User).filter(User.is_subscribed == True).all()
        
        sent_count = 0
        failed_count = 0
        
        for subscriber in subscribers:
            try:
                await context.bot.send_message(
                    chat_id=subscriber.telegram_id,
                    text=f"📧 {newsletter_data['title']}\n\n{newsletter_data['content']}"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки рассылки пользователю {subscriber.telegram_id}: {e}")
                failed_count += 1
        
        # Очищаем состояние
        del NEWSLETTER_STATES[user_id]
        
        await query.edit_message_text(
            f"✅ Рассылка отправлена!\n\n"
            f"📊 Статистика:\n"
            f"• Отправлено: {sent_count}\n"
            f"• Ошибок: {failed_count}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки: {e}")
        await query.edit_message_text("❌ Произошла ошибка при отправке рассылки.")
        db.rollback()
    finally:
        db.close()

async def edit_newsletter(query, user_id):
    """Редактирование рассылки"""
    NEWSLETTER_STATES[user_id]['step'] = 'title'
    
    await query.edit_message_text(
        "📝 Редактирование рассылки\n\n"
        "Введите новый заголовок:"
    )

async def cancel_newsletter(query, user_id):
    """Отмена рассылки"""
    if user_id in NEWSLETTER_STATES:
        del NEWSLETTER_STATES[user_id]
    
    await query.edit_message_text("❌ Рассылка отменена.")

async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр базы пользователей"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа.")
        return
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        total_users = len(users)
        subscribed_users = len([u for u in users if u.is_subscribed])
        
        stats_text = f"""
👥 СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ

📊 Общее количество: {total_users}
✅ Подписанных: {subscribed_users}
❌ Отписанных: {total_users - subscribed_users}

📋 Последние 10 пользователей:
        """
        
        for user in users[-10:]:
            status = "✅" if user.is_subscribed else "❌"
            username = f"@{user.username}" if user.username else "не указан"
            stats_text += f"\n{status} {user.first_name} {username} (ID: {user.telegram_id})"
        
        await update.message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.")
    finally:
        db.close()

async def view_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр заявок на курс"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа.")
        return
    
    db = SessionLocal()
    try:
        applications = db.query(CourseApplication).order_by(CourseApplication.created_at.desc()).all()
        
        if not applications:
            await update.message.reply_text("📋 Заявок на курс пока нет.")
            return
        
        apps_text = f"📋 ЗАЯВКИ НА КУРС ({len(applications)})\n\n"
        
        for app in applications[:10]:  # Показываем последние 10
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(app.status, '❓')
            
            username = f"@{app.username}" if app.username else "не указан"
            apps_text += f"{status_emoji} {app.first_name} {username}\n"
            apps_text += f"   ID: {app.user_telegram_id} | {app.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        if len(applications) > 10:
            apps_text += f"... и еще {len(applications) - 10} заявок"
        
        await update.message.reply_text(apps_text)
        
    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.")
    finally:
        db.close()

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    from keyboards import get_main_menu_keyboard
    
    await update.message.reply_text(
        "🏠 Возвращаемся в главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
