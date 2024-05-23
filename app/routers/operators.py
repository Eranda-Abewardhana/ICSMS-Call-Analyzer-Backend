from fastapi import APIRouter

from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from app.models.call_operator import CallOperator
from app.database.aggregation import get_next_operator_id_pipeline, operator_analytics_pipeline
from app.models.operator_dto import CallOperatorDTO

operator_router = APIRouter()

operators_db = DatabaseConnector("operators")
calls_db = DatabaseConnector("calls")


@operator_router.get('/get-all-operators', response_model=ActionResult)
async def get_all_operators():
    action_result = await operators_db.get_all_entities()
    operators = []
    for operator in action_result.data:
        operator['id'] = operator['_id']['$oid']
        operators.append(operator)
    action_result.data = operators
    return action_result


@operator_router.get('/get-operator/{operator_id}', response_model=ActionResult)
async def get_operator(operator_id: int):
    pipeline = operator_analytics_pipeline(operator_id)
    calls_result = await calls_db.run_aggregation(pipeline)
    return calls_result


@operator_router.get('/get-operator-id', response_model=ActionResult)
async def get_next_operator_id():
    action_result = await operators_db.run_aggregation(get_next_operator_id_pipeline)
    return action_result


@operator_router.post('/add-operator', response_model=ActionResult)
async def add_operator(operator: CallOperator):
    action_result = await operators_db.add_entity(operator)
    action_result.data = str(action_result.data)
    return action_result


@operator_router.put('/update-operator', response_model=ActionResult)
async def update_operator(operatorDTO: CallOperatorDTO):
    operator = CallOperator(name=operatorDTO.name, operator_id=operatorDTO.operator_id, _id=operatorDTO.id)
    action_result = await operators_db.update_entity(operator)
    return action_result


@operator_router.delete('/delete-operator/{operator_id}', response_model=ActionResult)
async def delete_operator(operator_id: str):
    action_result = await operators_db.delete_entity(operator_id)
    return action_result
