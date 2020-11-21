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
    app.add_url_rule('/some/<key>', endpoint='playlist', view_func=views.playlist)
    app.add_url_rule('/add', endpoint='playlist_add', methods=['GET', 'POST'], view_func=views.playlist_add)

    @app.route('/search', methods=["POST"])
    def search():
        # do search
        ans = f"the ans is {request.form['query']})"
        b = "Hellow"
        return {"result_1": ans, "result_2": b}


    db = Database()
    app.config["db"] = db

    return app


if __name__ == "__main__":
    app = create_app()
#    app.run(host="0.0.0.0", port="8080", debug=True)
