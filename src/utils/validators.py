import re


def validate_email(email: str) -> bool:
    """Валідація email адреси"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Валідація номера телефону (український формат)"""
    # Видаляємо всі символи крім цифр
    digits_only = re.sub(r'\D', '', phone)
    # Перевіряємо, чи це український номер (починається з 0 або +380)
    if digits_only.startswith('380'):
        digits_only = '0' + digits_only[3:]
    return len(digits_only) == 10 and digits_only.startswith('0')
