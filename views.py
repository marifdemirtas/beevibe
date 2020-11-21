from flask import render_template, current_app, abort, url_for, request, redirect

from data import *

s1 = Song(title="SongTitle1",
          artist="Artist1",
          album="Album1",
          duration=120)
s2 = Song(title="SongTitle1",
          artist="Artist1",
          album="Album1",
          duration=120)
s3 = Song(title="SongTitle1",
          artist="Artist1",
          album="Album1",
          duration=120)
s1.s_id(25)
s2.s_id(30)
s3.s_id(35)


def index():
    return render_template("home.html")


def rand_playlist():
    # generate random playlist key
    return redirect(url_for("playlist", key="rand"))


def playlist(key):
    # database.get_playlist(key)
    playlist = Playlist("baykuş", "arif", "Happy birthday!!")
    playlist.add(s1)
    playlist.add(s2, "my " + key)
    playlist.add(s3)
    playlist.page.commenting = True
    return render_template("playlist.html", playlist=playlist)


def playlist_add():
    if request.method == "GET":
        return render_template("playlist-add.html")
    else:
        playlist = Playlist(title=request.form['playlist_title'],
                            creator=request.form['playlist_creator'],
                            descr=request.form['playlist_descr'])
        playlist.page.color = request.form['playlist_color']
        #return redirect(url_for("playlist", key=request.form['id']))
        return render_template("playlist.html", playlist=playlist)
