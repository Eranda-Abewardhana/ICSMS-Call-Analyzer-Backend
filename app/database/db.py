from bson import ObjectId
from pydantic import BaseModel
import motor.motor_asyncio
from pymongo import ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from bson import json_util
import json
import os

from app.config.constants import TextMessages
from app.models.action_result import ActionResult


class DatabaseConnector:
    def __init__(self, collection_name: str):
        self.__connection_string = os.getenv("MONGO_DB_URL")
        self.__database_name = "call_recordings"
        self.__client = motor.motor_asyncio.AsyncIOMotorClient(self.__connection_string)
        try:
            self.__client.server_info()
            self.__database = self.__client.get_database(self.__database_name)
            self.__collection = self.__database.get_collection(collection_name)
        except ServerSelectionTimeoutError as e:
            raise Exception("Database connection timed out")

    async def add_entity(self, entity: BaseModel) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            print(entity.model_dump())
            result = await self.__collection.insert_one(entity.model_dump(by_alias=True, exclude=["id"]))
            action_result.data = result.inserted_id
            action_result.message = TextMessages.INSERT_SUCCESS
        except PyMongoError as e:
            print(f"MongoDB error occurred: {e}")
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        except Exception as e:
            print("Exception", e)
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def delete_entity(self, entity_id: str) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            delete_result = await self.__collection.delete_one({"_id": ObjectId(entity_id)})
            if delete_result.deleted_count == 1:
                action_result.message = TextMessages.DELETE_SUCCESS
            else:
                action_result.status = False
                action_result.message = TextMessages.ACTION_FAILED
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def find_and_delete_entity(self, condition: dict) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            delete_result = await self.__collection.delete_one(condition)
            if delete_result.deleted_count == 1:
                action_result.message = TextMessages.DELETE_SUCCESS
            else:
                action_result.status = False
                action_result.message = TextMessages.ACTION_FAILED
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def update_entity(self, entity: BaseModel) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            entity_id = entity.model_dump(by_alias=True)["_id"]
            entity = {k: v for k, v in entity.model_dump(by_alias=True).items() if v is not None and k != "_id"}
            if len(entity) >= 1:
                update_result = await self.__collection.find_one_and_update(
                    {"_id": ObjectId(entity_id)},
                    {"$set": entity},
                    return_document=ReturnDocument.AFTER,
                )
                if update_result is not None:
                    action_result.message = TextMessages.UPDATE_SUCCESS
                else:
                    action_result.status = False
                    action_result.message = TextMessages.NOT_FOUND
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
            action_result.error_message = e
        finally:
            return action_result

    async def get_entity_by_id(self, entity_id: str) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            entity = await self.__collection.find_one({"_id": ObjectId(entity_id)})
            if entity is None:
                action_result.message = TextMessages.NOT_FOUND
                action_result.status = False

            else:
                json_data = json.loads(json_util.dumps(entity))
                action_result.data = json_data
                action_result.message = TextMessages.FOUND
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def find_entity(self, query_filter: dict, fields=None) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            if fields is None:
                entity = await self.__collection.find_one(query_filter)
            else:
                entity = await self.__collection.find_one(query_filter, fields)

            if entity is None:
                action_result.message = TextMessages.NOT_FOUND
            else:
                json_data = json.loads(json_util.dumps(entity))
                action_result.data = json_data
                action_result.message = TextMessages.FOUND
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def get_all_entities(self) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            documents = []
            async for document in self.__collection.find({}):
                json_doc = json.loads(json_util.dumps(document))
                documents.append(json_doc)
            action_result.data = documents
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def run_aggregation(self, pipeline: list) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            result = await self.__collection.aggregate(pipeline).to_list(None)
            action_result.data = result
        except Exception as e:
            action_result.status = False
            action_result.message = TextMessages.ACTION_FAILED
        finally:
            return action_result

    async def find_entities(self, filter_query: dict, fields=None) -> ActionResult:
        action_result = ActionResult(status=True)
        try:
            # Adjusting the find() based on whether fields are specified or not
            if fields is None:
                cursor = self.__collection.find(filter_query)
            else:
                cursor = self.__collection.find(filter_query, fields)

            data = await cursor.to_list(None)

            if not data:
                action_result.message = TextMessages.NOT_FOUND
            else:
                json_data = json.loads(json_util.dumps(data))  # Serialize the list of documents
                action_result.data = json_data
                action_result.message = TextMessages.FOUND

        except Exception as e:
            action_result.status = False
            action_result.message = f"{TextMessages.ACTION_FAILED}: {str(e)}"
        finally:
            return action_result
    # async def find_entities(self, filter_query: dict, fields=None) -> ActionResult:
    #     action_result = ActionResult(status=True)
    #     try:
    #         if fields is None:
    #             cursor = self.__collection.find(filter_query)
    #         else:
    #             cursor = self.__collection.find(filter_query, fields)
    #
    #         data = await cursor.to_list(None)
    #
    #         if len(data) == 0:
    #             action_result.message = TextMessages.NOT_FOUND
    #         else:
    #             json_data = json.loads(json_util.dumps(data))  # Serialize the list of documents
    #             action_result.data = json_data
    #             action_result.message = TextMessages.FOUND
    #     except Exception as e:
    #         action_result.status = False
    #         action_result.message = f"{TextMessages.ACTION_FAILED}: {str(e)}"
    #     finally:
    #         return action_result

    # async def find_entities(self, filter_query: dict, fields=None) -> ActionResult:
    #     action_result = ActionResult(status=True)
    #     try:
    #         if fields is None:
    #             cursor = self.__collection.find(filter_query)
    #         else:
    #             cursor = self.__collection.find(filter_query, fields)
    #
    #         data = []
    #
    #         for doc in await cursor.to_list(None):
    #             data.append(doc)
    #
    #         if len(data) == 0:
    #             action_result.message = TextMessages.NOT_FOUND
    #         else:
    #             json_data = json.loads(json_util.dumps(cursor))
    #             action_result.data = json_data
    #             action_result.message = TextMessages.FOUND
    #     except Exception as e:
    #         action_result.status = False
    #         action_result.message = TextMessages.ACTION_FAILED
    #     finally:
    #         return action_result