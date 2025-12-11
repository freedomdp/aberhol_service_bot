from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application
from ..utils.validators import validate_email, validate_phone


# Зберігання активних заявок (в продакшені краще використовувати БД)
active_applications: dict[int, Application] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /start - автоматично відправляє привітання з клавіатурою"""
    import logging
    from ..utils.messages import WELCOME_MESSAGE
    from ..keyboards.reply import get_main_keyboard
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("ОБРОБНИК /start ВИКЛИКАНО")
    logger.info(f"update: {update}")
    logger.info(f"update.effective_user: {update.effective_user}")
    logger.info(f"update.message: {update.message}")
    
    user = update.effective_user
    if not user:
        logger.error("Не вдалося отримати інформацію про користувача")
        return
    
    logger.info(f"Команда /start отримана від користувача {user.id} ({user.first_name})")
    
    # Перевіряємо, чи є повідомлення
    if not update.message:
        logger.error("update.message є None")
        return
    
    # Відправляємо привітальне повідомлення з клавіатурою
    try:
        logger.info(f"Спроба відправити повідомлення користувачу {user.id}")
        logger.info(f"WELCOME_MESSAGE: {WELCOME_MESSAGE}")
        
        keyboard = get_main_keyboard()
        logger.info(f"Клавіатура створена: {keyboard}")
        
        result = await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=keyboard
        )
        logger.info(f"Повідомлення успішно відправлено! Message ID: {result.message_id}")
        logger.info(f"Привітальне повідомлення з клавіатурою відправлено користувачу {user.id}")
    except Exception as e:
        logger.error(f"Помилка при відправці привітального повідомлення користувачу {user.id}: {e}", exc_info=True)
        raise


async def new_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Початок створення нової заявки"""
    from .conversation import WAITING_NAME, ConversationHandler
    from ..main import reminder_service
    
    user_id = update.effective_user.id
    
    # Якщо вже є активна заявка, видаляємо її и отменяем напоминания
    if user_id in active_applications:
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        del active_applications[user_id]
    
    # Створюємо нову заявку
    active_applications[user_id] = Application(user_id=user_id)
    
    await update.message.reply_text(
        "📝 <b>Створення нової заявки</b>\n\n"
        "Будь ласка, введіть ваше <b>ім'я та прізвище</b>:",
        parse_mode='HTML'
    )
    
    return WAITING_NAME


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /info"""
    info_message = (
        "ℹ️ <b>Інформація про сервісний центр</b>\n\n"
        "📞 <b>Режим роботи:</b> будні дні з 9:00 до 18:00\n\n"
        "⏱️ <b>Терміни обробки:</b>\n"
        "Відповідь на заявку надається протягом 2 робочих днів\n\n"
        "🎯 <b>Пріоритети:</b>\n"
        "Пріоритет обслуговування надається клієнтам, які придбали обладнання у нас\n\n"
        "🔧 <b>Гарантійний ремонт:</b>\n"
        "• Можливий виключно для товарів, придбаних у нашому магазині\n"
        "• Виконується виключно на території нашого сервісного центру\n"
        "• Умови гарантії описані на відповідній сторінці\n\n"
        "Для створення заявки натисніть /new_application"
    )

    await update.message.reply_text(
        info_message,
        parse_mode='HTML'
    )


async def handle_faq_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник кнопки '❓ Питання / Відповідь'"""
    import logging
    from ..utils.messages import FAQ_START
    from ..keyboards.inline import get_faq_keyboard
    
    logger = logging.getLogger(__name__)
    
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    logger.info(f"Користувач {user.id} обрав: ❓ Питання / Відповідь")
    
    try:
        await update.message.reply_text(
            FAQ_START,
            parse_mode='HTML',
            reply_markup=get_faq_keyboard()
        )
        logger.info(f"Повідомлення FAQ з клавіатурою відправлено користувачу {user.id}")
    except Exception as e:
        logger.error(f"Помилка при відправці повідомлення користувачу {user.id}: {e}", exc_info=True)


async def handle_faq_repair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник кнопки 'Куди відправляти принтер на ремонт' (працює поза ConversationHandler)"""
    import logging
    from ..utils.messages import FAQ_REPAIR_INFO
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("handle_faq_repair ВИКЛИКАНО (поза ConversationHandler)")
    logger.info(f"update: {update}")
    logger.info(f"update.callback_query: {update.callback_query}")
    logger.info(f"context.user_data: {context.user_data}")
    
    query = update.callback_query
    
    if not query:
        logger.error("handle_faq_repair: query is None")
        return
    
    logger.info(f"query.data: {query.data}")
    
    user = update.effective_user
    if not user:
        logger.error("handle_faq_repair: user is None")
        return
    
    logger.info(f"Користувач {user.id} обрав: Куди відправляти принтер на ремонт")
    
    try:
        # Відповідаємо на callback, щоб прибрати індикатор завантаження
        await query.answer()
        logger.info("query.answer() виконано")
        
        # Відправляємо текст у діалог
        if query.message:
            logger.info("Відправляємо повідомлення через query.message.reply_text()")
            await query.message.reply_text(FAQ_REPAIR_INFO)
            logger.info("Повідомлення FAQ_REPAIR_INFO відправлено")
        else:
            # Якщо немає повідомлення, відправляємо в чат
            logger.info("Відправляємо повідомлення через context.bot.send_message()")
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text=FAQ_REPAIR_INFO
            )
            logger.info("Повідомлення FAQ_REPAIR_INFO відправлено через bot.send_message")
        
        logger.info(f"Інформацію про ремонт відправлено користувачу {user.id}")
    except Exception as e:
        logger.error(f"Помилка при відправці інформації користувачу {user.id}: {e}", exc_info=True)
        # Спробуємо відправити повідомлення про помилку
        try:
            await query.answer("❌ Помилка при відправці інформації. Спробуйте ще раз.", show_alert=True)
        except Exception as e2:
            logger.error(f"Помилка при відправці alert: {e2}")


def register_commands(application):
    """Реєстрація команд бота"""
    import logging
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    logger = logging.getLogger(__name__)
    
    logger.info("Реєстрація обробника команди /start")
    application.add_handler(CommandHandler("start", start))
    
    # Реєстрація обробника кнопки FAQ (інші кнопки обробляються ConversationHandler)
    # Примітка: обробник callback FAQ реєструється в main.py з високим пріоритетом
    logger.info("Реєстрація обробника кнопки FAQ")
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("^❓ Питання / Відповідь$"),
            handle_faq_button
        )
    )
    
    # new_application реєструється в ConversationHandler
    logger.info("Реєстрація обробника команди /info")
    application.add_handler(CommandHandler("info", info))
    logger.info("Всі команди зареєстровано")
