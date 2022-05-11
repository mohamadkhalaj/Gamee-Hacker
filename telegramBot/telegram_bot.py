import functools
import logging
import random
import re
import sys
from collections import deque

from babel.support import Translations
from decouple import config as env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from models import Game, User, app, db

try:
    from ..gameeHacker.core import GameeHacker
except ImportError:
    sys.path.insert(0, "../gameeHacker/")
    from core import GameeHacker

TELEGRAM_TOKEN = env("TELEGRAM_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def divide_chunks(keyboard, n):
    for i in range(0, len(keyboard), n):
        yield keyboard[i : i + n]


def is_url(str):
    regex = (
        "((http|https)://)(www.)?"
        + "[a-zA-Z0-9@:%._\\+~#?&//=]"
        + "{2,256}\\.[a-z]"
        + "{2,6}\\b([-a-zA-Z0-9@:%"
        + "._\\+~#?&//=]*)"
    )
    p = re.compile(regex)
    if re.search(p, str):
        return True
    else:
        return False


def is_score(str):
    str = str.strip()
    regex = "^[0-9]+$"
    p = re.compile(regex)
    if re.search(p, str):
        return True
    else:
        return False


def user_preferences(func):
    @functools.wraps(func)
    def wrapper_user_preferences(*args, **kwargs):
        chat_id = int(args[0]["message"]["chat"]["id"])
        username = args[0]["message"]["chat"]["username"]
        message = args[0]["message"]["text"]
        language = get_user_language(chat_id)
        user_pref = {
            "lang": language,
            "chat_id": chat_id,
            "username": username,
            "message": message,
        }
        args = list(args)
        args.append(user_pref)
        args = tuple(args)
        value = func(*args, **kwargs)
        return value

    return wrapper_user_preferences


def admin_required(func):
    @functools.wraps(func)
    def wrapper_admin_required(*args, **kwargs):
        chat_id = args[0]["message"]["chat"]["id"]
        user = get_user(chat_id)
        if user.is_admin:
            value = func(*args, **kwargs)
            return value
        else:
            language = get_user_language(chat_id)
            _ = Translations.load("locales", [language]).gettext
            args[0].message.reply_text(_("Access forbidden."))

    return wrapper_admin_required


@admin_required
@user_preferences
def admin_panel(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    update.message.reply_text(_("Under construction."))


@user_preferences
def settings(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    keyboard = [[_("Change language") + " 🗣"], [_("Contribute" + " 🤝")], [_("Return") + " ↩️"]]
    message = _("Please select one item:")
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


@user_preferences
def add_game(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    message = _("Please send game URL:")
    update.message.reply_text(message)


@user_preferences
def get_game_url(update: Update, context: CallbackContext, user_pref=None) -> None:
    with app.app_context():
        user = get_user(user_pref["chat_id"])
        user.last_url = user_pref["message"]
        db.session.add(user)
        db.session.commit()
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    message = _("Please send your score:")
    update.message.reply_text(message)


@user_preferences
def start_hacking(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    score = int(user_pref["message"].strip())
    chat_id = user_pref["chat_id"]
    url = get_user_last_url(chat_id)
    if url:
        logger.info(
            f"START HACKING: user: {user_pref['chat_id']} username:{user_pref['username']}"
        )
        message = _("Please wait a moment...")
        update.message.reply_text(message)
        game_obj = GameeHacker(url, score, random.randint(10, 1000))
        game_obj.send_score()
        image = game_obj.get_game_img()
        name = game_obj.get_game_name()
        rank = game_obj.get_user_rank()
        record = game_obj.get_user_record()
        if game_obj.check_ban_status():
            message = _("You are banned!") + " 🗿"
            update.message.reply_text(message)
        else:
            with app.app_context():
                new_game = create_new_game(url, chat_id, image, name, rank, record)
                send_user_game_info(update, context, user_pref, new_game)
        games(update, context)
    else:
        message = _("Please send game URL:")
        update.message.reply_text(message)


def get_bot_username(context):
    data = context.bot.get_me()
    return data["username"]


def add_footer(context, message):
    username = f"@{get_bot_username(context)}"
    message += "\n\n"
    message += username
    return message


def send_user_game_info(update, context, user_pref, game_object):
    logger.info(
        f"SEND USER GAME INFO: user: {user_pref['chat_id']} username:{user_pref['username']}"
    )
    name = game_object.title
    record = game_object.score
    rank = game_object.rank
    image = game_object.photo_url
    message = user_game_status(user_pref["lang"], name, rank, record)
    new_message = add_footer(context, message)
    context.bot.send_photo(
        photo=image, caption=new_message, parse_mode="html", chat_id=update.message.chat_id
    )


def user_game_status(lang, name, rank, record):
    _ = Translations.load("locales", [lang]).gettext
    game_name = "🎳 " + _("Game name: ")
    user_rank = get_rank_emoji(rank) + _("Your rank: ")
    user_record = "🏆 " + _("Your record: ")
    message = f"{game_name}{name}\n{user_record}{record}\n{user_rank}{rank}"
    return message


def get_rank_emoji(rank):
    emojies = "🥇🥈🥉🎗"
    if rank in range(1, 4):
        return f"{emojies[rank-1]} "
    return f"{emojies[3]} "


def create_new_game(url, chat_id, image, name, rank, record):
    logger.info(f"NEW GAME CREATED: {chat_id}")
    new_game = Game(user_id=chat_id, title=name, url=url, photo_url=image, score=record, rank=rank)
    db.session.add(new_game)
    db.session.commit()
    return new_game


def get_all_user_games(chat_id):
    games = Game.query.filter_by(user_id=chat_id).all()
    return games


def get_user_last_url(chat_id):
    user = get_user(chat_id)
    url = user.last_url
    return url


@user_preferences
def set_en(update: Update, context: CallbackContext, user_pref=None) -> None:
    chat_id = user_pref["chat_id"]
    lang = "en_US"
    _ = Translations.load("locales", [lang]).gettext
    change_user_language(chat_id, lang)
    message = _("Language changed to english.")
    keyboard = [[_("فارسی") + " 🇮🇷", _("English") + " 🇺🇸"], [_("Return") + " ↩️"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


@user_preferences
def set_fa(update: Update, context: CallbackContext, user_pref=None) -> None:
    chat_id = user_pref["chat_id"]
    lang = "fa_IR"
    _ = Translations.load("locales", [lang]).gettext
    change_user_language(chat_id, lang)
    message = _("Language changed to persian.")
    keyboard = [[_("فارسی") + " 🇮🇷", _("English") + " 🇺🇸"], [_("Return") + " ↩️"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


def change_user_language(chat_id, lang):
    user = get_user(chat_id)
    user.language = lang
    db.session.add(user)
    db.session.commit()


@user_preferences
def games(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", user_pref["lang"]).gettext
    user_games = get_all_user_games(user_pref["chat_id"])
    user_game_keyboard = user_games_keyboard(user_games)
    chunked_keys = list(divide_chunks(user_game_keyboard, 4))
    keyboard = deque()
    keyboard.extend(chunked_keys)
    keyboard.extend([[_("New game") + " ➕", _("Remove game") + " ❌"], [_("Return") + " ↩️"]])
    keyboard = list(keyboard)
    message = _("Please select your game:")
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


def user_games_keyboard(games):
    key = []
    for game in games:
        key.append(game.title)
    return list(set(key))


@user_preferences
def view_game(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", user_pref["lang"]).gettext
    game_object = Game.query.filter_by(
        user_id=user_pref["chat_id"], title=user_pref["message"]
    ).all()[-1]
    send_user_game_info(update, context, user_pref, game_object)
    set_user_last_url(user_pref, game_object)


def set_user_last_url(user_pref, game_object):
    logger.info(
        f"SET USER LAST URL: user: {user_pref['chat_id']} username:{user_pref['username']}"
    )
    with app.app_context():
        new_user = User.query.filter_by(id=user_pref["chat_id"]).first()
        new_user.last_url = game_object.url
        db.session.add(new_user)
        db.session.commit()


@user_preferences
def change_language(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", user_pref["lang"]).gettext
    keyboard = [[_("فارسی") + " 🇮🇷", _("English") + " 🇺🇸"], [_("Return") + " ↩️"]]
    message = _("Please select your language:")
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


@user_preferences
def main_menu(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", user_pref["lang"]).gettext
    keyboard = [[_("Settings") + " ⚙️", _("Games") + " 🧩"]]
    if get_user(user_pref["chat_id"]).is_admin:
        keyboard.append([_("Admin panel") + " 👤"])
    message = _("Please select one item:")
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)


@user_preferences
def is_in_user_games(update: Update, context: CallbackContext, user_pref=None) -> None:
    chat_id = user_pref["chat_id"]
    message = user_pref["message"]
    all_games = get_all_user_games(chat_id)
    games_name = user_games_keyboard(all_games)
    if message in games_name:
        return True
    return False


@user_preferences
def contribute(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", user_pref["lang"]).gettext
    message = _("First if you enjoyed this bot please star 🌟 us on our github:")
    github_url = "<a href='https://github.com/mohamadkhalaj/Gamee-Hacker'>Link</a>"
    message += "\n\n" + github_url + "\n\n"
    message += _(
        "You can make a pull request and add your features or help for translating and add yout native language to this bot."
    )
    update.message.reply_text(message, parse_mode="html")


@user_preferences
def function_caller(update: Update, context: CallbackContext, user_pref=None) -> None:
    """Echo the user message."""
    _ = Translations.load("locales", user_pref["lang"]).gettext
    user = get_user(user_pref["chat_id"])
    not_in_stack = [set_fa, set_en, add_game]
    functions = {
        _("menu"): main_menu,
        _("Settings") + " ⚙️": settings,
        _("Change language") + " 🗣": change_language,
        _("Games") + " 🧩": games,
        _("فارسی") + " 🇮🇷": set_fa,
        _("English") + " 🇺🇸": set_en,
        _("New game") + " ➕": add_game,
        _("Admin panel") + " 👤": admin_panel,
        _("Contribute" + " 🤝"): contribute,
    }
    function = functions.get(update.message.text, None)
    with app.app_context():
        if function:
            logger.info(
                f"{function.__name__}: user: {user_pref['chat_id']} username:{user_pref['username']}"
            )
            if not function in user.return_stack and function not in not_in_stack:
                logger.info(
                    f"APPEND TO STACK: user: {user_pref['chat_id']} username:{user_pref['username']}"
                )
                stack = user.return_stack
                stack.append(function)
                db.session.add(user)
                db.session.commit()
            function(update, context)
        elif update.message.text == _("Return") + " ↩️":
            logger.info(f"RETURN: user: {user_pref['chat_id']} username:{user_pref['username']}")
            try:
                stack = user.return_stack
                stack.pop()
                stack.pop()(update, context)
                db.session.add(user)
                db.session.commit()
            except IndexError:
                main_menu(update, context)
        elif is_url(update.message.text):
            logger.info(f"GAME URL: user: {user_pref['chat_id']} username:{user_pref['username']}")
            get_game_url(update, context)
        elif is_score(update.message.text):
            logger.info(
                f"GAME SCORE: user: {user_pref['chat_id']} username:{user_pref['username']}"
            )
            start_hacking(update, context)
        elif is_in_user_games(update, context):
            logger.info(
                f"VIEW GAME: user: {user_pref['chat_id']} username:{user_pref['username']}"
            )
            view_game(update, context)
        else:
            logger.info(
                f"COMMAND NOT FOUND: user: {user_pref['chat_id']} username:{user_pref['username']}"
            )
            message = f"❌❗️ '{update.message.text}'"
            update.message.reply_text(message)


def get_user_language(chat_id):
    with app.app_context():
        language = User.query.filter_by(id=chat_id).first()
        if language:
            return language.language
        return "en_US"


def get_user(chat_id):
    with app.app_context():
        user = User.query.filter_by(id=chat_id).first()
        return user


def create_user(user_pref):
    username = user_pref["username"]
    chat_id = user_pref["chat_id"]
    lang = user_pref["lang"]
    with app.app_context():
        user = User.query.filter_by(id=chat_id).first()
        if not user:
            new_user = User(id=chat_id, username=username, return_stack=[main_menu], language=lang)
            db.session.add(new_user)
            db.session.commit()
            logger.info(
                f"ADDING USER TO DB: user: {user_pref['chat_id']} username:{user_pref['username']} added."
            )
        else:
            logger.info(
                f"ADDING USER TO DB: user: {user_pref['chat_id']} username:{user_pref['username']} already exists."
            )


# Define a few command handlers. These usually take the two arguments update and
# context.
@user_preferences
def start(update: Update, context: CallbackContext, user_pref=None) -> None:
    """Send a message when the command /start is issued."""
    logger.info(f"Bot started by user: {user_pref['chat_id']} username:{user_pref['username']}")
    create_user(user_pref)
    main_menu(update, context)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, function_caller))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def create_super_user():
    user_id = int(input("Enter telegram numeric ID: "))
    with app.app_context():
        user = User.query.filter_by(id=user_id).first()
        if user:
            if user.is_admin:
                print("This user already is admin.")
            else:
                user.is_admin = True
                db.session.add(user)
                db.session.commit()
                print(f'User "{user_id}" previllage escalated successfully.')
        else:
            new_user = User(id=user_id)
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            print(f"Superuser created successfully.")
    exit(0)
    return None


if len(sys.argv) == 2 and sys.argv[1] == "createsuperuser":
    create_super_user()

if __name__ == "__main__":
    main()
