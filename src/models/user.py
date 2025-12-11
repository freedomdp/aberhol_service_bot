from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
	"""
	Модель користувача
	"""
	user_id: int
	first_name: str
	last_name: str
	phone_number: Optional[str] = None
	order_number: Optional[str] = None

class UserManager:
	"""
	Менеджер для роботи з користувачами
	"""
	def __init__(self):
		self._users: dict[int, User] = {}
	
	def get_user(self, user_id: int, first_name: str, last_name: str) -> User:
		"""Отримати або створити користувача"""
		if user_id not in self._users:
			self._users[user_id] = User(
				user_id=user_id,
				first_name=first_name,
				last_name=last_name
			)
		return self._users[user_id]
	
	def update_user(self, user_id: int, **kwargs) -> None:
		"""Оновити дані користувача"""
		user = self._users.get(user_id)
		if user:
			for key, value in kwargs.items():
				setattr(user, key, value)
