from flask import Flask, request
from flask_login import LoginManager

import views
from data import *
from database import Database
import json
from user import get_user

lm = LoginManager()


@lm.user_loader
def load_user(user_id):
    return get_user(user_id)


def create_app():
    app = Flask(__name__)
    app.config.from_envvar("SETTINGS")

    app.add_url_rule('/', endpoint='index', view_func=views.index)
    app.add_url_rule('/random', endpoint='random', view_func=views.rand_playlist)
    app.add_url_rule('/featured', endpoint='featured', view_func=views.featured)
    app.add_url_rule('/playlist/<key>', endpoint='playlist', view_func=views.playlist)
    app.add_url_rule('/add', endpoint='playlist_add', methods=['GET', 'POST'], view_func=views.playlist_add)
    app.add_url_rule('/export/<key>', endpoint='export', view_func=views.export)
    app.add_url_rule('/search', endpoint='search', methods=["POST"], view_func=views.search)
    app.add_url_rule('/search-song', endpoint='search_song', methods=["POST"], view_func=views.search_song)
    app.add_url_rule('/add_comment/<key>', endpoint='add_comment', methods=["POST"], view_func=views.add_comment)
    app.add_url_rule('/login', endpoint='login', methods=["GET", "POST"], view_func=views.login)
    app.add_url_rule('/logout', endpoint='logout', view_func=views.logout)
    app.add_url_rule('/register', endpoint='register', methods=["GET", "POST"], view_func=views.register)
    app.add_url_rule('/playlist/<key>/edit', endpoint='playlist_edit', methods=['GET', 'POST'], view_func=views.playlist_edit)
    app.add_url_rule('/delete_comment/<key>', methods=['POST'], view_func=views.delete_comment)
    app.add_url_rule('/remove_song/<key>', methods=['POST'], view_func=views.remove_song)
    app.add_url_rule('/add_song/<key>', methods=['POST'], view_func=views.add_song)
    app.add_url_rule('/profile', endpoint='user', view_func=views.profile)
    app.add_url_rule('/profile/<int:key>', endpoint='user_ext', view_func=views.public_profile)
    app.add_url_rule('/playlist/<key>/auth', endpoint='get_password_for', methods=["GET", "POST"], view_func=views.get_password_for)

    lm.init_app(app)
    lm.login_view = "login"

    db = Database()
    app.config["db"] = db

    return app


if __name__ == "__main__":
    app = create_app()
#    app.run(host="0.0.0.0", port="8080", debug=True)
