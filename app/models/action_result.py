from pydantic import BaseModel
from typing_extensions import Any


class ActionResult(BaseModel):
    status: bool = True
    error_message: str = ""
    message: str = ""
    data: object = {}
