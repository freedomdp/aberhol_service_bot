from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class DialogState:
	"""
	Клас для зберігання стану діалогу
	"""
	user_id: int
	order_number: Optional[str] = None
	user_name: Optional[str] = None  # Добавляем поле для имени
	phone_number: Optional[str] = None
	issue_description: Optional[str] = None
	printer_model: Optional[str] = None
	photo_files: List[str] = None
	video_files: List[str] = None
	current_step: str = "initial"
	started_at: datetime = datetime.now()
	completed_at: Optional[datetime] = None
	temp_message_ids: list[int] = None  # Для зберігання тимчасових повідомлень
	
	def __post_init__(self):
		"""Ініціалізація після створення об'єкту"""
		self.temp_message_ids = [] if self.temp_message_ids is None else self.temp_message_ids
		self.photo_files = [] if self.photo_files is None else self.photo_files
		self.video_files = [] if self.video_files is None else self.video_files
		
	def get_summary(self) -> str:
		"""Формує зведення всіх даних заявки"""
		summary_parts = []
		
		if self.order_number:
			summary_parts.append(f"📋 Номер замовлення: {self.order_number}")
		else:
			summary_parts.append("📑 Замовлення: Купували не у нас")
			
		if self.user_name:
			summary_parts.append(f"👤 Контактна особа: {self.user_name}")
			
		if self.phone_number:
			summary_parts.append(f"📱 Телефон: {self.phone_number}")
			
		if self.printer_model:
			summary_parts.append(f"🖨 Модель принтера: {self.printer_model}")
			
		if self.issue_description:
			summary_parts.append(f"❗️ Опис проблеми:\n{self.issue_description}")
			
		# Добавляем информацию о медиафайлах
		if self.photo_files or self.video_files:
			media_count = len(self.photo_files) + len(self.video_files)
			summary_parts.append(f"📎 Додано медіафайлів: {media_count}")
			
		return "\n\n".join(summary_parts)


	
class DialogManager:
	"""
	Менеджер для роботи зі станом діалогу
	"""
	def __init__(self):
		self._dialogs: dict[int, DialogState] = {}
		
	def get_dialog(self, user_id: int) -> DialogState:
		"""Отримати або створити стан діалогу для користувача"""
		if user_id not in self._dialogs:
			self._dialogs[user_id] = DialogState(user_id=user_id)
		return self._dialogs[user_id]
	
	def update_dialog(self, user_id: int, **kwargs) -> None:
		"""Оновити стан діалогу"""
		dialog = self.get_dialog(user_id)
		for key, value in kwargs.items():
			setattr(dialog, key, value)
			
	def complete_dialog(self, user_id: int) -> None:
		"""Завершити діалог"""
		dialog = self.get_dialog(user_id)
		dialog.completed_at = datetime.now()
		
	def clear_dialog(self, user_id: int) -> None:
		"""Очистити дані діалогу"""
		if user_id in self._dialogs:
			del self._dialogs[user_id]