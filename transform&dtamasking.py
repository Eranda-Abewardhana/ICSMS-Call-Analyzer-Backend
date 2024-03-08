import whisper
import v2
import os

source_directory = "./mp3"

# Ensure the specified folder exists, create it if necessary
os.makedirs(source_directory, exist_ok=True)

def transcribe_audio(file_path):
    try :
    # Load the Whisper model
        model = whisper.load_model("tiny")

        # Process the audio file
        result = model.transcribe(file_path)
        anonymizer = v2.load_anonymizer("Isotonic/distilbert_finetuned_ai4privacy_v2")
        pii_masked_sentence = v2.anonymize_text(result["text"], anonymizer)

        # Print the transcription
        print("[INPUT]: ", result["text"])
        print("[PII_MASKED]: ", pii_masked_sentence)
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")


if __name__ == "__main__":
     # List all files in the directory
    for filename in os.listdir(source_directory):
        # Construct the full file path
        filepath = os.path.join(source_directory, filename)
        # Check if it is a file
        if os.path.isfile(filepath):
            # Specify the path to your audio file
               transcribe_audio(filepath)
