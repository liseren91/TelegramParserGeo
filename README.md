# Telegram Channels Parser

Автоматический парсер Telegram каналов с сохранением данных в Google Sheets.

## 📋 Возможности

- **Сбор информации о каналах**: название, количество подписчиков, описание
- **Парсинг постов**: содержание, просмотры, лайки, комментарии, медиа
- **Автоматическое обновление**: ежедневный запуск по расписанию
- **Интеграция с Google Sheets**: автоматическое сохранение данных
- **Обновление статистики**: после каждого запуска актуализируются просмотры, реакции и комментарии уже сохранённых постов
- **Отслеживание удалений**: колонка `Удален` показывает, если пост исчез из канала (проверяем в пределах окна сбора)
- **Избежание дубликатов**: новые посты добавляются только один раз

## 📦 Требования

- Python 3.8 или выше
- Telegram API credentials (API ID и API Hash)
- Google Service Account с доступом к Google Sheets
- Учетная запись Telegram с номером телефона

## 🚀 Установка

### 1. Клонируйте проект

```bash
cd D:\TelegramParser
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Получите Telegram API credentials

1. Перейдите на https://my.telegram.org/apps
2. Войдите в свой аккаунт Telegram
3. Создайте новое приложение
4. Сохраните `api_id` и `api_hash`

### 4. Настройте Google Sheets API

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API и Google Drive API
4. Создайте Service Account:
   - Перейдите в "IAM & Admin" → "Service Accounts"
   - Нажмите "Create Service Account"
   - Задайте имя и описание
   - Нажмите "Create and Continue"
   - Не назначайте роли (необязательно для Google Sheets)
   - Нажмите "Done"
5. Создайте ключ для Service Account:
   - Найдите созданный Service Account в списке
   - Нажмите на него
   - Перейдите на вкладку "Keys"
   - Нажмите "Add Key" → "Create new key"
   - Выберите JSON формат
   - Нажмите "Create"
   - Файл JSON будет скачан автоматически
6. Сохраните скачанный JSON файл как `service_account.json` в корне проекта

### 5. Создайте Google Spreadsheet

1. Перейдите на [Google Sheets](https://sheets.google.com/)
2. Создайте новую таблицу
3. Скопируйте ID таблицы из URL:
   - URL выглядит так: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Скопируйте часть `SPREADSHEET_ID`
4. Предоставьте доступ Service Account:
   - Откройте файл `service_account.json`
   - Найдите поле `client_email` (выглядит как `your-service-account@your-project.iam.gserviceaccount.com`)
   - В Google Sheets нажмите "Share" (Поделиться)
   - Добавьте email из `client_email` с правами "Editor" (Редактор)

### 6. Создайте файл .env

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Telegram API credentials
# Get them from https://my.telegram.org/apps
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+your_phone_number

# Google Sheets configuration
# Create service account at https://console.cloud.google.com/
GOOGLE_SHEET_ID=your_google_sheet_id_here
# Path to your service account JSON file
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
```

Замените:
- `your_api_id_here` на ваш API ID от Telegram
- `your_api_hash_here` на ваш API Hash от Telegram
- `+your_phone_number` на ваш номер телефона с кодом страны (например: +79991234567)
- `your_google_sheet_id_here` на ID вашей Google таблицы

## 📊 Структура Google Sheets

Скрипт автоматически создаст два листа:

### Лист "Каналы"
- Название канала
- Ссылка
- Подписчики
- Описание
- Дата обновления

### Лист "Посты"
- Название канала
- Время
- Дата публикации
- Рубрика
- Содержание поста
- Есть медиа
- Ссылка на пост
- Просмотры
- Лайки
- Реакции (детали)
- Комментарии
- Удален

## 🎯 Использование

### Первый запуск

При первом запуске вам нужно будет авторизоваться в Telegram:

```bash
python main.py
```

Telegram отправит вам код подтверждения. Введите его в консоли.

### Режимы работы

#### Полное обновление (каналы + посты)
```bash
python main.py full
```

#### Обновить только информацию о каналах
```bash
python main.py channels
```

#### Обновить только посты
```bash
python main.py posts
```
> Каждый запуск обновит просмотры, реакции и комментарии у уже сохранённых постов и добавит новые записи.

#### Обновить посты за несколько дней
```bash
python main.py posts 3  # Собрать посты за последние 3 дня
```

### Автоматический запуск по расписанию

Для автоматического обновления каждый час используйте scheduler:

```bash
python scheduler.py
```

По умолчанию обновление выполняется каждый час в начале часа. Интервал можно изменить в файле `scheduler.py`.

### Запуск в фоне (Windows)

Создайте файл `run_scheduler.bat`:

