from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator


PyObjectId = Annotated[str, BeforeValidator(str)]

class NotificatioSettings(BaseModel):
    id: Optional[str] = Field(alias="_id", default='')
    is_email_alerts_enabled: bool = Field(...)
    user_id: str = Field(...)
    is_lower_threshold_enabled: bool = Field(...)
    is_upper_threshold_enabled: bool = Field(...)
    sentiment_lower_threshold: float = Field(...)
    sentiment_upper_threshold: float = Field(...)
    call_directory: Optional[str] = Field(None)
    alert_keywords: list[str] = Field(...)
    alert_email_receptions: list[str] = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
   )
    
class NotificatioDirSettings(BaseModel):
    id: str = Field(alias="_id", default='')
    dir: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
   )