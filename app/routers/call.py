import os
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File
from app.database.db import DatabaseConnector
from app.models.call_record import CallRecord
from app.models.action_result import ActionResult
from app.config.config import Configurations
from app.utils.data_masking import DataMasker
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.transcriber import Transcriber

call_router = APIRouter()

db = DatabaseConnector("calls")
summary_analyzer = SummaryAnalyzer()
masking_analyzer = DataMasker()
sentiment_analyzer = SentimentAnalyzer()
transcriber = Transcriber()


@call_router.post("/add-calls", response_model=ActionResult)
async def add_call_record(call_record: CallRecord):
    action_result = await db.add_entity(call_record)  # Await the coroutine
    return action_result


@call_router.get("/get-call/{call_id}", response_model=ActionResult)
async def get_call_record_by_id(call_id: str):
    action_result = await db.get_entity_by_id(call_id)
    return action_result


@call_router.delete("/delete-call/{call_id}", response_model=ActionResult)
async def delete_call_record(call_id: str):
    action_result = await db.delete_entity(call_id)
    if not action_result.success:
        raise HTTPException(status_code=404, detail="Record not found.")
    return action_result


@call_router.get("/get-all-calls", response_model=ActionResult)
async def get_all_calls():
    action_result = await db.get_all_entities()
    return action_result


@call_router.post("/uploadcalls")
async def upload_file(file: UploadFile = File(...)):
    print("Received filename:", file.filename)
    file_location = os.path.join(Configurations.UPLOAD_FOLDER, file.filename)
    print("Saving file to:", file_location)

    # Ensure the UPLOAD_FOLDER exists
    if not os.path.exists(Configurations.UPLOAD_FOLDER):
        os.makedirs(Configurations.UPLOAD_FOLDER)

    # Save the uploaded file to the specified location
    try:
        file.file.seek(0)  # Ensure we're copying the file from the start
        with open(file_location, "wb") as file_out:
            shutil.copyfileobj(file.file, file_out)
        print("File saved successfully.")
    except Exception as e:
        print(f"Error saving file: {e}")
        return {"error": "Error saving the file."}

    # Close the file object to free resources
    await file.close()

    for filename in os.listdir(Configurations.UPLOAD_FOLDER):
        filepath = os.path.join(Configurations.UPLOAD_FOLDER, filename)
        # Check if it is a file
        if os.path.isfile(filepath):
            # Specify the path to your audio file
            transcription = transcriber.transcribe_audio(filepath)
            masking = masking_analyzer.mask_text(transcription)
            sentiment_category = sentiment_analyzer.analyze(masking, Configurations.sentiment_categories)
            print(masking, sentiment_category)
            print(masking)

            if not os.path.exists(Configurations.SAVED_FOLDER):
                os.makedirs(Configurations.SAVED_FOLDER)  # Create the mp3 folder if it doesn't exist
            new_file_location = os.path.join(Configurations.SAVED_FOLDER, file.filename)
            shutil.move(file_location, new_file_location)

    return {"filename": file.filename}
