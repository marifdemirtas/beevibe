from flask import render_template, current_app, abort, url_for, request, redirect, Response
from user import get_user, User
from data import *
import json
from flask_login import current_user, login_user, logout_user

def index():
    playlist = current_app.config["db"].get_featured_playlist()
    return render_template("home.html", playlist=playlist)


def rand_playlist():
    # generate random playlist key
    return redirect(url_for("playlist", key="rand"))

def featured():
    featured = current_app.config["db"].get_featured_playlists()
    return render_template("list-playlist.html", playlists=featured)


def playlist(key):
    playlist = current_app.config["db"].get_playlist(int(key))
    # validate
    print(playlist.songs)
    return render_template("playlist.html", playlist=playlist)


def export(key):
    export_obj = current_app.config["db"].get_playlist(int(key)).export()
    filename = 'attachment;filename=' + export_obj["title"] + '.json'

    encoded_obj = json.dumps(export_obj, ensure_ascii=False).encode('utf8')
    print(encoded_obj)
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'Content-Disposition': filename, 'charset': 'utf-8'})


def playlist_add():
    if request.method == "GET":
        return render_template("playlist-add.html")
    else:
        playlist = Playlist(title=request.form['playlist_title'],
                            creator=request.form['playlist_creator'],
                            descr=request.form['playlist_descr'])
        playlist.page.set_color(request.form['playlist_color'])
        playlist = current_app.config["db"].add_playlist(playlist)
        return redirect(url_for("playlist", key=playlist.id))


def add_comment(key):
    comment = Comment(request.form['content'], request.form['author'])
    current_app.config["db"].add_comment_to_playlist(int(key), comment)
    return redirect(url_for("playlist", key=key))


def search():
    response = {}

    # do search, set status accordingly
    status = True
    response["status"] = status

    ans = f"Result related to {request.form['query']})"
    b = f"Another result about {request.form['query']}"

    if status:
        # fill up result array
        results = []
        results.append(ans)
        results.append(b)
        response["results"] = results

    return response


def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        user = get_user(request.form['username'])
        if request.form['password'] == user.password:
            login_user(user)
            next_page = request.args.get("next", url_for("index"))
            return redirect(next_page)
        return render_template('login.html')


def logout():
    logout_user()
    return redirect(url_for("index"))