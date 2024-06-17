from pydantic import BaseModel, Field


class S3Request(BaseModel):
    call_id: str = Field(...)
    call_url: str = Field(...)
