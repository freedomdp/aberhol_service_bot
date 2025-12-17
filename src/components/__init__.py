"""
Універсальні компоненти для обробки введення даних
Використовуються в різних розділах бота
"""
from .universal_name_input import UniversalNameInput
from .universal_phone_input import UniversalPhoneInput
from .universal_photo_upload import UniversalPhotoUpload
from .universal_email_input import UniversalEmailInput
from .universal_text_input import UniversalTextInput

__all__ = [
    'UniversalNameInput',
    'UniversalPhoneInput',
    'UniversalEmailInput',
    'UniversalPhotoUpload',
    'UniversalTextInput',
]

