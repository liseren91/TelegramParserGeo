"""
Configuration module for Telegram Parser
"""
import base64
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
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64')

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
    'Реакции (детали)',
    'Комментарии',
    'Удален'
]

# Internal flag to capture service account provisioning issues
_SERVICE_ACCOUNT_INIT_ERROR = None


def _ensure_service_account_file():
    """
    Create the Google service account file from the provided Base64 string
    when it doesn't already exist on disk.
    """
    global _SERVICE_ACCOUNT_INIT_ERROR

    if not GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 or os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        return

    try:
        decoded_bytes = base64.b64decode(GOOGLE_SERVICE_ACCOUNT_JSON_BASE64)
        target_dir = os.path.dirname(GOOGLE_SERVICE_ACCOUNT_FILE)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(GOOGLE_SERVICE_ACCOUNT_FILE, 'wb') as file:
            file.write(decoded_bytes)
    except Exception as exc:
        _SERVICE_ACCOUNT_INIT_ERROR = (
            f"Failed to create Google service account file from "
            f"GOOGLE_SERVICE_ACCOUNT_JSON_BASE64: {exc}"
        )


_ensure_service_account_file()

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
    if _SERVICE_ACCOUNT_INIT_ERROR:
        errors.append(_SERVICE_ACCOUNT_INIT_ERROR)
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        errors.append(f"Google service account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True

