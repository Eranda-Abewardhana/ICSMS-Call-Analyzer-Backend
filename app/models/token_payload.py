from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    roles: list
    username: str
    token: str
