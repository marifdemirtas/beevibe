from flask import render_template, current_app, abort, url_for, request, redirect

import random

from data import Object

def index():
    return render_template("home.html", num=random.random())


def flowers():
    db = current_app.config["db"]
    flowers = db.get_all()
    return render_template("flowers.html", flowers=flowers)


def flower(key):
    db = current_app.config["db"]
    flower = db.get_object(key)
    if flower is None:
        abort(404)
    return render_template("flower.html", flower=flower)


def add_flower():
    if request.method == "GET":
        return render_template("flower_add.html")
    else:
        form_attr = request.form["attr"]
        form_attr2 = request.form["attr2"]
        current_app.config["db"].add_object(Object(form_attr, form_attr2))
        return redirect(url_for('flowers'))
