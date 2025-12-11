import logging
from typing import List, Optional, Tuple
from aiogram import types
from aiogram.types import Message

from models.dialog import DialogManager
from services.message_service import MessageService
from utils.keyboards import get_next_keyboard

logger = logging.getLogger(__name__)

class PhotoUploadComponent:
	"""
	Компонент для обработки загрузки фото и видео материалов.
	
	Attributes:
		dialog_manager: Менеджер диалогов для хранения состояния
		message_service: Сервис для отправки сообщений
		max_files: Максимальное количество файлов (по умолчанию 10)
		max_file_size: Максимальный размер файла в байтах (10 МБ)
	"""
	
	MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
	ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'video/mp4']
	
	def __init__(
		self,
		dialog_manager: DialogManager,
		message_service: MessageService,
		max_files: int = 10
	):
		self.dialog_manager = dialog_manager
		self.message_service = message_service
		self.max_files = max_files
	
	async def process_input(self, message: Message) -> None:
		"""Обрабатывает загрузку фото или видео."""
		try:
			user_id = message.from_user.id
			dialog = self.dialog_manager.get_dialog(user_id)
			
			# Инициализация списков если их нет
			if not hasattr(dialog, 'photo_files'):
				dialog.photo_files = []
			if not hasattr(dialog, 'video_files'):
				dialog.video_files = []
			
			# Проверка формата и размера файла
			file_info = await self._validate_file(message)
			if not file_info:
				return
			
			file_id, is_video = file_info
			
			total_files = len(dialog.photo_files) + len(dialog.video_files)
			if total_files >= self.max_files:
				await self.message_service.send_message(
					chat_id=message.chat.id,
					text=f"❌ Досягнуто ліміт файлів ({self.max_files})"
				)
				return
			
			# Сохранение файла в соответствующий список
			if is_video:
				dialog.video_files.append(file_id)
			else:
				dialog.photo_files.append(file_id)
			
			# Отправка подтверждения
			total_files = len(dialog.photo_files) + len(dialog.video_files)
			await self.message_service.send_message(
				chat_id=message.chat.id,
				text=f"✅ Файл додано ({total_files}/{self.max_files})\nФото: {len(dialog.photo_files)} шт.\nВідео: {len(dialog.video_files)} шт.\nМожете додати ще файли або натисніть 'Далі'",
				keyboard=get_next_keyboard()
			)
			
		except Exception as e:
			logger.error(f"Error processing media upload: {str(e)}")
			await self._send_error_message(message.chat.id, "Виникла помилка при обробці файлу")
	
	async def _validate_file(self, message: Message) -> Optional[Tuple[str, bool]]:
		"""
		Проверяет валидность файла.
		
		Returns:
			Tuple[str, bool]: (file_id, is_video) или None если файл невалиден
		"""
		if message.photo:
			file_info = message.photo[-1]
			if file_info.file_size > self.MAX_FILE_SIZE:
				await self._send_error_message(
					message.chat.id,
					"❌ Розмір файлу перевищує максимально допустимий (10 МБ)"
				)
				return None
			return file_info.file_id, False
			
		elif message.video:
			if message.video.mime_type not in self.ALLOWED_MIME_TYPES:
				await self._send_error_message(
					message.chat.id,
					"❌ Непідтримуваний формат відео. Дозволено тільки MP4"
				)
				return None
				
			if message.video.file_size > self.MAX_FILE_SIZE:
				await self._send_error_message(
					message.chat.id,
					"❌ Розмір файлу перевищує максимально допустимий (10 МБ)"
				)
				return None
			return message.video.file_id, True
			
		await self._send_error_message(
			message.chat.id,
			"❌ Будь ласка, надішліть фото або відео у форматі MP4"
		)
		return None
	
	async def _send_error_message(self, chat_id: int, text: str) -> None:
		"""Отправляет сообщение об ошибке."""
		await self.message_service.send_message(
			chat_id=chat_id,
			text=text,
			keyboard=get_next_keyboard()
		)
