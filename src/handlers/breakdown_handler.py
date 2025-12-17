"""
Обробник діалогу для розділу '🔧 Поломка'
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from ..models.application import Application
from ..utils.validators import validate_phone
from ..utils.messages import REQUEST_ORDER, REQUEST_NAME, REQUEST_PHONE, REQUEST_EMAIL, REQUEST_PRINTER_MODEL, REQUEST_ISSUE_DESCRIPTION, REQUEST_PHOTO
from ..keyboards.reply import remove_keyboard, get_main_keyboard, get_skip_reply_keyboard, get_next_reply_keyboard, get_confirm_reply_keyboard
from .commands import active_applications

logger = logging.getLogger(__name__)

# Стани діалогу для розділу Поломка
(
    BD_WAITING_ORDER,
    BD_WAITING_ORDER_NUMBER,
    BD_WAITING_NAME,
    BD_WAITING_PHONE,
    BD_WAITING_EMAIL,           # Новий стан для введення email
    BD_WAITING_PRINTER_SERIES,  # Новий стан для вибору серії
    BD_WAITING_PRINTER_MODEL,   # Стан для вибору конкретної моделі
    BD_WAITING_DESCRIPTION,
    BD_WAITING_PHOTOS,
    BD_CONFIRMING,
) = range(10)


async def start_breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Початок діалогу про поломку"""
    from ..keyboards.reply import get_order_choice_keyboard
    
    logger.info("=" * 80)
    logger.info("start_breakdown ВИКЛИКАНО")
    user_id = update.effective_user.id
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")
    
    # Якщо вже є активна заявка, видаляємо її
    if user_id in active_applications:
        logger.info(f"Знайдено існуючу заявку для user_id {user_id}, видаляємо її")
        from ..services.context import get_reminder_service
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        del active_applications[user_id]
    
    # Створюємо нову заявку
    active_applications[user_id] = Application(user_id=user_id)
    logger.info(f"Створено нову заявку для user_id: {user_id}")
    
    await update.message.reply_text(
        "Ви обрали розділ '🔧 Поломка'. Для початку діалогу потрібно надати деяку інформацію.\n\n"
        + REQUEST_ORDER,
        reply_markup=remove_keyboard()
    )
    
    # Показуємо reply кнопки для вибору
    keyboard = get_order_choice_keyboard()
    logger.info(f"Reply клавіатура створена: {keyboard}")
    await update.message.reply_text(
        "Оберіть варіант:",
        reply_markup=keyboard
    )
    
    logger.info(f"Повертаємо стан BD_WAITING_ORDER (reply кнопки обробляються через MessageHandler)")
    return BD_WAITING_ORDER


async def handle_order_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору 'Є номер замовлення' (через reply кнопку)"""
    logger.info("=" * 80)
    logger.info("handle_order_yes ВИКЛИКАНО (через reply кнопку)")
    user_id = update.effective_user.id
    logger.info(f"message.text: {update.message.text}")
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")

    # Перевіряємо, чи є активна заявка
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END

    try:
        await update.message.reply_text(
            "🔢 Введіть номер вашого замовлення:",
            reply_markup=remove_keyboard()
        )
        logger.info("Повідомлення відправлено, очікуємо введення номера замовлення")
        logger.info("Перехід до BD_WAITING_ORDER_NUMBER")
        return BD_WAITING_ORDER_NUMBER
    except Exception as e:
        logger.error(f"Помилка в handle_order_yes: {e}", exc_info=True)
        await update.message.reply_text("❌ Помилка. Спробуйте ще раз.")
        return BD_WAITING_ORDER


async def handle_order_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка вибору 'Купував не у вас' (через reply кнопку)"""
    logger.info("=" * 80)
    logger.info("handle_order_no ВИКЛИКАНО (через reply кнопку)")
    user_id = update.effective_user.id
    logger.info(f"message.text: {update.message.text}")
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")

    # Перевіряємо, чи є активна заявка
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END

    try:
        # Встановлюємо, що замовлення немає
        active_applications[user_id].order_number = None
        logger.info("Встановлено order_number = None")
        
        await update.message.reply_text(
            "✅ Зафіксували, що ви купували не у нас",
            reply_markup=remove_keyboard()
        )
        await update.message.reply_text(REQUEST_NAME)
        logger.info("Повідомлення відправлено, очікуємо введення імені")
        logger.info("Перехід до BD_WAITING_NAME")
        return BD_WAITING_NAME
    except Exception as e:
        logger.error(f"Помилка в handle_order_no: {e}", exc_info=True)
        await update.message.reply_text("❌ Помилка. Спробуйте ще раз.")
        return BD_WAITING_ORDER




