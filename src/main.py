#!/usr/bin/env python3
"""
Минимальный Telegram бот для интеграции с KeyCRM
Бот работает напрямую с CRM, операторы общаются с клиентами через CRM
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, CommandHandler, filters

# Налаштування логування
import logging.handlers
from datetime import datetime

# Створюємо папку logs якщо її немає
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Налаштування логування: і в консоль, і в файл
log_file = os.path.join(logs_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log')

# Створюємо форматтер
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Налаштування для консолі
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Налаштування для файлу
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10 МБ
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Налаштування кореневого логера
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# ВАЖНО: не даём библиотечным HTTP-логерам печатать URL с токеном бота
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Логування налаштовано. Файл логів: {log_file}")


async def start_command(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Команда /start от пользователя {user.id} ({user.first_name})")
    
    welcome_text = (
        "👋 Вітаємо!\n\n"
        "Цей бот інтегрований з KeyCRM.\n"
        "Оператори будуть спілкуватися з вами через CRM систему.\n\n"
        "Просто надішліть ваше повідомлення, і ми відповімо найближчим часом."
    )
    
    await update.message.reply_text(welcome_text)


async def handle_message(update, context):
    """Обработчик всех сообщений от пользователей"""
    user = update.effective_user
    message = update.message
    
    if not message:
        return
    
    # Логируем сообщение
    logger.info(
        f"Сообщение от пользователя {user.id} ({user.first_name}): "
        f"text='{message.text}', message_id={message.message_id}"
    )
    
    # Если есть медиа (фото, видео, документ)
    if message.photo:
        logger.info(f"Получено фото от пользователя {user.id}")
        # KeyCRM будет обрабатывать медиа через webhook
    elif message.video:
        logger.info(f"Получено видео от пользователя {user.id}")
    elif message.document:
        logger.info(f"Получен документ от пользователя {user.id}: {message.document.file_name}")
    
    # KeyCRM управляет ботом напрямую через webhook
    # Здесь мы только логируем входящие сообщения
    # Ответы будут приходить из KeyCRM через webhook


async def handle_error(update, context):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка при обработке update: {context.error}", exc_info=context.error)


def main() -> None:
    """Главная функция для запуска бота"""
    # Завантажуємо змінні оточення
    load_dotenv()

    # Отримуємо токен бота
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN не встановлено в змінних оточення")

    # Створюємо додаток
    application = Application.builder().token(token).build()
    
    # Реєструємо обробники
    logger.info("Реєстрація обробників...")
    
    # Команда /start
    application.add_handler(CommandHandler("start", start_command))
    
    # Обработчик всех сообщений (текст, фото, видео, документы)
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Глобальный обработчик ошибок
    application.add_error_handler(handle_error)
    
    # Запускаємо бота
    logger.info("Бот запущено...")
    logger.info("Бот готов к работе с KeyCRM через webhook")
    logger.info("KeyCRM будет управлять ботом напрямую")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        logger.info("Бот остановлен")


if __name__ == '__main__':
    main()
