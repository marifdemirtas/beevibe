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
        self.s1.s_id(30)
        self.s1.s_id(35)


if __name__ == "__main__":
    unittest.main()
