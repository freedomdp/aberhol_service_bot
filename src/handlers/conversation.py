import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from ..models.application import Application
from ..utils.validators import validate_email, validate_phone
from ..keyboards.inline import (
    get_skip_keyboard, 
    get_confirm_keyboard,
    get_printer_series_keyboard,
    get_printer_model_keyboard,
    get_filament_type_keyboard,
    get_filament_manufacturer_keyboard,
    PRINTER_MODELS_BY_SERIES,
    FILAMENT_TYPES,
    FILAMENT_MANUFACTURERS
)
from .commands import active_applications

logger = logging.getLogger(__name__)

# Стани розмови
(
    WAITING_NAME,
    WAITING_EMAIL,
    WAITING_PHONE,
    WAITING_ORDER_NUMBER,
    WAITING_PRINTER_MODEL,
    WAITING_FILAMENT_TYPE,
    WAITING_FILAMENT_MANUFACTURER,
    WAITING_PHOTOS,
    WAITING_MODEL_FILE,
    WAITING_DESCRIPTION,
    CONFIRMING,
) = range(11)


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання імені та прізвища"""
    from ..services.context import get_reminder_service
    
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text(
            "❌ Помилка. Будь ласка, почніть з команди /new_application"
        )
        return ConversationHandler.END
    
    full_name = update.message.text.strip()
    
    if len(full_name) < 2:
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректне ім'я та прізвище:"
        )
        return WAITING_NAME
    
    active_applications[user_id].full_name = full_name
    
    # Планируем напоминания после ввода имени
    reminder_service = get_reminder_service()
    if reminder_service:
        reminder_service.schedule_reminders(user_id, active_applications[user_id])
    
    await update.message.reply_text(
        "✅ Дякую! Тепер введіть ваш <b>email адресу</b>:",
        parse_mode='HTML'
    )
    
    return WAITING_EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання email"""
    user_id = update.effective_user.id
    email = update.message.text.strip()

    if not validate_email(email):
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректну email адресу:"
        )
        return WAITING_EMAIL

    active_applications[user_id].email = email

    await update.message.reply_text(
        "✅ Дякую! Тепер введіть ваш <b>номер телефону</b> "
        "(у форматі 0501234567 або +380501234567):",
        parse_mode='HTML'
    )

    return WAITING_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання номера телефону"""
    user_id = update.effective_user.id
    phone = update.message.text.strip()

    if not validate_phone(phone):
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректний номер телефону "
            "(український формат, наприклад: 0501234567):"
        )
        return WAITING_PHONE

    active_applications[user_id].phone_number = phone

    await update.message.reply_text(
        "✅ Дякую! Якщо ви купували у нас, вкажіть <b>номер замовлення</b> "
        "(або номер телефону/ПІБ покупця).\n"
        "Якщо ні, натисніть 'Пропустити':",
        parse_mode='HTML',
        reply_markup=get_skip_keyboard()
    )

    return WAITING_ORDER_NUMBER


async def get_order_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання номера замовлення"""
    user_id = update.effective_user.id
    order_number = update.message.text.strip()

    active_applications[user_id].order_number = order_number

    await update.message.reply_text(
        "✅ Дякую! Оберіть <b>серію вашого 3D-принтера</b>:",
        parse_mode='HTML',
        reply_markup=get_printer_series_keyboard()
    )

    return WAITING_PRINTER_MODEL


