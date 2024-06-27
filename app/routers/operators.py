from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.call_operator import CallOperator
from app.database.aggregation import get_next_operator_id_pipeline, operator_analytics_pipeline
from app.models.operator_dto import CallOperatorDTO

operator_router = APIRouter()

operators_db = DatabaseConnector("operators")
calls_db = DatabaseConnector("calls")


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
    pipeline = operator_analytics_pipeline(operator_id)
    calls_result = await calls_db.run_aggregation_async(pipeline)
    return calls_result


@operator_router.get('/operator-id', response_model=ActionResult)
async def get_next_operator_id():
    action_result = await operators_db.run_aggregation_async(get_next_operator_id_pipeline)
    if len(action_result.data) == 0:
        action_result.data = [{"operator_id": 1}]
    return action_result


@operator_router.post('/operators', response_model=ActionResult)
async def add_operator(operator: CallOperator):
    action_result = await operators_db.add_entity_async(operator)
    action_result.data = str(action_result.data)
    return action_result


@operator_router.put('/operators', response_model=ActionResult)
async def update_operator(operatorDTO: CallOperatorDTO):
    operator = CallOperator(name=operatorDTO.name, operator_id=operatorDTO.operator_id, _id=operatorDTO.id)
    action_result = await operators_db.update_entity_async(operator)
    return action_result


@operator_router.delete('/operators/{operator_id}', response_model=ActionResult)
async def delete_operator(operator_id: str):
    action_result = await operators_db.delete_entity_async(operator_id)
    return action_result
