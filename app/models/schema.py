from pydantic import BaseModel


class CallSchema(BaseModel):
    _id: int
    name: str
    summary: str
    topic: str
    sender_no: int
    rec_url: str
    senti_score: float
