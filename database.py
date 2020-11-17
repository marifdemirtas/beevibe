from data import Object

class Database(object):

    def __init__(self):
        self.playlists = {}
        self.songs = {}
        self.song_id = 0
        self.playlist_id = 0

    def get_playlist(self, key):
        playlist = self.playlists.get(key)
        if playlist is None:
            return None
        else:
            return playlist

    def del_playlist(self, key):
        if key in playlists:
            del playlists[key]

    def update_playlist(self, key, song_id):
        if key in playlists:
            playlists[key].add_song(song_id)

    def get_playlist(self, key):
        return self.playlists.get(key)

    def add_song(self, song):
        if song not in self.songs:
            song.set_id(self.song_id)
            self.songs[self.song_id] = song
            self.song_id += 1

    def search_song_by_name(self, song_name):

    def get_song(self, song_id):

    def del_song(self, song_id)