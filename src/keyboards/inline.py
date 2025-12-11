from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# Серії принтерів Bambu Lab
PRINTER_SERIES = [
    "Серія A",
    "Серія P",
    "Серія X",
    "Серія H",
    "Інший виробник",
]

# Моделі принтерів по серіях
PRINTER_MODELS_BY_SERIES = {
    "A": [
        "A1",
        "A1 Combo",
        "A1 mini",
        "A1 mini Combo",
    ],
    "P": [
        "P1P",
        "P1S",
        "P1S Combo",
        "P2S",
        "P2S Combo",
    ],
    "X": [
        "X1",
        "X1 Combo",
        "X1E",
    ],
    "H": [
        "H2D",
        "H2D Combo",
        "H2D Laser",
        "H2S",
        "H2S Combo",
        "H2S Laser",
        "H2C",
        "H2C Combo",
        "H2C Laser",
    ],
}

# Типи філаменту
FILAMENT_TYPES = [
    "PLA",
    "PETG",
    "ABS",
    "ASA",
    "TPU",
    "PA (Nylon)",
    "PC (Polycarbonate)",
    "PP (Polypropylene)",
    "PVA",
    "PET",
    "Інший тип",
]

# Виробники філаменту
FILAMENT_MANUFACTURERS = [
    "Bambu Lab",
    "Polymaker",
    "eSun",
    "Sunlu",
    "Overture",
    "HATCHBOX",
    "Prusament",
    "Інший виробник",
]


def get_printer_series_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору серії принтера"""
    buttons = [
        [InlineKeyboardButton(series, callback_data=f"series_{i}")]
        for i, series in enumerate(PRINTER_SERIES)
    ]
    return InlineKeyboardMarkup(buttons)


def get_printer_model_keyboard(series: str) -> InlineKeyboardMarkup:
    """Клавіатура для вибору конкретної моделі принтера в залежності від серії"""
    if series == "other":
        # Якщо інший виробник, дозволяємо ввести текст
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Ввести вручну", callback_data="printer_manual")]
        ])
    
    models = PRINTER_MODELS_BY_SERIES.get(series, [])
    buttons = [
        [InlineKeyboardButton(model, callback_data=f"model_{series}_{i}")]
        for i, model in enumerate(models)
    ]
    return InlineKeyboardMarkup(buttons)


def get_filament_type_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору типу філаменту"""
    buttons = [
        [InlineKeyboardButton(filament_type, callback_data=f"filament_type_{i}")]
        for i, filament_type in enumerate(FILAMENT_TYPES)
    ]
    return InlineKeyboardMarkup(buttons)


def get_filament_manufacturer_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору виробника філаменту"""
    buttons = [
        [InlineKeyboardButton(manufacturer, callback_data=f"filament_man_{i}")]
        for i, manufacturer in enumerate(FILAMENT_MANUFACTURERS)
    ]
    return InlineKeyboardMarkup(buttons)


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура з кнопкою 'Пропустити'"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Пропустити", callback_data="skip")]
    ])


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для підтвердження заявки"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Підтвердити", callback_data="confirm"),
            InlineKeyboardButton("❌ Скасувати", callback_data="cancel")
        ]
    ])


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для розділу FAQ"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Куди відправляти принтер на ремонт", callback_data="faq_repair")],
        [InlineKeyboardButton("📚 Бібліотека Bambu Lab Wiki", url="https://wiki.bambulab.com/en/home")]
    ])


def get_order_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору наявності номера замовлення"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Є номер замовлення", callback_data="order_yes")],
        [InlineKeyboardButton("❌ Купував не у вас", callback_data="order_no")]
    ])
