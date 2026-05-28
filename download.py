import os
from yt_dlp import YoutubeDL

from pydub import AudioSegment
from pytubefix import Search

# DOWNLOAD_PATH = 'C://Users//Nico//OneDrive//Escritorio//music'

def search_download(name, artist, output_path, result_number=0, audio_only=True):
    complete_path = os.path.join(output_path, name + ".mp3")
    if os.path.isfile(complete_path):
        print("Skipping " + name)
        return

    search_name = f'{artist} {name} lyrics'

    try:
        query = f"ytsearch{result_number}:{search_name}"

        ydl_opts = {
            'quiet': False,
            'outtmpl': os.path.join(output_path, name),
        }

        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })

        # Run yt-dlp
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])

    except Exception as e:
        print(f'Could not download: {name}, Error: {e}')
        if result_number < 5:
            print(f'Trying again, attempt {result_number + 1}')
            search_download(name, artist, output_path, result_number + 1)
        else:
            print('GAVE UP on:', name)