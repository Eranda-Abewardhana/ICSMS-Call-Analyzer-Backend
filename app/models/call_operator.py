from typing import Optional
from typing_extensions import Annotated

from pydantic import BaseModel, Field, BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]

class CallOperator(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    operator_id: int = Field(...)
    name: str = Field(...)