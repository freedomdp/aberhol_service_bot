"""
Сервис для сохранения и управления медиафайлами
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MediaStorage:
    """Класс для работы с медиафайлами"""
    
    def __init__(self, storage_path: Optional[str] = None, base_url: Optional[str] = None):
        """
        Инициализация хранилища медиафайлов
        
        Args:
            storage_path: Путь к директории для хранения файлов
            base_url: Базовый URL для доступа к файлам (например, http://your-server.com/media)
        """
        self.storage_path = Path(storage_path or os.getenv('MEDIA_STORAGE_PATH', './media'))
        self.base_url = base_url or os.getenv('BASE_URL', 'http://localhost:8000')
        
        # Создаем директории если их нет
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / 'photos').mkdir(exist_ok=True)
        (self.storage_path / 'videos').mkdir(exist_ok=True)
        (self.storage_path / 'models').mkdir(exist_ok=True)
        
        logger.info(f"MediaStorage инициализирован: {self.storage_path}")
    
    def save_file(self, file_data: bytes, file_type: str, user_id: int) -> Tuple[str, str]:
        """
        Сохраняет файл и возвращает путь и URL
        
        Args:
            file_data: Данные файла
            file_type: Тип файла ('photo', 'video', 'model')
            user_id: ID пользователя
            
        Returns:
            Tuple[путь_к_файлу, URL_для_доступа]
        """
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Определяем расширение и директорию
        if file_type == 'photo':
            ext = '.jpg'
            subdir = 'photos'
        elif file_type == 'video':
            ext = '.mp4'
            subdir = 'videos'
        elif file_type == 'model':
            ext = '.stl'  # или другое расширение
            subdir = 'models'
        else:
            ext = '.bin'
            subdir = 'photos'
        
        # Создаем директорию для пользователя
        user_dir = self.storage_path / subdir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл
        filename = f"{timestamp}_{file_id}{ext}"
        file_path = user_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Генерируем URL
        relative_path = f"{subdir}/{user_id}/{filename}"
        file_url = f"{self.base_url}/media/{relative_path}"
        
        logger.info(f"Файл сохранен: {file_path} -> {file_url}")
        
        return str(file_path), file_url
    
    def get_file_url(self, file_path: str) -> str:
        """
        Генерирует URL для существующего файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            URL для доступа к файлу
        """
        # Преобразуем абсолютный путь в относительный
        path = Path(file_path)
        try:
            relative_path = path.relative_to(self.storage_path)
            return f"{self.base_url}/media/{relative_path}"
        except ValueError:
            # Если путь не относительный, возвращаем как есть
            logger.warning(f"Не удалось создать относительный путь для {file_path}")
            return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        Удаляет файл
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл удален, False если ошибка
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Файл удален: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {file_path}: {e}")
            return False

