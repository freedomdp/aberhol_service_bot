"""
Обробник команди /start та головного меню
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import get_main_keyboard
from utils.messages import WELCOME_MESSAGE
from config import logger
from models.dialog import DialogManager
from models.user import UserManager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробляє команду /start та показує головне меню
    """
    user = update.effective_user
    
    # Отримуємо менеджери з контексту бота
    dialog_manager = context.bot_data['dialog_manager']
    user_manager = context.bot_data['user_manager']
    
    # Ініціалізуємо користувача
    user_manager.get_user(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name or ""
    )
    
    # Ініціалізуємо новий діалог
    dialog_manager.get_dialog(user.id)
    
    logger.info(f"Користувач {user.id} ({user.first_name} {user.last_name or ''}) запустив бота")
    
    await update.message.reply_text(
        text=WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )