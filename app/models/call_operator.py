from typing import Optional

from pydantic import BaseModel, Field, BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class CallOperator(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    operator_id: int = Field(...)
    name: str = Field(...)
    email: str = Field(...)
