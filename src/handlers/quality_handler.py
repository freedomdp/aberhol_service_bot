"""
Обробник діалогу для розділу '🖨 Якість друку'
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from ..models.application import Application
from ..utils.validators import validate_phone
from ..utils.messages import REQUEST_NAME, REQUEST_PHONE, REQUEST_PHOTO
from ..keyboards.inline import get_skip_keyboard, get_confirm_keyboard
from ..keyboards.reply import remove_keyboard
from .commands import active_applications

logger = logging.getLogger(__name__)

# Стани діалогу для розділу Якість друку
(
    QL_WAITING_NAME,
    QL_WAITING_PHONE,
    QL_WAITING_PHOTOS,
    QL_WAITING_COMMENTS,
    QL_CONFIRMING,
) = range(5)


async def start_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Початок діалогу про якість друку"""
    user_id = update.effective_user.id
    
    # Якщо вже є активна заявка, видаляємо її
    if user_id in active_applications:
        from ..services.context import get_reminder_service
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        del active_applications[user_id]
    
    # Створюємо нову заявку
    active_applications[user_id] = Application(user_id=user_id)
    
    await update.message.reply_text(
        "Ви обрали розділ '🖨 Якість друку'. Для початку діалогу потрібно надати деяку інформацію.\n\n" + REQUEST_NAME,
        reply_markup=remove_keyboard()
    )
    
    return QL_WAITING_NAME


