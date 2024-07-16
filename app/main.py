import asyncio
import json
import os
import redis
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every

from app.config.config import Configurations
from app.database.database_connector import DatabaseConnector
from app.routers.filtering import filter_router
from app.routers.operators import operator_router
from app.routers.serversentevent import server_sent_event
from app.routers.settings import settings_router
from app.routers.analytics import analytics_router
from app.routers.call import call_router
from app.utils.auth import get_current_user
from app.utils.notification_handler import NotificationHandler
from app.utils.sentiment_analyzer import SentimentAnalyzer

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(title="SentiView Call Analyzer REST API")
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router, tags=["Call Recordings"], dependencies=[Depends(get_current_user)])
app.include_router(analytics_router, tags=["Call Analytics"], dependencies=[Depends(get_current_user)])
app.include_router(settings_router, tags=["Call Settings"], dependencies=[Depends(get_current_user)])
app.include_router(operator_router, tags=["Call Operators"], dependencies=[Depends(get_current_user)])
app.include_router(filter_router, tags=["Call Filtering"], dependencies=[Depends(get_current_user)])
app.include_router(server_sent_event, tags=["Server Sent Event"])

sentiment_analyzer = SentimentAnalyzer()
settings_db = DatabaseConnector("settings")


async def redis_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe("task_notifications")
    print("Redis channel subscribed")
    while True:
        try:
            # Get the message from redis channel
            message = pubsub.get_message(ignore_subscribe_messages=True)

            if message is not None:
                print("Message received from redis channel")
        except Exception as e:
            print(f"Error in redis_listener: {e}")
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())


@app.on_event("startup")
@repeat_every(seconds=Configurations.status_check_frequency, wait_first=True)
async def check_overall_sentiment_score():
    avg_score_data = sentiment_analyzer.get_overall_avg_sentiment()
    avg_score = avg_score_data.get("avg_score") * 10
    action_result = settings_db.get_all_entities()
    settings_configuration = action_result.data[0]
    settings_configuration = json.loads(json.dumps(settings_configuration))
    is_email_alerts_enabled = settings_configuration.get("is_email_alerts_enabled")
    is_push_notifications_enabled = settings_configuration.get("is_push_notifications_enabled")
    email_receptions = settings_configuration.get("alert_email_receptions")

    await NotificationHandler.send_below_sentiment_notification(
        settings_configuration.get("sentiment_lower_threshold"),
        avg_score,
        is_email_alerts_enabled,
        is_push_notifications_enabled,
        email_receptions
    )

    await NotificationHandler.send_above_sentiment_notification(
        settings_configuration.get("sentiment_upper_threshold"),
        avg_score,
        is_email_alerts_enabled,
        is_push_notifications_enabled,
        email_receptions
    )


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
