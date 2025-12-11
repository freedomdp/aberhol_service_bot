# Простой запуск бота без Docker

## Шаг 1: Установка зависимостей

```powershell
cd D:\Dev\aberhol_service_bot
python -m pip install -r requirements.txt
```

## Шаг 2: Проверка файла .env

Убедитесь, что файл `.env` находится в корне проекта `D:\Dev\aberhol_service_bot\.env` и содержит:

```env
TELEGRAM_TOKEN=7273544087:AAFjIiwRlT2FqaFCR3yrT2dyBAGloF6nC8c
ENGINEER_TELEGRAM_ID=103059062
MEDIA_STORAGE_PATH=./media
BASE_URL=http://localhost:8000
```

## Шаг 3: Запуск бота

```powershell
cd D:\Dev\aberhol_service_bot
python -m src.main
```

Или:

```powershell
python src/main.py
```

## Шаг 4: Проверка работы

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте команду `/start`
4. Бот должен ответить приветственным сообщением

## Остановка бота

Нажмите `Ctrl+C` в терминале
