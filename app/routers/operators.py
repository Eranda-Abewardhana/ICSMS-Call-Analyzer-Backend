from datetime import datetime, timedelta
from typing import Annotated
from dotenv import load_dotenv

from fastapi import APIRouter, Depends
import requests
import os

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.call_operator import CallOperator
from app.database.aggregation import get_next_operator_id_pipeline, operator_analytics_pipelines
from app.models.operator_dto import CallOperatorDTO
from app.models.token_payload import TokenPayload
from app.utils.auth import get_current_user

operator_router = APIRouter()

operators_db = DatabaseConnector("operators")
calls_db = DatabaseConnector("calls")

load_dotenv()


@operator_router.get('/operators', response_model=ActionResult)
async def get_all_operators():
    action_result = await operators_db.get_all_entities_async()
    operators = []
    for operator in action_result.data:
        operator['id'] = operator['_id']['$oid']
        operators.append(operator)
    action_result.data = operators
    return action_result


@operator_router.get('/operators/{operator_id}', response_model=ActionResult)
async def get_operator(operator_id: int):
    now_time = datetime.now()
    date_time_before_24_hours = now_time - timedelta(hours=24)
    operator_details_pipeline, last_day_calls_pipeline = operator_analytics_pipelines(operator_id, now_time,
                                                                                      date_time_before_24_hours)
    calls_result = await calls_db.run_aggregation_async(operator_details_pipeline)
    last_day_calls_result = await calls_db.run_aggregation_async(last_day_calls_pipeline)
    calls_result.data[0]["calls_in_last_day"] = last_day_calls_result.data[0]["total_calls"]
    return calls_result


@operator_router.get('/operator-id', response_model=ActionResult)
async def get_next_operator_id():
    action_result = await operators_db.run_aggregation_async(get_next_operator_id_pipeline)
    if len(action_result.data) == 0:
        action_result.data = [{"operator_id": 1}]
    return action_result


@operator_router.post('/operators', response_model=ActionResult)
async def add_operator(operatorDTO: CallOperatorDTO, payload: Annotated[TokenPayload, Depends(get_current_user)]):
    operator = CallOperator(name=operatorDTO.name, operator_id=operatorDTO.operator_id, email=operatorDTO.email)
    action_result = await operators_db.add_entity_async(operator)
    try:
        data = {"email": operator.email, "username": operator.email, "password": operatorDTO.password, "phone_number": "", "roles": ["CallOperator"]}
        headers = {"Authorization": f"Bearer {payload.token}"}
        response = requests.post(os.getenv("UM_API_URL"), json=data, headers=headers)
        if response.status_code != 200:
            await operators_db.delete_entity_async(str(action_result.data))
            action_result.status = False
            action_result.message = "Failed to create user in Cognito"
        else:
            action_result.data = str(action_result.data)
    except Exception as e:
        print(e)
        await operators_db.delete_entity_async(str(action_result.data))
        action_result.status = False
        action_result.message = "Failed to create user in Cognito"
    return action_result


@operator_router.put('/operators', response_model=ActionResult)
async def update_operator(operatorDTO: CallOperatorDTO):
    operator = CallOperator(name=operatorDTO.name, operator_id=operatorDTO.operator_id, _id=operatorDTO.id,
                            email=operatorDTO.email)
    action_result = await operators_db.update_entity_async(operator)
    return action_result


@operator_router.delete('/operators/{operator_id}', response_model=ActionResult)
async def delete_operator(operator_id: str):
    action_result = await operators_db.delete_entity_async(operator_id)
    return action_result
