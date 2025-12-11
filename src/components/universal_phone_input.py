"""
Універсальний компонент для введення номера телефону
Використовується в розділах "🔧 Поломка" та "🖨 Якість друку"
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application
from ..utils.validators import validate_phone

logger = logging.getLogger(__name__)


class UniversalPhoneInput:
    """
    Універсальний компонент для обробки введення номера телефону
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
        Обробляє введення номера телефону
        
        Args:
            update: Update об'єкт
            context: Context об'єкт
            application: Application об'єкт для збереження даних
            next_message: Повідомлення для наступного кроку
            next_state: Наступний стан діалогу
        
        Returns:
            tuple: (success, response_message, next_state)
        """
        if not update.message:
            return False, "❌ Помилка. Будь ласка, введіть номер телефону.", None
        
        # Перевіряємо, чи це контакт
        if update.message.contact:
            phone = update.message.contact.phone_number
            if not phone.startswith('+'):
                phone = f"+{phone}"
        else:
            phone = update.message.text.strip()
        
        # Валідація
        if not validate_phone(phone):
            return False, "❌ Введіть будь ласка номер тільки у форматі +380XXXXXXXXX або 0XXXXXXXXX", None
        
        # Зберігаємо номер телефону
        application.phone_number = phone
        
        # Формуємо повідомлення
        response_message = f"✅ Зафіксували номер телефону: {phone}"
        if next_message:
            response_message += f"\n\n{next_message}"
        
        return True, response_message, next_state

