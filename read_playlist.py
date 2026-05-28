import pandas as pd
from dotenv import load_dotenv
import spotipy
import spotipy.util as util
import os

from utils import clean_text
from download import search_download
import re
from add_metadata import add_metadata

# The Playlist 4CM7TumLjeGl6Gkkidbb5N
# Deutsches Dump 3OyuIfUjXIfU3mcgQkUJaS
# Techno 2vtOovtunvrspYh1ei0HYw
# Svenska 49p2D6VweBSyhpbjJZ5BEx
# Mozart 5rKNrA6HljKoEzq6EmXHHs

playlist = 'Deutsches Dump'
playlist_id = '3OyuIfUjXIfU3mcgQkUJaS'


DOWNLOAD_PATH = 'C:\\Users\\Nico\\OneDrive\\Escritorio\\music'

# Spotify login
load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:8080'
scope = 'user-library-read'
username = 'Franz Peter Schubert'

# PATTERN = '[^A-Za-z0-9]+öÖäÄüÜ'

token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)  # TODO Don't let this here
# token = auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, username=username, scope=scope)
sp = spotipy.Spotify(auth=token)

full_path = os.path.join(DOWNLOAD_PATH, "playlist")
if not os.path.isdir(full_path):
    os.makedirs(full_path)



def get_playlist_tracks(username, playlist_id):
    results = sp.user_playlist_tracks(username, playlist_id)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return clean_names(tracks)


def get_playlist_tracks(csv_filename):
    df_playlist = pd.read_csv(csv_filename)

    output_songs = []

    for index, row in df_playlist.iterrows():
        output_songs.append({
            "name": clean_text(row['Track name']),
            "artist": clean_text(row['Artist name']),
            "id": row['Spotify - id']
        })

    return output_songs



def get_favourite_songs():
    offset = 0
    tracks = []
    while offset < 1000:
        results = sp.current_user_saved_tracks(offset=offset, limit=50)
        tracks.extend(results['items'])
        offset += 50
    return clean_names(tracks)


def remove_song_from_playlist(song):
    pass

ILLEGAL_SET_OF_CHARACTERS = '\\/:*?<>|"'
def remove_characters(string ,characters_to_remove):
    for character in characters_to_remove:
            string = string.replace(character, '').strip()
    string = string[:-1] if string.endswith('.') else string
    return string

def clean_names(tracks):
    return_list = []
    print(len(tracks))
    for info in tracks:
        dictionary_inside_list = {
            "name": remove_characters(info['track']['name'], ILLEGAL_SET_OF_CHARACTERS),
            "artist": info['track']['artists'][0]['name'],
            "album": info['track']['album']['name'],
            "picture": info['track']['album']['images'][0]["url"]}
            # "name": re.sub(PATTERN, ' ', info['track']['name']).replace("/", "").replace("<", "").replace(":", ""),
            # "artist": re.sub(PATTERN, ' ', info['track']['artists'][0]['name']).replace("/", ""),
            # "album": re.sub(PATTERN, ' ', info['track']['album']['name']).replace("/", ""),
            # "picture": re.sub(PATTERN, ' ', info['track']['album']['images'][0]["url"])}
        return_list.append(dictionary_inside_list)
    return return_list

# get_playlist_tracks(username, playlist_id)

# music_list = get_playlist_tracks(username, playlist_id)
# get_favourite_songs()

# print(music_list)
# for i in music_list:
#     if music_list.count(i) > 1:
#         remove_song_from_playlist(i)

output_path = os.path.join(DOWNLOAD_PATH, playlist)
# print(music_list)
# for progress, music_data in enumerate(music_list):
#     print(progress + 1, '/', len(music_list))
#     search_download(music_data["name"], music_data["artist"], output_path)

# print("Finished! Adding metadata...")

# for progress, music_data in enumerate(music_list):
#     print(progress + 1, '/', len(music_list))
#     song_path = os.path.join(output_path, music_data["name"] + ".mp3")
#     add_metadata(song_path, music_data["name"], music_data["artist"], music_data["album"],
#                  music_data["picture"])



