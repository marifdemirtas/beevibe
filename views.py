from flask import render_template, current_app, abort, url_for, request, redirect, Response
from user import get_user, User
from data import *
import json
from flask_login import current_user, login_user, logout_user, login_required

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
    if playlist is None:
        playlist = current_app.config["db"].get_playlist(key)
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


@login_required
def playlist_add():
    if request.method == "GET":
        return render_template("playlist-add.html")
    else:
        playlist = Playlist(title=request.form['playlist_title'],
                            creator=current_user.username,
                            descr=request.form['playlist_descr'])
        playlist.page.set_color(request.form['playlist_color'])
        playlist = current_app.config["db"].add_playlist(playlist)
        return redirect(url_for("playlist", key=playlist.id))


@login_required
def playlist_edit(key):
    if request.method == "GET":
        playlist = current_app.config["db"].get_playlist(int(key))
        return render_template("playlist_edit.html", playlist=playlist)


def delete_comment(key):
    comment_ids = request.form.keys()
    comments = [int(cid) for cid in comment_ids]
    current_app.config["db"].remove_comments_from_playlist(int(key), comments)
    return redirect(url_for("playlist_edit", key=key))



def remove_song(key):
    song_ids = request.form.keys()
    songs = [int(sid) for sid in song_ids]
    current_app.config["db"].remove_songs_from_playlist(int(key), songs)
    return redirect(url_for("playlist_edit", key=key))


def add_song(key):
    song = Song(request.form["new_song"], request.form["new_artist"],
                request.form["new_album"], request.form["new_duration"])
    song = current_app.config["db"].add_song_to_database(song)
    current_app.config["db"].add_songs_to_playlist(int(key), [song.id])
    return redirect(url_for("playlist_edit", key=key))


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


def search_song():
    response = {}

    # do search, set status accordingly
    status = True
    response["status"] = status

    s1 = Song(f"Given title {request.form['query']}", "some artist", "album", 111)
    s2 = Song("Midnight", "Lianne La Havas", "Live at Sofar", 290)

    s1.s_id(12)
    s2.s_id(44)

    if status:
        # fill up result array
        results = []
        results.append(s1.to_dict())
        results.append(s2.to_dict())
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