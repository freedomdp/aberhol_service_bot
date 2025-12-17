"""
Сервис для отправки заявок в CRM через email
"""
import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class EmailService:
    """Класс для отправки заявок в CRM через email"""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_use_tls: bool = True,
        recipient_emails: Optional[List[str]] = None
    ):
        """
        Инициализация email сервиса
        
        Args:
            smtp_host: SMTP сервер
            smtp_port: SMTP порт
            smtp_user: Логин для SMTP
            smtp_password: Пароль для SMTP
            smtp_use_tls: Использовать TLS (True) или SSL (False)
            recipient_emails: Список email адресов получателей
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'mail.adm.tools')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', 'support@bambulab.net.ua')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = smtp_use_tls
        recipient_emails_str = recipient_emails or os.getenv(
            'CRM_EMAIL_RECIPIENTS', 
            'support@bambulab.net.ua'
        )
        
        # Если это строка, разбиваем по запятой
        if isinstance(recipient_emails_str, str):
            self.recipient_emails = [email.strip() for email in recipient_emails_str.split(',')]
        else:
            self.recipient_emails = recipient_emails_str
        
        # Убираем пустые адреса
        self.recipient_emails = [email for email in self.recipient_emails if email]
        
        
        logger.info(f"EmailService инициализирован: SMTP={self.smtp_host}:{self.smtp_port}, отправитель={self.smtp_user}, получатели={self.recipient_emails}")
    
    def _format_email_body(self, application) -> str:
        """
        Формирует тело email по шаблону из формы
        
        Args:
            application: Объект Application
            
        Returns:
            Текст email body
        """
        # Форматируем по шаблону из формы Fluent Forms
        body = f"ІМ'Я ТА ПРІЗВИЩЕ: {application.full_name or 'Не вказано'}\n"
        body += f"НОМЕР ЗАМОВЛЕННЯ: {application.order_number or 'Не вказано'}\n"
        body += f"НОМЕР ТЕЛЕФОНУ: {application.phone_number or 'Не вказано'}\n"
        body += f"EMAIL: {application.email or 'Не вказано'}\n"
        body += f"МОДЕЛЬ ПРИНТЕРУ: {application.printer_model or 'Не вказано'}\n"
        
        if application.filament_type:
            body += f"ТИП ФІЛАМЕНТУ: {application.filament_type}\n"
        
        if application.filament_manufacturer:
            body += f"ВИРОБНИК ФІЛАМЕНТУ: {application.filament_manufacturer}\n"
        
        # Информация о файлах (сами файлы будут во вложениях)
        media_count = len(application.media_messages) if application.media_messages else len(application.photo_file_ids)
        if media_count:
            body += f"ФОТО ЯКІ ПОКАЗУЮТЬ ПРОБЛЕМУ: {media_count} файлів (в додатках)\n"
        
        if application.model_file or application.model_file_id:
            body += f"ВАША ЗД МОДЕЛЬ: Є (в додатках)\n"
        
        if application.problem_description:
            body += f"ОПИС ПРОБЛЕМИ ТА ДОДАТКОВА ІНФОРМАЦІЯ: {application.problem_description}\n"
        
        return body
    
    def _get_email_subject(self, application) -> str:
        """
        Формирует тему email
        
        Args:
            application: Объект Application
            
        Returns:
            Тема email
        """
        phone = application.phone_number or 'Не вказано'
        return f"Запит до СЦ - {phone}"
    
    async def _download_file_from_telegram(
        self,
        bot,
        file_id: str,
        file_type: str
    ) -> Optional[Tuple[bytes, str]]:
        """
        Скачивает файл из Telegram
        
        Args:
            bot: Telegram Bot объект
            file_id: ID файла в Telegram
            file_type: Тип файла ('photo', 'video', 'model')
            
        Returns:
            Tuple[данные_файла, расширение] или None при ошибке
        """
        try:
            file = await bot.get_file(file_id)
            file_data = await file.download_as_bytearray()
            
            # Определяем расширение по типу файла
            extension_map = {
                'photo': '.jpg',
                'video': '.mp4',
                'model': '.stl'
            }
            extension = extension_map.get(file_type, '.bin')
            
            return bytes(file_data), extension
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {file_id}: {e}")
            return None
    
    async def send_application_to_crm(
        self,
        application,
        bot,
        include_photos: bool = True,
        include_videos: bool = True,
        include_models: bool = True
    ) -> bool:
        """
        Отправляет заявку в CRM через email
        
        Args:
            application: Объект Application
            bot: Telegram Bot объект для скачивания файлов
            include_photos: Прикреплять фото
            include_videos: Прикреплять видео
            include_models: Прикреплять 3D модели
            
        Returns:
            True если успешно, False при ошибке
        """
        if not self.smtp_password:
            logger.error("SMTP пароль не установлен. Проверьте переменную окружения SMTP_PASSWORD.")
            return False
        
        try:
            # Создаем сообщение
            msg = MIMEMultipart()
            
            # Используем реальный email клиента как адрес отправителя (From)
            # Это позволяет CRM создавать новую карточку для каждого клиента
            sender_email = application.email
            if not sender_email:
                # Fallback: если email не указан, используем формат на основе телефона
                phone_clean = ''.join(filter(str.isdigit, application.phone_number or ''))
                if phone_clean:
                    sender_email = f"telegram_{phone_clean}@bambulab.net.ua"
                else:
                    sender_email = f"telegram_{application.user_id}@bambulab.net.ua"
                logger.warning(f"Email клиента не указан, используем fallback: {sender_email}")
            
            logger.info(f"Отправка email: From={sender_email}, To={self.recipient_emails}, Subject={self._get_email_subject(application)}")
            
            # Отправитель = email клиента (для CRM)
            # Получатель = адрес из CRM_EMAIL_RECIPIENTS
            msg['From'] = sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = self._get_email_subject(application)
            # Добавляем важные заголовки для доставки
            msg['X-Mailer'] = 'BambuLab Service Bot'
            
            # Добавляем тело письма
            body = self._format_email_body(application)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Скачиваем и прикрепляем файлы
            attachments_count = 0
            
            try:
                # Фото и видео
                if include_photos or include_videos:
                    for i, file_id in enumerate(application.photo_file_ids):
                        if i >= len(application.photo_file_types):
                            file_type = 'photo'  # По умолчанию
                        else:
                            file_type = application.photo_file_types[i]
                        
                        # Проверяем, нужно ли прикреплять этот тип
                        if (file_type == 'photo' and not include_photos) or \
                           (file_type == 'video' and not include_videos):
                            continue
                        
                        file_data, extension = await self._download_file_from_telegram(bot, file_id, file_type)
                        if file_data:
                            # Создаем вложение
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file_data)
                            encoders.encode_base64(part)
                            
                            filename = f"{file_type}_{i+1}{extension}"
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {filename}'
                            )
                            msg.attach(part)
                            attachments_count += 1
                            logger.info(f"Прикреплен файл: {filename}")
                
                # 3D модель
                if include_models and application.model_file_id:
                    file_data, extension = await self._download_file_from_telegram(bot, application.model_file_id, 'model')
                    if file_data:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= 3d_model{extension}'
                        )
                        msg.attach(part)
                        attachments_count += 1
                        logger.info("Прикреплена 3D модель")
            
            except Exception as e:
                logger.error(f"Ошибка при подготовке вложений: {e}", exc_info=True)
                # Продолжаем отправку даже если вложения не удалось прикрепить
            
            # Отправляем email
            try:
                if self.smtp_use_tls:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    server.starttls()
                    logger.info(f"Подключение к SMTP через TLS: {self.smtp_host}:{self.smtp_port}")
                else:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
                    logger.info(f"Подключение к SMTP через SSL: {self.smtp_host}:{self.smtp_port}")
                
                # Авторизуемся с реальным SMTP аккаунтом
                server.login(self.smtp_user, self.smtp_password)
                logger.info(f"SMTP авторизация успешна: {self.smtp_user}")
                
                text = msg.as_string()
                
                # Отправляем письмо с адресом клиента в From (для CRM)
                # SMTP авторизация с self.smtp_user, но в заголовке From указываем email клиента
                logger.info(f"Отправка письма через SMTP: From={sender_email}, To={self.recipient_emails}")
                logger.info(f"SMTP авторизация: {self.smtp_user}")
                
                # Пробуем отправить с адресом клиента в From
                # Если SMTP отклонит, попробуем с реальным адресом и добавим Reply-To
                try:
                    result = server.sendmail(sender_email, self.recipient_emails, text)
                    logger.info(f"Email отправлен с адреса клиента: {sender_email}")
                except smtplib.SMTPSenderRefused as e:
                    logger.warning(f"SMTP отклонил адрес отправителя {sender_email}: {e}")
                    logger.info(f"Пробуем отправить с реального адреса {self.smtp_user}, добавляем Reply-To={sender_email}")
                    # Если SMTP не позволяет отправлять с адреса клиента, используем реальный адрес
                    # но добавляем Reply-To с адресом клиента для CRM
                    msg['Reply-To'] = sender_email
                    msg['X-Original-From'] = sender_email
                    text = msg.as_string()
                    result = server.sendmail(self.smtp_user, self.recipient_emails, text)
                    logger.info(f"Email отправлен с реального адреса {self.smtp_user}, Reply-To={sender_email}")
                
                server.quit()
                
                if result:
                    # result - это словарь с ошибками для каждого получателя
                    logger.error(f"❌ SMTP вернул ошибки для получателей: {result}")
                    for recipient, error in result.items():
                        logger.error(f"  Получатель {recipient}: {error}")
                    return False
                else:
                    logger.info(f"✅ Email успешно отправлен в CRM для заявки пользователя {application.user_id}")
                    logger.info(f"   Отправитель (From): {sender_email}")
                    logger.info(f"   Получатели (To): {', '.join(self.recipient_emails)}")
                    logger.info(f"   Вложений: {attachments_count}")
                    logger.info(f"   Тема: {self._get_email_subject(application)}")
                    return True
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ SMTP отказал в приеме получателей: {e}")
                return False
            except smtplib.SMTPSenderRefused as e:
                logger.error(f"❌ SMTP отказал в приеме отправителя {self.smtp_user}: {e}")
                return False
            except smtplib.SMTPDataError as e:
                logger.error(f"❌ SMTP ошибка данных: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке email в CRM: {e}", exc_info=True)
            return False
