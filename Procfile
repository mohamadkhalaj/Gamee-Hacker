release: export FLASK_APP='models.py' && flask db init && flask db migrate && flask db upgrade
worker: cd telegramBot && python3 telegram_bot.py