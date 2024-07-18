from pydantic import BaseModel


class MailObject(BaseModel):
    to: list[str]
    subject: str
    context: dict
    template: str