async def skip_order_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск номера замовлення"""
    user_id = update.effective_user.id

    if user_id not in active_applications:
        await update.callback_query.answer("❌ Помилка. Будь ласка, почніть з команди /new_application")
        return ConversationHandler.END

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Оберіть <b>серію вашого 3D-принтера</b>:",
        parse_mode='HTML',
        reply_markup=get_printer_series_keyboard()
    )

    return WAITING_PRINTER_MODEL


async def get_printer_series_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору серії принтера"""
    user_id = update.effective_user.id
    query = update.callback_query

    if user_id not in active_applications:
        await query.answer("❌ Помилка. Будь ласка, почніть з команди /new_application")
        return ConversationHandler.END

    if query.data.startswith("series_"):
        from ..keyboards.inline import PRINTER_SERIES
        series_index = int(query.data.split("_")[1])
        selected_series = PRINTER_SERIES[series_index]
        
        # Визначаємо ключ серії
        if "Серія A" in selected_series or "серія A" in selected_series:
            series_key = "A"
        elif "Серія P" in selected_series or "серія P" in selected_series:
            series_key = "P"
        elif "Серія X" in selected_series or "серія X" in selected_series:
            series_key = "X"
        elif "Серія H" in selected_series or "серія H" in selected_series:
            series_key = "H"
        else:
            series_key = "other"
        
        context.user_data['printer_series_key'] = series_key
        
        # Показуємо клавіатуру з моделями обраної серії
        keyboard = get_printer_model_keyboard(series_key)
        await query.answer()
        await query.edit_message_text(
            f"✅ Обрано: {selected_series}\n\nОберіть конкретну модель:",
            reply_markup=keyboard
        )
        return WAITING_PRINTER_MODEL

    return WAITING_PRINTER_MODEL


async def get_printer_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору моделі принтера з клавіатури"""
    user_id = update.effective_user.id
    query = update.callback_query

    if user_id not in active_applications:
        await query.answer("❌ Помилка. Будь ласка, почніть з команди /new_application")
        return ConversationHandler.END

    # Обробка нового формату: model_{series}_{index} або printer_manual
    if query.data.startswith("model_"):
        # Новий формат: model_{series}_{index}
        parts = query.data.split("_")
        series_key = parts[1]
        model_index = int(parts[2])
        models = PRINTER_MODELS_BY_SERIES.get(series_key, [])
        if model_index < len(models):
            printer_model = models[model_index]
            active_applications[user_id].printer_model = printer_model
            
            await query.answer()
            await query.edit_message_text(
                f"✅ Модель принтера: {printer_model}\n\n"
                "Оберіть <b>тип філаменту</b>:",
                parse_mode='HTML',
                reply_markup=get_filament_type_keyboard()
            )
            return WAITING_FILAMENT_TYPE
    elif query.data == "printer_manual":
        # Ручний ввід - поки що не підтримується в старому flow
        await query.answer("Будь ласка, оберіть модель зі списку")
        return WAITING_PRINTER_MODEL

    return WAITING_PRINTER_MODEL


async def get_filament_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору типу філаменту"""
    user_id = update.effective_user.id
    query = update.callback_query

    if user_id not in active_applications:
        await query.answer("❌ Помилка. Будь ласка, почніть з команди /new_application")
        return ConversationHandler.END

    if query.data.startswith("filament_type_"):
        filament_index = int(query.data.split("_")[2])
        active_applications[user_id].filament_type = FILAMENT_TYPES[filament_index]

        await query.answer()
        await query.edit_message_text(
            f"✅ Тип філаменту: {FILAMENT_TYPES[filament_index]}\n\n"
            "Оберіть <b>виробника філаменту</b>:",
            parse_mode='HTML',
            reply_markup=get_filament_manufacturer_keyboard()
        )

        return WAITING_FILAMENT_MANUFACTURER

    return WAITING_FILAMENT_TYPE


