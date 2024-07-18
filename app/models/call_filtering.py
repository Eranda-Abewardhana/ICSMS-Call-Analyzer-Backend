from pydantic import BaseModel, Field


class CallFilter(BaseModel):
    start_date: str = Field(...)
    end_date: str = Field(...)
    keywords: list[str] = Field(...)
    duration: int = Field(...)
    sentiment_category: list[str] = Field(...)
    topics: list[str] = Field(...)
