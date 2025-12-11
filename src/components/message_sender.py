from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

class MessageSender:
	"""
	Компонент для надсилання повідомлень користувачу
	"""
	def __init__(self, bot: Bot):
		self.bot = bot
		
	async def send_message(
		self,
		chat_id: int,
		text: str,
		keyboard: ReplyKeyboardMarkup | ReplyKeyboardRemove | None = None
	) -> Message:
		"""
		Надсилає повідомлення користувачу
		"""
		return await self.bot.send_message(
			chat_id=chat_id,
			text=text,
			reply_markup=keyboard
		)

	async def delete_message(self, chat_id: int, message_id: int) -> bool:
		"""
		Видаляє повідомлення
		"""
		try:
			return await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
		except Exception:
			return False
