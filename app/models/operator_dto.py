from pydantic import BaseModel, Field


class CallOperatorDTO(BaseModel):
    operator_id: int = Field(...)
    name: str = Field(...)
    id: str = Field(...)
    