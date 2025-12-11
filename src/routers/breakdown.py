from aiogram import Router, F
import logging
from aiogram.filters import Command  # Убедимся что этот импорт есть

logger = logging.getLogger(__name__)
from aiogram.types import Message, Contact
from aiogram.fsm.context import FSMContext
from config import config
from components.photo_upload import PhotoUploadComponent

from models.dialog import DialogManager
from models.user import UserManager
from services.message_service import MessageService
from states.breakdown import BreakdownStates
from utils.validators import validate_phone
from utils.messages import (
    REQUEST_NAME, REQUEST_PRINTER_MODEL, REQUEST_ISSUE_DESCRIPTION,
    REQUEST_PHOTO, ISSUE_CONFIRMED, PHOTO_ADDED, REQUEST_COMPLETED,
    REVIEW_REQUEST, REQUEST_PHONE, WELCOME_MESSAGE  # Добавим импорт WELCOME_MESSAGE
)
from utils.keyboards import (
    remove_keyboard, get_profile_name_keyboard,
    get_printer_model_keyboard, get_next_keyboard,
    get_confirmation_keyboard, get_phone_keyboard,
    get_main_keyboard
)

router = Router(name="breakdown")

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "🔧 Поломка")
async def start_breakdown(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	user_manager: UserManager,
	message_service: MessageService
) -> None:
	"""Початок діалогу про поломку"""
	user = message.from_user

	# Ініціалізація користувача
	user_manager.get_user(
		user_id=user.id,
		first_name=user.first_name,
		last_name=user.last_name or ""
	)

	# Ініціалізація діалогу
	dialog = dialog_manager.get_dialog(user.id)
	dialog.current_step = "initial"

	# Встановлення стану та відправка повідомлень
	await state.set_state(BreakdownStates.waiting_order)
	await message_service.send_message(
		chat_id=message.chat.id,
		text="Ви обрали розділ '🔧 Поломка'. Для початку діалогу потрібно надати деяку інформацію.\n\n🔢 Введіть номер вашого замовлення на сайті bambulab.net.ua, за яким ви купували принтер (якщо купували не у нас, просто напишіть 'немає')",
		keyboard=remove_keyboard  # Убираем клавиатуру на время диалога
	)


@router.message(BreakdownStates.waiting_order)
async def process_order(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обробка номера замовлення"""
	user_id = message.from_user.id
	order_number = message.text.lower()

	if order_number == "немає":
		# Якщо користувач не купував у нас
		dialog_manager.update_dialog(
			user_id,
			order_number=None,
			current_step='name_input'
		)

		await message_service.send_message(
			chat_id=message.chat.id,
			text="✅ Зафіксували, що ви купували не у нас"
		)

		# Перехід до введення імені
		await state.set_state(BreakdownStates.waiting_name)
		await message_service.send_message(
			chat_id=message.chat.id,
			text=REQUEST_NAME,
			keyboard=get_profile_name_keyboard()
		)
	else:
		# Якщо вказано номер замовлення
		dialog_manager.update_dialog(
			user_id,
			order_number=order_number,
			current_step='printer_model_input'
		)

		await message_service.send_message(
			chat_id=message.chat.id,
			text=f"✅ Зафіксували номер замовлення: {order_number}"
		)

		# Перехід до вибору моделі принтера
		await state.set_state(BreakdownStates.waiting_printer_model)
		await message_service.send_message(
			chat_id=message.chat.id,
			text=REQUEST_PRINTER_MODEL,
			keyboard=get_printer_model_keyboard()
		)


@router.message(BreakdownStates.waiting_name, F.text == "👤 Використати ім'я з профілю")
async def use_profile_name(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Использование имени из профиля Telegram"""
	user = message.from_user
	user_id = user.id

	# Формируем полное имя из данных профиля
	full_name = f"{user.first_name}"
	if user.last_name:
		full_name += f" {user.last_name}"

	# Сохраняем имя в диалоге
	dialog_manager.update_dialog(
		user_id,
		user_name=full_name,
		current_step='phone_input'
	)

	# Отправляем подтверждение
	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"✅ Зафіксували ваше ім'я: {full_name}"
	)

	# Переходим к вводу телефона
	await state.set_state(BreakdownStates.waiting_phone)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_PHONE,
		keyboard=get_phone_keyboard()
	)

