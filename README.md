# Service Bot

Telegram бот для сервісного центру Bambu Lab Україна.

## Функціонал

* Створення заявок на сервісне обслуговування
* Збір інформації про принтер та проблему
* Завантаження фото та відео (до 10 файлів, підтримка медіа-груп)
* Відправка заявок інженеру або в Telegram групу
* Три типи заявок:
  - 🔧 Поломка (з підтримкою номера замовлення)
  - 🖨 Якість друку
  - ❓ Питання / Відповідь (FAQ)

## Встановлення та запуск

1. Створіть віртуальне середовище:

```bash
python -m venv venv
```

2. Активуйте віртуальне середовище:
* Windows:
```bash
venv\Scripts\activate
```
* Linux/MacOS:
```bash
source venv/bin/activate
```

3. Встановіть залежності:

```bash
pip install -r requirements.txt
```

4. Створіть файл `.env` та заповніть необхідні змінні:

```
TELEGRAM_TOKEN=your_telegram_bot_token
ENGINEER_TELEGRAM_ID=your_engineer_telegram_id
GROUP_CHAT_ID=-1001234567890  # Опціонально: ID групи для отримання заявок (пріоритет над ENGINEER_TELEGRAM_ID)
MEDIA_STORAGE_PATH=./media
BASE_URL=http://localhost:8000
```

**Примітка:** Якщо встановлено `GROUP_CHAT_ID`, заявки будуть відправлятися в групу. Інакше - на `ENGINEER_TELEGRAM_ID`. Див. `GROUP_SETUP.md` для деталей налаштування групи.

5. Запустіть бота:

```bash
python src/main.py
```

## Структура проекту

```
aberhol_service_bot/
├── src/
│   ├── main.py              # Головний файл бота
│   ├── handlers/            # Обробники команд та повідомлень
│   ├── keyboards/           # Клавіатури для бота
│   ├── models/              # Моделі даних
│   └── utils/               # Допоміжні функції
├── requirements.txt
├── .env.example
└── README.md
```
