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
                p_id, title, descr, color, commenting, privacy, expire_date, _, _ = res
                playlist = Playlist(title, creator, descr)
                playlist.page.set_color(color)
                playlist.page.set_commenting(commenting)
                playlist.page.password = privacy
                playlist.page.set_expiration(expire_date)
                playlist.s_id(p_id)
                curr.execute("SELECT ENCODE(playlists.thumbnail, 'base64') FROM playlists WHERE playlist_id=%s", (playlist.id,))
                img = curr.fetchone()[0]
                if img is not None:
                    playlist.metadata.set_thumbnail("data:image/png;base64," + img)

        if playlist is not None:
            if playlist.page.expiration is not None and playlist.page.expiration < datetime.datetime.now():
                self.remove_playlist(playlist.id)
                playlist = None
            else:
                with self.conn.cursor() as curr:
                    curr.execute('''SELECT songs.song_id, songs.title, songs.artist, songs.album, songs.duration, songs.release_year, songplaylist_map.song_description
                                    FROM (songplaylist_map INNER JOIN songs ON songs.song_id = songplaylist_map.song_id)
                                    WHERE songplaylist_map.playlist_id=%s;''', (playlist.id,))
                    songs = curr.fetchall()
                    for song_t in songs:
                        song = Song(*song_t[1:-1])
                        song.s_id(song_t[0])
                        playlist.add(song, song_t[-1])
                    curr.execute('''SELECT comments.comment_id, comments.content, users.nickname, comments.publish_date
                                    FROM ((comments INNER JOIN playlists ON comments.playlist_id = playlists.playlist_id)
                                    INNER JOIN users ON comments.author_id = users.user_id)
                                    WHERE playlists.playlist_id=%s;''', (playlist.id,))
                    comments = curr.fetchall()
                    for comment_t in comments:
                        comment = Comment(*comment_t[1:])
                        comment.id = comment_t[0]
                        playlist.add_comment(comment)
            playlist.total_duration = self.get_total_duration_of_playlist(playlist.id)
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
                          playlist.page.password, playlist.page.expiration, psql.Binary(playlist.metadata.thumbnail),
                          creator_id))
            playlist.s_id(curr.fetchone()[0])
            for song_id in playlist.songs:
                curr.execute('''INSERT INTO songplaylist_map (song_id, playlist_id, song_description) VALUES
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
            curr.execute("SELECT * FROM songs WHERE title ILIKE %s;", (title + '%',))
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
                            WHERE users.nickname ILIKE %s;''', (creator + '%',))
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
            curr.execute("SELECT color, description FROM playlists WHERE playlist_id=%s;",(playlist.id,))
            color, descr = curr.fetchone()
            color = playlist.page.color if playlist.page.color != color else color
            descr = playlist.metadata.descr if playlist.metadata.descr != descr else descr
            curr.execute('''UPDATE playlists SET
                            color=%s,
                            description=%s,
                            commenting=%s
                            WHERE playlist_id=%s;''',
                         (color, descr, playlist.page.commenting, playlist.id))
            self.conn.commit()
        return self.get_playlist(playlist.id)

    @handle_db_exception
    def add_song_to_playlist(self, key, song, descr=None):
        '''Adds new songs to a playlist by updating the `songplaylist_map` table.

        Adds the songs given (as ids) to the playlist given (as key).

        Args:
            key (int): Playlist id that songs will be added.
            songs (int): Song id.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        with self.conn.cursor() as curr:
            if descr:
                curr.execute('''INSERT INTO songplaylist_map (playlist_id, song_id, song_description) VALUES
                                (%s, %s, %s);''', (key, song, descr))
            else:
                curr.execute('''INSERT INTO songplaylist_map (playlist_id, song_id) VALUES
                                (%s, %s);''', (key, song))
            self.conn.commit()
        return self.get_playlist(key)

    @handle_db_exception
    def remove_songs_from_playlist(self, key, songs):
        '''Removes songs from playlist by updating the `songplaylist_map` table.

        Removes the songs given (as ids) from the playlist given (as key).

        Args:
            key (int): Playlist id that songs will be removed from.
            songs (list[int]): List of song ids.

        Returns:
            playlist (Playlist object): The updated playlist.
        '''
        with self.conn.cursor() as curr:
            for song_id in songs:
                curr.execute('''SELECT * FROM songplaylist_map WHERE
                                song_id=%s;''', (song_id,))
                if len(curr.fetchmany(5)) == 1:
                    curr.execute('''DELETE FROM songs WHERE
                                    song_id=%s''', (song_id,))
                else:
                    curr.execute('''DELETE FROM songplaylist_map WHERE
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
        with self.conn.cursor() as curr:
            for comment in comment_id:
                curr.execute("DELETE FROM comments WHERE comment_id=%s", (comment,))
            self.conn.commit()
        return self.get_playlist(key)

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
                curr.execute('''INSERT INTO songs (title, artist, album, duration, release_year) VALUES
                                (%s, %s, %s, %s, %s) RETURNING song_id;''',
                                (song.title, song.artist, song.album, song.duration, song.release_year))
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
            avg_playlist = self.get_featured_playlist_duration_avg(*playlists)
            return playlists, avg_playlist


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
            curr.execute('''SELECT playlist_id
                            FROM playlists WHERE creator_id=%s;''', (user_id,))
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
    def delete_user(self, user_id):
        '''Delete user

        Args:
            user_id (int): ID of user.
        '''
        with self.conn.cursor() as curr:
            curr.execute("DELETE FROM users WHERE user_id=%s;", (user_id,))
            self.conn.commit()

    @handle_db_exception
    def register_user(self, user):
        '''Adds a new user to the `users` table.

        Args:
            user (User object): User to be inserted to database.

        Returns:
            user (User object): User with updated id.
        '''
        with self.conn.cursor() as curr:
            curr.execute("INSERT INTO users (nickname, email, password, public, register_date) VALUES (%s,%s,%s,%s,%s) RETURNING user_id;", (user.username, user.email, user.password, user.public, user.register_date))
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

    @handle_db_exception
    def is_user_private(self, user_id):
        '''Checks if user with given id has a private profile.

        Args:
            user_id (int): id of the user.

        Returns:
            bool: True if that user is private, False otherwise.
        '''
        with self.conn.cursor() as curr:
            curr.execute("SELECT public FROM users WHERE user_id=%s;", (user_id,))
            if curr.fetchone()[0] is True:
                return False
            else:
                return True

    @handle_db_exception
    def set_public_profile(self, user_id, value):
        '''Sets the user profile publicity to given value
        '''
        with self.conn.cursor() as curr:
            curr.execute("UPDATE users SET public=%s WHERE user_id=%s;", (value, user_id,))
            self.conn.commit()

    @handle_db_exception
    def get_all_playlist_durations_user(self, user_id):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT SUM(songs.duration) FROM 
                            ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id)
                            WHERE playlists.creator_id=%s''', (user_id,))
            res = curr.fetchone()[0]
            if res is None:
                res = 0
            return res

    @handle_db_exception
    def get_total_duration_of_playlist(self, playlist_id):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT SUM(songs.duration) FROM ((playlists INNER JOIN songplaylist_map 
                            ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.playlist_id=%s;
                        ''', (playlist_id,))
            res = curr.fetchone()[0]
            if res is None:
                res = 0
            return res


    @handle_db_exception
    def get_featured_playlist_duration_avg(self, id1, id2, id3):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT AVG(united.sum) FROM (
                            (SELECT SUM(songs.duration) FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.playlist_id=%s) UNION 
                            (SELECT SUM(songs.duration) FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.playlist_id=%s) UNION
                            (SELECT SUM(songs.duration) FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.playlist_id=%s)
                            ) AS united;
                            ''', (id1.id, id2.id, id3.id))
            res = curr.fetchone()[0]
            if res is None:
                res = 0
            return res

    #for finding common songs
    @handle_db_exception
    def get_common_songs(self, user_id, current_id):
        with self.conn.cursor() as curr:
            curr.execute('''SELECT * FROM ((SELECT songs.title FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.creator_id=%s) INTERSECT (SELECT songs.title FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id) WHERE playlists.creator_id=%s)) AS new_set;''', (user_id, current_id))
            return curr.fetchall()

    #for finding top 3 artists
    @handle_db_exception
    def get_top_three_artists(self, user_id):
        '''Returns the top 3 artists in all of players playlists
        '''
        with self.conn.cursor() as curr:
            curr.execute('''SELECT count(songs.title) as song_count, songs.artist 
                            FROM ((playlists INNER JOIN songplaylist_map ON songplaylist_map.playlist_id=playlists.playlist_id)
                            INNER JOIN songs ON songplaylist_map.song_id=songs.song_id)
                            WHERE playlists.creator_id=%s GROUP BY songs.artist ORDER BY song_count DESC LIMIT 3;''', (user_id,))
            return curr.fetchall()
