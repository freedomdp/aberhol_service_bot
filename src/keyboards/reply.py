from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру головного меню з 3 кнопками в один рядок
	"""
	kb = [
		[
			KeyboardButton(text="🔧 Поломка"),
			KeyboardButton(text="🖨 Якість друку"),
			KeyboardButton(text="❓ Питання / Відповідь")
		]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_order_choice_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру для вибору наявності номера замовлення (ReplyKeyboard)
	"""
	kb = [
		[KeyboardButton(text="✅ Є номер замовлення")],
		[KeyboardButton(text="❌ Купував не у вас")]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_printer_series_reply_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру для вибору серії принтера (ReplyKeyboard) в 2 колонки
	"""
	kb = [
		[KeyboardButton(text="Серія A"), KeyboardButton(text="Серія P")],
		[KeyboardButton(text="Серія X"), KeyboardButton(text="Серія H")],
		[KeyboardButton(text="Інший виробник")]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_printer_model_reply_keyboard(series: str) -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру для вибору моделі принтера (ReplyKeyboard) в 2 колонки
	"""
	from .inline import PRINTER_MODELS_BY_SERIES
	
	if series == "other":
		# Якщо інший виробник, дозволяємо ввести текст
		kb = [
			[KeyboardButton(text="✏️ Ввести вручну")]
		]
	else:
		models = PRINTER_MODELS_BY_SERIES.get(series, [])
		# Групуємо кнопки по 2 в ряд
		kb = []
		for i in range(0, len(models), 2):
			row = [KeyboardButton(text=models[i])]
			if i + 1 < len(models):
				row.append(KeyboardButton(text=models[i + 1]))
			kb.append(row)
	
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_skip_reply_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру з кнопкою 'Пропустити' (ReplyKeyboard)
	"""
	kb = [
		[KeyboardButton(text="⏭️ Пропустити")]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_next_reply_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру з кнопкою 'Далі' (ReplyKeyboard)
	"""
	kb = [
		[KeyboardButton(text="➡️ Далі")]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_confirm_reply_keyboard() -> ReplyKeyboardMarkup:
	"""
	Повертає клавіатуру для підтвердження заявки (ReplyKeyboard) в 2 колонки
	"""
	kb = [
		[KeyboardButton(text="✅ Підтвердити"), KeyboardButton(text="❌ Скасувати")]
	]
	return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
	"""
	Повертає об'єкт для видалення клавіатури
	"""
	return ReplyKeyboardRemove()
