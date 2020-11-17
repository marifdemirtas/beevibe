from flask import Flask

import views
from data import Object
from database import Database


def create_app():
    app = Flask(__name__)
    app.config.from_envvar("SETTINGS")

    app.add_url_rule('/', endpoint='index', view_func=views.index)
    app.add_url_rule('/flowers', endpoint='flowers', view_func=views.flowers)
    app.add_url_rule('/flower/<int:key>', endpoint='flower', view_func=views.flower)
    app.add_url_rule('/add_flower', endpoint='add_flower', view_func=views.add_flower, methods=["GET", "POST"])

    db = Database()
    db.add_object(Object("Papatya", "pembe"))
    db.add_object(Object("Karanfil", "yeşil"))
    app.config["db"] = db

    return app


if __name__ == "__main__":
    app = create_app()
#    app.run(host="0.0.0.0", port="8080", debug=True)
