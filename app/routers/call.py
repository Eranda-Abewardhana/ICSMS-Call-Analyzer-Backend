import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aioboto3
import aiofiles
import aiohttp
import boto3
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config.constants import TextMessages
from app.database.db import DatabaseConnector
from app.models.call_record import CallRecord
from app.models.action_result import ActionResult
from app.config.config import Configurations
from app.utils.data_masking import DataMasker
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.transcriber import Transcriber
from datetime import datetime

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
    action_result = ActionResult(status=True)
    print("Received filename:", file.filename)
    file_location = os.path.join(Configurations.UPLOAD_FOLDER, file.filename)

    try:
        file.file.seek(0)  # Ensure we're copying the file from the start
        with open(file_location, "wb") as file_out:
            shutil.copyfileobj(file.file, file_out)
        print("File saved successfully.")
    except Exception as e:
        print(f"Error saving file: {e}")
        return {"error": "Error saving the file."}

    await file.close()
    action_result.error_message = []
    for filename in os.listdir(Configurations.UPLOAD_FOLDER):
        filepath = os.path.join(Configurations.UPLOAD_FOLDER, filename)

        # Check if it is a file
        if os.path.isfile(filepath):
            # Specify the path to your audio file
            try:
                transcription = transcriber.transcribe_audio(filepath)
                masked_transcription = masking_analyzer.mask_text(transcription)
                print(masked_transcription)
                call_record = CallRecord(transcription=masked_transcription, call_duration=0, call_date="tody",
                                         call_recording_url="dummy URL")
                await db.add_entity(call_record)

                await upload_to_s3(filepath,Configurations.bucket_name ,filename,Configurations.aws_access_key_id,Configurations.aws_secret_access_key)

                # Remove the file after processing
                os.remove(file_location)

            except Exception as e:
                action_result.status = False
                action_result.message = TextMessages.ACTION_FAILED
                action_result.error_message.append((filename, e))

    return action_result


async def upload_to_s3(file_path, bucket_name, object_name, aws_access_key_id, aws_secret_access_key):
    try:
        async with aiofiles.open(file_path, mode='rb') as file:
            data = await file.read()
            # Create an S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )

            # Define a function to upload file in a synchronous manner
            def upload_file():
                return s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    Body=data
                )

            # Use ThreadPoolExecutor to run the synchronous S3 operation
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(executor, upload_file)

            # Check response status
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("File uploaded successfully")
            else:
                print("Error uploading file:", response)
    except Exception as e:
        print(f"Error uploading file: {e}")
