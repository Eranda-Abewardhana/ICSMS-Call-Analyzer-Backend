from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class AnalyticsRecord(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    call_id: str = Field(...)
    sentiment_category: str = Field(...)
    keywords: list[str] = Field(...)
    summary: str = Field(...)
    sentiment_score: float = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
