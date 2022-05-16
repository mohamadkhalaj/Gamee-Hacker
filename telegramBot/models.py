import os
from datetime import datetime

from decouple import config as env
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app = Flask(__name__)


database_path = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
database_path = database_path.replace("postgres", "postgresql")

app.config["SECRET_KEY"] = env("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = database_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

migrate = Migrate(app, db)
db.init_app(app)


class User(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(255), nullable=True, default=None)
    game = db.relationship("Game", backref="user", lazy=True)
    return_stack = db.Column(db.PickleType, nullable=False)
    last_url = db.Column(db.PickleType, nullable=True, default=None)
    language = db.Column(db.String(255))
    register_date = db.Column(db.DateTime, default=datetime.utcnow())


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255))
    photo_url = db.Column(db.String(255))
    score = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
