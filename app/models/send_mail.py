from pydantic import BaseModel


class MailObject(BaseModel):
    to: list[str]
    subject: str
    body: str