@router.message(BreakdownStates.waiting_name)
async def process_name(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка введенного имени"""
	user_id = message.from_user.id
	name = message.text

	# Сохраняем имя в диалоге
	dialog_manager.update_dialog(
		user_id,
		user_name=name,
		current_step='phone_input'
	)

	# Отправляем подтверждение и переходим к телефону
	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"✅ Зафіксували ваше ім'я: {name}"
	)

	await state.set_state(BreakdownStates.waiting_phone)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_PHONE,
		keyboard=get_phone_keyboard()
	)

@router.message(BreakdownStates.waiting_phone, F.contact)
async def process_phone_from_profile(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка номера телефона из профиля"""
	user_id = message.from_user.id
	contact = message.contact

	if not contact or not contact.phone_number:
		await message_service.send_message(
			chat_id=message.chat.id,
			text="Через налаштування вашого профілю ми не можемо отримати номер телефону, вкажіть ваш номер вручну",
			keyboard=remove_keyboard
		)
		return

	phone = f"+{contact.phone_number}" if not contact.phone_number.startswith('+') else contact.phone_number
	is_valid, validated_phone = validate_phone(phone)

	if not is_valid:
		await message_service.send_message(
			chat_id=message.chat.id,
			text=validated_phone,
			keyboard=remove_keyboard
		)
		return

	# Сохраняем телефон и переходим к выбору модели
	dialog_manager.update_dialog(
		user_id,
		phone_number=validated_phone,
		current_step='printer_model_input'
	)

	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"✅ Зафіксували номер телефону: {validated_phone}"
	)

	await state.set_state(BreakdownStates.waiting_printer_model)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_PRINTER_MODEL,
		keyboard=get_printer_model_keyboard()
	)

@router.message(BreakdownStates.waiting_phone)
async def process_phone(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка введенного номера телефона"""
	user_id = message.from_user.id
	phone = message.text

	is_valid, result = validate_phone(phone)
	if not is_valid:
		await message_service.send_message(
			chat_id=message.chat.id,
			text=result,
			keyboard=get_phone_keyboard()
		)
		return

	# Сохраняем телефон и переходим к выбору модели
	dialog_manager.update_dialog(
		user_id,
		phone_number=result,
		current_step='printer_model_input'
	)

	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"✅ Зафіксували номер телефону: {result}"
	)

	await state.set_state(BreakdownStates.waiting_printer_model)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_PRINTER_MODEL,
		keyboard=get_printer_model_keyboard()
	)

@router.message(BreakdownStates.waiting_printer_model)
async def process_printer_model(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка выбора модели принтера"""
	user_id = message.from_user.id
	model = message.text

	# Сохраняем модель принтера и обновляем состояние диалога
	dialog_manager.update_dialog(
		user_id,
		printer_model=model,
		current_step='issue_description'
	)

	# Отправляем подтверждение и убираем клавиатуру
	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"✅ Зафіксували модель принтеру: {model}",
		keyboard=remove_keyboard  # Используем remove_keyboard вместо get_main_keyboard
	)

	# Переходим к следующему этапу
	await state.set_state(BreakdownStates.waiting_description)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_ISSUE_DESCRIPTION
	)


