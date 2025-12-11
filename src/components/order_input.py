from aiogram.types import Message

from models.dialog import DialogManager
from services.message_service import MessageService

class OrderInputComponent:
	"""
	Компонент для обробки введення номера замовлення
	"""
	def __init__(self, dialog_manager: DialogManager, message_service: MessageService):
		self.dialog_manager = dialog_manager
		self.message_service = message_service
		
	async def process_input(self, message: Message) -> None:
		"""
		Обробляє введення номера замовлення
		"""
		user_id = message.from_user.id
		order_number = message.text
		
		# Зберігаємо номер замовлення в стані діалогу
		next_step = 'printer_model_input' if order_number.lower() != 'немає' else 'name_input'
		
		self.dialog_manager.update_dialog(
			user_id,
			order_number=order_number if order_number.lower() != 'немає' else None,
			current_step=next_step
		)
		
		# Відправляємо підтвердження
		confirmation_text = ("✅ Зафіксували, що ви купували не у нас" 
						   if order_number.lower() == 'немає' 
						   else f"✅ Зафіксували номер замовлення: {order_number}")
		
		await self.message_service.send_message(
			chat_id=message.chat.id,
			text=confirmation_text
		)