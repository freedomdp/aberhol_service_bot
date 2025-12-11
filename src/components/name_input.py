from telegram import Update
from telegram.ext import ContextTypes

from models.dialog import DialogManager
from models.user import UserManager
from components.message_sender import MessageSender
from utils.keyboards import remove_keyboard

class NameInputComponent:
	"""
	Компонент для обробки введення імені та прізвища
	"""
	def __init__(self, dialog_manager: DialogManager, user_manager: UserManager, message_sender: MessageSender):
		self.dialog_manager = dialog_manager
		self.user_manager = user_manager
		self.message_sender = message_sender
		
	async def process_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		"""
		Обробляє введення імені та прізвища
		"""
		user_id = update.effective_user.id
		full_name = update.message.text
		dialog = self.dialog_manager.get_dialog(user_id)
		
		# Розділяємо введений текст на ім'я та прізвище
		name_parts = full_name.strip().split(maxsplit=1)
		if len(name_parts) < 2:
			await self.message_sender.send_message(
				update,
				context,
				"❌ Будь ласка, введіть і ім'я, і прізвище"
			)
			return
			
		first_name, last_name = name_parts
		
		# Оновлюємо дані користувача
		self.user_manager.update_user(
			user_id,
			first_name=first_name,
			last_name=last_name
		)
		
		# Оновлюємо стан діалогу
		self.dialog_manager.update_dialog(
			user_id,
			current_step='phone_input'
		)
		
		# Відправляємо підтвердження
		await self.message_sender.send_message(
			update,
			context,
			f"✅ Зафіксували ваші дані: {first_name} {last_name}",
			keyboard=remove_keyboard()
		)