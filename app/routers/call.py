import os
import shutil
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config.config import Configurations
from app.config.constants import TextMessages
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.models.s3_request import S3Request
from app.utils.data_masking import DataMasker
from app.utils.helpers import get_audio_duration
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.s3 import upload_to_s3
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.transcriber import Transcriber

call_router = APIRouter()

db = DatabaseConnector("calls")
analytics_db = DatabaseConnector("analytics")

summary_analyzer = SummaryAnalyzer()
masking_analyzer = DataMasker()
sentiment_analyzer = SentimentAnalyzer()
transcriber = Transcriber()
keyword_extractor = KeywordExtractor()


@call_router.get("/get-call/{call_id}", response_model=ActionResult)
async def get_call_record_by_id(call_id: str):
    action_result = await db.get_entity_by_id(call_id)
    return action_result


@call_router.put("/update-call-url", response_model=ActionResult)
async def update_call_url(s3_request: S3Request):
    action_result = await db.get_entity_by_id(s3_request.call_id)
    if action_result.status:
        existing_record = action_result.data
        existing_call_record: CallRecord = CallRecord(_id=s3_request.call_id,
                                                      description=existing_record["description"],
                                                      transcription=existing_record['transcription'],
                                                      call_recording_url=s3_request.call_url,
                                                      call_duration=existing_record['call_duration'],
                                                      call_date=datetime.strptime(existing_record['call_date']['$date'],
                                                                                  '%Y-%m-%dT%H:%M:%SZ'),
                                                      operator_id=existing_record['operator_id'])
        result = await db.update_entity(existing_call_record)
        return result
    return action_result


@call_router.delete("/delete-call/{call_id}", response_model=ActionResult)
async def delete_call_record(call_id: str):
    action_result_call = await db.delete_entity(call_id)
    action_result_analytics = await analytics_db.find_and_delete_entity({"call_id": call_id})
    if not action_result_call.status and action_result_analytics.status:
        raise HTTPException(status_code=404, detail="Record not found.")
    return action_result_call and action_result_analytics


@call_router.get("/get-all-calls", response_model=ActionResult)
async def get_all_calls():
    action_result = await db.get_all_entities()
    return action_result


@call_router.get("/get-calls-list", response_model=ActionResult)
async def get_calls_list():
    action_result = await db.get_all_entities()
    call_collection = action_result.data
    call_list = []
    for call_record in call_collection:
        call_list_item = call_record
        call_sentiment_data = await analytics_db.find_entity({"call_id": call_list_item["_id"]["$oid"]},
                                                             {"sentiment_category": 1, "_id": 0})
        call_sentiment: dict = call_sentiment_data.data
        call_list_item["id"] = call_list_item["_id"]["$oid"]
        call_list_item["sentiment"] = call_sentiment.get("sentiment_category")
        call_date_time: str = call_record["call_date"]["$date"]
        call_list_item["call_recording_url"]: str = call_list_item["call_recording_url"]
        cal_date, call_time = call_date_time.split("T")
        call_time = call_time[:-1]
        cale_datetime_string = f'{cal_date} {call_time}'
        call_list_item["call_date"] = datetime.strptime(cale_datetime_string, '%Y-%m-%d %H:%M:%S')
        call_list.append(call_list_item)
    action_result.data = call_list
    return action_result


@call_router.post("/upload-calls")
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

                operator_id = int(filename.split("_")[0])
                call_date = filename.split('_')[1]
                call_time = filename.split('_')[2]

                call_datetime = datetime.strptime(call_date + call_time, '%Y%m%d%H%M%S')

                call_record = CallRecord(description=filename, transcription=masked_transcription,
                                         call_duration=get_audio_duration(filepath),
                                         call_date=call_datetime,
                                         operator_id=operator_id,
                                         call_recording_url="")
                result = await db.add_entity(call_record)

                summary = summary_analyzer.generate_summary(masked_transcription)
                print('Summary Data ' + summary)

                sentiment = sentiment_analyzer.analyze(transcription, Configurations.sentiment_categories)
                sentiment_score = sentiment_analyzer.get_sentiment_score()
                print('Sentiment Data ' + sentiment)

                keywords = keyword_extractor.extract_keywords(masked_transcription)

                analyzer_record = AnalyticsRecord(call_id=str(result.data), sentiment_category=sentiment,
                                                  call_date=call_datetime,
                                                  keywords=keywords, summary=summary, sentiment_score=sentiment_score)

                await analytics_db.add_entity(analyzer_record)

                await upload_to_s3(filepath, Configurations.bucket_name, filename + "call_record_id" + str(result.data),
                                   Configurations.aws_access_key_id,
                                   Configurations.aws_secret_access_key)

                # Remove the file after processing
                os.remove(file_location)

            except Exception as e:
                action_result.status = False
                action_result.message = TextMessages.ACTION_FAILED
                action_result.error_message.append((filename, e))

    return action_result
