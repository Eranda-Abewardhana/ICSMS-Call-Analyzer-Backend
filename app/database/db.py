from typing import Optional, Union, Any, Mapping
import asyncio
import motor.motor_asyncio

uri = "mongodb+srv://erandaabewardhana:19765320@cluster0.7coezqv.mongodb.net/users?retryWrites=true&w=majority"


async def connect_to_database() -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)

    # Check if the connection to MongoDB is successful
    try:
        await client.server_info()  # Using server_info to check connection
        print("Connected to MongoDB!")

        db = client.get_database()
        return db
    except motor.motor_asyncio.errors.ServerSelectionTimeoutError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

async def main():
    db = await connect_to_database()
    if db:
        # Do something with the database
        pass
    else:
        print("Failed to connect to the database")

# Running the event loop
if __name__ == "__main__":
    asyncio.run(main())
