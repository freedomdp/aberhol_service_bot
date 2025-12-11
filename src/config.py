import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('config')

class Config:
    """Конфигурация бота"""
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    ENGINEER_TELEGRAM_ID = int(os.getenv('ENGINEER_TELEGRAM_ID'))

config = Config()

