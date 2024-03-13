from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.action_result import ActionResult

analytics_router = APIRouter()

db = DatabaseConnector("analytics")


@analytics_router.post("/add-analytics", response_model=ActionResult)
def add_analytics_record(analytics_record: AnalyticsRecord):
    action_result = db.add_entity(analytics_record)
    return action_result


@analytics_router.get("/get-analytics", response_model=ActionResult)
def get_analytics_record_by_id(call_id: str):
    ...