async def get_quality_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання імені (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalNameInput
    
    app = active_applications[user_id]
    success, message, _ = await UniversalNameInput.process(
        update, context, app, next_message=REQUEST_PHONE, next_state=QL_WAITING_PHONE
    )
    
    if not success:
        await update.message.reply_text(message)
        return QL_WAITING_NAME
    
    await update.message.reply_text(message)
    return QL_WAITING_PHONE


async def get_quality_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання номера телефону (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalPhoneInput
    
    app = active_applications[user_id]
    success, message, _ = await UniversalPhoneInput.process(
        update, context, app, next_message=REQUEST_PHOTO, next_state=QL_WAITING_PHOTOS
    )
    
    if not success:
        await update.message.reply_text(message)
        return QL_WAITING_PHONE
    
    await update.message.reply_text(message, reply_markup=get_skip_keyboard())
    return QL_WAITING_PHOTOS


async def get_quality_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання фото/відео (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalPhotoUpload
    
    app = active_applications[user_id]
    success, message, is_max = await UniversalPhotoUpload.process(
        update, context, app, max_files=10
    )
    
    if not success:
        await update.message.reply_text(message, reply_markup=get_skip_keyboard())
        return QL_WAITING_PHOTOS
    
    if is_max:
        await update.message.reply_text(
            "✅ Досягнуто максимум файлів (10). Переходимо до коментарів."
        )
        await update.message.reply_text(
            "✍️ Напишіть додаткові деталі та коментарі про проблему з якістю друку:"
        )
        return QL_WAITING_COMMENTS
    
    await update.message.reply_text(message, reply_markup=get_skip_keyboard())
    return QL_WAITING_PHOTOS


async def skip_quality_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропуск фото"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✍️ Напишіть додаткові деталі та коментарі про проблему з якістю друку:"
    )
    
    return QL_WAITING_COMMENTS


async def get_quality_comments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання коментарів (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalTextInput
    
    app = active_applications[user_id]
    success, _, _ = await UniversalTextInput.process(
        update, context, app,
        field_name="problem_description",
        next_state=QL_CONFIRMING
    )
    
    if not success:
        await update.message.reply_text("❌ Будь ласка, введіть коментарі.")
        return QL_WAITING_COMMENTS
    
    # Формуємо підсумок заявки
    summary = f"📋 <b>Нова заявка: 🖨 Якість друку</b>\n\n"
    summary += f"👤 <b>Клієнт:</b> {app.full_name}\n"
    summary += f"📱 <b>Телефон:</b> {app.phone_number}\n"
    
    if app.problem_description:
        summary += f"\n📝 <b>Додаткові деталі та коментарі:</b>\n{app.problem_description}\n"
    
    if app.photos:
        summary += f"\n📷 <b>Фото/відео:</b> {len(app.photos)} файлів\n"
    
    summary += f"\n🕐 <b>Час створення:</b> {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    await update.message.reply_text(
        f"{summary}\n\nПеревірте інформацію та підтвердіть відправку заявки:",
        parse_mode='HTML',
        reply_markup=get_confirm_keyboard()
    )
    
    return QL_CONFIRMING


async def confirm_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Підтвердження та відправка заявки інженеру"""
    import os
    
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await query.answer("❌ Помилка. Заявка не знайдена.")
        return ConversationHandler.END
    
    app = active_applications[user_id]
    
    # Перевіряємо обов'язкові поля
    if not app.full_name or not app.phone_number:
        await query.answer("❌ Заявка не повна. Будь ласка, заповніть всі обов'язкові поля.")
        return QL_CONFIRMING
    
    # Отримуємо ID інженера або групи для відправки заявок
    # Спочатку перевіряємо GROUP_CHAT_ID, якщо не встановлено - використовуємо ENGINEER_TELEGRAM_ID
    recipient_id = os.getenv('GROUP_CHAT_ID') or os.getenv('ENGINEER_TELEGRAM_ID')
    
    if not recipient_id:
        await query.answer("❌ Помилка конфігурації. Не налаштовано отримувача заявок (GROUP_CHAT_ID або ENGINEER_TELEGRAM_ID).")
        return ConversationHandler.END
    
    try:
        recipient_id = int(recipient_id)
        
        # Формуємо повідомлення для інженера
        message_text = f"📋 <b>Нова заявка: 🖨 Якість друку</b>\n\n"
        message_text += f"👤 <b>Клієнт:</b> {app.full_name}\n"
        message_text += f"📱 <b>Телефон:</b> {app.phone_number}\n"
        
        if app.problem_description:
            message_text += f"\n📝 <b>Додаткові деталі та коментарі:</b>\n{app.problem_description}\n"
        
        message_text += f"\n🕐 <b>Час створення:</b> {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        if app.photos:
            message_text += f"\n📷 <b>Фото/відео:</b> {len(app.photos)} файлів\n"
        
        # Відправляємо заявку інженеру або в групу
        await context.bot.send_message(
            chat_id=recipient_id,
            text=message_text,
            parse_mode='HTML'
        )
        
        # Відправляємо фото/відео якщо є
        if app.photo_file_ids:
            media_group = []
            for i, photo_id in enumerate(app.photo_file_ids[:10]):
                # Використовуємо збережений тип файлу, якщо він є
                if i < len(app.photo_file_types):
                    media_type = app.photo_file_types[i]
                else:
                    # Fallback: визначаємо тип по префіксу file_id
                    media_type = 'photo'  # По умолчанию фото
                    if not photo_id.startswith('AgAC'):
                        media_type = 'video'
                
                media_group.append({
                    'type': media_type,
                    'media': photo_id
                })
            
            # Розділяємо на групи по 10 файлів
            for i in range(0, len(media_group), 10):
                group = media_group[i:i+10]
                try:
                    await context.bot.send_media_group(
                        chat_id=recipient_id,
                        media=group
                    )
                except Exception as e:
                    logger.error(f"Помилка при відправці медіа: {e}")
        
        # Підтверджуємо користувачу
        await query.answer("✅ Заявка успішно відправлена!")
        await query.edit_message_text(
            "✅ <b>Заявка успішно відправлена!</b>\n\n"
            "Наш спеціаліст надасть вам відповідь протягом до 2 робочих днів.\n\n"
            "Дякуємо за звернення! 🙏",
            parse_mode='HTML'
        )
        
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
        await query.answer(f"❌ Помилка при відправці заявки: {str(e)}")
        return QL_CONFIRMING


async def cancel_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Скасування створення заявки"""
    user_id = update.effective_user.id
    
    if user_id in active_applications:
        from ..services.context import get_reminder_service
        reminder_service = get_reminder_service()
        if reminder_service:
            reminder_service.cancel_reminders(user_id)
        del active_applications[user_id]
    
    cancel_message = "❌ Створення заявки скасовано.\n\nДля створення нової заявки оберіть розділ з меню."
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(cancel_message)
    elif update.message:
        await update.message.reply_text(cancel_message)
    
    return ConversationHandler.END


def get_quality_conversation_handler() -> ConversationHandler:
    """Створює ConversationHandler для розділу Якість друку"""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^🖨 Якість друку$"), start_quality)],
        states={
            QL_WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quality_name)],
            QL_WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quality_phone)],
            QL_WAITING_PHOTOS: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_quality_photos),
                CallbackQueryHandler(skip_quality_photos, pattern="^skip$"),
            ],
            QL_WAITING_COMMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quality_comments)],
            QL_CONFIRMING: [
                CallbackQueryHandler(confirm_quality, pattern="^confirm$"),
                CallbackQueryHandler(cancel_quality, pattern="^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_quality)],
    )
