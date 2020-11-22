'''
Defines data models for: songs, playlists
'''
import copy
import datetime


class Song(object):
    '''
    An object representing a song.

    Attrs:
    id: A unique id for the song, generated by the creator
    title: name of the song
    artist: main artist of the song
    album: album in which the song is found
    duration: length of the song in seconds
    '''

    def __init__(self, title, artist, album, duration):
        self.id = None
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration

    def __iter__(self):
        return iter((self.id, self.title,
                     self.artist, self.album, self.duration))

    def to_dict(self):
        song = {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration
        }
        return song

    def get(self):
        return self.to_dict()

    def copy(self):
        return copy.deepcopy(self)

    def s_id(self, s_id=None):
        if s_id is not None:
            self.id = s_id
        return self.id


class Playlist(object):
    '''
    A base object for playlists of different kinds.

    Attrs:
    id: A unique id for the playlist, generated by the creator
    title: Name for the playlist
    descr: Description of the playlist
    creator: Creator of the playlists

    songs: List of songs in the playlists
    song_descr: Dict of descriptions for each song, indexed by id
    '''

    def __init__(self, title, creator, descr=""):
        self.id = None
        self.title = title
        self.creator = creator
        self.songs = list()
        self.song_descr = dict()
        self.size = 0
        self.page = PlaylistPage()
        self.comments = []

        self.metadata = Metadata()
        self.metadata.set_descr(descr)

    def add(self, song, descr=""):
        self.songs.append(song)
        self.song_descr[song.id] = descr
        self.size += 1

    def update_song_descr(self, song, descr):
        self.song_descr[song.id] = descr

    def remove_song(self, song):
        if song in self.songs:
            deleted_song = self.songs.pop(song)
            del self.song_descr[song.id]
            self.size -= 1
            return deleted_song
        else:
            raise ValueError("Song not found")

    def add_comment(self, comment):
        pass

    def id(self, p_id=None):
        if p_id is not None:
            self.id = p_id
        return self.id

    def __iter__(self):
        return PlaylistIterator(self)

    def __next__(self):
        pass


class PlaylistIterator:
    '''
    Iterator for playlists
    '''

    def __init__(self, playlist):
        self.playlist = playlist
        self.index = 0

    def __next__(self):
        if self.index < self.playlist.size:
            self.index += 1
            return self.playlist.songs[self.index - 1].get()
        else:
            raise StopIteration()


class PlaylistPage:
    '''
    Stores the settings related to the page that will display the playlist
    '''

    def __init__(self, color=None, commenting=False):
        self.color = color # 7 character hex string: #RRGGBB
        self.commenting = commenting


class Comment:
    '''
    Helper class that contains a comment, its author, date
    '''

    def __init__(self, content, author, date=None):
        self.content = content
        self.author = author
        if date:
            self.date = date
        else:
            self.date = datetime.datetime.now()

class Metadata:
    '''
    Helper class that contains some metadata about playlists
    '''

    def __init__(self, descr=None, image=None):
        self.image = image
        self.descr = descr
        self.status = False
        if descr or image:
            self.status = True

    def set_descr(self,content):
        self.descr = content
        self.status = True

    def set_thumbnail(self,img):
        self.thumbnail = img
        self.status = True
