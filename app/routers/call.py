import os
import shutil
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from app.database.schema import CallSchema
from app.config.config import Configurations
from app.database.db import connect_to_database
import motor.motor_asyncio

router = APIRouter()

async def get_collection():
    db = await connect_to_database()
    return db.get_collection('calls')

# Counter for user IDs
async def get_call_id_counter():
    db = await connect_to_database()
    return db.get_collection('counters').find_one_and_update(
        {'_id': 'call_id'},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )

@router.post("/allcalls", response_model=CallSchema)
async def create_user(request: CallSchema):
    collection = await get_collection()
    call_id_counter = await get_call_id_counter()  # Add await here

    # Use the incremented user_id_counter value as the _id
    call_id = call_id_counter['seq']
    call_data = request.dict()
    call_data["_id"] = call_id

    result = await collection.insert_one(call_data)
    return JSONResponse(content=call_data, status_code=201)


class UserWithNaturalIDSchema(CallSchema):
    natural_id: int


@router.get("/getallcalls", response_model=List[UserWithNaturalIDSchema])
async def read_all_calls():
    collection = await get_collection()
    all_calls = collection.find({})
    calls_with_object_id = [
        {"natural_id": call["_id"], **call} for call in await all_calls.to_list(length=None)
    ]
    return calls_with_object_id


@router.delete("/delectallcall", response_model=dict)
async def delete_all_blogs():
    collection = await get_collection()
    deleted_result = await collection.delete_many({})

    # Reset the user ID counter to 1
    db = await connect_to_database()
    await db.get_collection('counters').update_one({'_id': 'call_id'}, {'$set': {'seq': 1}})

    return {"message": f"{deleted_result.deleted_count} call deleted, call ID counter reset"}


@router.get("/getcall/{call_id}", response_model=CallSchema)
async def read_blog(call_id: str):
    collection = await get_collection()
    call = await collection.find_one({"_id": call_id})
    if call:
        return call
    else:
        raise HTTPException(status_code=404, detail="Call not found")


@router.put("/updatecall/{call_id}", response_model=CallSchema)
async def update_blog(call_id: str, request: CallSchema):
    collection = await get_collection()
    updated_call = await collection.find_one_and_update(
        {"_id": call_id},
        {"$set": request.dict()},
        return_document=True
    )
    if updated_call:
        return updated_call
    else:
        raise HTTPException(status_code=404, detail="Call not found")

@router.post("/addcall", response_model=CallSchema)
async def create_call(call_data: CallSchema):
    collection = await get_collection()

    # Increment the call ID counter
    call_id_counter = await get_call_id_counter()
    call_id = call_id_counter['seq']

    # Create the call document
    call_document = {
        "_id": call_id,
        "name": call_data.name,
        "summary": call_data.summary,
        "topic": call_data.topic,
        "sender_no": call_data.sender_no,
        "rec_url": call_data.rec_url,
        "senti_score": call_data.senti_score
    }

    # Insert the call document into the database
    result = await collection.insert_one(call_document)

    # Return the created call document
    return JSONResponse(content=call_document, status_code=201)
@router.delete("/delectcall/{call_id}", response_model=CallSchema)
async def delete_blog(call_id: str):
    collection = await get_collection()
    deleted_call = await collection.find_one_and_delete({"_id": call_id})

    if deleted_call:
        return deleted_call
    else:
        raise HTTPException(status_code=404, detail="Call not found")


@router.post("/uploadcalls")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the file to the specified folder
        file_path = os.path.join(Configurations.UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as mp3_file:
            shutil.copyfileobj(file.file, mp3_file)

        return JSONResponse(content={"message": "File uploaded successfully", "file_path": file_path})
    except Exception as e:
        return JSONResponse(content={"message": f"Error uploading file: {str(e)}"}, status_code=500)
