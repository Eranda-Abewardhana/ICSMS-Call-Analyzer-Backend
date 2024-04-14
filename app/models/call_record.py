from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class CallRecord(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    code : str = Field(...)
    description: str = Field(...)
    transcription: str = Field(...)
    call_recording_url: str = Field(...)
    call_duration: int = Field(...)
    call_date: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
