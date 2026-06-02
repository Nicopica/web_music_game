from scripts.ProcessorPlaylsit import ProcessorPlaylist
from utils.utils import dictionary_languages


def main():
    not_processed = {}

    for lang_code in dictionary_languages.keys():
        processor = ProcessorPlaylist(lang_code)
        processor.execute()

        if processor.notProcessed:
            not_processed[lang_code] = processor.notProcessed

    print("Finished!")

    if not_processed:
        print("Not processed songs per language:")
        for lang, errors in not_processed.items():
            print(f"- {lang.upper()}: {len(errors)} songs ({errors})")

if __name__ == '__main__':
    main()