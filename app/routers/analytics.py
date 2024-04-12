from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.analytics_record import AnalyticsRecord
from app.models.action_result import ActionResult

analytics_router = APIRouter()

db = DatabaseConnector("analytics")


class AnalyticsRouter:
    @analytics_router.post("/add-analytics", response_model=ActionResult)
    def add_analytics_record(self, analytics_record: AnalyticsRecord):
        action_result = db.add_entity(analytics_record)
        return action_result

    @analytics_router.get("/get-all-analytics", response_model=ActionResult)
    async def get_all_analytics(self):
        action_result = await db.get_all_entities()
        return action_result

    @analytics_router.get("/get-analytics/{analytics_id}", response_model=ActionResult)
    async def get_analytics_record_by_id(self, analytics_id: str):
        action_result = await db.get_entity_by_id(analytics_id)
        return action_result

    @analytics_router.delete("/delete-analytics/{analytics_id}", response_model=ActionResult)
    async def delete_analytics_record(self, analytics_id: str):
        action_result = await db.delete_entity(analytics_id)
        return action_result

    @analytics_router.patch("/update-analytics", response_model=ActionResult)
    async def update_analytics_record(self, entity: AnalyticsRecord):
        action_result = await db.update_entity(entity)
        return action_result
