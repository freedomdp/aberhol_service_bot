import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext

from models.dialog import DialogManager
from models.user import UserManager
from services.message_service import MessageService

logger = logging.getLogger(__name__)

class DialogLoggingMiddleware(BaseMiddleware):
	"""
	Middleware для логирования этапов диалога с пользователем.
	Отслеживает все сообщения и текущие состояния диалога.
	"""
	# Словарь для перевода состояний в человекочитаемый формат
	STATE_DESCRIPTIONS = {
		'BreakdownStates:waiting_order': 'Ожидание номера заказа',
		'BreakdownStates:waiting_name': 'Ожидание ввода имени',
		'BreakdownStates:waiting_phone': 'Ожидание номера телефона',
		'BreakdownStates:waiting_printer_model': 'Выбор модели принтера',
		'BreakdownStates:waiting_description': 'Ожидание описания проблемы',
		'BreakdownStates:waiting_media': 'Ожидание фото/видео материалов',
		'BreakdownStates:confirmation': 'Подтверждение заявки'
	}
	
	async def __call__(
		self,
		handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
		event: Message,
		data: Dict[str, Any]
	) -> Any:
		state: FSMContext = data.get('state')
		if state:
			current_state = await state.get_state()
			user_id = event.from_user.id
			state_description = self.STATE_DESCRIPTIONS.get(str(current_state), str(current_state))
			logger.info(
				f"User {user_id} | Current step: {state_description} | "
				f"Message: {event.text if event.text else 'No text'}"
			)
		
		return await handler(event, data)

class ServicesMiddleware(BaseMiddleware):
	"""Middleware для внедрения зависимостей"""
	def __init__(
		self,
		dialog_manager: DialogManager,
		user_manager: UserManager,
		message_service: MessageService
	):
		self.dialog_manager = dialog_manager
		self.user_manager = user_manager
		self.message_service = message_service

	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any]
	) -> Any:
		data["dialog_manager"] = self.dialog_manager
		data["user_manager"] = self.user_manager
		data["message_service"] = self.message_service
		return await handler(event, data)

def setup_middlewares(dp: Dispatcher, dialog_manager: DialogManager, 
					 user_manager: UserManager, message_service: MessageService) -> None:
	"""Налаштування middleware для бота"""
	services_middleware = ServicesMiddleware(dialog_manager, user_manager, message_service)
	logging_middleware = DialogLoggingMiddleware()
	
	# Регистрация middleware для обработки сообщений
	dp.message.middleware.register(services_middleware)
	dp.message.middleware.register(logging_middleware)
	
	# Регистрация middleware для обработки callback запросов
	dp.callback_query.middleware.register(services_middleware)