```batch
@echo off
cd /d D:\TelegramParser
python scheduler.py
```

Для автозапуска при старте Windows:
1. Нажмите `Win + R`
2. Введите `shell:startup`
3. Создайте ярлык на `run_scheduler.bat` в открывшейся папке

Или используйте Task Scheduler для более гибкой настройки.

## ⚙️ Настройка

### Изменить список каналов

Отредактируйте файл `config.py`, найдите список `TELEGRAM_CHANNELS` и добавьте/удалите нужные каналы:

```python
TELEGRAM_CHANNELS = [
    'eLama_russia',
    'pixeltools',
    # ... добавьте свои каналы
]
```

### Изменить время запуска

Отредактируйте файл `scheduler.py`:

```python
# По умолчанию: каждый час, ровно в начале часа
schedule.every().hour.at(":00").do(run_update)

# Пример: каждые 30 минут
schedule.every(30).minutes.do(run_update)
```

## 📝 Логи

Все операции логируются в файлы:
- `telegram_parser.log` - логи основной работы парсера
- `scheduler.log` - логи планировщика

## ❗ Важные замечания

### Лимиты Telegram API

- Telegram имеет ограничения на количество запросов
- Скрипт автоматически делает паузы между запросами
- По умолчанию данные обновляются каждый час. Если заметите лимиты/капчи, увеличьте интервал запуска.

### Приватность

- Файл `service_account.json` содержит секретные данные - не публикуйте его
- Файл `.env` также содержит секретные данные - не публикуйте его
- Добавьте эти файлы в `.gitignore` (уже добавлены)

### Сессия Telegram

- При первом запуске создается файл `session.session`
- Этот файл содержит авторизационные данные
- Не удаляйте его, иначе придется авторизоваться заново
- Не публикуйте этот файл

#### Использование на сервере (Railway, Docker, cron)

Telethon не может спросить код подтверждения в headless-средах, поэтому нужно заранее сохранить готовую сессию:

1. Запустите `python main.py` локально и пройдите авторизацию.
2. Убедитесь, что в корне проекта появился файл `session.session`.
3. Преобразуйте файл в Base64. Для PowerShell подойдёт команда:
   ```
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("session.session"))
   ```
4. Сохраните полученную строку в переменную окружения `TELEGRAM_SESSION_BASE64` (например, в Railway → Variables).
5. (Опционально) если хотите изменить имя/путь файла, задайте `TELEGRAM_SESSION_NAME`. По умолчанию используется `session`, что соответствует файлу `session.session`.

> На сервере скрипт восстановит `session.session` из переменной `TELEGRAM_SESSION_BASE64`, и вход в Telegram пройдёт без ручного ввода кода.

## 🐛 Решение проблем

### "Configuration errors"

Проверьте, что:
- Файл `.env` создан и содержит все необходимые данные
- Файл `service_account.json` существует в корне проекта
- Все значения в `.env` корректны

### "Error getting info for channel"

Возможные причины:
- Канал не существует или изменил username
- Канал заблокирован или приватный
- Проблемы с сетью

### "Permission denied" для Google Sheets

Убедитесь, что:
- Service Account email добавлен в список редакторов таблицы
- Google Sheets API и Google Drive API включены в проекте
- ID таблицы в `.env` корректен

### "Phone number is already in use"

Если вы уже используете этот номер в другом приложении:
- Удалите файл `session.session`
- Запустите скрипт заново
- Пройдите авторизацию

## 📚 Структура проекта

```
TelegramParser/
│
├── config.py              # Конфигурация
├── telegram_parser.py     # Модуль для работы с Telegram API
├── sheets_manager.py      # Модуль для работы с Google Sheets
├── main.py               # Основной скрипт
├── scheduler.py          # Планировщик задач
├── requirements.txt      # Зависимости Python
├── .env                  # Переменные окружения (создать вручную)
├── .gitignore           # Файлы для игнорирования в Git
├── service_account.json # Google credentials (создать вручную)
├── session.session      # Сессия Telegram (создается автоматически)
└── README.md           # Эта инструкция
```

## 🔄 Обновление

Для обновления зависимостей:

```bash
pip install -r requirements.txt --upgrade
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `telegram_parser.log`
2. Убедитесь, что все конфигурационные файлы настроены правильно
3. Проверьте, что у вас установлены все зависимости

## 📄 Лицензия

Этот проект создан для личного использования. Используйте на свой страх и риск.

## ⚖️ Disclaimer

Этот инструмент предназначен только для легального использования. Убедитесь, что вы соблюдаете:
- Условия использования Telegram
- Правила владельцев каналов
- Законы о защите данных в вашей юрисдикции

Автор не несет ответственности за неправомерное использование данного инструмента.

