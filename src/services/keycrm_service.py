"""
Сервис для отправки заявок в KeyCRM через API
"""
import os
import logging
import httpx
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class KeyCRMService:
    """Класс для отправки заявок в KeyCRM через API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        pipeline_id: Optional[int] = None,
        source_id: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        """
        Инициализация KeyCRM сервиса
        
        Args:
            api_key: API ключ KeyCRM
            pipeline_id: ID воронки (если None, будет использована первая воронка)
            source_id: ID источника (если None, будет использован источник по умолчанию)
            enabled: Включен ли сервис (если None, берется из KEYCRM_ENABLED, по умолчанию True)
        """
        # Проверяем флаг включения/отключения
        if enabled is None:
            enabled_str = os.getenv('KEYCRM_ENABLED', 'true').lower()
            self.enabled = enabled_str in ('true', '1', 'yes', 'on')
        else:
            self.enabled = enabled
        
        if not self.enabled:
            logger.info("KeyCRMService отключен (KEYCRM_ENABLED=false). Интеграция с KeyCRM не будет выполняться.")
            self.api_key = None
            self.pipeline_id = None
            self.source_id = None
            self.base_url = "https://openapi.keycrm.app/v1"
            return
        
        self.api_key = api_key or os.getenv('KEYCRM_API_KEY', 'YWNkZTg1ZWNiOGUzZmQwOTk0MzI5ZmFmNjdhNzgwNWU5NzcwMDU4OQ')
        self.pipeline_id = pipeline_id or os.getenv('KEYCRM_PIPELINE_ID')
        if self.pipeline_id:
            try:
                self.pipeline_id = int(self.pipeline_id)
            except (ValueError, TypeError):
                self.pipeline_id = None
        
        self.source_id = source_id or os.getenv('KEYCRM_SOURCE_ID')
        if self.source_id:
            try:
                self.source_id = int(self.source_id)
            except (ValueError, TypeError):
                self.source_id = None
        
        self.base_url = "https://openapi.keycrm.app/v1"
        
        if not self.api_key:
            logger.warning("KEYCRM_API_KEY не установлен. KeyCRMService будет отключен.")
        else:
            logger.info(f"KeyCRMService инициализирован: pipeline_id={self.pipeline_id}, source_id={self.source_id}")
            # Если pipeline_id не указан, попробуем найти воронку "Сервісний центр" при первом использовании
            if not self.pipeline_id:
                logger.info("Pipeline ID не указан, будет выполнен поиск воронки 'Сервісний центр' при создании карточки")
    
    def _get_headers(self) -> Dict[str, str]:
        """Возвращает заголовки для API запросов"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_pipelines(self) -> Optional[List[Dict]]:
        """
        Получает список воронок для поиска ID воронки "Сервісний центр"
        
        Returns:
            Список воронок или None при ошибке
        """
        if not self.enabled:
            logger.debug("KeyCRMService отключен, пропускаем получение списка воронок")
            return None
        
        if not self.api_key:
            logger.warning("KEYCRM_API_KEY не установлен, невозможно получить список воронок")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Пробуем разные возможные endpoints для получения воронок
                endpoints = [
                    f"{self.base_url}/pipelines",
                    f"{self.base_url}/funnels",
                    f"{self.base_url}/pipeline"
                ]
                
                for endpoint in endpoints:
                    try:
                        response = await client.get(
                            endpoint,
                            headers=self._get_headers()
                        )
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                # Может быть data или сразу список
                                pipelines = data.get('data', []) if isinstance(data, dict) else data
                                if isinstance(pipelines, list) and len(pipelines) > 0:
                                    logger.info(f"Получено {len(pipelines)} воронок из KeyCRM через {endpoint}")
                                    return pipelines
                            except Exception as e:
                                logger.warning(f"Ошибка при парсинге ответа от {endpoint}: {e}")
                                continue
                        elif response.status_code == 401:
                            logger.error(f"Ошибка авторизации KeyCRM API (401). Проверьте KEYCRM_API_KEY")
                            return None
                        elif response.status_code == 404:
                            logger.debug(f"Endpoint {endpoint} не найден (404), пробуем следующий")
                            continue
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout при запросе к {endpoint}")
                        continue
                    except httpx.RequestError as e:
                        logger.warning(f"Ошибка сети при запросе к {endpoint}: {e}")
                        continue
                    except Exception as e:
                        logger.debug(f"Ошибка при получении воронок через {endpoint}: {e}")
                        continue
                
                logger.warning("Не удалось получить список воронок ни через один endpoint")
                return None
        except Exception as e:
            logger.error(f"Критическая ошибка при получении списка воронок: {e}", exc_info=True)
            return None
    
    async def find_pipeline_id(self, pipeline_name: str = "Сервісний центр") -> Optional[int]:
        """
        Находит ID воронки по названию
        
        Args:
            pipeline_name: Название воронки
            
        Returns:
            ID воронки или None
        """
        pipelines = await self.get_pipelines()
        if not pipelines:
            return None
        
        for pipeline in pipelines:
            if pipeline.get('name') == pipeline_name:
                pipeline_id = pipeline.get('id')
                logger.info(f"Найдена воронка '{pipeline_name}' с ID={pipeline_id}")
                return pipeline_id
        
        logger.warning(f"Воронка '{pipeline_name}' не найдена")
        return None
    
    def _format_manager_comment(self, application) -> str:
        """
        Формирует комментарий менеджера из данных заявки
        
        Args:
            application: Объект Application
            
        Returns:
            Текст комментария
        """
        comment = f"📋 Заявка з Telegram бота\n\n"
        
        if application.order_number:
            comment += f"🛒 Номер замовлення: {application.order_number}\n"
        
        if application.printer_model:
            comment += f"🖨️ Модель принтера: {application.printer_model}\n"
        
        if application.filament_type:
            comment += f"🧵 Тип філаменту: {application.filament_type}\n"
        
        if application.filament_manufacturer:
            comment += f"🏭 Виробник філаменту: {application.filament_manufacturer}\n"
        
        if application.problem_description:
            comment += f"\n📝 Опис проблеми:\n{application.problem_description}\n"
        
        media_count = len(application.media_messages) if application.media_messages else len(application.photo_file_ids)
        if media_count:
            comment += f"\n📷 Фото/відео: {media_count} файлів\n"
        
        if application.model_file or application.model_file_id:
            comment += f"\n📦 3D модель: Є\n"
        
        comment += f"\n🕐 Час створення: {application.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        return comment
    
    async def create_card(
        self,
        application,
        bot=None
    ) -> Optional[int]:
        """
        Создает карточку в воронке KeyCRM
        
        Args:
            application: Объект Application
            bot: Telegram Bot объект для скачивания файлов (опционально)
            
        Returns:
            ID созданной карточки или None при ошибке
        """
        if not self.enabled:
            logger.debug("KeyCRMService отключен, пропускаем создание карточки в KeyCRM")
            return None
        
        if not self.api_key:
            logger.error("KEYCRM_API_KEY не установлен. Заявка в KeyCRM не будет отправлена.")
            return None
        
        try:
            # Определяем pipeline_id
            pipeline_id = self.pipeline_id
            if not pipeline_id:
                try:
                    # Пытаемся найти воронку "Сервісний центр"
                    pipeline_id = await self.find_pipeline_id("Сервісний центр")
                    if not pipeline_id:
                        logger.warning("Не удалось найти воронку 'Сервісний центр', будет использована первая воронка")
                except Exception as e:
                    logger.warning(f"Ошибка при поиске воронки 'Сервісний центр': {e}. Будет использована первая воронка.")
                    pipeline_id = None
            
            # Формируем данные для создания карточки
            data = {
                "title": f"Заявка: {application.phone_number or 'Без телефону'}",
                "contact": {
                    "full_name": application.full_name or "Не вказано",
                }
            }
            
            # Добавляем email и телефон если есть
            if application.email:
                data["contact"]["email"] = application.email
            
            if application.phone_number:
                data["contact"]["phone"] = application.phone_number
            
            # Добавляем pipeline_id если найден
            if pipeline_id:
                data["pipeline_id"] = pipeline_id
            
            # Добавляем source_id если указан
            if self.source_id:
                data["source_id"] = self.source_id
            
            # Добавляем комментарий менеджера
            try:
                manager_comment = self._format_manager_comment(application)
                data["manager_comment"] = manager_comment
            except Exception as e:
                logger.warning(f"Ошибка при формировании комментария менеджера: {e}")
                data["manager_comment"] = "Заявка з Telegram бота"
            
            # Отправляем запрос в KeyCRM
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Создание карточки в KeyCRM: pipeline_id={pipeline_id}, contact={data['contact']}")
                
                response = await client.post(
                    f"{self.base_url}/pipelines/cards",
                    json=data,
                    headers=self._get_headers()
                )
                
                if response.status_code == 201:
                    try:
                        result = response.json()
                        card_id = result.get('data', {}).get('id')
                        if card_id:
                            logger.info(f"✅ Карточка создана в KeyCRM с ID={card_id}")
                            
                            # Отправляем файлы в чат карточки (если есть)
                            if bot and (application.photo_file_ids or application.model_file_id):
                                try:
                                    await self._send_files_to_card_chat(card_id, application, bot)
                                except Exception as e:
                                    logger.error(f"Ошибка при отправке файлов в карточку {card_id}: {e}", exc_info=True)
                                    # Продолжаем, даже если файлы не отправились
                            
                            return card_id
                        else:
                            logger.error(f"Карточка создана, но ID не получен. Ответ: {result}")
                            return None
                    except Exception as e:
                        logger.error(f"Ошибка при парсинге ответа от KeyCRM: {e}. Ответ: {response.text}")
                        return None
                else:
                    logger.error(f"❌ Ошибка создания карточки в KeyCRM: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout при создании карточки в KeyCRM: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"❌ Ошибка сети при создании карточки в KeyCRM: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при создании карточки в KeyCRM: {e}", exc_info=True)
            return None
    
    async def _send_files_to_card_chat(
        self,
        card_id: int,
        application,
        bot
    ) -> bool:
        """
        Отправляет файлы в чат карточки
        
        Args:
            card_id: ID карточки
            application: Объект Application
            bot: Telegram Bot объект
            
        Returns:
            True если успешно
        """
        files_sent = 0
        files_failed = 0
        
        try:
            # Отправляем фото и видео
            if application.photo_file_ids:
                for i, file_id in enumerate(application.photo_file_ids):
                    try:
                        file = await bot.get_file(file_id)
                        file_data = await file.download_as_bytearray()
                        
                        # Определяем тип файла
                        file_type = 'photo'
                        if i < len(application.photo_file_types):
                            file_type = application.photo_file_types[i]
                        
                        # Определяем расширение
                        extension = '.jpg' if file_type == 'photo' else '.mp4'
                        filename = f"{file_type}_{i+1}{extension}"
                        
                        # Отправляем файл в KeyCRM
                        if await self._upload_file_to_card(card_id, file_data, filename, file_type):
                            files_sent += 1
                            logger.info(f"Файл {filename} отправлен в карточку {card_id}")
                        else:
                            files_failed += 1
                            logger.warning(f"Не удалось отправить файл {filename} в карточку {card_id}")
                    except Exception as e:
                        files_failed += 1
                        logger.error(f"Ошибка при отправке файла {file_id}: {e}", exc_info=True)
            
            # Отправляем 3D модель
            if application.model_file_id:
                try:
                    file = await bot.get_file(application.model_file_id)
                    file_data = await file.download_as_bytearray()
                    if await self._upload_file_to_card(card_id, file_data, "3d_model.stl", "model"):
                        files_sent += 1
                        logger.info(f"3D модель отправлена в карточку {card_id}")
                    else:
                        files_failed += 1
                        logger.warning(f"Не удалось отправить 3D модель в карточку {card_id}")
                except Exception as e:
                    files_failed += 1
                    logger.error(f"Ошибка при отправке 3D модели: {e}", exc_info=True)
            
            if files_sent > 0:
                logger.info(f"Отправлено файлов в карточку {card_id}: успешно={files_sent}, ошибок={files_failed}")
            elif files_failed > 0:
                logger.warning(f"Не удалось отправить файлы в карточку {card_id}: ошибок={files_failed}")
            
            return files_sent > 0
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке файлов в чат карточки {card_id}: {e}", exc_info=True)
            return False
    
    async def _upload_file_to_card(
        self,
        card_id: int,
        file_data: bytes,
        filename: str,
        file_type: str
    ) -> bool:
        """
        Загружает файл в карточку
        
        Args:
            card_id: ID карточки
            file_data: Данные файла
            filename: Имя файла
            file_type: Тип файла ('photo', 'video', 'model')
            
        Returns:
            True если успешно
        """
        try:
            # KeyCRM API для загрузки файлов в карточку
            # Пробуем несколько возможных endpoints
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {
                    'file': (filename, file_data, self._get_content_type(file_type))
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                
                # Пробуем endpoint для файлов карточки
                endpoints = [
                    f"{self.base_url}/pipelines/cards/{card_id}/files",
                    f"{self.base_url}/cards/{card_id}/files",
                    f"{self.base_url}/files"
                ]
                
                for endpoint in endpoints:
                    try:
                        response = await client.post(
                            endpoint,
                            files=files,
                            headers=headers
                        )
                        
                        if response.status_code in (200, 201):
                            logger.info(f"Файл {filename} загружен в карточку {card_id} через {endpoint}")
                            return True
                        elif response.status_code == 404:
                            logger.debug(f"Endpoint {endpoint} не найден (404), пробуем следующий")
                            continue
                        elif response.status_code == 401:
                            logger.error(f"Ошибка авторизации при загрузке файла {filename} (401)")
                            return False
                        else:
                            logger.debug(f"Ошибка {response.status_code} при загрузке через {endpoint}: {response.text}")
                            continue
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout при загрузке файла через {endpoint}")
                        continue
                    except httpx.RequestError as e:
                        logger.debug(f"Ошибка сети при загрузке через {endpoint}: {e}")
                        continue
                    except Exception as e:
                        logger.debug(f"Ошибка при попытке загрузки через {endpoint}: {e}")
                        continue
                
                logger.warning(f"Не удалось загрузить файл {filename} ни через один endpoint. Файл будет указан в комментарии.")
                return False
                    
        except httpx.TimeoutException as e:
            logger.error(f"Timeout при загрузке файла {filename}: {e}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при загрузке файла {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке файла {filename}: {e}", exc_info=True)
            return False
    
    
    def _get_content_type(self, file_type: str) -> str:
        """Возвращает Content-Type для файла"""
        content_types = {
            'photo': 'image/jpeg',
            'video': 'video/mp4',
            'model': 'application/octet-stream'
        }
        return content_types.get(file_type, 'application/octet-stream')

