import json
import os
from datetime import datetime
from typing import List

from app.config.celery_config import celery_app, redis_client
from app.config.config import Configurations
from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_notification import CallNotification
from app.models.call_record import CallRecord
from app.models.notification_settings import CallSettings
from app.utils.data_masking import DataMasker
from app.utils.helpers import get_audio_duration
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.mail_sender import send_mail
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
notification_db = DatabaseConnector("notifications")

upload_process = True


def _analyze_and_save_calls(filepath_list: List[str]):
    settings_result = settings_db.get_all_entities()
    settings_configuration: CallSettings = settings_result.data[0]
    print(settings_configuration)
    settings = json.loads(json.dumps(settings_configuration))

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

                s3_object_url = upload_to_s3(filepath, Configurations.bucket_name,
                                             filename,
                                             Configurations.aws_access_key_id,
                                             Configurations.aws_secret_access_key)
                print(s3_object_url)
                call_record = CallRecord(description=call_description, transcription=masked_transcription,
                                         call_duration=get_audio_duration(filepath),
                                         call_date=call_datetime,
                                         operator_id=operator_id,
                                         call_recording_url=f"https://{Configurations.bucket_name}.s3.amazonaws.com/{filename}")
                result = db.add_entity(call_record)
                print("Call Id", result)
                try:
                    summary = summary_analyzer.generate_summary(masked_transcription)
                    print('Summary Data ' + summary)

                    sentiment, sentiment_score = sentiment_analyzer.analyze_sentiment(transcription)
                    print('Sentiment Data ' + sentiment)

                    keywords = keyword_extractor.extract_keywords(masked_transcription)
                    print(keywords)

                    try:
                        if settings.get("is_keyword_alerts_enabled"):
                            print("============ OK =============")
                            print(settings)
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
                            if settings.get("is_push_notifications_enabled"):
                                notification = CallNotification(title="Keywords Detected In Calls",
                                                                description=f"Below keywords are recently detected in call recordings. Keywords: {', '.join(alert_keywords)}",
                                                                isRead=False, datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
                                notification_db.add_entity(notification)
                                print("Notification Sent")
                    except Exception as e:
                        print(e)

                    topics = topic_modeler.categorize(masked_transcription, settings.get("topics"))

                    analyzer_record = AnalyticsRecord(call_id=str(result.data), sentiment_category=sentiment,
                                                      call_date=call_datetime, topics=topics,
                                                      keywords=keywords, summary=summary,
                                                      sentiment_score=sentiment_score)

                    analytics_db.add_entity(analyzer_record)
                    os.remove(filepath)
                except Exception as e:
                    db.delete_entity(str(result.data))
                    os.remove(filepath)
                    upload_process = False
                    print(e)

            except Exception as e:
                os.remove(filepath)
                upload_process = False
                print(e)


@celery_app.task
def analyze_and_save_calls(filepath_list: List[str]):
    _analyze_and_save_calls(filepath_list)

    # Publish the task completion notification
    if upload_process:
        notification = CallNotification(title="Call Recordings Processed",
                                        description="Call recordings have been successfully processed and saved to the database.",
                                        isRead=False, datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        notification_db.add_entity(notification)
        print("Notification Sent")
    else:
        notification = CallNotification(title="Call Recordings Processing Failed",
                                        description="Call recordings processing failed.",
                                        isRead=False, datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        notification_db.add_entity(notification)
        print("Notification Sent")

    redis_client.publish("task_notifications", json.dumps({"task_id": 23, "status": "message"}))
