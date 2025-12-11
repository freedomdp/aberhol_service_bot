from aiogram.types import Message, Contact

from models.dialog import DialogManager
from services.message_service import MessageService
from utils.validators import PhoneValidator
from utils.keyboards import get_phone_keyboard, remove_keyboard

class PhoneInputComponent:
	"""
	Компонент для обробки введення номера телефону
	"""
	def __init__(self, dialog_manager: DialogManager, message_service: MessageService):
		self.dialog_manager = dialog_manager
		self.message_service = message_service
		
	async def process_input(self, message: Message) -> None:
		"""
		Обробляє введення номера телефону
		"""
		user_id = message.from_user.id
		dialog = self.dialog_manager.get_dialog(user_id)
		
		# Перевіряємо, чи це контакт
		if message.contact is not None:
			phone_number = f"+{message.contact.phone_number}"
			is_valid, result = PhoneValidator.validate(phone_number)
		else:
			phone_number = message.text
			is_valid, result = PhoneValidator.validate(phone_number)
		
		if not is_valid:
			# Відправляємо повідомлення про помилку
			await self.message_service.send_message(
				chat_id=message.chat.id,
				text=result,
				keyboard=get_phone_keyboard()
			)
			return
			
		# Зберігаємо номер телефону в стані діалогу
		self.dialog_manager.update_dialog(
			user_id,
			phone_number=result,
			current_step='printer_model_input'
		)
		
		# Відправляємо підтвердження
		await self.message_service.send_message(
			chat_id=message.chat.id,
			text=f"✅ Зафіксували ваш номер телефону: {result}",
			keyboard=remove_keyboard()
		)
