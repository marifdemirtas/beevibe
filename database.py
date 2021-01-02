from data import *
import random
import datetime

import psycopg2 as psql


'''
TODO
update playlist
comment operations
song operations
'''


class DuplicateError(Exception):
    def __init__(self):
        super(DuplicateError, self).__init__()

def handle_db_exception(f):
    def wrap(*args, **kwargs):
        print("HERE")
        try:
            return f(*args, **kwargs)
        except Exception as e:
            args[0].conn.rollback()
            if isinstance(e, psql.errors.UniqueViolation):
                raise DuplicateError()
            #return None
 #   return wrap
    return f

class Database(object):

    def __init__(self):
        self.conn = psql.connect(database="test", user="marif")

    @handle_db_exception
    def get_playlist(self, key):
        '''
        Fetches the playlist with given key, returns Playlist object
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM playlists WHERE playlist_id=%s", (key,))
            res = curr.fetchone()
            if res == None:
                playlist = None
            else:
                curr.execute("SELECT nickname FROM users WHERE user_id=%s", (res[-1],))
                creator = curr.fetchone()[0]
                print(creator)
                p_id, title, descr, color, commenting, privacy, expire_date, thumbnail, _ = res
                playlist = Playlist(title, creator, descr)
                playlist.page.set_color(color)
                playlist.page.set_commenting(commenting)
                playlist.page.set_password(privacy)
                playlist.page.set_expiration(expire_date)
                playlist.metadata.set_thumbnail(thumbnail)
                playlist.s_id(p_id)


        if playlist != None:
            if playlist.page.expiration is not None and playlist.page.expiration < datetime.datetime.now():
                self.remove_playlist(playlist.id)
                playlist = None
            else:
                with self.conn.cursor() as curr:
                    curr.execute('''SELECT songs.song_id, songs.title, songs.artist, songs.album, songs.duration, spmap.song_description
                                    FROM (spmap INNER JOIN songs ON songs.song_id = spmap.song_id)
                                    WHERE spmap.playlist_id=%s;''', (playlist.id,))
                    songs = curr.fetchall()
                    for song_t in songs:
                        song = Song(*song_t[1:-1])
                        song.s_id(song_t[0])
                        playlist.add(song, song_t[-1])
                    #populate with comments
                    curr.execute('''SELECT comments.content, users.nickname, comments.publish_date
                                    FROM ((comments INNER JOIN playlists ON comments.playlist_id = playlists.playlist_id)
                                    INNER JOIN users ON comments.author_id = users.user_id)
                                    WHERE playlists.playlist_id=%s;''', (playlist.id,))
                    comments = curr.fetchall()
                    print(comments)
                    for comment_t in comments:
                        comment = Comment(*comment_t)
                        playlist.add_comment(comment)
        return playlist

    def remove_playlist(self, key):
        with self.conn.cursor() as curr:
            curr.execute("DELETE FROM playlists WHERE playlist_id=%s", (key,))
            self.conn.commit()

    def add_playlist(self, playlist):
        '''
        Adds the given playlist to the db
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT user_id FROM users WHERE nickname=%s", (playlist.creator,))
            creator_id = curr.fetchone()[0]
            curr.execute('''INSERT INTO playlists (title, description, color, commenting, privacy, expire_date, thumbnail, creator_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING playlist_id''',
                            (playlist.title, playlist.metadata.descr, playlist.page.color, playlist.page.commenting, playlist.page.password, playlist.page.expiration, playlist.metadata.thumbnail, creator_id));
            playlist.s_id(curr.fetchone()[0])
            for song_id in playlist.songs:
                curr.execute('''INSERT INTO spmap (song_id, playlist_id, song_description) VALUES
                            (%s, %s, %s)''', (song_id, playlist.id, playlist.song_descr[song_id]))
            self.conn.commit()
        return playlist

    def search_playlists_by_title(self, title):
        '''
        Returns the corePlaylist objects related with title.
        '''
        # search database for title and return the matching
        # for playlist in query_results
        #   build corePlaylists
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id, playlists.title, users.nickname FROM playlists
                            INNER JOIN users ON users.user_id=playlists.creator_id
                            WHERE playlists.title LIKE %s''', (title + '%',))
            return [corePlaylist(*row) for row in curr.fetchmany(5)]


    def search_song_by_title(self, title):
        ret_songs = []
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM songs WHERE title LIKE %s", (title + '%',))
            for song in curr.fetchmany(5):
                ret_songs.append(Song(*song[1:]))
                ret_songs[-1].s_id(song[0])
        return ret_songs


    def search_playlists_by_creator(self, creator):
        '''
        Returns the corePlaylist objects related with creator.
        '''
        # search database for title and return the matching
        # for playlist in query_results
        #   build corePlaylists
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id, playlists.title, users.nickname FROM playlists
                            INNER JOIN users ON users.user_id=playlists.creator_id
                            WHERE users.nickname LIKE %s''', (creator + '%',))
            return [corePlaylist(*row) for row in curr.fetchmany(5)]

    def del_playlist(self, key):
        '''
        Deletes the playlist with given key.
        '''
        with self.conn.cursor() as curr:
            curr.execute("DELETE FROM playlists WHERE playlist_id=%s", (key,))


    def update_playlist(self, playlist):
        '''
        Given a playlist object, updates the one in database with the same key
        with the given object.
        '''
        db_playlist = self.get_playlist(playlist.key)
        # for diff_attr in (db_playlist, playlist)
        #    update database accordingly

    @handle_db_exception
    def add_songs_to_playlist(self, key, songs):
        '''
        Adds the songs given (as ids) to the playlist given (as key).
        Returns the updated playlist.
        '''
        with self.conn.cursor() as curr:
            for song_id in songs:
                curr.execute('''INSERT INTO spmap (playlist_id, song_id) VALUES
                                (%s, %s)''', (key, song_id))
            self.conn.commit()
        return self.get_playlist(key)

    def remove_songs_from_playlist(self, key, songs):
        '''
        Removes the songs given (as ids) from the playlist given (as key).
        Returns the updated playlist.
        '''
        if key in playlists:
            for song_id in songs:
                plmap[key].remove(int(song_id))
                # remove song_id from plmap
        return self.get_playlist(key)

    def add_comment_to_playlist(self, key, comment):
        '''
        Adds a comment by an user to the database
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT user_id FROM users WHERE nickname=%s", (comment.author,))
            curr.execute('''INSERT INTO comments (content, publish_date, author_id, playlist_id)
                            VALUES (%s, %s, %s, %s)''',
                            (comment.content, comment.date, curr.fetchone()[0], key))
            self.conn.commit()
        return self.get_playlist(key)

    def remove_comments_from_playlist(self, key, comment_id):
        '''
        Adds a comment by an user to the database
        '''
        for comment in comment_id:
            self.playlists[key].delete_comment(comment)
        # update playlist-comment mapping
        return self.playlists[key]

    @handle_db_exception
    def add_song_to_database(self, song):
        '''
        Adds a given song object to the database
        '''
        with self.conn.cursor() as curr:
#            if song.duration == '':
 #               song.duration = None
            curr.execute("SELECT song_id FROM songs WHERE title=%s AND artist=%s AND album=%s ", (song.title, song.artist, song.album))
            song_id = curr.fetchone()
            if not song_id:
                curr.execute('''INSERT INTO songs (title, artist, album, duration) VALUES
                                (%s, %s, %s, %s) RETURNING song_id''',
                                (song.title, song.artist, song.album, song.duration))
                song.s_id(curr.fetchone()[0])
                self.conn.commit()
            else:
                song.s_id(song_id[0])
        return song

    def get_featured_playlist(self):
        '''
        Returns a randomly selected playlist from featured ones
        '''
        # get a random key from featured playlists
        with self.conn.cursor() as curr:
            curr.execute("SELECT playlist_id FROM playlists WHERE privacy IS NULL")
            playlist = self.get_playlist(random.choice(curr.fetchall()))
            return playlist

    def get_featured_playlists(self, n=3):
        '''
        Returns randomly chosen n featured playlists
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT playlist_id FROM playlists WHERE privacy IS NULL")
            playlists = [self.get_playlist(key) for key in random.sample(curr.fetchall(), n)]
            return playlists


    def get_playlists_by(self, user):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id
                            FROM (users INNER JOIN playlists ON playlists.creator_id = users.user_id)
                            WHERE users.nickname=%s;''', (user.username,))
            playlists = [self.get_playlist(key) for key in curr.fetchall()]
        return playlists

    def get_playlists_using_id(self, user_id):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id
                            FROM (users INNER JOIN playlists ON playlists.creator_id = users.user_id)
                            WHERE users.user_id=%s;''', (user_id,))
            playlists = [self.get_playlist(key) for key in curr.fetchall()]
        return playlists


    def get_user_tuple(self, username):
        '''
        Returns the user with given username
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM users WHERE nickname=%s", (username,))
            return curr.fetchone()

    def get_username(self, user_id):
        '''
        Returns the user with given username
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT nickname FROM users WHERE user_id=%s", (user_id,))
            return curr.fetchone()[0]


    def register_user(self, user):
        with self.conn.cursor() as curr:
            curr.execute("INSERT INTO users (nickname, email, password) VALUES (%s,%s,%s)", (user.username, user.email, user.password))
            curr.execute("SELECT user_id FROM users WHERE nickname=%s", (user.username,))
            user.id = curr.fetchone()[0]
            self.conn.commit()
        return user