from pydantic import BaseModel, EmailStr

class CallSchema(BaseModel):
        _id: int
        name: str
        summary: str
        topic: str
        sender_no: int
        rec_url: str
        senti_score: float  


# Example usage
call_data = {
    "_id": 1,
    "name": "janaka",
    "summary": "recooneting issue",
    "topic": "network",
    "sender_no": 123,
    "receiver_no": 456,
    "rec_url": "https://www.google.com",
    "senti_score": 0.5
}

# Validate the data against the schema
call_instance = CallSchema(**call_data)
