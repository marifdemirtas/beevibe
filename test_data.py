import unittest

from data import Song, Playlist, PlaylistIterator

class TestSong(unittest.TestCase):

    def setUp(self):
        self.s1 = Song(title="SongTitle1",
                       artist="Artist1",
                       album="Album1",
                       duration=120)
        self.s1.s_id(25)

    def test_creation(self):
        self.assertTrue(isinstance(self.s1, Song))

    def test_id(self):
        self.assertEqual(25, self.s1.id)
        self.s1.s_id(30)
        self.assertEqual(30, self.s1.id)

    def test_unpacking(self):
        self.assertEqual((25, "SongTitle1", "Artist1", "Album1", 120),
                         (*self.s1,))

    def test_copy(self):
        self.assertIsNot(self.s1, self.s1.copy())
        self.assertEqual((*self.s1,), (*(self.s1.copy()),))

    def test_get(self):
        expectedDict = {"id": 25,
                        "title": "SongTitle1",
                        "artist": "Artist1",
                        "album": "Album1",
                        "duration": 120}
        self.assertEqual(expectedDict, self.s1.get())


class TestPlaylist(unittest.TestCase):

    def setUp(self):
        self.s1 = Song(title="SongTitle1",
                       artist="Artist1",
                       album="Album1",
                       duration=120)
        self.s2 = Song(title="SongTitle1",
                       artist="Artist1",
                       album="Album1",
                       duration=120)
        self.s3 = Song(title="SongTitle1",
                       artist="Artist1",
                       album="Album1",
                       duration=120)
        self.s1.s_id(25)
        self.s2.s_id(30)
        self.s3.s_id(35)
        self.p1 = Playlist(creator="creator1",
                           title="title1",
                           descr="this is a Playlist")

    def test_empty(self):
        c = 0
        for song in self.p1:
            c += 1
        self.assertEqual(c, 0)

    def test_adding_single(self):
        self.p1.add(self.s1)
        c = 0
        for song in self.p1:
            self.assertEqual(song.get(), self.s1.get())
            c += 1
        self.assertEqual(c, 1)

    def test_adding_multiple(self):
        for song in [self.s1, self.s2, self.s3]:
            self.p1.add(song)
        c = 0
        for song, orig_song in zip(self.p1, [self.s1, self.s2, self.s3]):
            c += 1
            self.assertEqual(song.get(), orig_song.get())


if __name__ == "__main__":
    unittest.main()
