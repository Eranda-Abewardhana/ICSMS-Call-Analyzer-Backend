from pathlib import Path

class Configurations:
    UPLOAD_FOLDER = Path(".\data").resolve()
    SAVED_FOLDER = Path(".\mp3").resolve()
    sentiment_categories = ["Sad", "Anger", "Toxic", "Happy"]
