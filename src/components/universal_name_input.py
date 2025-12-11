"""
Універсальний компонент для введення імені та прізвища
Використовується в розділах "🔧 Поломка" та "🖨 Якість друку"
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application
from ..utils.messages import REQUEST_NAME, REQUEST_PHONE
from ..services.context import get_reminder_service

logger = logging.getLogger(__name__)


class UniversalNameInput:
    """
    Універсальний компонент для обробки введення імені
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
        Обробляє введення імені та прізвища
        
        Args:
            update: Update об'єкт
            context: Context об'єкт
            application: Application об'єкт для збереження даних
            next_message: Повідомлення для наступного кроку (за замовчуванням REQUEST_PHONE)
            next_state: Наступний стан діалогу
        
        Returns:
            tuple: (success, response_message, next_state)
        """
        if not update.message or not update.message.text:
            return False, "❌ Помилка. Будь ласка, введіть текст.", None
        
        full_name = update.message.text.strip()
        
        # Валідація
        if len(full_name) < 2:
            return False, "❌ Будь ласка, введіть коректне ім'я та прізвище:", None
        
        # Зберігаємо ім'я
        application.full_name = full_name
        
        # Планируем напоминания
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.schedule_reminders(application.user_id, application)
        
        # Формуємо повідомлення
        response_message = f"✅ Зафіксували ваше ім'я: {full_name}\n\n"
        if next_message:
            response_message += next_message
        else:
            response_message += REQUEST_PHONE
        
        return True, response_message, next_state

