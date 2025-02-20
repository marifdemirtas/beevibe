from flask import render_template, current_app, abort, url_for, request, redirect, Response, flash
from flask_login import current_user, login_user, logout_user, login_required
from hashlib import sha256
import _datetime
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
    featured, avg_playlists = current_app.config["db"].get_featured_playlists()
    return render_template("list-playlist.html", playlists=featured, avg_playlists=avg_playlists)

@login_required
@error_direction
def profile():
    form = ProfileUpdateForm()
    playlists = current_app.config["db"].get_playlists_by(current_user)
    stats = {'numplaylist': 5,
             'numsong': 30,
             'favartist': 'The Doors',
             'favsong': 'Riders on the Storm'}
    if form.validate_on_submit():
        current_app.config["db"].set_public_profile(current_user.id, form.privacy.data)
        current_user.public = form.privacy.data
    form.privacy.data = current_user.public
    sum_playlists = current_app.config["db"].get_all_playlist_durations_user(current_user.id)
    artists = current_app.config["db"].get_top_three_artists(current_user.id)
    return render_template("list-playlist.html",
                           playlists=playlists,
                           profile=current_user.username,
                           sum_playlists=sum_playlists,
                           artists=artists,
                           form=form)


@error_direction
def public_profile(key):
    if current_user.is_authenticated and current_user.id == int(key):
        return redirect(url_for('user'))
    if current_app.config["db"].is_user_private(int(key)):
        return abort(403)
    playlists = current_app.config["db"].get_playlists_using_id(int(key))
    if playlists is None:
        return abort(403)
    stats = {'numplaylist': 5,
             'numsong': 30,
             'favartist': 'The Doors',
             'favsong': 'Riders on the Storm'}
    sum_playlists = current_app.config["db"].get_all_playlist_durations_user(int(key))
    artists = current_app.config["db"].get_top_three_artists(int(key))
    if current_user.is_authenticated:
        common_songs = current_app.config["db"].get_common_songs(int(key), current_user.id)
    else:
        common_songs=None
    return render_template("list-playlist.html",
                           playlists=playlists,
                           profile=current_app.config["db"].get_username(int(key)),
                           sum_playlists=sum_playlists,
                           artists=artists,
                           common_songs=common_songs,
                           stats=stats)

@error_direction
def playlist(key):
    playlist = current_app.config["db"].get_playlist(int(key))
    # validate
    current_app.logger.debug("checkpoint 1")
    if playlist is None:
        return abort(404)
    current_app.logger.debug("checkpoint 2")
    if playlist.page.password is not None:
        if current_user.is_authenticated and (current_user.username == playlist.creator):
            pass
        else:
            return redirect(url_for("get_password_for", key=key))
    current_app.logger.debug("checkpoint 3")
    return render_template("playlist.html", playlist=playlist)


@error_direction
def get_password_for(key):
    if request.method == "GET":
        return render_template("password-enter.html", status=True)
    else:
        playlist = current_app.config["db"].get_playlist(int(key))
        if sha256(request.form["password"].encode('utf-8')).hexdigest() == playlist.page.password:
            if current_user.is_authenticated:
                current_user.auth_playlists.append(playlist.id)
                current_app.logger.debug(current_user.auth_playlists)
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
                            s['track']['album']['name'], int(s['track']['duration_ms']/1000), s['track']['album']['release_date'][:4]), None)
                      for s in pl['tracks']['items']]
        }
        return ps
    except Exception as e:
        flash("Import unsuccessful.")
        return None


def import_from(ps):
    playlist = Playlist(title=ps['title'],
                        creator=ps['creator'],
                        descr=ps['description'])
    playlist = current_app.config["db"].add_playlist(playlist)
    for song in ps['songs'][:25]:
        song = current_app.config["db"].add_song_to_database(song[0]) #modify spotify exports to fit with file exports
        try:
            current_app.config["db"].add_song_to_playlist(playlist.id, song.id)
        except DuplicateError as e:
            continue

    return redirect(url_for("playlist", key=playlist.id))


@error_direction
def export(key):
    export_obj = current_app.config["db"].get_playlist(int(key)).export()
    filename = 'attachment;filename=' + export_obj["title"] + '.json'

    encoded_obj = json.dumps(export_obj, ensure_ascii=False).encode('utf8', 'ignore')
    return Response(encoded_obj,
                    mimetype="application/json",
                    headers={'Content-Disposition': filename, 'charset': 'utf-8'})



