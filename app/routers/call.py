import os
import shutil

from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config.constants import TextMessages
from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.models.action_result import ActionResult
from app.utils.data_masking import DataMasker
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.s3 import upload_to_s3
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.transcriber import Transcriber
from app.config.config import Configurations

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
        call_sentiment_data = await analytics_db.find_entity({"call_id": call_list_item["_id"]["$oid"]}, {"sentiment_category": 1, "_id": 0})
        call_sentiment: dict = call_sentiment_data.data
        call_list_item["id"] = call_list_item["_id"]["$oid"]
        call_list_item["sentiment"] = call_sentiment.get("sentiment_category")
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

                call_record = CallRecord(description=filename, transcription=masked_transcription,
                                         call_duration=0,
                                         call_date="today",
                                         call_recording_url="https://call-analytics-bucket.s3.ap-south-1.amazonaws.com/mr%20john_20240403_183000_mr%20john.mp3?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAgaCmV1LW5vcnRoLTEiRzBFAiA7IwmgpjZGnDy9KC9RMIvqHyRDg7iLE0j2PAdchUyfXAIhAK5R92ZaI%2Bm%2BVCyegbLmjnJ0%2BhU0zbsw6pxCowI8eNStKv0CCEEQARoMNjIwNzQ5OTAwMDY2Igz3cfpSmCJ%2BrkoJXkEq2gIDbWVmUiuwJ68ZoFS%2F%2B5vJskn6w4d2Eq%2F3YFM7td2MUGzmGGUc5evLna04e1Yov5FHX8sIN9gN0PWFxyzyceXF33qKl6AdHZwrCp2Jtx%2BCP7BbCGNbKzkRMKTYF8%2FGGrgG21mO2EQdqDCCX83SBHZZ%2BMdxRPswSd26Th%2FTU2zpI0vjRWFeClDDrFv9lbDeTDkOAMDlnhU8%2BguAAqYrYM0u7jqTyQaXVjg6Kq1TeTJjHPaDT9ynwWNcJFSM9WGBc6YY7kKL25VzBlrVjmtxpr1vsFSoxLlUuw8ub4oSlBULbNRcWPW2NxYQuqP5Vqaab%2BCIp34Ylj0M9%2FlBTkiqL1R4Nwib1gDjKd8YJL9oyGujcg7xMezeEdDdrpfpAyGJoytFNLdKbJFbcA3xjhSjmYuHvYu6qH23Zi8ded3pxB%2BbDVLlxg%2FVQuRbcC628XUc0aY9EfURPGNFgTpZMOuy3rAGOrMCwDNBxwGtCLypG3gLVxIz91KDo78WkwDDBpi6rpu%2FSgVjt62qrXhDu2FHaF8FNp5gQ4wH5L29B9vN6yirPIT8x4fZfr%2FfeDvGq%2Ff%2Bg1nJRkBoZCZVQ3isxlEFvSzfkGnTZgdoHxLePGb1%2F3HZB719ZYi47gXmQ7y%2BpDYUnsb1arUxyORPwmG%2BlNzWoEONl%2BzbyteTdqc9iacsycrY40oDzso6RzK5L777XE%2Bkc8DyEhf1CHDJ4T3f15CYErgHOziT1SG%2FrSBOcdcnUoSvPgVqOnJRrlYxsZSByWLkBrHpSWHHUAxzz61LgtpQeahvhkknUK%2BwhI9QITKG3YSfCUxAmYhAJXf%2FFaRHMxdIIKnlqaxAbOyDoqpR5kT%2BpGWVMO4%2BR40dFbFIF38MO3GUQ7ZRdbxC5Q%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240411T143459Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIAZBB4TZERPGMLYVP4%2F20240411%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Signature=5cf1b80d4dfa8faba0c13aa052e3dd99cdd8e6b7cb6dc02cb9954ecfdbe417e2")
                result = await db.add_entity(call_record)

                summary = summary_analyzer.generate_summary(masked_transcription)
                print('Summary Data ' + summary)

                sentiment = sentiment_analyzer.analyze(transcription, Configurations.sentiment_categories)
                print('Sentiment Data ' + sentiment)

                keywords = keyword_extractor.extract_keywords(masked_transcription)

                # sentiment_score = sentiment_analyzer.analyze_sentiment(transcription)
                # print('Sentiment Score ' + sentiment_score)

                analyzer_record = AnalyticsRecord(call_id=result.data, sentiment_category=sentiment,
                                                  keywords=keywords, summary=summary, sentiment_score=0.4)

                await analytics_db.add_entity(analyzer_record)

                await upload_to_s3(filepath, Configurations.bucket_name, filename, Configurations.aws_access_key_id,
                                   Configurations.aws_secret_access_key)

                # Remove the file after processing
                os.remove(file_location)

            except Exception as e:
                action_result.status = False
                action_result.message = TextMessages.ACTION_FAILED
                action_result.error_message.append((filename, e))

    return action_result
