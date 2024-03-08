from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import List
from bson import ObjectId
from ApiRequest.blog import schemas
import shutil
import os
from fastapi import FastAPI, File, UploadFile

# Define the path where you want to save the uploaded MP3 files
UPLOAD_FOLDER = "./mp3"

# Ensure the specified folder exists, create it if necessary
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


uri = "mongodb+srv://erandaabewardhana:19765320@cluster0.7coezqv.mongodb.net/users?retryWrites=true&w=majority"
client = MongoClient(uri)

# Check if the connection to MongoDB is successful
try:
    client.server_info()  # Using server_info to check connection
    print("Connected to MongoDB!")
except ServerSelectionTimeoutError as e:
    print(f"Error connecting to MongoDB: {e}")

app = FastAPI()


db = client.get_database()
collection = db['calls']
# Counter for user IDs
call_id_counter = db.get_collection('counters').find_one_and_update(
    {'_id': 'call_id'},
    {'$inc': {'seq': 1}},
    upsert=True,
    return_document=True
)

@app.post("/allcalls", response_model=schemas.CallSchema)
def create_user(request: schemas.CallSchema):
    # Use the incremented user_id_counter value as the _id
    call_id = call_id_counter['seq']
    call_data = request.dict()
    call_data["_id"] = call_id

    result = collection.insert_one(call_data)
    return JSONResponse(content=call_data, status_code=201)


class UserWithNaturalIDSchema(schemas.CallSchema):
    natural_id: int

@app.get("/getallcalls", response_model=List[UserWithNaturalIDSchema])
def read_all_calls():
    all_calls = collection.find({})
    calls_with_object_id = [
        {"natural_id": call["_id"], **call} for call in list(all_calls)
    ]
    return calls_with_object_id


@app.delete("/delectallcall", response_model=dict)
def delete_all_blogs():
    deleted_result = collection.delete_many({})
    
    # Reset the user ID counter to 1
    db.get_collection('counters').update_one({'_id': 'call_id'}, {'$set': {'seq': 1}})
    
    return {"message": f"{deleted_result.deleted_count} blogs deleted, call ID counter reset"}



@app.get("/getcall/{call_id}", response_model=schemas.CallSchema)
def read_blog(call_id: str):
    call = collection.find_one({"_id": call_id})
    if call:
        return call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")

@app.put("/updatecall/{call_id}", response_model=schemas.CallSchema)
def update_blog(call_id: str, request: schemas.CallSchema):
    updated_call = collection.find_one_and_update(
        {"_id": call},
        {"$set": request.dict()},
        return_document=True
    )
    if updated_call:
        return updated_call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")

@app.delete("/delectcall/{blog_id}", response_model=schemas.CallSchema)
def delete_blog(call_id: str):
    deleted_call = collection.find_one_and_delete({"_id": call_id})
    if deleted_call:
        return deleted_call
    else:
        raise HTTPException(status_code=404, detail="Blog not found")

@app.post("/uploadcalls")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the file to the specified folder
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as mp3_file:
            shutil.copyfileobj(file.file, mp3_file)

        return JSONResponse(content={"message": "File uploaded successfully", "file_path": file_path})
    except Exception as e:
        return JSONResponse(content={"message": f"Error uploading file: {str(e)}"}, status_code=500)
