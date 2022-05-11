# Gamee-Hacker
The most advanced telegram games (gamee) hacker on github.

# Usage:
```
gameeHacker.py [--argument] [value]

Args                 Description                       Default
-h, --help           Throwback this help manaul        False
-u, --url            Url of your game in gamee         None
-t, --time           Play time                         Random
-s, --score   	     Your score                        None

--get-rank       Rank of you in current game           False
--get-record     Your record in current game           False
--get-summery    All of your data in gamee             False 
--get-name       Name of game                          False 

```

# Installation
For installing this script and run from anywhere of your terminal, please follow below steps:
```
chmod +x install.sh
sudo ./install.sh
```

# Run telegram bot
```
export FLASK_APP='models.py'
cd telegramBot
flask db init && flask db migrate && flask db upgrade
python3 telegram_bot.py
```
