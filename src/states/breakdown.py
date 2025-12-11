"""
Модуль определяет состояния для диалога о поломке принтера.
Каждое состояние представляет определенный этап в процессе сбора информации о проблеме.
"""
from aiogram.fsm.state import State, StatesGroup

class BreakdownStates(StatesGroup):
	"""
	Состояния диалога о поломке:
	- waiting_order: ожидание номера заказа
	- waiting_name: ожидание ввода имени
	- waiting_phone: ожидание ввода телефона
	- waiting_printer_model: ожидание выбора модели принтера
	- waiting_description: ожидание описания проблемы
	- waiting_media: ожидание фото/видео материалов
	- confirmation: подтверждение заявки
	"""
	waiting_order = State()
	waiting_name = State()
	waiting_phone = State()
	waiting_printer_model = State()
	waiting_description = State()
	waiting_media = State()
	confirmation = State()
