from fastapi import APIRouter, Depends

from app.database.aggregation import get_topics_pipeline
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.notification_settings import CallSettings
from app.models.settings_dto import SettingsDTO
from app.utils.auth import get_current_user

settings_router = APIRouter(dependencies=[Depends(get_current_user)])

db = DatabaseConnector("settings")


@settings_router.get("/notification-settings", response_model=ActionResult)
async def get_notification_settings():
    action_result = await db.get_all_entities_async()
    settings_id = action_result.data[0]["_id"]["$oid"]
    action_result.data[0]["id"] = settings_id
    action_result.data = action_result.data[0]
    del action_result.data["_id"]
    return action_result


@settings_router.post("/notification-settings", response_model=ActionResult)
async def update_notification_settings(settings: SettingsDTO):
    settings_dict = settings.dict()
    settings_id = settings_dict["id"]
    settings_dict["_id"] = settings_id
    del settings_dict["id"]
    call_settings = CallSettings(**settings_dict)
    action_result = await db.update_entity_async(call_settings)
    return action_result


@settings_router.get("/topics", response_model=ActionResult)
def get_topics():
    action_result = db.run_aggregation_sync(get_topics_pipeline)
    action_result.data = action_result.data[0]["topics"]
    return action_result
