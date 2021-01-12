'''Database class for BeeVibe app.

Implements the required database operations using psycopg2 API, using
SQL queries.

Example:
    db = Database("url_to_database")
    playlist = db.get_playlist(playlist_id)

Todo:
    update playlist
    comment operations
    song operations
    remove_comments_from_playlist
    get_featured_playlist -> handle expiration
'''
import random
import datetime

import psycopg2 as psql

from data import *
from utils import handle_db_exception


class Database(object):
    '''Database class for communication with db server.

    Args:
        db_url (str): Database url that connection will be made with.
    '''

    def __init__(self, db_url):
        self.conn = psql.connect(db_url, sslmode='require')

    @handle_db_exception
    def get_playlist(self, key):
        '''Fetches the playlist with given key (playlist_id) from `playlists` table.

        Args:
            key (int): playlist_id of the playlist.

        Returns:
            playlist (Playlist object): The fetched playlist, None if it's not
                found or it's removed.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM playlists WHERE playlist_id=%s;",
                         (key,))
            res = curr.fetchone()
            if res is None:
                playlist = None
            else:
                curr.execute("SELECT nickname FROM users WHERE user_id=%s;",
                             (res[-1],))
                creator = curr.fetchone()[0]
                p_id, title, descr, color, commenting, privacy, expire_date, thumbnail, _ = res
                playlist = Playlist(title, creator, descr)
                playlist.page.set_color(color)
                playlist.page.set_commenting(commenting)
                playlist.page.password = privacy
                playlist.page.set_expiration(expire_date)
                playlist.metadata.set_thumbnail(thumbnail)
                playlist.s_id(p_id)

        if playlist is not None:
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
                    curr.execute('''SELECT comments.content, users.nickname, comments.publish_date
                                    FROM ((comments INNER JOIN playlists ON comments.playlist_id = playlists.playlist_id)
                                    INNER JOIN users ON comments.author_id = users.user_id)
                                    WHERE playlists.playlist_id=%s;''', (playlist.id,))
                    comments = curr.fetchall()
                    for comment_t in comments:
                        comment = Comment(*comment_t)
                        playlist.add_comment(comment)
        return playlist

    @handle_db_exception
    def remove_playlist(self, key):
        '''Removes a playlist with given playlist_id from the `playlists` table.

        Args:
            key (int): playlist_id of the playlist to be removed.
        '''
        with self.conn.cursor() as curr:
            curr.execute("DELETE FROM playlists WHERE playlist_id=%s;", (key,))
            self.conn.commit()

    @handle_db_exception
    def add_playlist(self, playlist):
        '''Adds the given playlist to the `playlists` table.

        Args:
            playlist (Playlist object): New Playlist to be added to database.

        Returns:
            playlist (Playlist object): Inserted Playlist object
                with new playlist_id updated.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT user_id FROM users WHERE nickname=%s;", (playlist.creator,))
            creator_id = curr.fetchone()[0]
            curr.execute('''INSERT INTO playlists (title, description, color, commenting, privacy, expire_date, thumbnail, creator_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING playlist_id;''',
                         (playlist.title, playlist.metadata.descr, playlist.page.color, playlist.page.commenting,
                          playlist.page.password, playlist.page.expiration, playlist.metadata.thumbnail, creator_id))
            playlist.s_id(curr.fetchone()[0])
            for song_id in playlist.songs:
                curr.execute('''INSERT INTO spmap (song_id, playlist_id, song_description) VALUES
                                (%s, %s, %s);''', (song_id, playlist.id, playlist.song_descr[song_id]))
            self.conn.commit()
        return playlist

    @handle_db_exception
    def search_playlists_by_title(self, title):
        '''Returns the corePlaylist objects of matching titles from the `playlists` table.

        Args:
            title (string): Start of the title of searched playlists.

        Returns:
            list: First 5 matching corePlaylist objects.
        '''
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id, playlists.title, users.nickname FROM playlists
                            INNER JOIN users ON users.user_id=playlists.creator_id
                            WHERE playlists.title ILIKE %s;''', (title + '%',))
            return [corePlaylist(*row) for row in curr.fetchmany(5)]

    @handle_db_exception
    def search_song_by_title(self, title):
        '''Returns the Song objects with matching title from the `songs` table.

        Args:
            title (string): Start of the title of searched songs.

        Returns:
            list: First 5 matching Song objects.
        '''
        ret_songs = []
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM songs WHERE title LIKE %s;", (title + '%',))
            for song in curr.fetchmany(5):
                ret_songs.append(Song(*song[1:]))
                ret_songs[-1].s_id(song[0])
        return ret_songs

    @handle_db_exception
    def search_playlists_by_creator(self, creator):
        '''Returns the corePlaylist objects searched with creator from the `playlists` table.

        Args:
            creator (string): Start of the creator of searched playlists.

        Returns:
            list: First 5 matching corePlaylist objects.
        '''
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id, playlists.title, users.nickname FROM playlists
                            INNER JOIN users ON users.user_id=playlists.creator_id
                            WHERE users.nickname LIKE %s;''', (creator + '%',))
            return [corePlaylist(*row) for row in curr.fetchmany(5)]


    @handle_db_exception
    def update_playlist(self, playlist):
        '''Updates a playlist in the the `playlists` table.

        Given a playlist object, updates the one in database with the same key
        with the given object.

        Args:
            playlist (Playlist object): Playlist to be updated.

        Returns:
            playlist (Playlist object): Updated Playlist object.
        '''
        with self.conn.cursor() as curr:
            print(playlist, playlist.id)
            curr.execute("SELECT color, description FROM playlists WHERE playlist_id=%s;",(playlist.id,))
            color, descr = curr.fetchone()
            color = playlist.page.color if playlist.page.color != color else color
            descr = playlist.metadata.descr if playlist.metadata.descr != descr else descr
            curr.execute('''UPDATE playlists SET
                            color=%s,
                            description=%s
                            WHERE playlist_id=%s;''',
                         (color, descr, playlist.id))
            self.conn.commit()
        return self.get_playlist(playlist.id)

    @handle_db_exception
    def add_songs_to_playlist(self, key, songs):
        '''Adds new songs to a playlist by updating the `spmap` table.

        Adds the songs given (as ids) to the playlist given (as key).

        Args:
            key (int): Playlist id that songs will be added.
            songs (list[int]): List of song ids.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        with self.conn.cursor() as curr:
            for song_id in songs:
                curr.execute('''INSERT INTO spmap (playlist_id, song_id) VALUES
                                (%s, %s);''', (key, song_id))
            self.conn.commit()
        return self.get_playlist(key)

    @handle_db_exception
    def remove_songs_from_playlist(self, key, songs):
        '''Removes songs from playlist by updating the `spmap` table.

        Removes the songs given (as ids) from the playlist given (as key).

        Args:
            key (int): Playlist id that songs will be removed from.
            songs (list[int]): List of song ids.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        with self.conn.cursor() as curr:
            for song_id in songs:
                curr.execute('''DELETE FROM spmap WHERE
                                song_id=%s AND playlist_id=%s;''',
                             (song_id, key))
            self.conn.commit()
        return self.get_playlist(key)

    @handle_db_exception
    def add_comment_to_playlist(self, key, comment):
        '''Adds a new comment to a playlist by updating the `comments` table.

        Adds the given comment to the playlist with the given id.

        Args:
            key (int): Playlist id that comment will be added to.
            comment (Comment object): New comment to be added.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT user_id FROM users WHERE nickname=%s", (comment.author,))
            curr.execute('''INSERT INTO comments (content, publish_date, author_id, playlist_id)
                            VALUES (%s, %s, %s, %s);''',
                            (comment.content, comment.date, curr.fetchone()[0], key))
            self.conn.commit()
        return self.get_playlist(key)

    @handle_db_exception
    def remove_comments_from_playlist(self, key, comment_id):
        '''Removes a comment from the playlist by updating the `comments` table.

        Removes the comment with given id from the playlist with the given id.

        Args:
            key (int): Playlist id that comment will be removed from.
            comment_id (int): ID of the comment to be removed.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        for comment in comment_id:
            pass
        return self.playlists[key]

    @handle_db_exception
    def add_song_to_database(self, song):
        '''Adds new songs to the `songs` table.

        Adds the Song objects to `songs` table in database.

        Args:
            song (Song object): Song to be added.

        Returns:
            song (Song object): Added Song with id updated.
        '''
        with self.conn.cursor() as curr:
