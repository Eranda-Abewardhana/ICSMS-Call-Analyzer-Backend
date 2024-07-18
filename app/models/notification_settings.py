from typing import Optional

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class CallSettings(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    is_email_alerts_enabled: bool = Field(...)
    is_lower_threshold_enabled: bool = Field(...)
    is_upper_threshold_enabled: bool = Field(...)
    is_keyword_alerts_enabled: bool = Field(...)
    is_push_notifications_enabled: bool = Field(...)
    sentiment_lower_threshold: float = Field(...)
    sentiment_upper_threshold: float = Field(...)
    alert_keywords: list[str] = Field(...)
    alert_email_receptions: list[str] = Field(...)
    topics: list[str] = Field(...)
