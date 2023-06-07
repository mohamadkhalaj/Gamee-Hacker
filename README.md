# Gamee-Hacker
The most advanced telegram games named Gamee, hacker on the Github.

[Click for donate ❤️](https://t.me/Gamee_donation)

# This script works in two different ways:
## 1 CLI (on your PC):
First you should change directory to `GameeHacker`

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
### Installation (Optional)
For installing this script and run from anywhere of your terminal, please follow below steps:
```
chmod +x install.sh
sudo ./install.sh
```

# 2 Telegram bot

### Step 1
First you should get Telegram API token from botFather.

### Step 2
```
cd telegramBot
mv .env-sample .env
```
### Step 3
After running above commands you should copy your Telegram token in `.env` file and put it in `TELEGRAM_TOKEN`.
after that create a desired random string for `SECRET_KEY`.

### Step 4
Create a virtual-environment and install dependencies.
```
pip install -r requirements.txt
```

### Step 5
```
export FLASK_APP='models.py'
cd telegramBot
flask db init && flask db migrate && flask db upgrade
python3 telegram_bot.py
```

## Create superuser
Run below command and enter your telegram numeric id
```
python3 telegram_bot.py createsuperuser
```
superuser can see some statistics such number of users and Games.


# Screenshots of the telegram bot
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/767d76df-aae3-447f-ba6e-aca88ec5c193">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/268e27b6-66d1-45a3-98d1-536728eeeb81">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/ff3fd834-531a-43b2-af8f-b42a64fd83b6">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/991fa5a5-0a64-4278-9d32-c0bdf832dbd1">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/8c9caa5e-5b75-4620-8271-01e535065308">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/fba8e4c5-e15f-46a7-9289-2439723443f2">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/98ad65ec-8962-4e9c-8684-28d14850b039">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/2cfb7e7e-d4b7-453f-923f-85a3c246383f">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/50a30d33-4dbb-4bd0-85ec-72f94721002f">
<img width="492" alt="image" src="https://github.com/mohamadkhalaj/Gamee-Hacker/assets/62938359/2fbec2c6-4c19-4b0d-8907-d6fc8a04cbf9">
