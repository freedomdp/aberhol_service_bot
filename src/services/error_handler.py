"""
Сервис для обработки ошибок и восстановления состояния бота
"""
import os
import logging
import traceback
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Класс для обработки ошибок и восстановления состояния"""
    
    def __init__(self):
        self.error_count: Dict[int, int] = {}  # Счетчик ошибок по user_id
        self.max_errors = 3  # Максимальное количество ошибок подряд
    
    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик глобальных ошибок бота
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
        """
        error = context.error
        user_id = None
        
        if update and update.effective_user:
            user_id = update.effective_user.id
        
        # Логируем ошибку
        logger.error(
            f"Ошибка в боте (user_id={user_id}): {error}",
            exc_info=error
        )
        
        # Отправляем сообщение пользователю
        if update and update.effective_chat:
            try:
                # Проверяем количество ошибок
                if user_id:
                    self.error_count[user_id] = self.error_count.get(user_id, 0) + 1
                    
                    if self.error_count[user_id] >= self.max_errors:
                        await self._handle_max_errors(update, context)
                        return
                
                # Отправляем понятное сообщение об ошибке
                error_message = (
                    "😔 <b>Вибачте, сталася помилка</b>\n\n"
                    "Наша команда вже працює над вирішенням проблеми.\n"
                    "Будь ласка, спробуйте ще раз через кілька хвилин.\n\n"
                    "Якщо проблема повторюється, напишіть /start для початку спочатку."
                )
                
                await update.effective_chat.send_message(
                    error_message,
                    parse_mode='HTML'
                )
                
                # Предлагаем начать заново
                from ..handlers.commands import start
                await start(update, context)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
    
    async def _handle_max_errors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка ситуации, когда достигнуто максимальное количество ошибок
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
        """
        user_id = update.effective_user.id
        
        error_message = (
            "⚠️ <b>Виявлено багато помилок підряд</b>\n\n"
            "Для вирішення проблеми будь ласка:\n"
            "1. Перезапустіть бота командою /start\n"
            "2. Якщо проблема залишається, зверніться до підтримки\n\n"
            "Ми вже повідомили про цю проблему наших інженерів."
        )
        
        try:
            await update.effective_chat.send_message(
                error_message,
                parse_mode='HTML'
            )
            
            # Сбрасываем счетчик ошибок
            self.error_count[user_id] = 0
            
            # Уведомляем инженера о проблеме
            engineer_id = os.getenv('ENGINEER_TELEGRAM_ID')
            if engineer_id:
                await context.bot.send_message(
                    chat_id=int(engineer_id),
                    text=f"⚠️ Проблема з користувачем {user_id}: багато помилок підряд"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке максимального количества ошибок: {e}")
    
    def reset_error_count(self, user_id: int) -> None:
        """Сбрасывает счетчик ошибок для пользователя"""
        self.error_count[user_id] = 0
    
    async def handle_conversation_error(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception
    ) -> int:
        """
        Обработка ошибок в разговоре
        
        Args:
            update: Обновление от Telegram
            context: Контекст бота
            error: Исключение
            
        Returns:
            Состояние для возврата в разговор
        """
        from telegram.ext import ConversationHandler
        
        user_id = update.effective_user.id
        logger.error(f"Ошибка в разговоре (user_id={user_id}): {error}")
        
        try:
            error_message = (
                "😔 <b>Сталася помилка під час обробки вашого запиту</b>\n\n"
                "Будь ласка, спробуйте ще раз або почніть з команди /start"
            )
            
            if update.message:
                await update.message.reply_text(error_message, parse_mode='HTML')
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message, parse_mode='HTML')
            
            # Очищаем состояние пользователя
            if user_id in context.user_data:
                context.user_data.clear()
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке ошибки разговора: {e}")
            return ConversationHandler.END

