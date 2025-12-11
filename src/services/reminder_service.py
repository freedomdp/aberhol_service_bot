"""
Сервис для напоминаний о брошенных заявках
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot
from telegram.ext import ContextTypes

from ..models.application import Application
from ..handlers.commands import active_applications

logger = logging.getLogger(__name__)


class ReminderService:
    """Сервис для управления напоминаниями о незавершенных заявках"""
    
    def __init__(self, bot: Bot):
        """
        Инициализация сервиса напоминаний
        
        Args:
            bot: Экземпляр бота Telegram
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.pending_reminders: Dict[int, Dict] = {}  # user_id -> {application, reminders}
        
    def start(self):
        """Запускает планировщик напоминаний"""
        self.scheduler.start()
        logger.info("ReminderService запущен")
    
    def stop(self):
        """Останавливает планировщик"""
        self.scheduler.shutdown()
        logger.info("ReminderService остановлен")
    
    def schedule_reminders(self, user_id: int, application: Application) -> None:
        """
        Планирует напоминания для незавершенной заявки
        
        Args:
            user_id: ID пользователя
            application: Объект заявки
        """
        # Удаляем старые напоминания если есть
        self.cancel_reminders(user_id)
        
        # Сохраняем информацию о заявке
        self.pending_reminders[user_id] = {
            'application': application,
            'created_at': datetime.now(),
            'reminder_count': 0
        }
        
        # Планируем напоминания
        reminders = [
            (30, "30 хвилин"),   # Через 30 минут
            (90, "1.5 години"),  # Через 1.5 часа
            (1440, "1 день")      # Через день
        ]
        
        for minutes, text in reminders:
            trigger_time = datetime.now() + timedelta(minutes=minutes)
            
            self.scheduler.add_job(
                self._send_reminder,
                'date',
                run_date=trigger_time,
                args=[user_id, text],
                id=f"reminder_{user_id}_{minutes}",
                replace_existing=True
            )
        
        logger.info(f"Напоминания запланированы для user_id={user_id}")
    
    async def _send_reminder(self, user_id: int, time_text: str) -> None:
        """
        Отправляет напоминание пользователю
        
        Args:
            user_id: ID пользователя
            time_text: Текст времени (например, "30 хвилин")
        """
        # Проверяем, существует ли еще незавершенная заявка
        if user_id not in self.pending_reminders:
            logger.info(f"Заявка для user_id={user_id} уже завершена, напоминание отменено")
            return
        
        if user_id not in active_applications:
            logger.info(f"Активная заявка для user_id={user_id} не найдена, напоминание отменено")
            self.pending_reminders.pop(user_id, None)
            return
        
        application = active_applications[user_id]
        
        # Определяем, на каком этапе остановился пользователь
        stage_message = self._get_stage_message(application)
        
        reminder_text = (
            f"👋 <b>Нагадування про незавершену заявку</b>\n\n"
            f"Ви почали оформлення заявки {time_text} тому, але не завершили її.\n\n"
            f"{stage_message}\n\n"
            f"Продовжити оформлення заявки? Натисніть /new_application"
        )
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=reminder_text,
                parse_mode='HTML'
            )
            
            # Увеличиваем счетчик напоминаний
            if user_id in self.pending_reminders:
                self.pending_reminders[user_id]['reminder_count'] += 1
                
                # После третьего напоминания удаляем из списка
                if self.pending_reminders[user_id]['reminder_count'] >= 3:
                    logger.info(f"Достигнуто максимальное количество напоминаний для user_id={user_id}")
                    self.pending_reminders.pop(user_id, None)
            
            logger.info(f"Напоминание отправлено user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания user_id={user_id}: {e}")
            # Если пользователь заблокировал бота, удаляем из списка
            if "chat not found" in str(e).lower() or "blocked" in str(e).lower():
                self.pending_reminders.pop(user_id, None)
    
    def _get_stage_message(self, application: Application) -> str:
        """
        Определяет сообщение о текущем этапе заполнения заявки
        
        Args:
            application: Объект заявки
            
        Returns:
            Текст сообщения о текущем этапе
        """
        if not application.full_name:
            return "Ви ввели своє ім'я та прізвище. Потрібно ввести email."
        elif not application.email:
            return "Ви ввели email. Потрібно ввести номер телефону."
        elif not application.phone_number:
            return "Ви ввели контактні дані. Потрібно вибрати модель принтера."
        elif not application.printer_model:
            return "Ви ввели основну інформацію. Потрібно вибрати тип філаменту."
        elif not application.problem_description:
            return "Ви ввели інформацію про принтер. Залишилось описати проблему."
        else:
            return "Ви майже завершили заявку. Залишилось тільки підтвердити відправку."
    
    def cancel_reminders(self, user_id: int) -> None:
        """
        Отменяет все напоминания для пользователя
        
        Args:
            user_id: ID пользователя
        """
        # Удаляем задачи из планировщика
        for minutes in [30, 90, 1440]:
            job_id = f"reminder_{user_id}_{minutes}"
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass  # Задача может не существовать
        
        # Удаляем из списка ожидающих
        self.pending_reminders.pop(user_id, None)
        logger.info(f"Напоминания отменены для user_id={user_id}")
    
    def check_and_cleanup(self) -> None:
        """Проверяет и очищает устаревшие напоминания"""
        now = datetime.now()
        to_remove = []
        
        for user_id, reminder_data in self.pending_reminders.items():
            created_at = reminder_data['created_at']
            # Удаляем напоминания старше 2 дней
            if (now - created_at).days > 2:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            self.cancel_reminders(user_id)
            logger.info(f"Удалено устаревшее напоминание для user_id={user_id}")

