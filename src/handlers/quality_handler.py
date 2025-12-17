"""
Обробник діалогу для розділу '🖨 Якість друку'
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from ..models.application import Application
from ..utils.validators import validate_phone
from ..utils.messages import REQUEST_NAME, REQUEST_PHONE, REQUEST_EMAIL, REQUEST_PHOTO
from ..keyboards.inline import get_skip_keyboard, get_confirm_keyboard
from ..keyboards.reply import remove_keyboard
from .commands import active_applications

logger = logging.getLogger(__name__)

# Стани діалогу для розділу Якість друку
(
    QL_WAITING_NAME,
    QL_WAITING_PHONE,
    QL_WAITING_EMAIL,      # Новий стан для введення email
    QL_WAITING_PHOTOS,
    QL_WAITING_COMMENTS,
    QL_CONFIRMING,
) = range(6)


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
        update, context, app, next_message=REQUEST_EMAIL, next_state=QL_WAITING_EMAIL
    )
    
    if not success:
        await update.message.reply_text(message)
        return QL_WAITING_PHONE
    
    await update.message.reply_text(message)
    return QL_WAITING_EMAIL


async def get_quality_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отримання email адреси (використовує універсальний компонент)"""
    user_id = update.effective_user.id
    
    if user_id not in active_applications:
        await update.message.reply_text("❌ Помилка. Будь ласка, почніть знову.")
        return ConversationHandler.END
    
    from ..components import UniversalEmailInput
    
    app = active_applications[user_id]
    success, message, _ = await UniversalEmailInput.process(
        update, context, app, next_message=REQUEST_PHOTO, next_state=QL_WAITING_PHOTOS
    )
    
    if not success:
        await update.message.reply_text(message)
        return QL_WAITING_EMAIL
    
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
    import asyncio
    
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

        # Запам'ятовуємо, куди відправляємо (для ретраїв)
        app.engineer_chat_id = recipient_id
        
        # Формуємо та відправляємо повідомлення для інженера ОДИН раз (щоб ретраї не дублювали summary)
        if not app.engineer_summary_message_id:
            message_text = f"📋 <b>Нова заявка: 🖨 Якість друку</b>\n\n"
            message_text += f"👤 <b>Клієнт:</b> {app.full_name}\n"
            message_text += f"📱 <b>Телефон:</b> {app.phone_number}\n"
            
            if app.problem_description:
                message_text += f"\n📝 <b>Додаткові деталі та коментарі:</b>\n{app.problem_description}\n"
            
            message_text += f"\n🕐 <b>Час створення:</b> {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            media_count = len(app.media_messages) if app.media_messages else len(app.photo_file_ids)
            if media_count:
                message_text += f"\n📷 <b>Фото/відео:</b> {media_count} файлів (відправлено окремо)\n"
            
            sent_msg = await context.bot.send_message(
                chat_id=recipient_id,
                text=message_text,
                parse_mode='HTML'
            )
            app.engineer_summary_message_id = getattr(sent_msg, "message_id", None)

        # Надійно доставляємо медіа інженеру: копіюємо оригінальні повідомлення користувача
        logger.info(f"confirm_quality: media_messages={len(app.media_messages)}, photo_file_ids={len(app.photo_file_ids)}")
        
        pending_media = [m for m in app.media_messages if m.get("message_id") not in app.media_messages_sent]
        media_sent_to_engineer = False
        
        # Fallback: якщо media_messages не збережені (старий код або помилка), використовуємо send_media_group
        if not pending_media and app.photo_file_ids:
            logger.warning(f"media_messages порожній, але є {len(app.photo_file_ids)} photo_file_ids. Використовуємо fallback (send_media_group)")
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
                    await query.answer("❌ Не вдалося переслати файли інженеру. Спробуйте підтвердити ще раз.")
                    return QL_CONFIRMING
        
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
                if not ok:
                    failed.append((msg_id, last_err))

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
                        await query.answer("❌ Не всі файли вдалося переслати. Спробуйте підтвердити ще раз.")
                        return QL_CONFIRMING
                else:
                    await query.answer("❌ Не всі файли вдалося переслати. Спробуйте підтвердити ще раз.")
                    return QL_CONFIRMING
        
        # Перевіряємо, що медіа були відправлені інженеру
        if app.photo_file_ids and not media_sent_to_engineer:
            logger.error(f"❌ КРИТИЧНА ПОМИЛКА: Є {len(app.photo_file_ids)} photo_file_ids, але медіа не були відправлені інженеру!")
            await query.answer("❌ Помилка: файли не були відправлені інженеру. Спробуйте підтвердити ще раз.")
            return QL_CONFIRMING
        
        # Формуємо повідомлення для клієнта
        client_message = f"📋 <b>Нова заявка: 🖨 Якість друку</b>\n\n"
        client_message += f"👤 <b>Клієнт:</b> {app.full_name}\n"
        client_message += f"📱 <b>Телефон:</b> {app.phone_number}\n"
        
        if app.problem_description:
            client_message += f"\n📝 <b>Додаткові деталі та коментарі:</b>\n{app.problem_description}\n"
        
        media_count = len(app.media_messages) if app.media_messages else len(app.photo_file_ids)
        if media_count:
            client_message += f"\n📷 <b>Фото/відео:</b> {media_count} файлів\n"
        
        client_message += f"\n🕐 <b>Час створення:</b> {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        client_message += (
            "\n\n"
            "✅ <b>Заявка успішно відправлена!</b>\n\n"
            "Наш спеціаліст надасть вам відповідь протягом до 2 робочих днів.\n\n"
            "Дякуємо за звернення! 🙏"
        )
        
        # Підтверджуємо користувачу
        await query.answer("✅ Заявка успішно відправлена!")
        await query.edit_message_text(
            client_message,
            parse_mode='HTML'
        )
        
        # ВАЖЛИВО: Показуємо клієнту його файли, щоб він бачив, що вони прикріплені
        user_chat_id = query.message.chat.id
        client_media_to_show = app.media_messages if app.media_messages else []
        
        # Якщо media_messages порожній, але є photo_file_ids, відправляємо через send_media_group
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
                    caption = client_message
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
            QL_WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quality_email)],
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
