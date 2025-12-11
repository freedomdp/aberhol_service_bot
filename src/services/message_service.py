from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

class MessageService:
	"""
	Сервіс для роботи з повідомленнями
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

	async def send_photo(
		self,
		chat_id: int,
		photo: str,
		caption: str = None
	) -> Message:
		"""
		Надсилає фото користувачу
		"""
		return await self.bot.send_photo(
			chat_id=chat_id,
			photo=photo,
			caption=caption
		)

	async def send_video(
		self,
		chat_id: int,
		video: str,
		caption: str = None
	) -> Message:
		"""
		Надсилає відео користувачу
		"""
		return await self.bot.send_video(
			chat_id=chat_id,
			video=video,
			caption=caption
		)

	async def delete_messages(self, chat_id: int, message_ids: list[int]) -> None:
		"""
		Видаляє повідомлення за їх ідентифікаторами
		"""
		for message_id in message_ids:
			try:
				await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
			except Exception:
				pass  # Ігноруємо помилки при видаленні повідомлень