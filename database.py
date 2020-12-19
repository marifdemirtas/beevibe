from data import *
import random

users = {
    'ali': (1, "ali@gmail.com", "ali", "HASHali"),
    'ayşe': (2, "ayse@gmail.com", "ayşe", "HASHayse")
}

songs = {}

songs[0] = Song("Tütün Kâıt", "Ethnique Punch", "Sarhoş Baykuş", 228)
songs[1] = Song("Midnight", "Lianne La Havas", "Live at Sofar", 290)
songs[2] = Song("Bittersweet", "Lianne La Havas", "Lianne La Havas", 228)
songs[3] = Song("Hallelujah", "Jeff Buckley", "Grace", None)
songs[4] = Song("Dagenham Dream", "Blood Orange", "Negro Swan", 192)
songs[5] = Song("Oi Va Voi", "Refugee", "Live at VPRO", 422)
songs[6] = Song("Borderline", "Tame Impala", "The Slow Rush", 228)
songs[7] = Song("The Sky is Crying", "Gary B.B. Coleman", None, 554)
songs[8] = Song("No Surprises", "Radiohead", "OK Computer", None)
songs[9] = Song("Like Someone in Love", "Bill Evans", None, None)

for key in songs:
    songs[key].s_id(key)

playlists = {}

playlists[1] = Playlist("gece", "ali")
playlists[2] = Playlist("doğum", "ali")
playlists[3] = Playlist("köprü", "ayşe")

playlists[1].metadata.set_descr("This is about the night")
playlists[2].metadata.set_descr("Best played at sunrise")

playlists[1].page.set_color("#0a0022")
#playlists[2].page.set_color("#af220a")
playlists[2].page.set_color("#aaffff")
playlists[3].page.set_color("#0f1088")

playlists[1].page.set_commenting(True)
playlists[2].page.set_commenting(False)
playlists[3].page.set_commenting(True)
playlists[3].comments = [Comment("I loved it", "jeff"), Comment("Didn't liked it that much", "nick")]

playlists[3].comments[1].s_id(1)
playlists[3].comments[0].s_id(0)

for key in playlists:
    playlists[key].s_id(key)


plmap = {} #playlist song map - playlist_id: song_id
plmap[1] = [1, 6, 8, 5]
plmap[2] = [2, 4, 5, 6]
plmap[3] = [9, 7, 8, 0, 4]

class Database(object):

    def __init__(self):
        self.playlists = playlists
        self.songs = songs
        self.plmap = plmap
        self.song_id = 10
        self.playlist_id = 0

    def get_playlist(self, key):
        '''
        Fetches the playlist with given key, returns Playlist object
        '''
        playlist = self.playlists.get(key)
        if playlist is None:
            return playlist
        else:
            playlist = playlist.copy()
            for song_id in self.plmap[key]:
                playlist.add(self.get_song(song_id))
        return playlist

    def add_playlist(self, playlist):
        '''
        Adds the given playlist to the db
        '''
        playlist.s_id(5)
        self.playlists[5] = playlist
        self.plmap[5] = []
        # update mappings, create id etc.
        # return updated playlist
        return playlist

    def search_playlists_by_title(self, title):
        '''
        Returns the corePlaylist objects related with title.
        '''
        # search database for title and return the matching
        # for playlist in query_results
        #   build corePlaylists
        res = [corePlaylist(1, "gece", "arif")]
        return res

    def search_playlists_by_creator(self, creator):
        '''
        Returns the corePlaylist objects related with creator.
        '''
        # search database for title and return the matching
        # for playlist in query_results
        #   build corePlaylists
        res = [corePlaylist(1, "gece", "arif")]
        return res

    def del_playlist(self, key):
        '''
        Deletes the playlist with given key.
        '''
        if key in playlists:
            del playlists[key] # cascade to other tables

    def update_playlist(self, playlist):
        '''
        Given a playlist object, updates the one in database with the same key
        with the given object.
        '''        
        db_playlist = self.get_playlist(playlist.key)
        # for diff_attr in (db_playlist, playlist)
        #    update database accordingly

    def add_songs_to_playlist(self, key, songs):
        '''
        Adds the songs given (as ids) to the playlist given (as key).
        Returns the updated playlist.
        '''
        if key in playlists:
            for song_id in songs:
                plmap[key].append(song_id)
                # update plmap
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
        self.playlists[key].add_comment(comment)
        # update playlist-comment mapping
        return self.playlists[key]

    def remove_comments_from_playlist(self, key, comment_id):
        '''
        Adds a comment by an user to the database
        '''
        for comment in comment_id:
            self.playlists[key].delete_comment(comment)
        # update playlist-comment mapping
        return self.playlists[key]

    def add_song_to_database(self, song):
        '''
        Adds a given song object to the database
        '''
        song.s_id(self.song_id)
        self.song_id += 1
        songs[song.id] = song
        # add song to songs database
#        db_id = 5 # get the id back
#        song.s_id(db_id)
        return song

    def get_song(self, song_id):
        '''
        Gets the song with the given id from the database
        '''
        song = self.songs.get(song_id)
        if song is None:
            return None
        else:
            return song.copy()

    def del_song(self, song_id):
        '''
        Deletes the song with the given id from the database
        '''
        # remove song_id from songs

    def get_featured_playlist(self):
        '''
        Returns a randomly selected playlist from featured ones
        '''
        # get a random key from featured playlists
        return self.get_playlist(random.choice([1,2,3]))

    def get_featured_playlists(self, n=15):
        '''
        Returns randomly chosen n featured playlists
        '''
        featured = []
        for i in range(max(n, 3)): #3 = len of playlists
            fpl = self.get_featured_playlist()
            while(fpl in featured):
                fpl = self.get_featured_playlist()
            featured.append(fpl)
        return [playlists[1], playlists[2], playlists[3]]

    def get_playlists_by(self, user):
        res_playlists = []
        #SELECT * FROM playlists WHERE creator_id = (SELECT user_id FROM users WHERE username=user.name)
        for pl in playlists:
            if playlists[pl].creator == user.username:
                res_playlists.append(playlists[pl])
        return res_playlists


    def get_user_tuple(self, user_id):
        return users.get(user_id)

    def register_user(self, user):
        users[user.username] = (user.id, user.email, user.username, user.password)
        return user
