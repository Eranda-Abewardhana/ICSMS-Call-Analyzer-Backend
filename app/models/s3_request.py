from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class S3Request(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    call_id: str = Field(...)
    call_recording_url: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
