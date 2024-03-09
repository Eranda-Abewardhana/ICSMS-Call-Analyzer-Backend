import os
import shutil
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.database.schema import CallSchema
from app.config.config import Configurations
from app.database.db import connect_to_database

router = APIRouter()

db = connect_to_database()
collection = db.get_collection('calls')

# Counter for user IDs
call_id_counter = db.get_collection('counters').find_one_and_update(
    {'_id': 'call_id'},
    {'$inc': {'seq': 1}},
    upsert=True,
    return_document=True
)


@router.post("/allcalls", response_model=CallSchema)
def create_user(request: CallSchema):
    # Use the incremented user_id_counter value as the _id
    call_id = call_id_counter['seq']
    call_data = request.dict()
    call_data["_id"] = call_id

    result = collection.insert_one(call_data)
    return JSONResponse(content=call_data, status_code=201)


class UserWithNaturalIDSchema(CallSchema):
    natural_id: int


@router.get("/getallcalls", response_model=List[UserWithNaturalIDSchema])
def read_all_calls():
    all_calls = collection.find({})
    calls_with_object_id = [
        {"natural_id": call["_id"], **call} for call in list(all_calls)
    ]
    return calls_with_object_id


@router.delete("/delectallcall", response_model=dict)
def delete_all_blogs():
    deleted_result = collection.delete_many({})

    # Reset the user ID counter to 1
    db.get_collection('counters').update_one({'_id': 'call_id'}, {'$set': {'seq': 1}})

    return {"message": f"{deleted_result.deleted_count} blogs deleted, call ID counter reset"}


@router.get("/getcall/{call_id}", response_model=CallSchema)
def read_blog(call_id: str):
    call = collection.find_one({"_id": call_id})
    if call:
        return call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")


@router.put("/updatecall/{call_id}", response_model=CallSchema)
def update_blog(call_id: str, request: CallSchema):
    updated_call = collection.find_one_and_update(
        {"_id": call_id},
        {"$set": request.dict()},
        return_document=True
    )
    if updated_call:
        return updated_call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")


@router.delete("/delectcall/{call_id}", response_model=CallSchema)
def delete_blog(call_id: str):
    deleted_call = collection.find_one_and_delete({"_id": call_id})
    if deleted_call:
        return deleted_call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")


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
