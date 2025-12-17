"""
Тестовый скрипт для проверки отправки email
Запуск: python test_email.py
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.email_service import EmailService
from src.models.application import Application
from telegram import Bot

# Загружаем переменные окружения
load_dotenv()

async def test_email():
    """Тестовая отправка email"""
    print("=" * 60)
    print("ТЕСТ ОТПРАВКИ EMAIL")
    print("=" * 60)
    
    # Создаем тестовую заявку
    test_application = Application(
        user_id=123456789,
        full_name="Тестовый Клиент",
        phone_number="+380991234567",
        email="test@example.com",
        order_number="TEST-001",
        printer_model="X1",
        problem_description="Тестовое описание проблемы"
    )
    
    # Инициализируем EmailService
    email_service = EmailService()
    
    print(f"\nSMTP настройки:")
    print(f"  Host: {email_service.smtp_host}")
    print(f"  Port: {email_service.smtp_port}")
    print(f"  User: {email_service.smtp_user}")
    print(f"  Получатели: {email_service.recipient_emails}")
    
    # Проверка на self-loop
    if email_service.smtp_user in email_service.recipient_emails:
        print(f"\n⚠️  ВНИМАНИЕ: Обнаружена отправка самому себе!")
        print(f"   Отправитель: {email_service.smtp_user}")
        print(f"   Получатель: {email_service.recipient_emails}")
        print(f"   Некоторые почтовые серверы блокируют self-loop.")
        print(f"   Рекомендуется использовать внешний адрес для теста.")
        
        # Предлагаем добавить тестовый адрес
        test_email = input("\nВведите тестовый email для проверки (или Enter для пропуска): ").strip()
        if test_email:
            print(f"\nДобавляем тестовый адрес: {test_email}")
            email_service.recipient_emails.append(test_email)
            print(f"Новый список получателей: {email_service.recipient_emails}")
    
    # Создаем временный bot (не используется для скачивания файлов в тесте)
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN не установлен")
        return
    
    bot = Bot(token=token)
    
    print(f"\nОтправка тестового письма...")
    print(f"  От: {email_service.smtp_user}")
    print(f"  Кому: {', '.join(email_service.recipient_emails)}")
    print(f"  Reply-To: {test_application.email}")
    
    try:
        result = await email_service.send_application_to_crm(
            test_application,
            bot,
            include_photos=False,
            include_videos=False,
            include_models=False
        )
        
        if result:
            print("\n✅ Письмо успешно отправлено!")
            print("\nПроверьте почтовый ящик support@bambulab.net.ua")
            print("Если письма нет:")
            print("  1. Проверьте папку 'Спам'")
            print("  2. Проверьте логи бота на наличие ошибок")
            print("  3. Проверьте настройки SMTP на хостинге")
        else:
            print("\n❌ Не удалось отправить письмо")
            print("Проверьте логи выше для деталей ошибки")
    except Exception as e:
        print(f"\n❌ Ошибка при отправке: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_email())
