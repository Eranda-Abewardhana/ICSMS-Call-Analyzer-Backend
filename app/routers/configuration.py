from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.settings_configuration import SettingsConfiguration
from app.models.action_result import ActionResult

settings_configuration_router = APIRouter()

db = DatabaseConnector("calls")


@settings_configuration_router.post("/add-config", response_model=ActionResult)
async def add_config_record(settings_configuration: SettingsConfiguration):
    action_result = await db.add_entity(settings_configuration)
    return action_result

    ...
@settings_configuration_router.delete("/delete-config/{config_id}", response_model=ActionResult)
async def delete_config_record(config_id: str):
    action_result = await db.delete_entity(settings_configuration)
    if not action_result.success:
        raise HTTPException(status_code=404, detail="Record not found.")
    return action_result
from fastapi import HTTPException

@settings_configuration_router.get("/get-config/{config_id}", response_model=ActionResult)
async def get_config_record_by_id(config_id: str):
    settings_configuration = await db.get_entity_by_id(config_id)
    if not settings_configuration:
        raise HTTPException(status_code=404, detail="Record not found")
    return analytics_record
