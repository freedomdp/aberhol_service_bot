from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура головного меню"""
    kb = [[
        KeyboardButton(text="🔧 Поломка"),
        KeyboardButton(text="🖨 Якість друку"),
    ]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_name_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для використання імені з профілю"""
    kb = [[KeyboardButton(text="👤 Використати ім'я з профілю")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура з кнопкою надання номера телефону"""
    kb = [[KeyboardButton(text="📱 Надати номер телефону", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_printer_model_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура вибору моделі принтера"""
    kb = [
        [
            KeyboardButton(text="A1 (Combo)"),
            KeyboardButton(text="A1 mini (Combo)")
        ],
        [
            KeyboardButton(text="P1P"),
            KeyboardButton(text="P1S (Combo)")
        ],
        [
            KeyboardButton(text="X1C (Combo)"),
            KeyboardButton(text="X1E")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура підтвердження заявки"""
    kb = [[
        KeyboardButton(text="❌ Скасувати"),
        KeyboardButton(text="✅ Підтверджую")
    ]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_next_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для переходу далі"""
    kb = [[KeyboardButton(text="Далі")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Створюємо об'єкт для видалення клавіатури
remove_keyboard = ReplyKeyboardRemove()
