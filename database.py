from data import *

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

playlists[1] = Playlist("gece", "arif")
playlists[2] = Playlist("doğum", "mehmet")
playlists[3] = Playlist("köprü", "demir")

playlists[1].metadata.set_descr("This is about the night")
playlists[2].metadata.set_descr("Best played at sunrise")

playlists[1].page.color = "#0a0022"
playlists[2].page.color = "#af220a"
playlists[3].page.color = "#0f1088"

playlists[1].page.commenting = True
playlists[2].page.commenting = False
playlists[3].page.commenting = True
playlists[3].comments = [Comment("I loved it", "jeff"), Comment("Didn't liked it that much", "nick")]

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
        self.song_id = 0
        self.playlist_id = 0

    def get_playlist(self, key):
        playlist = self.playlists.get(key, 321).copy()
        if playlist is not None:
            for song_id in self.plmap[key]:
                playlist.add(self.get_song(song_id))
        return playlist

    def del_playlist(self, key):
        if key in playlists:
            del playlists[key]

    def update_playlist(self, key, song_id):
        if key in playlists:
            playlists[key].add_song(song_id)

    def add_song(self, song):
        if song not in self.songs:
            song.set_id(self.song_id)
            self.songs[self.song_id] = song
            self.song_id += 1

    def search_song_by_name(self, song_name):
        pass

    def get_song(self, song_id):
        return self.songs.get(song_id)

    def del_song(self, song_id):
        pass