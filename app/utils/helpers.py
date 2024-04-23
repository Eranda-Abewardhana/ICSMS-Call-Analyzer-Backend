from mutagen.mp3 import MP3
from mutagen.wave import WAVE


def get_audio_duration(audio_file_path: str) -> int:
    filetype = audio_file_path.split('.')[-1]
    if filetype == 'mp3':
        mp3 = MP3(audio_file_path)
        return int(mp3.info.length)

    elif filetype == 'wav':
        wav = WAVE(audio_file_path)
        return int(wav.info.length)

    else:
        raise TypeError(f'Unsupported filetype. Filetype must be either mp3 or wav')