async def get_breakdown_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання номера замовлення (текстовий ввід)"""
    logger.info("=" * 80)
    logger.info("get_breakdown_order ВИКЛИКАНО")
    user_id = update.effective_user.id
    logger.info(f"user_id: {user_id}")
    logger.info(f"message.text: {update.message.text if update.message else None}")
    logger.info(f"context.user_data: {context.user_data}")
    
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    order_text = update.message.text.strip()
    logger.info(f"order_text: {order_text}")
    
    if not order_text:
        logger.warning("Порожній номер замовлення")
        await update.message.reply_text("❌ Будь ласка, введіть номер замовлення:")
        return BD_WAITING_ORDER_NUMBER
    
    active_applications[user_id].order_number = order_text
    logger.info(f"Збережено номер замовлення: {order_text}")
    await update.message.reply_text(f"✅ Зафіксували номер замовлення: {order_text}")
    # Якщо є номер замовлення, пропускаємо ім'я і переходимо до вибору серії принтера
    from ..keyboards.reply import get_printer_series_reply_keyboard
    context.user_data['breakdown_state'] = BD_WAITING_PRINTER_SERIES
    await update.message.reply_text(
        REQUEST_PRINTER_MODEL,
        reply_markup=get_printer_series_reply_keyboard()
    )
    logger.info("Перехід до BD_WAITING_PRINTER_SERIES")
    return BD_WAITING_PRINTER_SERIES


async def get_breakdown_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання імені (використовує універсальний компонент)"""
    logger.info("=" * 80)
    logger.info("get_breakdown_name ВИКЛИКАНО")
    user_id = update.effective_user.id
    logger.info(f"user_id: {user_id}")
    logger.info(f"message.text: {update.message.text if update.message else None}")
    logger.info(f"context.user_data: {context.user_data}")
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalNameInput
    
    app = active_applications[user_id]
    success, message, _ = await UniversalNameInput.process(
        update, context, app, next_message=REQUEST_PHONE, next_state=BD_WAITING_PHONE
    )
    
    if not success:
        await update.message.reply_text(message)
        return BD_WAITING_NAME
    
    await update.message.reply_text(message)
    logger.info("Перехід до BD_WAITING_PHONE")
    return BD_WAITING_PHONE


