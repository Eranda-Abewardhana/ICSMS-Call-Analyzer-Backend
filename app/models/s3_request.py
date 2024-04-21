from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator


class S3Request(BaseModel):
    call_id: str = Field(...)
    call_url: str = Field(...)
