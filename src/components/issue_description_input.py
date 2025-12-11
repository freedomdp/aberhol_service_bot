from aiogram.types import Message

from models.dialog import DialogManager
from services.message_service import MessageService
from utils.validators import IssueDescriptionValidator
from utils.keyboards import remove_keyboard, get_next_keyboard

class IssueDescriptionInputComponent:
	"""
	Компонент для обробки введення опису проблеми
	"""
	def __init__(self, dialog_manager: DialogManager, message_service: MessageService):
		self.dialog_manager = dialog_manager
		self.message_service = message_service
		
	async def process_input(self, message: Message) -> None:
		"""
		Обробляє введення опису проблеми
		"""
		user_id = message.from_user.id
		description = message.text
		
		# Валідація опису
		is_valid, result = IssueDescriptionValidator.validate(description)
		
		if not is_valid:
			await self.message_service.send_message(
				chat_id=message.chat.id,
				text=result
			)
			return
			
		# Зберігаємо опис проблеми в стані діалогу
		self.dialog_manager.update_dialog(
			user_id,
			issue_description=result,
			current_step='photo_upload'
		)
		
		# Відправляємо підтвердження
		await self.message_service.send_message(
			chat_id=message.chat.id,
			text=f"✅ Зафіксували опис проблеми: {result}",
			keyboard=remove_keyboard
		)
		
		# Запит на додавання фото
		await self.message_service.send_message(
			chat_id=message.chat.id,
			text="📸 Надішліть фото або відео, які демонструють проблему (до 10 фото) або оберіть 'Далі'",
			keyboard=get_next_keyboard()
		)