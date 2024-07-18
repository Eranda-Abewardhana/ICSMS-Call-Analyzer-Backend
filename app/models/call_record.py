from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class CallRecord(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    description: str = Field(...)
    transcription: str = Field(...)
    call_recording_url: str = Field(...)
    call_duration: int = Field(...)
    call_date: datetime = Field(...)
    operator_id: int = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
