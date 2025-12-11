from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Application:
    """Модель заявки на сервісне обслуговування"""
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    order_number: Optional[str] = None
    printer_model: Optional[str] = None
    filament_type: Optional[str] = None
    filament_manufacturer: Optional[str] = None
    problem_description: Optional[str] = None
    photos: List[str] = field(default_factory=list)  # Список URL фото/відео
    photo_file_ids: List[str] = field(default_factory=list)  # Временные file_id для сохранения
    photo_file_types: List[str] = field(default_factory=list)  # Типы файлов: 'photo' или 'video' (соответствует photo_file_ids)
    model_file: Optional[str] = None  # URL 3D моделі
    model_file_id: Optional[str] = None  # Временный file_id для сохранения
    created_at: datetime = field(default_factory=datetime.now)

    def is_complete(self) -> bool:
        """Перевіряє, чи заповнені всі обов'язкові поля"""
        return (
            self.full_name is not None and
            self.email is not None and
            self.phone_number is not None
        )

    def to_message(self) -> str:
        """Формує повідомлення для відправки інженеру"""
        message = f"📋 <b>Нова заявка на сервісне обслуговування</b>\n\n"
        message += f"👤 <b>Клієнт:</b> {self.full_name or 'Не вказано'}\n"
        if self.email:
            message += f"📧 <b>Email:</b> {self.email}\n"
        message += f"📱 <b>Телефон:</b> {self.phone_number or 'Не вказано'}\n"

        if self.order_number:
            message += f"🛒 <b>Номер замовлення:</b> {self.order_number}\n"

        message += "\n<b>Інформація про принтер:</b>\n"

        if self.printer_model:
            message += f"🖨️ <b>Модель принтера:</b> {self.printer_model}\n"

        if self.filament_type:
            message += f"🧵 <b>Тип філаменту:</b> {self.filament_type}\n"

        if self.filament_manufacturer:
            message += f"🏭 <b>Виробник філаменту:</b> {self.filament_manufacturer}\n"

        if self.problem_description:
            message += f"\n📝 <b>Опис проблеми:</b>\n{self.problem_description}\n"

        message += f"\n🕐 <b>Час створення:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"

        if self.photo_file_ids:
            # Файли відправляються окремо через send_media_group, тому не додаємо посилання
            message += f"\n📷 <b>Фото/відео:</b> {len(self.photo_file_ids)} файлів (відправлено окремо)\n"

        if self.model_file:
            message += f"\n📦 <b>3D модель:</b> {self.model_file}\n"

        return message
