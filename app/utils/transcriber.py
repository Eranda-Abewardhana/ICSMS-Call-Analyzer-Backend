import whisper
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


class Transcriber:
    def __init__(self):
        self.__model = whisper.load_model("tiny")

    def transcribe_audio(self, file_path: str) -> str:
        result = self.__model.transcribe(file_path)
        return result["text"]
