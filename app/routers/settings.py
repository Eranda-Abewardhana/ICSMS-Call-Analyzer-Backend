from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.notification_settings import CallSettings
from app.models.settings_dto import SettingsDTO

settings_router = APIRouter()

db = DatabaseConnector("settings")


@settings_router.get("/get-notification-settings", response_model=ActionResult)
async def get_notification_settings():
    action_result = await db.get_all_entities()
    settings_id = action_result.data[0]["_id"]["$oid"]
    action_result.data[0]["id"] = settings_id
    action_result.data = action_result.data[0]
    del action_result.data["_id"]
    return action_result


@settings_router.post("/update-notification-settings", response_model=ActionResult)
async def update_notification_settings(settings: SettingsDTO):
    settings_dict = settings.dict()
    settings_id = settings_dict["id"]
    settings_dict["_id"] = settings_id
    del settings_dict["id"]
    call_settings = CallSettings(**settings_dict)
    action_result = await db.update_entity(call_settings)
    return action_result
