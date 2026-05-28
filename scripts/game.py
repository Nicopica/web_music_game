import pandas as pd
import webbrowser
import random
import time

file_game = ("game/playlist_months.csv")

try:
    df_playlist = pd.read_csv(file_game)

    print(f"\n Game mode: {file_game}")

    quantity = min(10, len(df_playlist))
    songs = df_playlist.sample(n=quantity)

    for index, s in songs.iterrows():
        name = s['name']
        artist = s['artist']
        words = s['foundWords']
        sentences = s['matchedLines']
        link = s['link']

        if "track/" in link:
            track_id = link.split("track/")[-1].split("?")[0]
            link = f"spotify:track:{track_id}"

        webbrowser.open(link)

        # wait for input
        input("ENTER for next song...")

        print(f"Artist: {artist}, song: {name}\n"
              f"Answers: {words}\n"
              f"Sentences: {sentences}\n")

except FileNotFoundError:
    print(f"File {file_game} not found")