@login_required
@error_direction
def playlist_add():
    form = CreatePlaylistForm()
    import_form = ImportPlaylistForm()
    if form.validate_on_submit():
        if len(form.color.data.hex) < 7:
            form.color.data.hex = (form.color.data.hex + '000000')[:7]
        playlist = Playlist(title=form.title.data,
                            creator=current_user.username,
                            descr=form.descr.data)
        playlist.page.set_color(form.color.data.hex)
        playlist.page.set_commenting(form.commenting.data)
        playlist.page.set_password(form.privacy.data)
        current_app.logger.debug(form.date.data)
        if form.date.data is not None:
            playlist.page.set_expiration(_datetime.datetime.now() + _datetime.timedelta(days=form.date.data))
        else:
            playlist.page.set_expiration(None)        
        if 'image' in request.files:
            image = request.files['image'].read()
            playlist.metadata.set_thumbnail(image)
        playlist = current_app.config["db"].add_playlist(playlist)
        return redirect(url_for("playlist_edit", key=playlist.id))
    elif import_form.validate_on_submit():
        f = import_form.file.data
        if f is not None:
            try:
                return import_from(json.loads(f.stream.read()))
            except Exception as e:
                flash("Import unsuccessful.")
                import_form.file.errors.append("Invalid file.")
        else:
#            current_app.logger.debug()
            try:
                return import_from(get_dict_from_spotify(import_form.uri.data.split(':')[-1]))
            except:
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
        current_app.logger.debug(isinstance(form.color.data, colour.Color))
        current_app.logger.debug(form.descr.data)
        playlist.metadata.set_descr(form.descr.data)
        playlist.page.set_color(form.color.data.hex)
        playlist.page.set_commenting(form.commenting.data)
        playlist.id = int(key)
        playlist = current_app.config["db"].update_playlist(playlist)
        return redirect(url_for('playlist', key=playlist.id))
    else:
        form.descr.data = playlist.metadata.descr
        form.color.data = colour.Color(playlist.page.color)
        current_app.logger.debug(form.color.data)
        current_app.logger.debug(form.color.data.hex)
        form.commenting.data = playlist.page.commenting
        return render_template("playlist-edit.html", playlist=playlist, form=form)


def delete_comment(key):
    if not current_app.config['db'].check_auth(current_user.id, int(key)):
        return abort(403)
    comments = [int(cid) for cid in request.form]
    current_app.logger.debug(comments)
    current_app.config["db"].remove_comments_from_playlist(int(key), comments)
    return redirect(url_for("playlist_edit", key=key))


@error_direction
def delete_playlist(key):
    if not current_app.config['db'].check_auth(current_user.id, int(key)):
        return abort(403)
    current_app.config["db"].remove_playlist(int(key))
    return redirect(url_for("user"))


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
                request.form["new_album"], request.form["new_duration"], request.form["new_release_year"])
    song = current_app.config["db"].add_song_to_database(song)
    try:
        current_app.config["db"].add_song_to_playlist(int(key), song.id, request.form["new_song_descr"])
    except DuplicateError as e:
        flash("Song already in playlist.")
        current_app.logger.debug("Song already in playlist.")
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
        response["results"] = [f"{res.title}, by {res.creator}:{res.id}" for res in results]

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
        form.password.errors.append("Wrong username or password.")
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
                user = User(None, form.username.data, form.email.data, sha256(form.password.data.encode('utf-8')).hexdigest(), form.public.data, _datetime.date.today())
                current_app.logger.debug(user.register_date)
                user = current_app.config['db'].register_user(user)
                login_user(user)
                next_page = request.args.get("next", url_for("index"))
                return redirect(next_page)
        else:
            form.username.errors.append("This nickname is already registered.")
        return render_template('register.html', form=form)
    form.public.data = True
    return render_template('register.html', form=form)


def page_not_found(e):
    return render_template('not-found.html'), 404


def page_forbidden(e):
    return render_template('forbidden.html'), 403


@login_required
@error_direction
def delete_user(key):
    logout_user()
    current_app.config["db"].delete_user(key)
    return redirect(url_for("index"))


@error_direction
def search_page():
    current_app.logger.debug(request.form)
    if request.form['query'] == "":
        return redirect(url_for('featured'))
    results = current_app.config['db'].search_playlists_by_title(request.form['query'])
    current_app.logger.debug(results)
    return render_template("list-playlist.html", playlists=results, search=request.form["query"])

@error_direction
def profile_redir(name):
    tup = current_app.config["db"].get_user_tuple(name)
    if tup is not None:
        key, *_ = tup
        return redirect(url_for('user_ext', key=key))
    else:
        return abort(404)
