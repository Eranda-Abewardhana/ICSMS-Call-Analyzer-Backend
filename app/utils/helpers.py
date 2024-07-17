import re

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


def extract_call_details_from_filename(filename: str) -> tuple[int, str, str, str]:
    operator_id_text = filename.split("_")[0]
    pattern = r'\d+'
    operator_id = int(re.findall(pattern, operator_id_text)[0])
    call_date = filename.split('_')[1]
    call_time = filename.split('_')[2]
    filename_text = filename.split('.')[0]
    call_description = "_".join(filename_text.split("_")[3:])
    return operator_id, call_date, call_time, call_description


def merge_operator_analytics_over_time(operators: list[dict], analytics: list[dict]) -> list[dict]:
    data = []
    for operator in operators:
        operator_id = operator['operator_id']
        for analytic in analytics:
            operator_analytic_id = analytic['_id']
            if operator_analytic_id == operator_id:
                op_analytics = {
                    'operator_id': operator_id,
                    'operator_name': operator['name'],
                    'positive': analytic['positive_calls'],
                    'negative': analytic['negative_calls'],
                    'neutral': analytic['neutral_calls'],
                }
                data.append(op_analytics)
                break
        else:
            op_analytics = {
                'operator_id': operator_id,
                'operator_name': operator['name'],
                'positive': 0,
                'negative': 0,
                'neutral': 0,
            }
            data.append(op_analytics)
    return data