async def get_filament_manufacturer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору виробника філаменту"""
    user_id = update.effective_user.id
    query = update.callback_query

    if user_id not in active_applications:
        await query.answer("❌ Помилка. Будь ласка, почніть з команди /new_application")
        return ConversationHandler.END

    if query.data.startswith("filament_man_"):
        manufacturer_index = int(query.data.split("_")[2])
        active_applications[user_id].filament_manufacturer = FILAMENT_MANUFACTURERS[manufacturer_index]

        await query.answer()
        await query.edit_message_text(
            f"✅ Виробник філаменту: {FILAMENT_MANUFACTURERS[manufacturer_index]}\n\n"
            "📷 Тепер надішліть <b>фото або відео</b>, які показують проблему "
            "(можна надіслати до 10 файлів).\n"
            "Якщо фото немає, натисніть 'Пропустити':",
            parse_mode='HTML',
            reply_markup=get_skip_keyboard()
        )

        return WAITING_PHOTOS

    return WAITING_FILAMENT_MANUFACTURER


async def get_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання фото/відео"""
    from ..services.context import get_media_storage
    
    user_id = update.effective_user.id
    media_storage = get_media_storage()
    
    try:
        if update.message.photo:
            # Беремо найбільше фото (останнє в списку)
            photo = update.message.photo[-1]
            file_id = photo.file_id
            
            # Сохраняем временный file_id
            active_applications[user_id].photo_file_ids.append(file_id)
            
            # Скачиваем и сохраняем файл
            if media_storage:
                file = await context.bot.get_file(file_id)
                file_data = await file.download_as_bytearray()
                _, file_url = media_storage.save_file(
                    bytes(file_data), 
                    'photo', 
                    user_id
                )
                active_applications[user_id].photos.append(file_url)
            else:
                # Если хранилище не настроено, используем file_id
                active_applications[user_id].photos.append(file_id)
            
            count = len(active_applications[user_id].photos)
            if count < 10:
                await update.message.reply_text(
                    f"✅ Фото додано ({count}/10). Можете надіслати ще фото або натисніть 'Пропустити':",
                    reply_markup=get_skip_keyboard()
                )
            else:
                await update.message.reply_text(
                    "✅ Досягнуто максимум фото (10). Переходимо далі.",
                    reply_markup=get_skip_keyboard()
                )
                return await skip_photos(update, context)
            
            return WAITING_PHOTOS
        
        elif update.message.video:
            file_id = update.message.video.file_id
            
            # Сохраняем временный file_id
            active_applications[user_id].photo_file_ids.append(file_id)
            
            # Скачиваем и сохраняем файл
            if media_storage:
                file = await context.bot.get_file(file_id)
                file_data = await file.download_as_bytearray()
                _, file_url = media_storage.save_file(
                    bytes(file_data), 
                    'video', 
                    user_id
                )
                active_applications[user_id].photos.append(file_url)
            else:
                active_applications[user_id].photos.append(file_id)
            
            count = len(active_applications[user_id].photos)
            if count < 10:
                await update.message.reply_text(
                    f"✅ Відео додано ({count}/10). Можете надіслати ще файли або натисніть 'Пропустити':",
                    reply_markup=get_skip_keyboard()
                )
            else:
                await update.message.reply_text(
                    "✅ Досягнуто максимум файлів (10). Переходимо далі.",
                    reply_markup=get_skip_keyboard()
                )
                return await skip_photos(update, context)
            
            return WAITING_PHOTOS
        
        else:
            await update.message.reply_text(
                "❌ Будь ласка, надішліть фото або відео, або натисніть 'Пропустити':",
                reply_markup=get_skip_keyboard()
            )
            return WAITING_PHOTOS
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении медиафайла: {e}")
        await update.message.reply_text(
            "❌ Помилка при збереженні файлу. Спробуйте ще раз або пропустіть цей крок.",
            reply_markup=get_skip_keyboard()
        )
        return WAITING_PHOTOS


async def skip_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск завантаження фото"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📦 Тепер надішліть вашу <b>3D модель</b> (файл .stl, .obj або інший формат).\n"
            "Якщо моделі немає, натисніть 'Пропустити':",
            parse_mode='HTML',
            reply_markup=get_skip_keyboard()
        )
    else:
        await update.message.reply_text(
            "📦 Тепер надішліть вашу <b>3D модель</b> (файл .stl, .obj або інший формат).\n"
            "Якщо моделі немає, натисніть 'Пропустити':",
            parse_mode='HTML',
            reply_markup=get_skip_keyboard()
        )

    return WAITING_MODEL_FILE