@router.message(BreakdownStates.waiting_description)
async def process_description(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка описания проблемы"""
	user_id = message.from_user.id
	description = message.text

	# Сохраняем описание проблемы
	dialog_manager.update_dialog(
		user_id,
		issue_description=description,
		current_step='waiting_media'
	)

	# Отправляем подтверждение
	await message_service.send_message(
		chat_id=message.chat.id,
		text=f"{ISSUE_CONFIRMED}:\n{description}"
	)

	# Переходим к этапу фотографий
	await state.set_state(BreakdownStates.waiting_media)
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REQUEST_PHOTO,
		keyboard=get_next_keyboard()
	)

@router.message(BreakdownStates.waiting_media, F.text == "Далі")
async def finish_photos(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Завершение этапа отправки фото"""
	user_id = message.from_user.id
	dialog = dialog_manager.get_dialog(user_id)

	# Переходим к этапу подтверждения
	dialog.current_step = 'confirmation'
	await state.set_state(BreakdownStates.confirmation)

	# Отправляем сообщение с данными заявки
	await message_service.send_message(
		chat_id=message.chat.id,
		text=REVIEW_REQUEST + "\n\n" + dialog.get_summary(),
		keyboard=get_confirmation_keyboard()
	)

@router.message(BreakdownStates.confirmation, F.text == "✅ Підтверджую")
async def confirm_request(
    message: Message,
    state: FSMContext,
    dialog_manager: DialogManager,
    message_service: MessageService
) -> None:
    """Подтверждение заявки"""
    user_id = message.from_user.id
    dialog = dialog_manager.get_dialog(user_id)

    # Сначала отправляем заявку инженеру
    engineer_id = config.ENGINEER_TELEGRAM_ID
    await message_service.send_message(
        chat_id=engineer_id,
        text=f"🆕 Нова заявка!\n\n{dialog.get_summary()}"
    )

    # Отправляем медиафайлы инженеру
    if hasattr(dialog, 'photo_files') and dialog.photo_files:
        for photo_id in dialog.photo_files:
            try:
                await message_service.send_photo(
                    chat_id=engineer_id,
                    photo=photo_id
                )
            except Exception as e:
                logger.error(f"Error sending photo to engineer: {e}")

    if hasattr(dialog, 'video_files') and dialog.video_files:
        for video_id in dialog.video_files:
            try:
                await message_service.send_video(
                    chat_id=engineer_id,
                    video=video_id
                )
            except Exception as e:
                logger.error(f"Error sending video to engineer: {e}")

    # Очищаем историю сообщений
    try:
        last_message_id = message.message_id
        for i in range(last_message_id - 100, last_message_id + 1):
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=i)
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")

    # Очищаем состояние и диалог
    await state.clear()
    dialog_manager.clear_dialog(user_id)

    # Отправляем только два финальных сообщения
    await message_service.send_message(
        chat_id=message.chat.id,
        text="✅ Дякуємо!\nВашу заявку прийнято.\n\nПриблизний термін оброки заявки - 2 робочих дні."
    )

    # Показываем главное меню
    await message_service.send_message(
        chat_id=message.chat.id,
        text="Оберіть, будь ласка, тему звернення:",
        keyboard=get_main_keyboard()
    )

@router.message(BreakdownStates.confirmation, F.text == "❌ Скасувати")
async def cancel_request(
    message: Message,
    state: FSMContext,
    dialog_manager: DialogManager,
    message_service: MessageService
) -> None:
    """Отмена заявки"""
    user_id = message.from_user.id

    # Очищаем историю сообщений
    try:
        last_message_id = message.message_id
        for i in range(last_message_id - 100, last_message_id + 1):
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=i)
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")

    # Очищаем состояние и диалог
    await state.clear()
    dialog_manager.clear_dialog(user_id)

    # Отправляем сообщение об отмене
    await message_service.send_message(
        chat_id=message.chat.id,
        text="❌ Заявку скасовано"
    )

    # Вызываем команду /start
    await cmd_start(message)

@router.message(BreakdownStates.waiting_media, F.photo | F.video)
async def process_media(
	message: Message,
	state: FSMContext,
	dialog_manager: DialogManager,
	message_service: MessageService
) -> None:
	"""Обработка фото/видео файлов"""
	photo_upload = PhotoUploadComponent(dialog_manager, message_service)
	await photo_upload.process_input(message)
