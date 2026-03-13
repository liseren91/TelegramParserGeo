"""
Configuration module for Telegram Parser
"""
import base64
import gzip
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


def _get_int_env(name, default_value, min_value=None):
    """Read integer env var with fallback and optional lower bound."""
    raw = os.getenv(name)
    if raw is None:
        return default_value
    try:
        value = int(raw)
    except ValueError:
        return default_value
    if min_value is not None and value < min_value:
        return min_value
    return value

# Telegram channels to parse
TELEGRAM_CHANNELS = [
    'hiaimedia',
    'ai_machinelearning_big_data',
    'neuraldvig',
    'gpt_news',
    'neuralpony',
    'techno_yandex',
    'ai_newz',
    'jarvisnew',
    'data_secrets',
    'seeallochnaya',
    'neuralshit',
    'studgpt',
    'stablediffusionbest',
    'dailyprompts',
    'neuro_praxis',
    'machinelearning_interview',
    'molyanov_blog',
    'promtext',
    'lama_channel_gpt',
    'ai_chad',
    'neural_braining',
    'iidlyabi',
    'notboring_tech',
    'inclient',
    'it_abc',
    'olya_tashit',
    'tochkinadai',
    'ppprompt',
    'svodkaai_ai',
    'prompt1_ru',
    'cgit_vines',
    'neurozeh',
    'midjourney_a1',
    'neuro_art0',
    'ict_moscow_ai',
    'datasciencegx',
    'primus_ai',
    'digitalshkaf',
    'digital_in_pharma',
    'psy_eyes',
    'midjornium',
    'projplus',
    'kdoronin_blog',
    'neuroluv',
    'nerdhubchannel',
    'sky_net_ai',
    'chatgpt_neuronews',
    'omggpt',
    'vvs_studio_ai',
    'myspacet_ai',
    'futuris',
    'ainetworkss',
    'victoriya_academy',
    'tabu_openai',
    'aisapiens',
    'iitebe',
    'gpt_access',
    'creative_volshba_kj',
    'ai_vibe',
    'ultravibecoder',
    'aigeneratedstuff',
    'ii_papka',
    'robocounsel',
    'lexel_channel',
    'syntxprompts',
    'neuro_images',
    'aivasilisa',
    'growth1hack',
    'sipout_ai',
    'bolshiedannye',
    'ai4bus',
    'gulnarafotoii',
    'pixelprohh',
    'ei_ai_channel',
    'ohfuture',
    'clipart_ai',
    'neuro_dopamine',
    'bpa_tech',
    'vibecode_memes',
    'aizool',
    'neuralrus',
    'ml_product',
    'nikita_ai_web3',
    'speechaipro',
    'neiromagiya_contenta',
    'ai_barkov',
    'ai_datysho',
    'nonempty_string',
    'aihubfeed',
    'datacluster',
    'nii_krokodil',
    'igorekonair',
    'durova_hohma',
    'hitomirec',
    'aizaveta',
    'business30neuro',
    'neiroseti_2',
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

# Parser throttling configuration
PARSER_BATCH_SIZE = _get_int_env('PARSER_BATCH_SIZE', 5, min_value=1)
PARSER_CHANNEL_DELAY_MIN_SEC = _get_int_env('PARSER_CHANNEL_DELAY_MIN_SEC', 7, min_value=0)
PARSER_CHANNEL_DELAY_MAX_SEC = _get_int_env('PARSER_CHANNEL_DELAY_MAX_SEC', 10, min_value=0)
PARSER_BATCH_DELAY_MIN_SEC = _get_int_env('PARSER_BATCH_DELAY_MIN_SEC', 120, min_value=0)
PARSER_BATCH_DELAY_MAX_SEC = _get_int_env('PARSER_BATCH_DELAY_MAX_SEC', 180, min_value=0)
PARSER_FLOOD_WAIT_BUFFER_SEC = _get_int_env('PARSER_FLOOD_WAIT_BUFFER_SEC', 90, min_value=0)

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

        if decoded_bytes.startswith(b'\x1f\x8b'):
            try:
                decoded_bytes = gzip.decompress(decoded_bytes)
            except OSError:
                pass

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

