from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class AnalyticsRecord(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    call_id: str = Field(...)
    sentiment_category: str = Field(...)
    keywords: list[str] = Field(...)
    topics: list[str] = Field(...)
    summary: str = Field(...)
    sentiment_score: float = Field(...)
    call_date: datetime = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
