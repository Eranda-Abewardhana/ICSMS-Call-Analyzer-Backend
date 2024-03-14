from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.call_record import CallRecord
from app.models.action_result import ActionResult

call_router = APIRouter()

db = DatabaseConnector("calls")


@call_router.post("/add-calls", response_model=ActionResult)
async def add_call_record(call_record: CallRecord):
    action_result = await db.add_entity(call_record)  # Await the coroutine
    return action_result

@call_router.get("/get-call/{call_id}", response_model=ActionResult)
async def get_call_record_by_id(call_id: str):
    action_result = await db.get_entity_by_id(call_id)
    return action_result


    ...
@call_router.delete("/delete-call/{call_id}", response_model=ActionResult)
async def delete_call_record(call_id: str):
    action_result = await db.delete_entity(call_id)
    if not action_result.success:
        raise HTTPException(status_code=404, detail="Record not found.")
    return action_result

@call_router.get("/get-all-calls", response_model=ActionResult)
async def get_all_calls():
    action_result = await db.get_all_entities()
    return action_result