async def get_breakdown_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання номера телефону (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalPhoneInput
    
    app = active_applications[user_id]
    
    # Після телефону завжди переходимо до введення email
    success, message, _ = await UniversalPhoneInput.process(
        update, context, app, next_message=REQUEST_EMAIL, next_state=BD_WAITING_EMAIL
    )
    
    if not success:
        await update.message.reply_text(message)
        return BD_WAITING_PHONE
    
    await update.message.reply_text(message)
    context.user_data['breakdown_state'] = BD_WAITING_EMAIL
    logger.info("Перехід до BD_WAITING_EMAIL")
    return BD_WAITING_EMAIL


async def get_breakdown_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання email адреси (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalEmailInput
    
    app = active_applications[user_id]
    
    # Визначаємо наступне повідомлення та стан залежно від наявності номера замовлення
    if not app.order_number:
        next_message = REQUEST_PRINTER_MODEL
        next_state = BD_WAITING_PRINTER_SERIES
        use_keyboard = True
    else:
        # Якщо є номер замовлення, після email переходимо до фото/відео
        next_message = REQUEST_PHOTO
        next_state = BD_WAITING_PHOTOS
        use_keyboard = False
    
    success, message, _ = await UniversalEmailInput.process(
        update, context, app, next_message=next_message, next_state=next_state
    )
    
    if not success:
        await update.message.reply_text(message)
        return BD_WAITING_EMAIL
    
    if use_keyboard:
        from ..keyboards.reply import get_printer_series_reply_keyboard
        context.user_data['breakdown_state'] = BD_WAITING_PRINTER_SERIES
        await update.message.reply_text(message, reply_markup=get_printer_series_reply_keyboard())
        logger.info("Перехід до BD_WAITING_PRINTER_SERIES")
    else:
        # Після email переходимо до фото/відео (показуємо "Пропустити", бо файлів ще немає)
        from ..keyboards.reply import get_skip_reply_keyboard
        context.user_data['breakdown_state'] = BD_WAITING_PHOTOS
        await update.message.reply_text(
            message,
            reply_markup=get_skip_reply_keyboard()
        )
        logger.info("Перехід до BD_WAITING_PHOTOS")
    
    return next_state


async def get_breakdown_printer_series(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання серії принтера через ReplyKeyboard (текстове повідомлення)"""
    logger.info("=" * 80)
    logger.info("get_breakdown_printer_series ВИКЛИКАНО (через ReplyKeyboard)")
    
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else "N/A"
    
    logger.info(f"message.text: {message_text}")
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")
    
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    # Перевіряємо, що користувач знаходиться в очікуваному стані
    if context.user_data.get('breakdown_state') != BD_WAITING_PRINTER_SERIES:
        logger.warning(f"Користувач {user_id} натиснув кнопку серії не в стані BD_WAITING_PRINTER_SERIES. Поточний стан: {context.user_data.get('breakdown_state')}")
        await update.message.reply_text("Будь ласка, почніть процес заново, обравши '🔧 Поломка'.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    try:
        selected_series = message_text.strip()
        logger.info(f"Обрана серія: {selected_series}")
        
        # Зберігаємо серію в контексті для подальшого використання
        context.user_data['printer_series'] = selected_series
        
        # Визначаємо ключ серії для отримання моделей
        if "Серія A" in selected_series or "серія A" in selected_series or selected_series == "Серія A":
            series_key = "A"
        elif "Серія P" in selected_series or "серія P" in selected_series or selected_series == "Серія P":
            series_key = "P"
        elif "Серія X" in selected_series or "серія X" in selected_series or selected_series == "Серія X":
            series_key = "X"
        elif "Серія H" in selected_series or "серія H" in selected_series or selected_series == "Серія H":
            series_key = "H"
        else:
            series_key = "other"
        
        context.user_data['printer_series_key'] = series_key
        logger.info(f"Ключ серії: {series_key}")
        
        # Встановлюємо стан через context.user_data для ConversationHandler
        context.user_data['breakdown_state'] = BD_WAITING_PRINTER_MODEL
        logger.info(f"Встановлено breakdown_state = {BD_WAITING_PRINTER_MODEL} в context.user_data")
        
        # Показуємо клавіатуру з моделями обраної серії (ReplyKeyboard)
        from ..keyboards.reply import get_printer_model_reply_keyboard, remove_keyboard
        keyboard = get_printer_model_reply_keyboard(series_key)
        
        await update.message.reply_text(
            f"✅ Обрано: {selected_series}\n\nОберіть конкретну модель:",
            reply_markup=remove_keyboard()  # Убираем предыдущую reply-клавиатуру
        )
        await update.message.reply_text(
            "Оберіть модель:",
            reply_markup=keyboard
        )
        logger.info("Перехід до BD_WAITING_PRINTER_MODEL")
        return BD_WAITING_PRINTER_MODEL
    except Exception as e:
        logger.error(f"Помилка в get_breakdown_printer_series: {e}", exc_info=True)
        await update.message.reply_text("❌ Помилка. Спробуйте ще раз.", reply_markup=get_main_keyboard())
        return BD_WAITING_PRINTER_SERIES


async def get_breakdown_printer_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання конкретної моделі принтера через ReplyKeyboard (текстове повідомлення)"""
    logger.info("=" * 80)
    logger.info("get_breakdown_printer_model ВИКЛИКАНО (через ReplyKeyboard)")
    
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else "N/A"
    
    logger.info(f"message.text: {message_text}")
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")
    
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    # Перевіряємо, що користувач знаходиться в очікуваному стані
    if context.user_data.get('breakdown_state') != BD_WAITING_PRINTER_MODEL:
        logger.warning(f"Користувач {user_id} натиснув кнопку моделі не в стані BD_WAITING_PRINTER_MODEL. Поточний стан: {context.user_data.get('breakdown_state')}")
        await update.message.reply_text("Будь ласка, почніть процес заново, обравши '🔧 Поломка'.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    try:
        from ..keyboards.inline import PRINTER_MODELS_BY_SERIES
        from ..keyboards.reply import remove_keyboard
        
        # Отримуємо серію з контексту
        series_key = context.user_data.get('printer_series_key', 'A')
        logger.info(f"Серія з контексту: {series_key}")
        
        # Перевіряємо, чи це ручний ввід
        if message_text.strip() == "✏️ Ввести вручну":
            await update.message.reply_text(
                "✏️ Введіть модель принтера вручну:",
                reply_markup=remove_keyboard()
            )
            context.user_data['waiting_manual_printer'] = True
            return BD_WAITING_PRINTER_MODEL
        
        # Перевіряємо, чи очікуємо ручний ввід
        if context.user_data.get('waiting_manual_printer', False):
            # Ручний ввід моделі
            selected_model = message_text.strip()
            if not selected_model:
                await update.message.reply_text("❌ Будь ласка, введіть модель принтера:")
                return BD_WAITING_PRINTER_MODEL
            logger.info(f"Введена модель вручну: {selected_model}")
            context.user_data.pop('waiting_manual_printer', None)
        else:
            # Отримуємо список моделей для перевірки
            models = PRINTER_MODELS_BY_SERIES.get(series_key, [])
            
            # Перевіряємо, чи обрана модель є в списку
            selected_model = message_text.strip()
            if selected_model not in models:
                logger.warning(f"Обрана модель '{selected_model}' не знайдена в списку моделей для серії {series_key}")
                await update.message.reply_text("❌ Будь ласка, оберіть модель з клавіатури.")
                return BD_WAITING_PRINTER_MODEL
        
        logger.info(f"Обрана модель: {selected_model}")
        
        active_applications[user_id].printer_model = selected_model
        
        app = active_applications[user_id]
        
        # Якщо є номер замовлення, то після моделі принтера запитуємо телефон
        # Якщо немає номера замовлення, то телефон вже введений, переходимо до фото/відео
        if app.order_number:
            await update.message.reply_text(
                f"✅ Зафіксували модель принтеру: {selected_model}\n\n" + REQUEST_PHONE,
                reply_markup=remove_keyboard()
            )
            logger.info("Перехід до BD_WAITING_PHONE")
            return BD_WAITING_PHONE
        else:
            # Після моделі принтера переходимо до фото/відео
            await update.message.reply_text(
                f"✅ Зафіксували модель принтеру: {selected_model}\n\n" + REQUEST_PHOTO,
                reply_markup=get_skip_reply_keyboard()
            )
            logger.info("Перехід до BD_WAITING_PHOTOS")
            context.user_data['breakdown_state'] = BD_WAITING_PHOTOS
            return BD_WAITING_PHOTOS
    except Exception as e:
        logger.error(f"Помилка в get_breakdown_printer_model: {e}", exc_info=True)
        await update.message.reply_text("❌ Помилка. Спробуйте ще раз.", reply_markup=get_main_keyboard())
        return BD_WAITING_PRINTER_MODEL


async def get_breakdown_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання опису проблеми (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else ""
    
    # Перевіряємо, чи це пропуск опису
    if message_text.strip() == "⏭️ Пропустити":
        return await skip_breakdown_description(update, context)
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalTextInput
    
    app = active_applications[user_id]
    success, message, _ = await UniversalTextInput.process(
        update, context, app,
        field_name="problem_description",
        next_message="",  # Не використовуємо, бо одразу переходимо до підтвердження
        next_state=BD_CONFIRMING
    )
    
    if not success:
        await update.message.reply_text(message, reply_markup=get_skip_reply_keyboard())
        return BD_WAITING_DESCRIPTION
    
    # Після опису показуємо підсумок заявки для підтвердження
    summary = app.to_message()
    await update.message.reply_text(
        f"{summary}\n\nПеревірте інформацію та підтвердіть відправку заявки:",
        parse_mode='HTML',
        reply_markup=get_confirm_reply_keyboard()
    )
    context.user_data['breakdown_state'] = BD_CONFIRMING
    logger.info("Перехід до BD_CONFIRMING (після опису)")
    return BD_CONFIRMING


async def skip_breakdown_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск опису проблеми - перехід до підтвердження"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    app = active_applications[user_id]
    
    # Показуємо підсумок заявки для підтвердження
    summary = app.to_message()
    await update.message.reply_text(
        f"{summary}\n\nПеревірте інформацію та підтвердіть відправку заявки:",
        parse_mode='HTML',
        reply_markup=get_confirm_reply_keyboard()
    )
    context.user_data['breakdown_state'] = BD_CONFIRMING
    logger.info("Перехід до BD_CONFIRMING (після пропуску опису)")
    return BD_CONFIRMING


async def get_breakdown_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання фото/відео (використовує універсальний компонент, підтримує медіа-групи)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalPhotoUpload
    
    app = active_applications[user_id]
    
    # Обробляємо файл(и)
    success, message, is_max = await UniversalPhotoUpload.process(
        update, context, app, max_files=10
    )
    
    # Якщо повідомлення порожнє (файл з медіа-групи вже оброблено), не відправляємо відповідь
    if not message:
        context.user_data['breakdown_state'] = BD_WAITING_PHOTOS
        return BD_WAITING_PHOTOS
    
    if not success:
        # Якщо помилка, показуємо кнопку в залежності від кількості файлів
        files_count = len(app.photo_file_ids)
        context.user_data['breakdown_state'] = BD_WAITING_PHOTOS
        if files_count == 0:
            await update.message.reply_text(message, reply_markup=get_skip_reply_keyboard())
        else:
            await update.message.reply_text(message, reply_markup=get_next_reply_keyboard())
        return BD_WAITING_PHOTOS
    
    # Якщо досягли максимуму (10 файлів), автоматично переходимо до опису
    if is_max:
        await update.message.reply_text(
            message + "\n\n" + REQUEST_ISSUE_DESCRIPTION,
            reply_markup=get_skip_reply_keyboard()
        )
        context.user_data['breakdown_state'] = BD_WAITING_DESCRIPTION
        logger.info("Перехід до BD_WAITING_DESCRIPTION (після максимуму фото - 10 файлів)")
        return BD_WAITING_DESCRIPTION
    
    # Визначаємо, яку кнопку показувати в залежності від кількості файлів
    files_count = len(app.photo_file_ids)
    
    # Встановлюємо стан для ConversationHandler
    context.user_data['breakdown_state'] = BD_WAITING_PHOTOS
    logger.info(f"Встановлено breakdown_state = {BD_WAITING_PHOTOS} в context.user_data")
    
    # Для медіа-груп відправляємо повідомлення тільки один раз (на останнє повідомлення групи)
    # Але оскільки ми не знаємо, яке повідомлення останнє, відправляємо на кожне
    # (Telegram сам об'єднає повідомлення в групу)
    if files_count == 0:
        # Якщо файлів ще немає, показуємо "Пропустити"
        await update.message.reply_text(message, reply_markup=get_skip_reply_keyboard())
    else:
        # Якщо є хоча б один файл, показуємо "Далі"
        await update.message.reply_text(message, reply_markup=get_next_reply_keyboard())
    
    logger.info(f"Повертаємо стан BD_WAITING_PHOTOS (файлів: {files_count})")
    return BD_WAITING_PHOTOS


async def skip_breakdown_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск фото або перехід далі - перехід до опису проблеми"""
    logger.info("=" * 80)
    logger.info("skip_breakdown_photos ВИКЛИКАНО")
    
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else ""
    
    logger.info(f"message_text: '{message_text}'")
    logger.info(f"user_id: {user_id}")
    logger.info(f"context.user_data: {context.user_data}")
    
    if user_id not in active_applications:
        logger.error(f"user_id {user_id} not in active_applications")
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    app = active_applications[user_id]
    
    # Після пропуску фото або натискання "Далі" переходимо до опису проблеми
    if message_text.strip() == "⏭️ Пропустити":
        logger.info("Користувач пропустив завантаження фото")
    elif message_text.strip() == "➡️ Далі":
        logger.info(f"Користувач перейшов далі після завантаження {len(app.photo_file_ids)} файлів")
    else:
        logger.warning(f"Невідомий текст кнопки: '{message_text.strip()}'")
    
    await update.message.reply_text(
        REQUEST_ISSUE_DESCRIPTION,
        reply_markup=get_skip_reply_keyboard()
    )
    context.user_data['breakdown_state'] = BD_WAITING_DESCRIPTION
    logger.info("Перехід до BD_WAITING_DESCRIPTION (після фото/відео)")
    return BD_WAITING_DESCRIPTION


async def confirm_breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Підтвердження та відправка заявки інженеру (через ReplyKeyboard)"""
    import os
    import asyncio
    
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else "N/A"
    
    logger.info(f"confirm_breakdown: message_text={message_text}, user_id={user_id}")
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Заявка не знайдена.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    app = active_applications[user_id]
    
    # Перевіряємо обов'язкові поля
    # Якщо є номер замовлення, то full_name не обов'язковий
    has_required_fields = (
        app.phone_number and 
        app.printer_model and 
        (app.full_name or app.order_number)  # Або ім'я, або номер замовлення
    )
    
    if not has_required_fields:
        missing_fields = []
        if not app.phone_number:
            missing_fields.append("телефон")
        if not app.printer_model:
            missing_fields.append("модель принтера")
        if not app.full_name and not app.order_number:
            missing_fields.append("ім'я або номер замовлення")
        
        await update.message.reply_text(
            f"❌ Заявка не повна. Будь ласка, заповніть всі обов'язкові поля: {', '.join(missing_fields)}.", 
            reply_markup=get_confirm_reply_keyboard()
        )
        return BD_CONFIRMING
    
    # Отримуємо ID інженера або групи для відправки заявок
    # Можна використовувати як ID користувача (позитивне число), так і ID групи (негативне число, наприклад -1001234567890)
    # Спочатку перевіряємо GROUP_CHAT_ID, якщо не встановлено - використовуємо ENGINEER_TELEGRAM_ID
    recipient_id = os.getenv('GROUP_CHAT_ID') or os.getenv('ENGINEER_TELEGRAM_ID')
    
    if not recipient_id:
        await update.message.reply_text("❌ Помилка конфігурації. Не налаштовано отримувача заявок (GROUP_CHAT_ID або ENGINEER_TELEGRAM_ID).", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    try:
        recipient_id = int(recipient_id)

        # Запам'ятовуємо, куди відправляємо (для ретраїв)
        app.engineer_chat_id = recipient_id
        
        # Відправляємо текст заявки інженеру ОДИН раз (щоб ретраї не дублювали summary)
        if not app.engineer_summary_message_id:
            engineer_message_text = app.to_message()
            engineer_message_text = engineer_message_text.replace(
                "📋 <b>Нова заявка на сервісне обслуговування</b>",
                "📋 <b>Нова заявка: 🔧 Поломка</b>"
            )
            sent_msg = await context.bot.send_message(
                chat_id=recipient_id,
                text=engineer_message_text,
                parse_mode='HTML'
            )
            app.engineer_summary_message_id = getattr(sent_msg, "message_id", None)

        # Надійно доставляємо медіа інженеру: копіюємо оригінальні повідомлення користувача
        logger.info(f"confirm_breakdown: media_messages={len(app.media_messages)}, photo_file_ids={len(app.photo_file_ids)}")
        
        pending_media = [m for m in app.media_messages if m.get("message_id") not in app.media_messages_sent]
        media_sent_to_engineer = False
        
        # Fallback: якщо media_messages не збережені (старий код або помилка), використовуємо send_media_group
        if not pending_media and app.photo_file_ids:
            logger.warning(f"media_messages порожній, але є {len(app.photo_file_ids)} photo_file_ids. Використовуємо fallback (send_media_group) для інженера")
            media_group = []
            for i, photo_id in enumerate(app.photo_file_ids[:10]):
                if i < len(app.photo_file_types):
                    media_type = app.photo_file_types[i]
                else:
                    media_type = 'photo' if photo_id.startswith('AgAC') else 'video'
                
                media_group.append({
                    'type': media_type,
                    'media': photo_id
                })
            
            for i in range(0, len(media_group), 10):
                group = media_group[i:i+10]
                try:
                    await context.bot.send_media_group(
                        chat_id=recipient_id,
                        media=group
                    )
                    logger.info(f"✅ Відправлено {len(group)} медіа інженеру через send_media_group (fallback)")
                    media_sent_to_engineer = True
                except Exception as e:
                    logger.error(f"❌ Помилка при відправці медіа інженеру через fallback: {e}", exc_info=True)
                    await update.message.reply_text(
                        f"❌ Не вдалося переслати файли інженеру. Спробуйте підтвердити ще раз.",
                        reply_markup=get_confirm_reply_keyboard()
                    )
                    return BD_CONFIRMING
        
        elif pending_media:
            logger.info(f"Копіюємо {len(pending_media)} медіа інженеру через copy_message")
            failed = []
            for m in pending_media:
                from_chat_id = int(m["chat_id"])
                msg_id = int(m["message_id"])
                ok = False
                last_err = None
                for delay in (0.0, 0.8, 1.6):
                    try:
                        if delay:
                            await asyncio.sleep(delay)
                        await context.bot.copy_message(
                            chat_id=recipient_id,
                            from_chat_id=from_chat_id,
                            message_id=msg_id
                        )
                        app.media_messages_sent.add(msg_id)
                        ok = True
                        logger.info(f"✅ Успішно скопійовано медіа інженеру message_id={msg_id}")
                        media_sent_to_engineer = True
                        break
                    except Exception as e:
                        last_err = e
                        logger.warning(f"Помилка при копіюванні медіа message_id={msg_id} (спроба з затримкою {delay}s): {e}")

            if failed:
                remaining = len([m for m in app.media_messages if m.get("message_id") not in app.media_messages_sent])
                logger.error(f"❌ Не вдалося переслати {len(failed)} медіа інженеру. Залишилось: {remaining}. Помилки: {[str(e) for _, e in failed]}")
                
                # Fallback: якщо copy_message не спрацював, пробуємо send_media_group
                if app.photo_file_ids:
                    logger.warning(f"Пробуємо fallback через send_media_group для {len(app.photo_file_ids)} файлів")
                    try:
                        media_group = []
                        for i, photo_id in enumerate(app.photo_file_ids[:10]):
                            if i < len(app.photo_file_types):
                                media_type = app.photo_file_types[i]
                            else:
                                media_type = 'photo' if photo_id.startswith('AgAC') else 'video'
                            
                            media_group.append({
                                'type': media_type,
                                'media': photo_id
                            })
                        
                        await context.bot.send_media_group(
                            chat_id=recipient_id,
                            media=media_group
                        )
                        logger.info(f"✅ Відправлено {len(media_group)} медіа інженеру через send_media_group (fallback після помилки copy_message)")
                        media_sent_to_engineer = True
                    except Exception as fallback_err:
                        logger.error(f"❌ Fallback також не спрацював: {fallback_err}")
                        await update.message.reply_text(
                            f"❌ Не вдалося переслати всі файли інженеру. Залишилось: {remaining}.\n"
                            f"Будь ласка, натисніть підтвердження ще раз — бот повторить відправку файлів.",
                            reply_markup=get_confirm_reply_keyboard()
                        )
                        return BD_CONFIRMING
                else:
                    await update.message.reply_text(
                        f"❌ Не вдалося переслати всі файли інженеру. Залишилось: {remaining}.\n"
                        f"Будь ласка, натисніть підтвердження ще раз — бот повторить відправку файлів.",
                        reply_markup=get_confirm_reply_keyboard()
                    )
                    return BD_CONFIRMING
        
        # Перевіряємо, що медіа були відправлені інженеру
        if app.photo_file_ids and not media_sent_to_engineer:
            logger.error(f"❌ КРИТИЧНА ПОМИЛКА: Є {len(app.photo_file_ids)} photo_file_ids, але медіа не були відправлені інженеру!")
            await update.message.reply_text(
                f"❌ Помилка: файли не були відправлені інженеру. Будь ласка, спробуйте підтвердити ще раз.",
                reply_markup=get_confirm_reply_keyboard()
            )
            return BD_CONFIRMING
        
        # Формуємо фінальне повідомлення з повною інформацією про заявку
        full_message = app.to_message()
        # Замінюємо заголовок для клієнта
        full_message = full_message.replace(
            "📋 <b>Нова заявка на сервісне обслуговування</b>",
            "📋 <b>Нова заявка: 🔧 Поломка</b>"
        )
        
        # Додаємо повідомлення про успішну відправку
        success_message = (
            "\n\n"
            "✅ <b>Заявка успішно відправлена!</b>\n\n"
            "Наш спеціаліст надасть вам відповідь протягом до 2 робочих днів.\n\n"
            "Дякуємо за звернення! 🙏"
        )
        
        # Відправляємо текст клієнту
        await update.message.reply_text(
            full_message + success_message,
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        
        # ВАЖЛИВО: Показуємо клієнту його файли, щоб він бачив, що вони прикріплені
        user_chat_id = update.effective_chat.id
        client_media_to_show = app.media_messages if app.media_messages else []
        
        # Якщо media_messages порожній, але є photo_file_ids, створюємо тимчасові посилання для показу
        if not client_media_to_show and app.photo_file_ids:
            logger.info(f"Для клієнта: media_messages порожній, але є {len(app.photo_file_ids)} photo_file_ids. Відправляємо через send_media_group")
            try:
                media_group = []
                for i, photo_id in enumerate(app.photo_file_ids[:10]):
                    if i < len(app.photo_file_types):
                        media_type = app.photo_file_types[i]
                    else:
                        media_type = 'photo' if photo_id.startswith('AgAC') else 'video'
                    
                    media_group.append({
                        'type': media_type,
                        'media': photo_id
                    })
                
                if media_group:
                    # Відправляємо перше фото/відео з caption (текст заявки)
                    first_media = media_group[0]
                    caption = full_message + success_message
                    if first_media['type'] == 'photo':
                        await context.bot.send_photo(
                            chat_id=user_chat_id,
                            photo=first_media['media'],
                            caption=caption[:1024],  # Telegram limit
                            parse_mode='HTML'
                        )
                    else:
                        await context.bot.send_video(
                            chat_id=user_chat_id,
                            video=first_media['media'],
                            caption=caption[:1024],
                            parse_mode='HTML'
                        )
                    
                    # Решту відправляємо без caption
                    if len(media_group) > 1:
                        await context.bot.send_media_group(
                            chat_id=user_chat_id,
                            media=media_group[1:10]
                        )
            except Exception as e:
                logger.error(f"Помилка при відправці медіа клієнту: {e}")
        elif client_media_to_show:
            # Копіюємо оригінальні повідомлення клієнту, щоб він бачив свої файли
            logger.info(f"Копіюємо {len(client_media_to_show)} медіа клієнту для перегляду")
            for m in client_media_to_show[:10]:  # Обмежуємо до 10 файлів
                try:
                    from_chat_id = int(m["chat_id"])
                    msg_id = int(m["message_id"])
                    await context.bot.copy_message(
                        chat_id=user_chat_id,
                        from_chat_id=from_chat_id,
                        message_id=msg_id
                    )
                except Exception as e:
                    logger.warning(f"Не вдалося скопіювати медіа клієнту message_id={msg_id}: {e}")
        
        # Отправляем заявку в KeyCRM через API (асинхронно, не блокируем ответ пользователю)
        from ..services.context import get_keycrm_service
        keycrm_service = get_keycrm_service()
        if keycrm_service:
            try:
                # Отправляем заявку в KeyCRM в фоне (не ждем результата)
                import asyncio
                async def send_to_keycrm_with_logging():
                    """Обертка для логирования результата отправки в KeyCRM"""
                    try:
                        card_id = await keycrm_service.create_card(app, context.bot)
                        if card_id:
                            logger.info(f"✅ Заявка успешно создана в KeyCRM (card_id={card_id}) для пользователя {user_id}")
                        else:
                            logger.error(f"❌ Не удалось создать заявку в KeyCRM для пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при отправке заявки в KeyCRM для пользователя {user_id}: {e}", exc_info=True)
                
                asyncio.create_task(send_to_keycrm_with_logging())
                logger.info(f"Запущена отправка заявки в KeyCRM для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при запуске отправки в KeyCRM: {e}", exc_info=True)
        else:
            logger.warning("KeyCRMService не инициализирован. Заявка в KeyCRM не будет отправлена.")
        
        # Отменяем напоминания
        from ..services.context import get_reminder_service
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        
        # Видаляємо заявку
        del active_applications[user_id]
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Помилка при відправці заявки: {e}")
        await update.message.reply_text(f"❌ Помилка при відправці заявки: {str(e)}", reply_markup=get_confirm_reply_keyboard())
        return BD_CONFIRMING


async def cancel_breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Скасування створення заявки (через ReplyKeyboard)"""
    user_id = update.effective_user.id
    
    if user_id in active_applications:
        from ..services.context import get_reminder_service
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        del active_applications[user_id]
    
    cancel_message = "❌ Створення заявки скасовано.\n\nДля створення нової заявки оберіть розділ з меню."
    
    await update.message.reply_text(cancel_message, reply_markup=get_main_keyboard())
    
    return ConversationHandler.END


def get_breakdown_conversation_handler() -> ConversationHandler:
    """Створює ConversationHandler для розділу Поломка"""
    logger.info("Створення ConversationHandler для розділу Поломка")
    logger.info("ВАЖЛИВО: Використовуємо ReplyKeyboard замість InlineKeyboard для order_yes/order_no")
    
    return ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^🔧 Поломка$"), start_breakdown)],
        states={
            BD_WAITING_ORDER: [
                # Обработка reply кнопок для выбора наличия номера заказа
                MessageHandler(filters.TEXT & filters.Regex("^✅ Є номер замовлення$"), handle_order_yes),
                MessageHandler(filters.TEXT & filters.Regex("^❌ Купував не у вас$"), handle_order_no),
            ],
            BD_WAITING_ORDER_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_order)],
            BD_WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_name)],
            BD_WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_phone)],
            BD_WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_email)],
            BD_WAITING_PRINTER_SERIES: [
                MessageHandler(filters.TEXT & filters.Regex("^(Серія A|Серія P|Серія X|Серія H|Інший виробник)$"), get_breakdown_printer_series),
            ],
            BD_WAITING_PRINTER_MODEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_printer_model),
            ],
            BD_WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & filters.Regex("^⏭️ Пропустити$"), skip_breakdown_description),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakdown_description),
            ],
            BD_WAITING_PHOTOS: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_breakdown_photos),
                MessageHandler(
                    filters.TEXT & (
                        filters.Regex("^⏭️ Пропустити$") | 
                        filters.Regex("^➡️ Далі$")
                    ), 
                    skip_breakdown_photos
                ),
            ],
            BD_CONFIRMING: [
                MessageHandler(filters.TEXT & filters.Regex("^✅ Підтвердити$"), confirm_breakdown),
                MessageHandler(filters.TEXT & filters.Regex("^❌ Скасувати$"), cancel_breakdown),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_breakdown)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )
