import json
import os
from datetime import datetime
from typing import List

from app.config.celery_config import celery_app, redis_client
from app.config.config import Configurations
from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.models.notification_settings import CallSettings
from app.utils.data_masking import DataMasker
from app.utils.helpers import get_audio_duration
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.mailer import send_mail
from app.utils.s3 import upload_to_s3
from app.utils.sentiment_analyzer import SentimentAnalyzer
from app.utils.summary_analyzer import SummaryAnalyzer
from app.utils.topic_modler import TopicModeler
from app.utils.transcriber import Transcriber
from app.utils.helpers import extract_call_details_from_filename

summary_analyzer = SummaryAnalyzer()
masking_analyzer = DataMasker()
sentiment_analyzer = SentimentAnalyzer()
transcriber = Transcriber()
keyword_extractor = KeywordExtractor()
topic_modeler = TopicModeler()

db = DatabaseConnector("calls")
analytics_db = DatabaseConnector("analytics")
settings_db = DatabaseConnector("settings")


def _analyze_and_save_calls(filepath_list: List[str]):
    settings_result = settings_db.get_all_entities()
    settings: CallSettings = settings_result.data[0]

    for filepath in filepath_list:
        print(filepath)
        if os.path.isfile(filepath):
            try:
                filename = filepath.split("\\")[-1]
                transcription = transcriber.transcribe_audio(filepath)
                masked_transcription = masking_analyzer.mask_text(transcription)
                print('Masked Data ' + masked_transcription)
                print(filename)

                operator_id, call_date, call_time, call_description = extract_call_details_from_filename(filename)

                call_datetime = datetime.strptime(call_date + call_time, '%Y%m%d%H%M%S')

                call_record = CallRecord(description=call_description, transcription=masked_transcription,
                                         call_duration=get_audio_duration(filepath),
                                         call_date=call_datetime,
                                         operator_id=operator_id,
                                         call_recording_url="")
                result = db.add_entity(call_record)
                print("Call Id", result)
                try:
                    summary = summary_analyzer.generate_summary(masked_transcription)
                    print('Summary Data ' + summary)

                    sentiment = sentiment_analyzer.analyze(transcription)
                    sentiment_score = sentiment_analyzer.get_sentiment_score()
                    print('Sentiment Data ' + sentiment)

                    keywords = keyword_extractor.extract_keywords(masked_transcription)

                    try:
                        if settings.get("is_keyword_alerts_enabled"):
                            alert_keywords = []
                            for keyword in keywords:
                                if keyword in settings.get("alert_keywords"):
                                    alert_keywords.append(keyword)

                            if settings.get("is_email_alerts_enabled"):
                                mail_obj = {
                                    "to": settings.get("alert_email_receptions"),
                                    "subject": "iCSMS: Keywords Detected In Calls",
                                    "body": f"Below keywords are recently detected in call recordings. Keywords: {', '.join(alert_keywords)}"
                                }
                                send_mail(mail_obj)
                    except Exception as e:
                        db.delete_entity(str(result.data))
                        os.remove(filepath)
                        print(e)

                    topics = topic_modeler.categorize(masked_transcription, settings.get("topics"))

                    analyzer_record = AnalyticsRecord(call_id=str(result.data), sentiment_category=sentiment,
                                                      call_date=call_datetime, topics=topics,
                                                      keywords=keywords, summary=summary,
                                                      sentiment_score=sentiment_score)

                    analytics_db.add_entity(analyzer_record)
                    upload_to_s3(filepath, Configurations.bucket_name, filename + "call_record_id" + str(result.data),
                                 Configurations.aws_access_key_id,
                                 Configurations.aws_secret_access_key)
                    os.remove(filepath)
                except Exception as e:
                    db.delete_entity(str(result.data))
                    os.remove(filepath)
                    print(e)

            except Exception as e:
                os.remove(filepath)
                print(e)


@celery_app.task
def analyze_and_save_calls(filepath_list: List[str]):
    _analyze_and_save_calls(filepath_list)
    # Publish the task completion notification
    redis_client.publish("task_notifications", json.dumps({"task_id": 23, "status": "message"}))
