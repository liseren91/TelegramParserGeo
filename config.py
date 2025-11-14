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

# Telegram session configuration (used for headless deployments)
_TELEGRAM_SESSION_FILE_ENV = os.getenv('TELEGRAM_SESSION_FILE')
_TELEGRAM_SESSION_NAME_ENV = os.getenv('TELEGRAM_SESSION_NAME')

if _TELEGRAM_SESSION_FILE_ENV:
    if _TELEGRAM_SESSION_FILE_ENV.endswith('.session'):
        TELEGRAM_SESSION_FILE = _TELEGRAM_SESSION_FILE_ENV
        TELEGRAM_SESSION_NAME = _TELEGRAM_SESSION_FILE_ENV[:-len('.session')]
    else:
        TELEGRAM_SESSION_FILE = f"{_TELEGRAM_SESSION_FILE_ENV}.session"
        TELEGRAM_SESSION_NAME = _TELEGRAM_SESSION_FILE_ENV
else:
    TELEGRAM_SESSION_NAME = _TELEGRAM_SESSION_NAME_ENV or 'session'
    if TELEGRAM_SESSION_NAME.endswith('.session'):
        TELEGRAM_SESSION_FILE = TELEGRAM_SESSION_NAME
        TELEGRAM_SESSION_NAME = TELEGRAM_SESSION_NAME[:-len('.session')]
    else:
        TELEGRAM_SESSION_FILE = f"{TELEGRAM_SESSION_NAME}.session"

TELEGRAM_SESSION_BASE64 = os.getenv('TELEGRAM_SESSION_BASE64')

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

# Track initialization issues for files reconstructed from Base64
_SERVICE_ACCOUNT_INIT_ERROR = None
_TELEGRAM_SESSION_INIT_ERROR = None


def _write_base64_file(encoded_value, target_path, description):
    """
    Create a file from a Base64-encoded string if the target does not exist.
    Returns an error message on failure, otherwise None.
    """
    if not encoded_value or os.path.exists(target_path):
        return None

    try:
        decoded_bytes = base64.b64decode(encoded_value)
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, 'wb') as file:
            file.write(decoded_bytes)
    except Exception as exc:
        return f"Failed to create {description} from Base64: {exc}"

    return None


_SERVICE_ACCOUNT_INIT_ERROR = _write_base64_file(
    GOOGLE_SERVICE_ACCOUNT_JSON_BASE64,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    "Google service account file"
)

_TELEGRAM_SESSION_INIT_ERROR = _write_base64_file(
    TELEGRAM_SESSION_BASE64,
    TELEGRAM_SESSION_FILE,
    "Telegram session file"
)

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
    if TELEGRAM_SESSION_BASE64 and _TELEGRAM_SESSION_INIT_ERROR:
        errors.append(_TELEGRAM_SESSION_INIT_ERROR)
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        errors.append(f"Google service account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True

