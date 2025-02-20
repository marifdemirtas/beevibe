from flask import Flask
from flask_login import LoginManager
import logging

import views
from database import Database
from user import get_user

lm = LoginManager()


@lm.user_loader
def load_user(user_id):
    return get_user(user_id)


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Development")

    app.add_url_rule('/', endpoint='index', view_func=views.index)
    app.add_url_rule('/random', endpoint='random', view_func=views.rand_playlist)
    app.add_url_rule('/featured', endpoint='featured', view_func=views.featured)
    app.add_url_rule('/playlist/<int:key>', endpoint='playlist', view_func=views.playlist)
    app.add_url_rule('/add', endpoint='playlist_add', methods=['GET', 'POST'], view_func=views.playlist_add)
    app.add_url_rule('/export/<int:key>', endpoint='export', view_func=views.export)
    app.add_url_rule('/search', endpoint='search', methods=["POST"], view_func=views.search)
    app.add_url_rule('/search-song', endpoint='search_song', methods=["POST"], view_func=views.search_song)
    app.add_url_rule('/add_comment/<int:key>', endpoint='add_comment', methods=["POST"], view_func=views.add_comment)
    app.add_url_rule('/login', endpoint='login', methods=["GET", "POST"], view_func=views.login)
    app.add_url_rule('/logout', endpoint='logout', view_func=views.logout)
    app.add_url_rule('/register', endpoint='register', methods=["GET", "POST"], view_func=views.register)
    app.add_url_rule('/playlist/<int:key>/edit', endpoint='playlist_edit', methods=['GET', 'POST'], view_func=views.playlist_edit)
    app.add_url_rule('/delete_comment/<int:key>', methods=['POST'], view_func=views.delete_comment)
    app.add_url_rule('/delete_playlist/<int:key>', view_func=views.delete_playlist)
    app.add_url_rule('/remove_song/<int:key>', methods=['POST'], view_func=views.remove_song)
    app.add_url_rule('/add_song/<int:key>', methods=['POST'], view_func=views.add_song)
    app.add_url_rule('/profile', endpoint='user',methods=['GET', 'POST'], view_func=views.profile)
    app.add_url_rule('/profile/<int:key>', endpoint='user_ext', view_func=views.public_profile)
    app.add_url_rule('/profile/<string:name>', endpoint='user_ext_name', view_func=views.profile_redir)
    app.add_url_rule('/playlist/<int:key>/auth', endpoint='get_password_for', methods=["GET", "POST"], view_func=views.get_password_for)
    app.add_url_rule('/delete_user/<int:key>', endpoint='delete_user', methods=["GET"], view_func=views.delete_user)
    app.add_url_rule('/search_page', endpoint='search_page', methods=["POST"], view_func=views.search_page)

    app.register_error_handler(404, views.page_not_found)
    app.register_error_handler(403, views.page_forbidden)

    lm.init_app(app)
    lm.login_view = "login"

    db = Database(app.config['DATABASE_URL'])
    app.config["db"] = db

    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    return app


if __name__ == "__main__":
    app = create_app()

#    app.run(host="0.0.0.0", port="8080", debug=True)
