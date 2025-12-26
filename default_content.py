"""Default messages and buttons for automatic seeding."""
DEFAULT_MESSAGES = {
    "main_menu": {
        "title": "🎉 Добро пожаловать в бот психолога Сауле Сайфуллиной!",
        "text": (
            "Я помогу вам:\n"
            "• Перейти в Сообщество 5-го потока Квеста \"Денежный прорыв\"\n"
            "• Купить запись 2-го потока квеста \"Денежный прорыв\"\n"
            "• Записаться на консультацию\n"
            "• Получить полезный контент\n\n"
            "Выберите нужное действие:"
        ),
        "parse_mode": "HTML",
        "is_main_menu": True,
        "buttons": [
            {"text": "📢 Открытый канал «Про деньги»", "type": "callback", "action": "tg_channel"},
            {"text": "🎯 Бесплатный Квест 'Денежный прорыв'", "type": "callback", "action": "quest_community"},
            {"text": "🧪 Пройти тест", "type": "url", "action": "https://t.me/saule_prodengi"},
            {"text": "🧘‍♀️ Забрать практику", "type": "url", "action": "https://t.me/saule_prodengi"},
            {"text": "🚀 Доступ в клуб «Квантовый скачок»", "type": "callback", "action": "closed_club"},
            {"text": "💰 Купить Курс 'Деньги в радости'", "type": "callback", "action": "course_buy"},
            {"text": "🎬 Купить запись 2-го потока Квеста", "type": "callback", "action": "buy_quest"},
            {"text": "💬 Консультация", "type": "callback", "action": "consultation"},
            {"text": "ℹ️ О боте", "type": "callback", "action": "about"},
        ],
    }
}
