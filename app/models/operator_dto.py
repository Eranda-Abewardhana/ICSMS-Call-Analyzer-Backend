from typing import Optional

from pydantic import BaseModel, Field


class CallOperatorDTO(BaseModel):
    operator_id: int = Field(...)
    name: str = Field(...)
    id: Optional[str] = Field(...)
    email: str = Field(...)
    password: str = Field(...)
