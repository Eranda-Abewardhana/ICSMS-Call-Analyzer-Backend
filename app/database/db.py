from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.config.constants import TextMessages
from app.models.action_result import ActionResult


class DatabaseConnector:
    def __init__(self, collection_name: str):
        self.__connection_string = "mongodb+srv://heshanhfernando:MVCld4tFIE1zeaMQ@hellocluster.9skju6b.mongodb.net/"
        self.__database_name = "call_recordings"
        self.__client = MongoClient(self.__connection_string)
        try:
            self.__client.server_info()
            self.__database = self.__client.get_database(self.__database_name)
            self.__collection = self.__database.get_collection(collection_name)
        except ServerSelectionTimeoutError as e:
            raise Exception("Database connection timed out")

    def add_entity(self, entity: BaseModel) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            self.__collection.insert_one(entity.model_dump(by_alias=True, exclude=["id"]))
            action_result.message = TextMessages.INSERT_SUCCESS
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    def delete_entity(self, entity_id: str) -> ActionResult:
        action_result = ActionResult(status=True)
        ...

    def update_entity(self, entity) -> ActionResult:
        action_result = ActionResult(status=True)
        ...

    def get_entity_by_id(self, entity_id: str) -> ActionResult:
        action_result = ActionResult(status=True)
        ...

    def get_all_entities(self) -> ActionResult:
        action_result = ActionResult(status=True)
        ...
