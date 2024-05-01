from fastapi import APIRouter

from app.database.aggregation import call_statistics_pipeline, sentiment_percentages_pipeline, \
    operator_calls_over_time_pipeline
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.analytics_record import AnalyticsRecord
from app.utils.helpers import merge_operator_analytics_over_time

analytics_router = APIRouter()

analytics_db = DatabaseConnector("analytics")
calls_db = DatabaseConnector("calls")
operator_db = DatabaseConnector("operators")


@analytics_router.post("/add-analytics", response_model=ActionResult)
def add_analytics_record(analytics_record: AnalyticsRecord):
    action_result = analytics_db.add_entity(analytics_record)
    return action_result


@analytics_router.get("/get-all-analytics", response_model=ActionResult)
async def get_all_analytics():
    action_result = await analytics_db.get_all_entities()
    return action_result


@analytics_router.get("/get-analytics/{analytics_id}", response_model=ActionResult)
async def get_analytics_record_by_id(analytics_id: str):
    action_result = await analytics_db.get_entity_by_id(analytics_id)
    return action_result


@analytics_router.delete("/delete-analytics/{analytics_id}", response_model=ActionResult)
async def delete_analytics_record(analytics_id: str):
    action_result = await analytics_db.delete_entity(analytics_id)
    return action_result


@analytics_router.get("/get-call-summary/{call_id}", response_model=ActionResult)
async def get_call_summary(call_id: str):
    action_result = await analytics_db.find_entity({"call_id": call_id}, {"summary": 1, "_id": 0})
    return action_result


@analytics_router.patch("/update-analytics", response_model=ActionResult)
async def update_analytics_record(entity: AnalyticsRecord):
    action_result = await analytics_db.update_entity(entity)
    return action_result


@analytics_router.get("/get-call-statistics", response_model=ActionResult)
async def get_call_statistics():
    action_result = await calls_db.run_aggregation(call_statistics_pipeline)
    action_result.data = action_result.data[0]
    return action_result


@analytics_router.get("/get-sentiment-percentages", response_model=ActionResult)
async def get_sentiment_percentages():
    action_result = await analytics_db.run_aggregation(sentiment_percentages_pipeline)
    action_result.data = action_result.data[0]
    return action_result


@analytics_router.get("/get-operator-calls-over-time", response_model=ActionResult)
async def get_operator_calls_over_time():
    pipeline_result = await calls_db.run_aggregation(operator_calls_over_time_pipeline)
    operator_result = await operator_db.get_all_entities()

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


@analytics_router.get("/get-topics-distribution", response_model=ActionResult)
async def get_topics_distribution():
    action_result = analytics_db.run_aggregation()
    return action_result