#            if song.duration == '':
 #               song.duration = None
            curr.execute("SELECT song_id FROM songs WHERE title=%s AND artist=%s AND album=%s;", (song.title, song.artist, song.album))
            song_id = curr.fetchone()
            if not song_id:
                curr.execute('''INSERT INTO songs (title, artist, album, duration) VALUES
                                (%s, %s, %s, %s) RETURNING song_id;''',
                                (song.title, song.artist, song.album, song.duration))
                song.s_id(curr.fetchone()[0])
                self.conn.commit()
            else:
                song.s_id(song_id[0])
        return song

    @handle_db_exception
    def get_featured_playlist(self):
        '''Returns a randomly selected playlist from the `playlists` table.

        Selected playlists will be public, so they will not require passwords.

        Returns:
            playlist (Playlist object): randomly selected playlist
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT playlist_id FROM playlists WHERE privacy IS NULL;")
            playlist = self.get_playlist(random.choice(curr.fetchall()))
            return playlist

    @handle_db_exception
    def get_featured_playlists(self, n=3):
        '''Returns a randomly selected playlists from the `playlists` table.

        Selected playlists will be public, so they will not require passwords.

        Args:
            n (int): Number of playlists to be selected.

        Returns:
            playlist (list[Playlist object]): Randomly selected playlists.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT playlist_id FROM playlists WHERE privacy IS NULL;")
            playlists = [self.get_playlist(key) for key in random.sample(curr.fetchall(), n)]
            return playlists


    @handle_db_exception
    def get_playlists_by(self, user):
        '''Returns the playlists created by given user from the `playlists` table.

        Args:
            user (User object): Creator to be searched.

        Returns:
            playlists (list[Playlist]): Playlists created by that user.
        '''
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id
                            FROM (users INNER JOIN playlists ON playlists.creator_id = users.user_id)
                            WHERE users.nickname=%s;''', (user.username,))
            playlists = [self.get_playlist(key) for key in curr.fetchall()]
        return playlists

    @handle_db_exception
    def get_playlists_using_id(self, user_id):
        '''Returns the playlists created by user with user_id from the `playlists` table.

        Args:
            user_id (int): Creator to be searched.

        Returns:
            playlists (list[Playlist]): Playlists created by that user.
        '''
        with self.conn.cursor() as curr:
            curr.execute('''SELECT playlists.playlist_id
                            FROM (users INNER JOIN playlists ON playlists.creator_id = users.user_id)
                            WHERE users.user_id=%s;''', (user_id,))
            playlists = [self.get_playlist(key) for key in curr.fetchall()]
        return playlists


    @handle_db_exception
    def get_user_tuple(self, username):
        '''Returns the information of user with given username from the `users` table. 

        Args:
            username (string): Username to be searched.

        Returns:
            tuple: (user_id, nickname, email, password) information of that user.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM users WHERE nickname=%s;", (username,))
            return curr.fetchone()

    @handle_db_exception
    def get_username(self, user_id):
        '''Returns the username of user with given id from the `users` table.

        Args:
            user_id (int): ID of the user.

        Returns:
            string: username of the user.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT nickname FROM users WHERE user_id=%s;", (user_id,))
            return curr.fetchone()[0]

    @handle_db_exception
    def get_user_by_email(self, email):
        '''Returns the information of user with given email from the `users` table.

        Args:
            email (string): Email to be searched.

        Returns:
            tuple: (user_id, nickname, email, password) information of that user.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT * FROM users WHERE email=%s;", (email,))
            return curr.fetchone()


    @handle_db_exception
    def register_user(self, user):
        '''Adds a new user to the `users` table.

        Args:
            user (User object): User to be inserted to database.

        Returns:
            user (User object): User with updated id.
        '''
        with self.conn.cursor() as curr:
            curr.execute("INSERT INTO users (nickname, email, password) VALUES (%s,%s,%s) RETURNING user_id;", (user.username, user.email, user.password))
            user.id = curr.fetchone()[0]
            self.conn.commit()
        return user


    @handle_db_exception
    def check_auth(self, user_id, key):
        '''Checks if user with given id is authorized to change playlist with given id.

        Args:
            user_id (int): id of the user.
            key (int): id of the playlist.

        Returns:
            bool: True if that user created that playlist, False otherwise.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT creator_id FROM playlists WHERE playlist_id=%s;", (key,))
            if curr.fetchone()[0] == user_id:
                return True
            else:
                return False
