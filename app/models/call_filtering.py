from pydantic import BaseModel, Field, ConfigDict


class CallFilter(BaseModel):
    start_date: str = Field(...)
    end_date: str = Field(...)
    keywords: list[str] = Field(...)
    duration: int = Field(...)
    sentiment_category: str = Field(...)
    topics: list[str] = Field(...)
