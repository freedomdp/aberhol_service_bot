from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from models.dialog import DialogManager
from models.user import UserManager

class DependencyMiddleware(BaseMiddleware):
	"""
	Middleware для внедрения зависимостей в хендлеры
	"""
	def __init__(self, dialog_manager: DialogManager, user_manager: UserManager):
		self.dialog_manager = dialog_manager
		self.user_manager = user_manager
		
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any]
	) -> Any:
		# Добавляем менеджеры в данные
		data["dialog_manager"] = self.dialog_manager
		data["user_manager"] = self.user_manager
		
		# Вызываем следующий обработчик
		return await handler(event, data)