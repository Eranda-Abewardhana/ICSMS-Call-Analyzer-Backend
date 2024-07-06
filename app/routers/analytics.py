from datetime import datetime

from fastapi import APIRouter, Query
from typing import Annotated

from collections import Counter
from app.database.aggregation import call_statistics_pipeline, sentiment_percentages_pipeline, \
    operator_calls_over_time_pipeline, get_all_keywords_pipeline, operator_rating_pipeline, \
    all_operator_sentiment_pipeline, get_topics_distribution_pipeline, sentiment_over_time_pipeline, \
    get_overall_avg_sentiment_score_pipeline
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.analytics_record import AnalyticsRecord
from app.utils.helpers import merge_operator_analytics_over_time

analytics_router = APIRouter()

analytics_db = DatabaseConnector("analytics")
calls_db = DatabaseConnector("calls")
operator_db = DatabaseConnector("operators")

TimeStampQuery = Annotated[str, Query(pattern=r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}")]


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
async def get_call_statistics(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await calls_db.run_aggregation_async(call_statistics_pipeline(start_date, end_date))
    avg_score_result = await analytics_db.run_aggregation_async(get_overall_avg_sentiment_score_pipeline(start_date, end_date))
    action_result.data = action_result.data[0]
    action_result.data["avg_score"] = avg_score_result.data[0].get("avg_score") * 10
    return action_result


@analytics_router.get("/sentiment-percentages", response_model=ActionResult)
async def get_sentiment_percentages(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await analytics_db.run_aggregation_async(sentiment_percentages_pipeline(start_date, end_date))
    action_result.data = action_result.data[0]
    return action_result


@analytics_router.get("/operator-calls-over-time", response_model=ActionResult)
async def get_operator_calls_over_time(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    pipeline_result = await calls_db.run_aggregation_async(operator_calls_over_time_pipeline(start_date, end_date))
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
async def get_topics_distribution(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await analytics_db.run_aggregation_async(get_topics_distribution_pipeline(start_date, end_date))
    action_result.data = action_result.data[0]
    topics_counter = Counter(action_result.data["topics"])
    action_result.data = topics_counter
    return action_result


@analytics_router.get("/all-keywords", response_model=ActionResult)
async def get_all_keywords(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await analytics_db.run_aggregation_async(get_all_keywords_pipeline(start_date, end_date))
    action_result.data = action_result.data[0]
    keywords_counter = Counter(action_result.data["keywords"])
    action_result.data = keywords_counter
    return action_result


@analytics_router.get("/operator-ratings", response_model=ActionResult)
async def get_operator_ratings(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await calls_db.run_aggregation_async(operator_rating_pipeline(3, start_date, end_date))
    action_result.data = action_result.data
    return action_result


@analytics_router.get("/average-operator-sentiment", response_model=ActionResult)
async def get_average_operator_sentiment():
    action_result = await calls_db.run_aggregation_async(all_operator_sentiment_pipeline)
    return action_result


@analytics_router.get("/sentiment-over-time", response_model=ActionResult)
async def get_sentiment_over_time(start: TimeStampQuery, end: TimeStampQuery):
    start_date = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S")
    action_result = await analytics_db.run_aggregation_async(sentiment_over_time_pipeline(start_date, end_date))
    return action_result
