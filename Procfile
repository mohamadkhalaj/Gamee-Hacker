release: export FLASK_APP='models.py' && cd telegramBot && flask db init && flask db migrate && flask db upgrade
worker: cd telegramBot && python3 telegram_bot.py