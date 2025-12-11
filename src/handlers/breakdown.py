"""
Обробник гілки діалогу 'Поломка'
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from utils.messages import BREAKDOWN_START, REQUEST_ORDER, REQUEST_PHONE
from utils.validators import PhoneValidator
from config import logger

# Стани діалогу
WAITING_ORDER = 1
WAITING_PHONE = 2

async def handle_breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє початок діалогу гілки 'Поломка'
    """
    user = update.effective_user
    logger.info(f"Користувач {user.id} ({user.full_name}) обрав розділ 'Поломка'")
    
    await update.message.reply_text(BREAKDOWN_START)
    await update.message.reply_text(REQUEST_ORDER)
    
    return WAITING_ORDER

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє отримання номера замовлення
    """
    order = update.message.text
    user = update.effective_user
    
    if order.lower() == 'немає':
        await update.message.reply_text("✅ Зафіксували, що ви купували не у нас")
    else:
        await update.message.reply_text(f"✅ Зафіксували номер замовлення: {order}")
    
    await update.message.reply_text(REQUEST_PHONE)
    return WAITING_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє отримання номера телефону
    """
    phone = update.message.text
    is_valid, message = PhoneValidator.validate(phone)
    
    if not is_valid:
        await update.message.reply_text(message)
        return WAITING_PHONE
    
    await update.message.reply_text(f"✅ Зафіксували ваш номер телефону: {message}")
    # Тут будет продолжение диалога
    return ConversationHandler.END