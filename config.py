import os


class Config(object):
    FLASK_APP = "server"
    DEBUG = False

    DATABASE_URL = os.environ.get("DATABASE_URL")

    SECRET_KEY = os.environ.get("SECRET_KEY")

    SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")


class Production(Config):
    FLASK_ENV = "production"


class Development(Config):
    FLASK_ENV = "development"
    DEBUG = True
