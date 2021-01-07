from flask import render_template, current_app, abort, url_for, request, redirect, Response, flash
from flask_login import current_user, login_user, logout_user, login_required
from hashlib import sha256
import json
import colour

from user import get_user, User
from data import *
from forms import *
from utils import error_direction, DuplicateError

'''
to-do
users should be able to delete playlists
users should be able to delete comments
import from spotify should be refined
'''



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


import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_dict_from_spotify(key):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=current_app.config['SPOTIPY_CLIENT_ID'],
                                                   client_secret=current_app.config['SPOTIPY_CLIENT_SECRET'],
                                                   redirect_uri=current_app.config['SPOTIPY_REDIRECT_URI']))
    try:
        pl = sp.playlist(key)
        ps = {
            'title': pl['name'],
            'creator': current_user.username,
            'description': pl['description'] + ", originally by " + pl['owner']['display_name'],
            'songs': [(Song(s['track']['name'], s['track']['artists'][0]['name'],
                            s['track']['album']['name'], int(s['track']['duration_ms']/1000)), None) 
                      for s in pl['tracks']['items']]
        }
        return ps
    except:
        return None


def import_from(ps):
    playlist = Playlist(title=ps['title'],
                        creator=ps['creator'],
                        descr=ps['description'])
    playlist = current_app.config["db"].add_playlist(playlist)
    for song in ps['songs']:
        song = current_app.config["db"].add_song_to_database(song[0]) #modify spotify exports to fit with file exports
        try:
            current_app.config["db"].add_songs_to_playlist(playlist.id, [song.id])
        except DuplicateError as e:
            pass

    return redirect(url_for("playlist", key=playlist.id))


@error_direction
def export(key):
    export_obj = current_app.config["db"].get_playlist(int(key)).export()
    filename = 'attachment;filename=' + export_obj["title"] + '.json'

    encoded_obj = json.dumps(export_obj, ensure_ascii=False).encode('utf8')
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'Content-Disposition': filename, 'charset': 'utf-8'})



@login_required
@error_direction
def playlist_add():
    form = CreatePlaylistForm()
    import_form = ImportPlaylistForm()
    if form.validate_on_submit():
        playlist = Playlist(title=form.title.data,
                            creator=current_user.username,
                            descr=form.descr.data)
        playlist.page.set_color(form.color.data.hex)
        playlist = current_app.config["db"].add_playlist(playlist)
        return redirect(url_for("playlist_edit", key=playlist.id))
    elif import_form.validate_on_submit():
        f = import_form.file.data
        if f is not None:
            try:
                import_from(json.loads(f.stream.read()))
            except Exception as e:
                print(e)
                import_form.file.errors.append("Invalid file.")
        else:
            temp = import_from(get_dict_from_spotify(import_form.uri.data))
            if temp is not None:
                return temp
            else:
                import_form.uri.errors.append("URI not found.")
    return render_template("playlist-add.html", form=form, import_form=import_form)


@login_required
@error_direction
def playlist_edit(key):
    if not current_app.config['db'].check_auth(current_user.id, key):
        return abort(403)
    form = EditPlaylistForm()
    playlist = current_app.config["db"].get_playlist(int(key))
    if request.method == "POST":
        playlist.metadata.set_descr(form.descr.data)
        playlist.page.set_color(form.color.data.hex)
        playlist = current_app.config["db"].update_playlist(playlist)
        return redirect(url_for('playlist', key=playlist.id))
    else:
        return render_template("playlist_edit.html", playlist=playlist, form=form)


@error_direction
def delete_comment(key):
    if not current_app.config['db'].check_auth(current_user.id, key):
        return abort(403)
    comment_ids = request.form.keys()
    comments = [int(cid) for cid in comment_ids]
    current_app.config["db"].remove_comments_from_playlist(int(key), comments)
    return redirect(url_for("playlist_edit", key=key))



@error_direction
def remove_song(key):
    if not current_app.config['db'].check_auth(current_user.id, key):
        return abort(403)
    song_ids = request.form.keys()
    songs = [int(sid) for sid in song_ids]
    current_app.config["db"].remove_songs_from_playlist(int(key), songs)
    return redirect(url_for("playlist_edit", key=key))


@error_direction
def add_song(key):
    if not current_app.config['db'].check_auth(current_user.id, key):
        return abort(403)
    song = Song(request.form["new_song"], request.form["new_artist"],
                request.form["new_album"], request.form["new_duration"])
    song = current_app.config["db"].add_song_to_database(song)
    try:
        current_app.config["db"].add_songs_to_playlist(int(key), [song.id])
    except DuplicateError as e:
        flash("Song already in playlist.")
        print("Song already in playlist.")
    return redirect(url_for("playlist_edit", key=key))


@login_required
@error_direction
def add_comment(key):
    if not current_app.config['db'].check_auth(current_user.id, key):
        return abort(403)
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
        return abort(403)
    return render_template('login.html', form=form)


@error_direction
def logout():
    logout_user()
    return redirect(url_for("index"))


@error_direction
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = get_user(form.username.data)
        if user is None:
            if current_app.config['db'].get_user_by_email(form.email.data):
                form.email.errors.append("This email is already registered.")
            else:
                user = User(None, form.email.data, form.username.data, sha256(form.password.data.encode('utf-8')).hexdigest())
                user = current_app.config['db'].register_user(user)
                login_user(user)
                next_page = request.args.get("next", url_for("index"))
                return redirect(next_page)
        else:
            form.username.errors.append("This nickname is already registered.")
        return render_template('register.html', form=form)
    return render_template('register.html', form=form)

