"""
Універсальний компонент для введення тексту
Використовується для опису проблеми, коментарів тощо
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application

logger = logging.getLogger(__name__)


class UniversalTextInput:
    """
    Універсальний компонент для обробки введення тексту
    """
    
    @staticmethod
    async def process(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        application: Application,
        field_name: str = "problem_description",
        validation_func: callable = None,
        next_message: str = None,
        next_state: int = None
    ) -> tuple[bool, str, int]:
        """
        Обробляє введення тексту
        
        Args:
            update: Update об'єкт
            context: Context об'єкт
            application: Application об'єкт для збереження даних
            field_name: Назва поля для збереження (за замовчуванням "problem_description")
            validation_func: Функція валідації (опціонально)
            next_message: Повідомлення для наступного кроку
            next_state: Наступний стан діалогу
        
        Returns:
            tuple: (success, response_message, next_state)
        """
        if not update.message or not update.message.text:
            return False, "❌ Помилка. Будь ласка, введіть текст.", None
        
        text = update.message.text.strip()
        
        # Валідація (якщо вказана)
        if validation_func:
            is_valid, error_message = validation_func(text)
            if not is_valid:
                return False, error_message, None
        
        # Зберігаємо текст
        setattr(application, field_name, text)
        
        # Формуємо повідомлення
        response_message = "✅ Зафіксували інформацію"
        if next_message:
            response_message += f"\n\n{next_message}"
        
        return True, response_message, next_state

