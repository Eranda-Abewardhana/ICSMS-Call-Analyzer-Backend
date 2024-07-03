from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime
from bson import ObjectId


class CallNotification(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    datetime: str = Field(...)
    isRead: bool = Field(...)
