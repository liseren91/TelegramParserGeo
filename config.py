"""
Configuration module for Telegram Parser
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')

# Google Sheets configuration
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')

# Telegram channels to parse
TELEGRAM_CHANNELS = [
    'eLama_russia',
    'pixeltools',
    'inside_vk',
    'yandexbusiness',
    'yagla',
    'ecom_with_love',
    'avito_b2b',
    'reklama_tochka',
    'market_marketplace',
    'russian_ecom',
    'hikollegi',
    'marketklad',
    'bs_business',
    'trends',
    'media1337',
    'oshestakovdigital',
    'ruslantxt',
    'kokina_kristina',
    'rudigital',
    'sale_caviar',
    'vcnews'
]

# Google Sheets configuration
CHANNELS_SHEET_NAME = 'Каналы'
POSTS_SHEET_NAME = 'Посты'

# Headers for channels sheet
CHANNELS_HEADERS = [
    'Название канала',
    'Ссылка',
    'Подписчики',
    'Описание',
    'Дата обновления'
]

# Headers for posts sheet
POSTS_HEADERS = [
    'Название канала',
    'Время',
    'Дата публикации',
    'Рубрика',
    'Содержание поста',
    'Есть медиа',
    'Ссылка на пост',
    'Просмотры',
    'Лайки',
    'Комментарии'
]

def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    if not TELEGRAM_API_ID:
        errors.append("TELEGRAM_API_ID not set in .env file")
    if not TELEGRAM_API_HASH:
        errors.append("TELEGRAM_API_HASH not set in .env file")
    if not TELEGRAM_PHONE:
        errors.append("TELEGRAM_PHONE not set in .env file")
    if not GOOGLE_SHEET_ID:
        errors.append("GOOGLE_SHEET_ID not set in .env file")
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        errors.append(f"Google service account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True

