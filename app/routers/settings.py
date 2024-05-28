import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.notification_settings import NotificatioDirSettings, NotificatioSettings

settings_router = APIRouter()

db = DatabaseConnector("settings")

@settings_router.get("/get-notification-settings/{userID}", response_model=ActionResult)
async def get_notification_settings(userID: str):
    action_result = await db.get_all_entities()
    # filter the result to get the user's settings
    action_result.data = [x for x in action_result.data if x["user_id"] == userID]
    return action_result

@settings_router.post("/update-notification-settings", response_model=ActionResult)
async def update_notification_settings(settings: NotificatioSettings):
    print(settings.dict())
    action_result = await db.update_entity(settings)
    return action_result

@settings_router.post("/update-dir-settings", response_model=ActionResult)
async def update_notification_settings(settings: NotificatioDirSettings):
    print(settings.dict())
    action_result = await db.update_entity(settings)
    return action_result