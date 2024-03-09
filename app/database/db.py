from typing import Optional, Union, Any, Mapping

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

uri = "mongodb+srv://erandaabewardhana:19765320@cluster0.7coezqv.mongodb.net/users?retryWrites=true&w=majority"


def connect_to_database() -> Optional[Database[Union[Mapping[str, Any], Any]]]:
    client = MongoClient(uri)

    # Check if the connection to MongoDB is successful
    try:
        client.server_info()  # Using server_info to check connection
        print("Connected to MongoDB!")

        db = client.get_database()
        return db
    except ServerSelectionTimeoutError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

