from fastapi import APIRouter
from collections import Counter
from app.database.aggregation import call_statistics_pipeline, sentiment_percentages_pipeline, \
    operator_calls_over_time_pipeline, get_all_keywords_pipeline, operator_rating_pipeline
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.analytics_record import AnalyticsRecord
from app.utils.helpers import merge_operator_analytics_over_time

analytics_router = APIRouter()

analytics_db = DatabaseConnector("analytics")
calls_db = DatabaseConnector("calls")
operator_db = DatabaseConnector("operators")


@analytics_router.post("/analytics", response_model=ActionResult)
def add_analytics_record(analytics_record: AnalyticsRecord):
    action_result = analytics_db.add_entity_async(analytics_record)
    return action_result


@analytics_router.get("/analytics", response_model=ActionResult)
async def get_all_analytics():
    action_result = await analytics_db.get_all_entities_async()
    return action_result


@analytics_router.get("/analytics/{analytics_id}", response_model=ActionResult)
async def get_analytics_record_by_id(analytics_id: str):
    action_result = await analytics_db.get_entity_by_id_async(analytics_id)
    return action_result


@analytics_router.delete("/analytics/{analytics_id}", response_model=ActionResult)
async def delete_analytics_record(analytics_id: str):
    action_result = await analytics_db.delete_entity_async(analytics_id)
    return action_result


@analytics_router.get("/call-summary/{call_id}", response_model=ActionResult)
async def get_call_summary(call_id: str):
    action_result = await analytics_db.find_entity_async({"call_id": call_id}, {"summary": 1, "_id": 0})
    return action_result


@analytics_router.patch("/analytics", response_model=ActionResult)
async def update_analytics_record(entity: AnalyticsRecord):
    action_result = await analytics_db.update_entity_async(entity)
    return action_result


@analytics_router.get("/call-statistics", response_model=ActionResult)
async def get_call_statistics():
    action_result = await calls_db.run_aggregation_async(call_statistics_pipeline)
    action_result.data = action_result.data[0]
    return action_result


@analytics_router.get("/sentiment-percentages", response_model=ActionResult)
async def get_sentiment_percentages():
    action_result = await analytics_db.run_aggregation_async(sentiment_percentages_pipeline)
    action_result.data = action_result.data[0]
    return action_result


@analytics_router.get("/operator-calls-over-time", response_model=ActionResult)
async def get_operator_calls_over_time():
    pipeline_result = await calls_db.run_aggregation_async(operator_calls_over_time_pipeline)
    operator_result = await operator_db.get_all_entities_async()

    action_result = ActionResult(error_message=[], status=True)

    if not operator_result.status:
        action_result.status = False
        action_result.error_message.append("Failed to call operator data")

    if not pipeline_result.status:
        action_result.status = False
        action_result.error_message.append("Failed to analytics data")

    if action_result.status:
        processed_entities = merge_operator_analytics_over_time(operator_result.data, pipeline_result.data)
        action_result.data = processed_entities

    return action_result


@analytics_router.get("/topics-distribution", response_model=ActionResult)
async def get_topics_distribution():
    action_result = analytics_db.run_aggregation_async()
    return action_result


@analytics_router.get("/all-keywords", response_model=ActionResult)
async def get_all_keywords():
    action_result = await analytics_db.run_aggregation_async(get_all_keywords_pipeline)
    action_result.data = action_result.data[0]
    keywords_counter = Counter(action_result.data["keywords"])
    action_result.data = keywords_counter
    return action_result


@analytics_router.get("/operator-ratings", response_model=ActionResult)
async def get_operator_ratings():
    action_result = await calls_db.run_aggregation_async(operator_rating_pipeline(3))
    action_result.data = action_result.data
    return action_result
