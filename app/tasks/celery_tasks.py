import os
from datetime import datetime
from typing import List
import asyncio
import websockets

from app.config.celery_config import celery_app
from app.config.config import Configurations
from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.utils.data_masking import DataMasker
from app.utils.helpers import get_audio_duration
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.s3 import upload_to_s3
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.topic_modler import TopicModeler
from app.utils.transcriber import Transcriber

summary_analyzer = SummaryAnalyzer()
masking_analyzer = DataMasker()
sentiment_analyzer = SentimentAnalyzer()
transcriber = Transcriber()
keyword_extractor = KeywordExtractor()
topic_modeler = TopicModeler()

db = DatabaseConnector("calls")
analytics_db = DatabaseConnector("analytics")


async def _analyze_and_save_calls(filepath_list: List[str]):
    for filepath in filepath_list:
        if os.path.isfile(filepath):
            try:
                filename = filepath.split("\\")[-1]
                transcription = transcriber.transcribe_audio(filepath)
                masked_transcription = masking_analyzer.mask_text(transcription)
                print('Masked Data ' + masked_transcription)

                operator_id = int(filename.split("_")[0])
                call_date = filename.split('_')[1]
                call_time = filename.split('_')[2]
                filename_text = filename.split('.')[0]
                call_description = "_".join(filename_text.split("_")[3:])

                call_datetime = datetime.strptime(call_date + call_time, '%Y%m%d%H%M%S')

                call_record = CallRecord(description=call_description, transcription=masked_transcription,
                                         call_duration=get_audio_duration(filepath),
                                         call_date=call_datetime,
                                         operator_id=operator_id,
                                         call_recording_url="")
                result = await db.add_entity(call_record)

                await upload_to_s3(filepath, Configurations.bucket_name, filename + "call_record_id" + str(result.data),
                                   Configurations.aws_access_key_id,
                                   Configurations.aws_secret_access_key)

                summary = summary_analyzer.generate_summary(masked_transcription)
                print('Summary Data ' + summary)

                sentiment = sentiment_analyzer.analyze(transcription)
                sentiment_score = sentiment_analyzer.get_sentiment_score()
                print('Sentiment Data ' + sentiment)

                keywords = keyword_extractor.extract_keywords(masked_transcription)
                topics = topic_modeler.categorize(masked_transcription, Configurations.topics)

                analyzer_record = AnalyticsRecord(call_id=str(result.data), sentiment_category=sentiment,
                                                  call_date=call_datetime, topics=topics,
                                                  keywords=keywords, summary=summary, sentiment_score=sentiment_score)

                await analytics_db.add_entity(analyzer_record)

                os.remove(filepath)
            except Exception as e:
                print(e)


async def notify_task_completion(task_id, result):
    uri = "ws://localhost:8000/ws/notify"
    async with websockets.connect(uri) as websocket:
        message = f"Task {task_id} completed with result: {result}"
        await websocket.send(message)


@celery_app.task
def analyze_and_save_calls(filepath_list: List[str]):
    task_result = asyncio.run(_analyze_and_save_calls(filepath_list))
    result = asyncio.run(notify_task_completion(analyze_and_save_calls.request.id, task_result))
    print(result)
    return result
