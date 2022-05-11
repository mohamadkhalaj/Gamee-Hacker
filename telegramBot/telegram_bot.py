import functools
import logging
import random
import re
import sys

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


@user_preferences
def settings(update: Update, context: CallbackContext, user_pref=None) -> None:
    _ = Translations.load("locales", [user_pref["lang"]]).gettext
    keyboard = [[_("Change language") + " 🗣"], [_("Return") + " ↩️"]]
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
    else:
        message = _("Please send game URL:")
        update.message.reply_text(message)


def send_user_game_info(update, context, user_pref, game_object):
    name = game_object.title
    record = game_object.score
    rank = game_object.rank
    image = game_object.photo_url
    message = user_game_status(user_pref["lang"], name, rank, record)
    context.bot.send_photo(
        photo=image, caption=message, parse_mode="html", chat_id=update.message.chat_id
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
    user_game_leyboard = user_games_keyboard(user_games)
    keyboard = [user_game_leyboard, [_("New game") + " ➕", _("Return") + " ↩️"]]
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
    }
    function = functions.get(update.message.text, None)
    with app.app_context():
        if function:
            if not function in user.return_stack and function not in not_in_stack:
                stack = user.return_stack
                stack.append(function)
                db.session.add(user)
                db.session.commit()
            function(update, context)
        elif update.message.text == _("Return") + " ↩️":
            try:
                stack = user.return_stack
                stack.pop()
                stack.pop()(update, context)
                db.session.add(user)
                db.session.commit()
            except IndexError:
                main_menu(update, context)
        elif is_url(update.message.text):
            get_game_url(update, context)
        elif is_score(update.message.text):
            start_hacking(update, context)
        elif is_in_user_games(update, context):
            view_game(update, context)
        else:
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


# Define a few command handlers. These usually take the two arguments update and
# context.
@user_preferences
def start(update: Update, context: CallbackContext, user_pref=None) -> None:
    """Send a message when the command /start is issued."""
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


if __name__ == "__main__":
    main()