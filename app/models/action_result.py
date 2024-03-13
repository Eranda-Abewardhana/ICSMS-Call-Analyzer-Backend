from pydantic import BaseModel


class ActionResult(BaseModel):
    status: bool = True
    error_message: str = ""
    message: str = ""
    data: object = {}
