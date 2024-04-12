import os
import random
import shutil
import string
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aioboto3
import aiofiles
import aiohttp
import boto3
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config.constants import TextMessages
from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.models.action_result import ActionResult
from app.config.config import Configurations
from app.routers.analytics import AnalyticsRouter
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
analytics_router = AnalyticsRouter()


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


@call_router.delete("/delete-call-list/{call_id}&{analytics_id}", response_model=ActionResult)
async def delete_call_record(call_id: str, analytics_id: str):
    action_result_call = await db.delete_entity(call_id)
    action_result_analytics = await analytics_router.delete_analytics_record(analytics_id)

    if not action_result_call.status and action_result_analytics.status:
        raise HTTPException(status_code=404, detail="Record not found.")
    return action_result_call and action_result_analytics


@call_router.get("/get-all-calls", response_model=ActionResult)
async def get_all_calls():
    action_result = await db.get_all_entities()
    return action_result


@call_router.get("/get-calls-list", response_model=ActionResult)
async def get_calls_list():
    call_collection_result = await db.get_all_entities()
    analytics_collection_result = await analytics_router.get_all_analytics()

    # Check if the results are successful
    if not call_collection_result.status or not analytics_collection_result.status:
        return {"error": "Failed to fetch collections"}

    # Access the data from the result objects
    call_collection = call_collection_result.data
    analytics_collection = analytics_collection_result.data

    # Check if data is present in both collections
    if not call_collection or not analytics_collection:
        return {"error": "No data found in one or both collections"}

    # Adjust the code to handle data appropriately
    merged_data = []
    for call_record in call_collection:
        for analytics_record in analytics_collection:
            if call_record["code"] == analytics_record["call_code"]:
                merged_record = {
                    "call_id": call_record["_id"]["$oid"],
                    "analytics_id": analytics_record["_id"]["$oid"],
                    "description": call_record['description'],
                    "transcription": call_record['transcription'],
                    "call_recording_url": call_record['call_recording_url'],
                    "call_duration": call_record['call_duration'],
                    "call_date": call_record['call_date'],
                    "call_code": call_record['code'],
                    "sentiment_category": analytics_record['sentiment_category'],
                    "keywords": analytics_record['keywords'],
                    "summary": analytics_record['summary'],
                    "sentiment_score": analytics_record['sentiment_score']
                }
                merged_data.append(merged_record)
                break  # Break the inner loop once a match is found

    return ActionResult(data=merged_data)


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
                print('Masked Data ' + masked_transcription)
                summary = summary_analyzer.generate_summary(masked_transcription)
                print('Summary Data ' + summary)
                sentiment = sentiment_analyzer.analyze(transcription, Configurations.sentiment_categories)
                print('Sentiment Data ' + sentiment)
                # sentiment_score = sentiment_analyzer.analyze_sentiment(transcription)
                #
                # print('Sentiment Score ' + sentiment_score)
                code = generate_random_string(16)
                call_record = CallRecord(code=code, description=filename, transcription=masked_transcription,
                                         call_duration=0,
                                         call_date="today",
                                         call_recording_url="https://call-analytics-bucket.s3.ap-south-1.amazonaws.com/mr%20john_20240403_183000_mr%20john.mp3?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCmV1LW5vcnRoLTEiRzBFAiA7IwmgpjZGnDy9KC9RMIvqHyRDg7iLE0j2PAdchUyfXAIhAK5R92ZaI%2Bm%2BVCyegbLmjnJ0%2BhU0zbsw6pxCowI8eNStKv0CCEEQARoMNjIwNzQ5OTAwMDY2Igz3cfpSmCJ%2BrkoJXkEq2gIDbWVmUiuwJ68ZoFS%2F%2B5vJskn6w4d2Eq%2F3YFM7td2MUGzmGGUc5evLna04e1Yov5FHX8sIN9gN0PWFxyzyceXF33qKl6AdHZwrCp2Jtx%2BCP7BbCGNbKzkRMKTYF8%2FGGrgG21mO2EQdqDCCX83SBHZZ%2BMdxRPswSd26Th%2FTU2zpI0vjRWFeClDDrFv9lbDeTDkOAMDlnhU8%2BguAAqYrYM0u7jqTyQaXVjg6Kq1TeTJjHPaDT9ynwWNcJFSM9WGBc6YY7kKL25VzBlrVjmtxpr1vsFSoxLlUuw8ub4oSlBULbNRcWPW2NxYQuqP5Vqaab%2BCIp34Ylj0M9%2FlBTkiqL1R4Nwib1gDjKd8YJL9oyGujcg7xMezeEdDdrpfpAyGJoytFNLdKbJFbcA3xjhSjmYuHvYu6qH23Zi8ded3pxB%2BbDVLlxg%2FVQuRbcC628XUc0aY9EfURPGNFgTpZMOuy3rAGOrMCwDNBxwGtCLypG3gLVxIz91KDo78WkwDDBpi6rpu%2FSgVjt62qrXhDu2FHaF8FNp5gQ4wH5L29B9vN6yirPIT8x4fZfr%2FfeDvGq%2Ff%2Bg1nJRkBoZCZVQ3isxlEFvSzfkGnTZgdoHxLePGb1%2F3HZB719ZYi47gXmQ7y%2BpDYUnsb1arUxyORPwmG%2BlNzWoEONl%2BzbyteTdqc9iacsycrY40oDzso6RzK5L777XE%2Bkc8DyEhf1CHDJ4T3f15CYErgHOziT1SG%2FrSBOcdcnUoSvPgVqOnJRrlYxsZSByWLkBrHpSWHHUAxzz61LgtpQeahvhkknUK%2BwhI9QITKG3YSfCUxAmYhAJXf%2FFaRHMxdIIKnlqaxAbOyDoqpR5kT%2BpGWVMO4%2BR40dFbFIF38MO3GUQ7ZRdbxC5Q%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240411T143459Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIAZBB4TZERPGMLYVP4%2F20240411%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Signature=5cf1b80d4dfa8faba0c13aa052e3dd99cdd8e6b7cb6dc02cb9954ecfdbe417e2")

                await add_call_record(call_record)

                analyzer_record = AnalyticsRecord(call_code=code, sentiment_category=sentiment,
                                                  keywords=['dummy keywords'], summary=summary, sentiment_score=0.2)

                await analytics_router.add_analytics_record(analyzer_record)

                await upload_to_s3(filepath, Configurations.bucket_name, filename, Configurations.aws_access_key_id,
                                   Configurations.aws_secret_access_key)

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


def generate_random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))
