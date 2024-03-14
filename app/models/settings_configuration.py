from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class SettingsConfiguration(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    config_id: str = Field(...)
    is_notification_enabled: bool = Field(...)
    is_email_alerts_enabled: bool = Field(...)
    alert_keywords: list[str] = Field(...)
    call_directory_url: str = Field(...)
    alert_email_receptions: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
