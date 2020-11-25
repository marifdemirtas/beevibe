from flask import Flask, request

import views
from data import *
from database import Database
import json

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
    app.add_url_rule('/add_comment/<key>', endpoint='add_comment', methods=["POST"], view_func=views.add_comment)

    db = Database()
    app.config["db"] = db

    return app


if __name__ == "__main__":
    app = create_app()
#    app.run(host="0.0.0.0", port="8080", debug=True)
