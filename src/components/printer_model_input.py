from aiogram.types import Message
from models.dialog import DialogManager
from services.message_service import MessageService
from utils.keyboards import get_printer_model_keyboard, remove_keyboard

class PrinterModelInputComponent:
	"""
	Компонент для обробки введення моделі принтера
	"""
	def __init__(self, dialog_manager: DialogManager, message_service: MessageService):
		self.dialog_manager = dialog_manager
		self.message_service = message_service
		
	async def process_input(self, message: Message) -> None:
		"""
		Обробляє введення моделі принтера
		"""
		user_id = message.from_user.id
		model = message.text
		
		# Зберігаємо модель принтера в стані діалогу
		self.dialog_manager.update_dialog(
			user_id,
			printer_model=model,
			current_step='issue_description'
		)
		
		# Відправляємо підтвердження
		await self.message_service.send_message(
			chat_id=message.chat.id,
			text=f"✅ Зафіксували модель принтеру: {model}",
			keyboard=remove_keyboard
		)
