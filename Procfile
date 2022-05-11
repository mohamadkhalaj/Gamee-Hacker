release: export FLASK_APP='models.py' && cd telegramBot && flask db init && flask db migrate && flask db upgrade
worker: python3 telegramBot/telegram_bot.py