import whisper
import data_masking
import os

from app.config.config import Configurations


def transcribe_audio(file_path):
    # Load the Whisper model
    model = whisper.load_model("tiny")

    # Process the audio file
    result = model.transcribe(file_path)
    anonymizer = data_masking.load_anonymizer("Isotonic/distilbert_finetuned_ai4privacy_v2")
    pii_masked_sentence = data_masking.anonymize_text(result["text"], anonymizer)

    # Print the transcription
    print("[INPUT]: ", result["text"])
    print("[PII_MASKED]: ", pii_masked_sentence)


if __name__ == "__main__":
    # List all files in the directory
    for filename in os.listdir(Configurations.UPLOAD_FOLDER):
        # Construct the full file path
        filepath = os.path.join(Configurations.UPLOAD_FOLDER, filename)
        # Check if it is a file
        if os.path.isfile(filepath):
            # Specify the path to your audio file
            transcribe_audio(filepath)