async def get_model_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання 3D моделі"""
    from ..services.context import get_media_storage
    
    user_id = update.effective_user.id
    media_storage = get_media_storage()
    
    if update.message.document:
        try:
            file_id = update.message.document.file_id
            active_applications[user_id].model_file_id = file_id
            
            # Скачиваем и сохраняем файл
            if media_storage:
                file = await context.bot.get_file(file_id)
                file_data = await file.download_as_bytearray()
                _, file_url = media_storage.save_file(
                    bytes(file_data), 
                    'model', 
                    user_id
                )
                active_applications[user_id].model_file = file_url
            else:
                active_applications[user_id].model_file = file_id
            
            await update.message.reply_text(
                "✅ 3D модель додано!\n\n"
                "📝 Тепер опишіть <b>проблему та додаткову інформацію</b>:",
                parse_mode='HTML'
            )
            
            return WAITING_DESCRIPTION
        except Exception as e:
            logger.error(f"Ошибка при сохранении 3D модели: {e}")
            await update.message.reply_text(
                "❌ Помилка при збереженні файлу. Спробуйте ще раз або пропустіть цей крок.",
                reply_markup=get_skip_keyboard()
            )
            return WAITING_MODEL_FILE
    else:
        await update.message.reply_text(
            "❌ Будь ласка, надішліть файл 3D моделі або натисніть 'Пропустити':",
            reply_markup=get_skip_keyboard()
        )
        return WAITING_MODEL_FILE


async def skip_model_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск завантаження 3D моделі"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📝 Опишіть <b>проблему та додаткову інформацію</b>:",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "📝 Опишіть <b>проблему та додаткову інформацію</b>:",
            parse_mode='HTML'
        )

    return WAITING_DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання опису проблеми"""
    user_id = update.effective_user.id
    description = update.message.text.strip()

    active_applications[user_id].problem_description = description

    # Показуємо підсумок заявки
    app = active_applications[user_id]
    summary = app.to_message()

    await update.message.reply_text(
        f"{summary}\n\n"
        "Перевірте інформацію та підтвердіть відправку заявки:",
        parse_mode='HTML',
        reply_markup=get_confirm_keyboard()
    )

    return CONFIRMING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Скасування створення заявки"""
    user_id = update.effective_user.id

    if user_id in active_applications:
        del active_applications[user_id]

    cancel_message = "❌ Створення заявки скасовано.\n\nДля створення нової заявки натисніть /new_application"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(cancel_message)
    elif update.message:
        await update.message.reply_text(cancel_message)

    return ConversationHandler.END


def register_conversation_handlers(application):
    """Реєстрація обробників розмови"""
    from telegram.ext import CommandHandler
    from .callbacks import handle_confirm
    from .commands import new_application

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("new_application", new_application)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            WAITING_ORDER_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_number),
                CallbackQueryHandler(skip_order_number, pattern="^skip$"),
            ],
            WAITING_PRINTER_MODEL: [
                CallbackQueryHandler(get_printer_series_callback, pattern="^series_"),
                CallbackQueryHandler(get_printer_model_callback, pattern="^model_|^printer_manual$"),
            ],
            WAITING_FILAMENT_TYPE: [
                CallbackQueryHandler(get_filament_type_callback, pattern="^filament_type_"),
            ],
            WAITING_FILAMENT_MANUFACTURER: [
                CallbackQueryHandler(get_filament_manufacturer_callback, pattern="^filament_man_"),
            ],
            WAITING_PHOTOS: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_photos),
                CallbackQueryHandler(skip_photos, pattern="^skip$"),
            ],
            WAITING_MODEL_FILE: [
                MessageHandler(filters.Document.ALL, get_model_file),
                CallbackQueryHandler(skip_model_file, pattern="^skip$"),
            ],
            WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CONFIRMING: [
                CallbackQueryHandler(handle_confirm, pattern="^confirm$"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conversation_handler)
