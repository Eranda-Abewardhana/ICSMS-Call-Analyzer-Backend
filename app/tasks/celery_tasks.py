import json
import os
from datetime import datetime
from typing import List

from app.config.celery_config import celery_app
from app.config.config import Configurations
from app.database.database_connector import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.call_record import CallRecord
from app.utils.data_masking import DataMasker
from app.utils.helpers import get_audio_duration
from app.utils.keyword_extractor import KeywordExtractor
from app.utils.notification_handler import NotificationHandler
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
success_count = 0
failed_count = 0


def _analyze_and_save_calls(filepath_list: List[str]):
    global success_count, failed_count, upload_process
    settings_result = settings_db.get_all_entities()
    settings_configuration = settings_result.data[0]
    settings = json.loads(json.dumps(settings_configuration))

    for filepath in filepath_list:
        if os.path.isfile(filepath):
            try:
                filename = filepath.split("\\")[-1]
                transcription = transcriber.transcribe_audio(filepath)
                masked_transcription = masking_analyzer.mask_text(transcription)

                operator_id, call_date, call_time, call_description = extract_call_details_from_filename(filename)
                call_datetime = datetime.strptime(call_date + call_time, '%Y%m%d%H%M%S')

                upload_to_s3(filepath, Configurations.bucket_name,
                             filename,
                             Configurations.aws_access_key_id,
                             Configurations.aws_secret_access_key)

                call_record = CallRecord(description=call_description, transcription=masked_transcription,
                                         call_duration=get_audio_duration(filepath),
                                         call_date=call_datetime,
                                         operator_id=operator_id,
                                         call_recording_url=f"https://{Configurations.bucket_name}.s3.amazonaws.com/{filename}")

                result = db.add_entity(call_record)
                try:
                    summary = summary_analyzer.generate_summary(masked_transcription)
                    print('Summary Data ' + summary)

                    sentiment, sentiment_score = sentiment_analyzer.analyze_sentiment(transcription)
                    print('Sentiment Data ' + sentiment)

                    keywords = keyword_extractor.extract_keywords(masked_transcription)

                    # Send Keyword Alerts
                    try:
                        detected_keywords = []
                        alert_keywords = settings.get("alert_keywords")
                        for keyword in keywords:
                            if keyword in alert_keywords:
                                detected_keywords.append(keyword)
                        if len(detected_keywords) > 0:
                            if settings.get("is_keyword_alerts_enabled"):
                                NotificationHandler.send_keyword_notification(
                                    detected_keywords,
                                    settings.get("is_email_alerts_enabled"),
                                    settings.get("is_push_notifications_enabled"),
                                    settings.get("alert_email_receptions")
                                )
                    except Exception as e:
                        print(e)

                    topics = topic_modeler.categorize(masked_transcription, settings.get("topics"))

                    analyzer_record = AnalyticsRecord(call_id=str(result.data), sentiment_category=sentiment,
                                                      call_date=call_datetime, topics=topics,
                                                      keywords=keywords, summary=summary,
                                                      sentiment_score=sentiment_score)

                    analytics_db.add_entity(analyzer_record)
                    os.remove(filepath)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    db.delete_entity(str(result.data))
                    os.remove(filepath)
                    upload_process = False
                    print(e)

            except Exception as e:
                failed_count += 1
                os.remove(filepath)
                upload_process = False
                print(e)


@celery_app.task
def analyze_and_save_calls(filepath_list: List[str]):
    _analyze_and_save_calls(filepath_list)

    if upload_process:
        NotificationHandler.send_analysis_success_notification(success_count)
    else:
        NotificationHandler.send_analysis_failed_notification(failed_count)
