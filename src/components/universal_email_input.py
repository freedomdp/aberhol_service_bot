"""
Універсальний компонент для введення email адреси
Використовується в розділах "🔧 Поломка" та "🖨 Якість друку"
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application
from ..utils.validators import validate_email

logger = logging.getLogger(__name__)


class UniversalEmailInput:
    """
    Універсальний компонент для обробки введення email адреси
    """
    
    @staticmethod
    async def process(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        application: Application,
        next_message: str = None,
        next_state: int = None
    ) -> tuple[bool, str, int]:
        """
        Обробляє введення email адреси
        
        Args:
            update: Update об'єкт
            context: Context об'єкт
            application: Application об'єкт для збереження даних
            next_message: Повідомлення для наступного кроку
            next_state: Наступний стан діалогу
        
        Returns:
            tuple: (success, response_message, next_state)
        """
        if not update.message or not update.message.text:
            return False, "❌ Помилка. Будь ласка, введіть email адресу.", None
        
        email = update.message.text.strip()
        
        # Валідація
        if not validate_email(email):
            return False, "❌ Введіть будь ласка коректну email адресу (наприклад: example@mail.com)", None
        
        # Зберігаємо email
        application.email = email
        
        # Формуємо повідомлення
        response_message = f"✅ Зафіксували email адресу: {email}"
        if next_message:
            response_message += f"\n\n{next_message}"
        
        return True, response_message, next_state
