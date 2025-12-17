"""
Універсальний компонент для завантаження фото та відео
Використовується в розділах "🔧 Поломка" та "🖨 Якість друку"
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..models.application import Application
from ..services.context import get_media_storage
from ..keyboards.inline import get_skip_keyboard

logger = logging.getLogger(__name__)


class UniversalPhotoUpload:
    """
    Універсальний компонент для обробки завантаження фото та відео
    """
    
    MAX_FILES = 10
    
    @staticmethod
    async def process(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        application: Application,
        skip_message: str = None,
        max_files: int = None
    ) -> tuple[bool, str, bool]:
        """
        Обробляє завантаження фото або відео (включаючи медиа-групи)
        
        Args:
            update: Update об'єкт
            context: Context об'єкт
            application: Application об'єкт для збереження даних
            skip_message: Повідомлення при досягненні максимуму файлів
            max_files: Максимальна кількість файлів (за замовчуванням 10)
        
        Returns:
            tuple: (success, response_message, is_max_reached)
        """
        max_files = max_files or UniversalPhotoUpload.MAX_FILES
        media_storage = get_media_storage()
        
        # Перевіряємо, чи досягнуто максимум
        if len(application.photo_file_ids) >= max_files:
            message = skip_message or f"✅ Досягнуто максимум файлів ({max_files}). Переходимо далі."
            return True, message, True
        
        try:
            # Перевіряємо, чи це медиа-група (кілька файлів відправлено одночасно)
            media_group_id = update.message.media_group_id if update.message else None
            
            if media_group_id:
                # Це медиа-група - обробляємо всі файли з групи
                return await UniversalPhotoUpload._process_media_group(
                    update, context, application, media_storage, max_files
                )
            else:
                # Одиночний файл - обробляємо як раніше
                return await UniversalPhotoUpload._process_single_file(
                    update, context, application, media_storage, max_files
                )
            
        except Exception as e:
            logger.error(f"Помилка при обробці файлу: {e}", exc_info=True)
            return False, "❌ Помилка при збереженні файлу. Спробуйте ще раз або пропустіть цей крок.", False
    
    @staticmethod
    async def _process_single_file(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        application: Application,
        media_storage,
        max_files: int
    ) -> tuple[bool, str, bool]:
        """Обробляє одиночний файл"""
        file_id = None
        file_type = None
        
        # Обробляємо фото
        if update.message.photo:
            photo = update.message.photo[-1]  # Беремо найбільше фото
            file_id = photo.file_id
            file_type = 'photo'
        
        # Обробляємо відео
        elif update.message.video:
            video = update.message.video
            file_id = video.file_id
            file_type = 'video'
        
        else:
            return False, "❌ Будь ласка, надішліть фото або відео, або натисніть 'Пропустити':", False

        # Зберігаємо посилання на оригінальне повідомлення користувача для надійної доставки інженеру (copy_message)
        try:
            if update.effective_chat and update.message:
                chat_id = int(update.effective_chat.id)
                message_id = int(update.message.message_id)
                ref = {"chat_id": chat_id, "message_id": message_id}
                # Перевіряємо, чи це повідомлення вже збережено (по message_id)
                existing_ids = {m.get("message_id") for m in application.media_messages}
                if message_id not in existing_ids and len(application.photo_file_ids) < max_files:
                    application.media_messages.append(ref)
                    logger.info(f"Збережено media_message: chat_id={chat_id}, message_id={message_id}, всього: {len(application.media_messages)}")
        except Exception as e:
            # Не ламаємо flow, якщо не змогли зберегти референс, але логуємо помилку
            logger.warning(f"Не вдалося зберегти media_message: {e}", exc_info=True)
        
        # Зберігаємо file_id та тип файлу
        application.photo_file_ids.append(file_id)
        application.photo_file_types.append(file_type)
        # Використовуємо file_id замість збереження на сервер (файли будуть відправлені через Telegram API)
        application.photos.append(file_id)
        
        # Формуємо повідомлення
        file_type_text = "Фото" if file_type == 'photo' else "Відео"
        files_count = len(application.photo_file_ids)
        if files_count >= max_files:
            response_message = f"✅ Досягнуто максимум файлів ({max_files}). Переходимо далі."
        else:
            response_message = (
                f"✅ {file_type_text} додано ({files_count}/{max_files}). "
                f"Можете додати ще файли або натисніть 'Далі'"
            )
        
        return True, response_message, len(application.photo_file_ids) >= max_files
    
    @staticmethod
    async def _process_media_group(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        application: Application,
        media_storage,
        max_files: int
    ) -> tuple[bool, str, bool]:
        """Обробляє медиа-групу (кілька файлів відправлено одночасно)"""
        media_group_id = update.message.media_group_id
        user_id = application.user_id
        
        # Ініціалізуємо структури для зберігання інформації про медіа-групи
        if 'media_groups' not in context.user_data:
            context.user_data['media_groups'] = {}  # {media_group_id: [file_ids]}
        
        # Структура для відстеження реально доданих файлів з кожної групи
        if 'media_groups_added' not in context.user_data:
            context.user_data['media_groups_added'] = {}  # {media_group_id: count}
        
        if media_group_id not in context.user_data['media_groups']:
            context.user_data['media_groups'][media_group_id] = []
            context.user_data['media_groups_added'][media_group_id] = 0
        
        # Обробляємо поточний файл
        file_id = None
        file_type = None
        message_id = update.message.message_id
        
        if update.message.photo:
            photo = update.message.photo[-1]  # Беремо найбільше фото
            file_id = photo.file_id
            file_type = 'photo'
        elif update.message.video:
            video = update.message.video
            file_id = video.file_id
            file_type = 'video'
        else:
            return False, "❌ Невідомий тип файлу в медіа-групі", False

        # Ініціалізуємо структури для відстеження message_id медіа-групи (для copy_message)
        if 'media_group_message_ids' not in context.user_data:
            context.user_data['media_group_message_ids'] = {}  # {media_group_id: [message_id]}
        if media_group_id not in context.user_data['media_group_message_ids']:
            context.user_data['media_group_message_ids'][media_group_id] = []
        if message_id not in context.user_data['media_group_message_ids'][media_group_id]:
            context.user_data['media_group_message_ids'][media_group_id].append(message_id)
        
        # Перевіряємо, чи цей файл вже оброблено
        if file_id in context.user_data['media_groups'][media_group_id]:
            logger.info(f"Файл {file_id} з групи {media_group_id} вже оброблено, пропускаємо")
            return True, "", False  # Повертаємо порожнє повідомлення, щоб не дублювати відповідь
        
        # Додаємо file_id до списку оброблених для цієї групи
        context.user_data['media_groups'][media_group_id].append(file_id)
        
        # Зберігаємо файл, якщо не досягли максимуму
        file_was_added = False
        if len(application.photo_file_ids) < max_files:
            # Зберігаємо посилання на оригінальне повідомлення користувача для надійної доставки інженеру (copy_message)
            try:
                if update.effective_chat and update.message:
                    chat_id = int(update.effective_chat.id)
                    msg_id = int(update.message.message_id)
                    ref = {"chat_id": chat_id, "message_id": msg_id}
                    # Перевіряємо, чи це повідомлення вже збережено (по message_id)
                    existing_ids = {m.get("message_id") for m in application.media_messages}
                    if msg_id not in existing_ids:
                        application.media_messages.append(ref)
                        logger.info(f"Збережено media_message з медіа-групи: chat_id={chat_id}, message_id={msg_id}, всього: {len(application.media_messages)}")
            except Exception as e:
                logger.warning(f"Не вдалося зберегти media_message з медіа-групи: {e}", exc_info=True)

            application.photo_file_ids.append(file_id)
            application.photo_file_types.append(file_type)
            file_was_added = True
            # Використовуємо file_id замість збереження на сервер (файли будуть відправлені через Telegram API)
            application.photos.append(file_id)
            
            # Відстежуємо кількість реально доданих файлів з цієї групи
            context.user_data['media_groups_added'][media_group_id] = context.user_data['media_groups_added'].get(media_group_id, 0) + 1
        
        # Ініціалізуємо структуру для відстеження відправлених повідомлень для медіа-груп
        if 'media_group_responses' not in context.user_data:
            context.user_data['media_group_responses'] = {}  # {media_group_id: bool}
        
        # Чекаємо трохи, щоб отримати всі повідомлення з групи
        # Telegram відправляє їх майже одночасно, але з невеликою затримкою
        import asyncio
        await asyncio.sleep(2.0)  # Чекаємо 2 секунди для отримання всіх повідомлень з групи
        
        # Перевіряємо, чи вже було відправлено повідомлення для цієї групи
        if context.user_data['media_group_responses'].get(media_group_id, False):
            logger.info(f"Повідомлення для групи {media_group_id} вже відправлено, пропускаємо")
            return True, "", False  # Повертаємо порожнє повідомлення, щоб не дублювати відповідь
        
        # Перевіряємо, чи це останній файл у групі (чекаємо ще трохи)
        files_in_group_before = len(context.user_data['media_groups'][media_group_id])
        await asyncio.sleep(1.0)  # Додаткова затримка для перевірки
        files_in_group_after = len(context.user_data['media_groups'][media_group_id])
        
        # Якщо кількість файлів не змінилась після затримки, значить це останній файл
        # НЕ відправляємо повідомлення після першого файлу - чекаємо всіх
        is_last_in_group = (files_in_group_before == files_in_group_after) and (files_in_group_before > 1)
        
        # Якщо це перший файл у групі, чекаємо ще трохи
        if files_in_group_before == 1:
            await asyncio.sleep(1.0)  # Додаткова затримка для першого файлу
            files_in_group_after = len(context.user_data['media_groups'][media_group_id])
            is_last_in_group = (files_in_group_before == files_in_group_after)
        
        # Відправляємо повідомлення тільки для останнього файлу в групі
        if not is_last_in_group:
            logger.info(f"Файл {file_id} не останній у групі {media_group_id} (було: {files_in_group_before}, стало: {files_in_group_after}), не відправляємо повідомлення")
            return True, "", False  # Повертаємо порожнє повідомлення, щоб не дублювати відповідь
        
        # Позначаємо, що повідомлення для цієї групи вже відправлено
        context.user_data['media_group_responses'][media_group_id] = True
        
        # Після затримки формуємо повідомлення з актуальною кількістю файлів
        files_count = len(application.photo_file_ids)
        # Перераховуємо скільки файлів з цієї групи реально додано до application
        # (після затримки всі файли з групи вже оброблені)
        files_in_group = context.user_data['media_groups'][media_group_id]
        files_added_from_group = len([fid for fid in files_in_group if fid in application.photo_file_ids])
        
        # Якщо не знайшли жодного файлу (малоймовірно, але на всяк випадок)
        if files_added_from_group == 0:
            files_added_from_group = context.user_data['media_groups_added'].get(media_group_id, 0)
        
        if files_count >= max_files:
            # Якщо досягнуто максимум, використовуємо правильне повідомлення
            response_message = f"✅ Досягнуто максимум файлів ({max_files}). Переходимо далі."
        else:
            # Якщо не досягнуто максимум, показуємо скільки додано з цієї групи
            if files_added_from_group > 0:
                response_message = (
                    f"✅ Додано {files_added_from_group} файлів ({files_count}/{max_files}). "
                    f"Можете додати ще файли або натисніть 'Далі'"
                )
            else:
                # Якщо файли не були додані (наприклад, досягнуто максимум раніше)
                response_message = (
                    f"✅ Досягнуто максимум файлів ({max_files}). Переходимо далі."
                )
        
        return True, response_message, len(application.photo_file_ids) >= max_files

