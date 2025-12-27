import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8300376368:AAGGP6Ln1f0QNoNHQr0xOxpmXzJBIHSpkhg')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '5450018125'))  # ID администратора
ADMIN_CHAT_ID_2 = int(os.getenv('ADMIN_CHAT_ID_2', '235639622'))  # ID второго администратора

# Список всех администраторов
ADMIN_IDS = [ADMIN_CHAT_ID, ADMIN_CHAT_ID_2, 6682947818]

# Taplink Configuration
TAPLINK_BASE_URL = os.getenv('TAPLINK_BASE_URL', 'https://Cclub.kz')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Channel Configuration
PRIVATE_CHANNEL_ID = os.getenv('PRIVATE_CHANNEL_ID', '')
COURSE_CHANNEL_LINK = os.getenv('COURSE_CHANNEL_LINK', 'https://t.me/+V3o-HKjHGRJkM2Uy') # Ссылка на курс "Деньги в радости"
WHATSAPP_GROUP_LINK = os.getenv('WHATSAPP_GROUP_LINK', '')
TG_CHANNEL_LINK = os.getenv('TG_CHANNEL_LINK', 'https://t.me/saule_prodengi') # Ссылка на канал "Про деньги"

# Taplink URLs
TAPLINK_URLS = {
    'quest_recording': "https://cclub.kz/p/tarif-proryv/",  # Купить запись квеста "Денежный прорыв"
    'free_quest': "https://cclub.kz/p/proryv/",  # Бесплатный квест "Денежный прорыв"
    'course_buy': "https://cclub.kz/p/kurs-dendi-v-radostui/",  # Купить Курс "Деньги в радости"
    'subscription': f"{TAPLINK_BASE_URL}/subscription", 
    'consultation': "https://cclub.kz/p/consultation/",
    'offer': "https://cclub.kz/p/ofertacoursejoy/",  # Договор публичной оферты
    'privacy': "https://cclub.kz/p/cofidentialitypolitics/",  # Политика конфиденциальности
    'closed_club': "https://cclub.kz/p/closedclub/"  # Доступ в клуб «Квантовый скачок»
}
