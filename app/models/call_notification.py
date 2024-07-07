from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class CallNotification(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(...)
    description: str = Field(...)
    datetime: str = Field(...)
    isRead: bool = Field(...)
