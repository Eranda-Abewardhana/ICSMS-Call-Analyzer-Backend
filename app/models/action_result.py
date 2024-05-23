from typing import Union

from pydantic import BaseModel


class ActionResult(BaseModel):
    status: bool = True
    error_message: Union[str, list] = ""
    message: str = ""
    data: object = {}
