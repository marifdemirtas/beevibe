'''
https://developer.spotify.com/documentation/web-api/reference/playlists/get-playlist/

title: res.name
creator: current_user.username
description: res.description
songs: [song, comment]

    song: get items
    comment: null
'''

import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = 'playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.current_user_playlists(limit=50)
print(results)