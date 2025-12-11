"""
Контекст для доступа к сервисам из обработчиков
"""
from typing import Optional
from .media_storage import MediaStorage
from .error_handler import ErrorHandler
from .reminder_service import ReminderService

# Глобальные экземпляры сервисов
_media_storage: Optional[MediaStorage] = None
_error_handler: Optional[ErrorHandler] = None
_reminder_service: Optional[ReminderService] = None


def set_media_storage(storage: MediaStorage):
    """Устанавливает экземпляр MediaStorage"""
    global _media_storage
    _media_storage = storage


def get_media_storage() -> Optional[MediaStorage]:
    """Возвращает экземпляр MediaStorage"""
    return _media_storage


def set_error_handler(handler: ErrorHandler):
    """Устанавливает экземпляр ErrorHandler"""
    global _error_handler
    _error_handler = handler


def get_error_handler() -> Optional[ErrorHandler]:
    """Возвращает экземпляр ErrorHandler"""
    return _error_handler


def set_reminder_service(service: ReminderService):
    """Устанавливает экземпляр ReminderService"""
    global _reminder_service
    _reminder_service = service


def get_reminder_service() -> Optional[ReminderService]:
    """Возвращает экземпляр ReminderService"""
    return _reminder_service

