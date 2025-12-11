#!/usr/bin/env python3
"""
Головний файл Telegram бота для сервісного центру Bambu Lab Україна
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

from src.handlers import register_commands, register_conversation_handlers
from src.services import MediaStorage, ErrorHandler, ReminderService
from src.services.context import (
    set_media_storage, set_error_handler, set_reminder_service
)

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

logger = logging.getLogger(__name__)
logger.info(f"Логування налаштовано. Файл логів: {log_file}")


def main() -> None:
    """Головна функція для запуску бота"""
    # Завантажуємо змінні оточення
    load_dotenv()

    # Отримуємо токен бота
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN не встановлено в змінних оточення")

    # Инициализируем сервисы
    media_storage = MediaStorage(
        storage_path=os.getenv('MEDIA_STORAGE_PATH', './media'),
        base_url=os.getenv('BASE_URL', 'http://localhost:8000')
    )
    
    error_handler = ErrorHandler()
    
    # Создаем временный bot для ReminderService (будет заменен после создания application)
    from telegram import Bot
    temp_bot = Bot(token=token)
    reminder_service = ReminderService(bot=temp_bot)
    
    # Устанавливаем сервисы в контекст для доступа из обработчиков
    set_media_storage(media_storage)
    set_error_handler(error_handler)
    set_reminder_service(reminder_service)
    
    # Создаем post_init callback для запуска ReminderService после создания event loop
    async def post_init(app: Application) -> None:
        """Вызывается после создания event loop"""
        # Обновляем bot в reminder_service на реальный
        reminder_service.bot = app.bot
        reminder_service.start()
        logger.info("ReminderService запущен")
    
    # Створюємо додаток з post_init callback
    application = Application.builder().token(token).post_init(post_init).build()
    
    # Реєструємо обробники (важливо: команды регистрируются ПЕРВЫМИ)
    # Реєструємо обробник callback для FAQ (використовуємо InlineKeyboard для FAQ)
    from telegram.ext import CallbackQueryHandler
    from src.handlers.commands import handle_faq_repair
    
    logger.info("Реєстрація обробника callback FAQ (faq_repair)...")
    application.add_handler(
        CallbackQueryHandler(handle_faq_repair, pattern="^faq_repair$"),
        group=-1  # Високий пріоритет (обробляється перед ConversationHandler)
    )
    
    logger.info("ВАЖЛИВО: Для breakdown використовуємо ReplyKeyboard, обробка через ConversationHandler")
    
    logger.info("Реєстрація обробників команд...")
    register_commands(application)
    
    # Потім реєструємо ConversationHandler (нижчий пріоритет)
    logger.info("Реєстрація обробників розмов...")
    register_conversation_handlers(application)
    
    # Реєструємо обробники для розділів "Поломка" та "Якість друку"
    from src.handlers.breakdown_handler import get_breakdown_conversation_handler
    from src.handlers.quality_handler import get_quality_conversation_handler
    
    logger.info("Реєстрація обробника розділу '🔧 Поломка'")
    application.add_handler(get_breakdown_conversation_handler())
    
    logger.info("Реєстрація обробника розділу '🖨 Якість друку'")
    application.add_handler(get_quality_conversation_handler())
    
    # Добавляем максимально подробное логирование всех update'ов
    from telegram import Update
    from telegram.ext import ContextTypes, CallbackQueryHandler as CQH, MessageHandler, filters
    
    async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Логирует все входящие update'ы для диагностики"""
        if update.message:
            logger.info(f"[UPDATE DEBUG] MESSAGE: user_id={update.effective_user.id}, chat_id={update.effective_chat.id}, text='{update.message.text}', message_id={update.message.message_id}")
        elif update.callback_query:
            logger.info(f"[UPDATE DEBUG] CALLBACK QUERY: user_id={update.effective_user.id}, chat_id={update.effective_chat.id}, data='{update.callback_query.data}', message_id={update.callback_query.message.message_id if update.callback_query.message else 'N/A'}")
        else:
            logger.info(f"[UPDATE DEBUG] OTHER UPDATE: {update}")
    
    application.add_handler(MessageHandler(filters.ALL, log_all_updates), group=-2) # Самый низкий приоритет
    application.add_handler(CQH(log_all_updates), group=-2) # Логирование callback queries
    
    # Регистрируем глобальный обработчик ошибок
    application.add_error_handler(error_handler.handle_error)
    
    # Запускаємо бота
    logger.info("Бот запущено...")
    logger.info("Очікування повідомлень від користувачів...")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        # Останавливаем сервисы
        reminder_service.stop()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    main()
