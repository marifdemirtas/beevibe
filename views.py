from flask import render_template, current_app, abort, url_for, request, redirect, Response, flash
from user import get_user, User
from data import *
from forms import *
from database import DuplicateError
import json
from flask_login import current_user, login_user, logout_user, login_required
from hashlib import sha256



def error_direction(f):
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return abort(404)
    wrap.__name__ = f.__name__
#    return wrap
    return f

@error_direction
def index():
    playlist = current_app.config["db"].get_featured_playlist()
    return render_template("home.html", playlist=playlist)


@error_direction
def rand_playlist():
    # generate random playlist key
    return redirect(url_for("playlist", key="rand"))


@error_direction
def featured():
    featured = current_app.config["db"].get_featured_playlists()
    return render_template("list-playlist.html", playlists=featured)

@login_required
@error_direction
def profile():
    playlists = current_app.config["db"].get_playlists_by(current_user)
    return render_template("list-playlist.html",
                           playlists=playlists,
                           profile=current_user.username)

@error_direction
def public_profile(key):
    playlists = current_app.config["db"].get_playlists_using_id(int(key))
    return render_template("list-playlist.html",
                           playlists=playlists,
                           profile=current_app.config["db"].get_username(int(key)))

@error_direction
def playlist(key):
    playlist = current_app.config["db"].get_playlist(int(key))
    # validate
    if playlist is None:
        return abort(404)
    #    playlist = current_app.config["db"].get_playlist(key)
    print(playlist.page.password is not None)
    if playlist.page.password is not None:
        return redirect(url_for("get_password_for", key=key))
    return render_template("playlist.html", playlist=playlist)


@error_direction
def get_password_for(key):
    if request.method == "GET":
        return render_template("password-enter.html", status=True)
    else:
        playlist = current_app.config["db"].get_playlist(int(key))
        if request.form["password"] == playlist.page.password:
            return render_template("playlist.html", playlist=playlist)
        else:
            return render_template("password-enter.html", status=False)


@error_direction
def export(key):
    export_obj = current_app.config["db"].get_playlist(int(key)).export()
    filename = 'attachment;filename=' + export_obj["title"] + '.json'

    encoded_obj = json.dumps(export_obj, ensure_ascii=False).encode('utf8')
    print(encoded_obj)
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'Content-Disposition': filename, 'charset': 'utf-8'})



@login_required
@error_direction
def playlist_add():
    form = CreatePlaylistForm()
    if form.validate_on_submit():
        playlist = Playlist(title=form.title.data,
                            creator=current_user.username,
                            descr=form.descr.data)
        playlist.page.set_color(form.color.data.hex)
        print(form.privacy)
        playlist = current_app.config["db"].add_playlist(playlist)
        return redirect(url_for("playlist_edit", key=playlist.id))
    return render_template("playlist-add.html", form=form)


@login_required
@error_direction
def playlist_edit(key):
    if request.method == "GET":
        playlist = current_app.config["db"].get_playlist(int(key))
        return render_template("playlist_edit.html", playlist=playlist)


@error_direction
def delete_comment(key):
    comment_ids = request.form.keys()
    comments = [int(cid) for cid in comment_ids]
    current_app.config["db"].remove_comments_from_playlist(int(key), comments)
    return redirect(url_for("playlist_edit", key=key))



@error_direction
def remove_song(key):
    song_ids = request.form.keys()
    songs = [int(sid) for sid in song_ids]
    current_app.config["db"].remove_songs_from_playlist(int(key), songs)
    return redirect(url_for("playlist_edit", key=key))


@error_direction
def add_song(key):
    song = Song(request.form["new_song"], request.form["new_artist"],
                request.form["new_album"], request.form["new_duration"])
    song = current_app.config["db"].add_song_to_database(song)
    try:
        current_app.config["db"].add_songs_to_playlist(int(key), [song.id])
    except DuplicateError as e:
        flash("Song already in database.")
        print("Song already in database.")
    return redirect(url_for("playlist_edit", key=key))


@login_required
@error_direction
def add_comment(key):
    comment = Comment(request.form['content'], current_user.username)
    current_app.config["db"].add_comment_to_playlist(int(key), comment)
    return redirect(url_for("playlist", key=key))


@error_direction
def search():
    response = {}

    # do search, set status accordingly
    status = True
    response["status"] = status

    if status:
        # fill up result array
        results = current_app.config['db'].search_playlists_by_title(request.form['query'])
        response["results"] = [f"{res.title}, by {res.creator}" for res in results]

    encoded_obj = json.dumps(response, ensure_ascii=False).encode('utf8')
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'charset': 'utf-8'})


@error_direction
def search_song():
    response = {}

    # do search, set status accordingly
    status = True
    response["status"] = status


    if status:
        # fill up result array
        results = current_app.config['db'].search_song_by_title(request.form['query'])
        response["results"] = [song.to_dict() for song in results]

    encoded_obj = json.dumps(response, ensure_ascii=False).encode('utf8')
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'charset': 'utf-8'})


@error_direction
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user(form.username.data)
        if user is not None and sha256(form.password.data.encode('utf-8')).hexdigest() == user.password:
            login_user(user)
            next_page = request.args.get("next", url_for("index"))
            return redirect(next_page)
        flash("Login unsuccessful")
        return render_template('login.html', form=form)
    if current_user.is_authenticated:
        return abort(404)
    return render_template('login.html', form=form)


@error_direction
def logout():
    logout_user()
    return redirect(url_for("index"))


@error_direction
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        user = get_user(request.form['username'])
        #check by email
        if user is None:
            user = User(5, request.form['email'], request.form['username'], sha256(request.form['password'].encode('utf-8')).hexdigest())
            user = current_app.config['db'].register_user(user)
            login_user(user)
            next_page = request.args.get("next", url_for("index"))
            return redirect(next_page)
        return render_template('register.html')
