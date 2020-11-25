from flask import render_template, current_app, abort, url_for, request, redirect, Response

from data import *
import json

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
    return Response(json.dumps(export_obj), 
        mimetype="application/json",
        headers={'Content-Disposition':filename})

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