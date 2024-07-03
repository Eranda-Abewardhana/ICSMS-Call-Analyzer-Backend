from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.call_notification import CallNotification

notification_router = APIRouter()

notification_db = DatabaseConnector("notifications")


@notification_router.get('/notifications', response_model=ActionResult)
async def get_all_notifications():
    action_result = await notification_db.get_all_entities_async()
    notifications = []
    for notification in action_result.data:
        notification['id'] = notification['_id']['$oid']
        notifications.append(notification)
    action_result.data = notifications
    return action_result


@notification_router.get('/notifications/{notification_id}', response_model=ActionResult)
async def get_operator(notification_id: str):
    notification = await notification_db.get_entity_by_id_async(notification_id)
    return notification


@notification_router.post('/addNotification', response_model=ActionResult)
async def add_notification(notification: CallNotification):
    action_result = await notification_db.add_entity_async(notification)
    action_result.data = str(action_result.data)
    return action_result

@notification_router.delete('/notifications/{notification_id}', response_model=ActionResult)
async def delete_operator(notification_id: str):
    action_result = await notification_db.delete_entity_async(notification_id)
    return action_result
