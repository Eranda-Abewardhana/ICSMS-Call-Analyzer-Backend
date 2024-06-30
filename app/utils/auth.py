import os

import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.models.token_payload import TokenPayload


def get_cognito_public_keys():
    response = requests.get(os.getenv('COGNITO_KEYS_URL'))
    response.raise_for_status()
    return response.json()['keys']


cognito_public_keys = get_cognito_public_keys()
security = HTTPBearer()


def decode_jwt(token: str):
    global cognito_public_keys
    try:
        header = jwt.get_unverified_header(token)
        key = next(k for k in cognito_public_keys if k['kid'] == header['kid'])
        return jwt.decode(token, key, algorithms=['RS256'], audience=os.getenv('COGNITO_APP_CLIENT_ID'))
    except JWTError:
        # If verification fails, try to fetch the keys again
        header = jwt.get_unverified_header(token)
        cognito_public_keys = get_cognito_public_keys()
        try:
            key = next(k for k in cognito_public_keys if k['kid'] == header['kid'])
            return jwt.decode(token, key, algorithms=['RS256'], audience=os.getenv('COGNITO_APP_CLIENT_ID'))
        except JWTError:
            raise HTTPException(status_code=403, detail="Could not validate credentials")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    jwt_payload = decode_jwt(token)
    roles = jwt_payload.get('cognito:groups', [])
    username = jwt_payload['cognito:username']
    token_payload = TokenPayload(sub=jwt_payload['sub'], roles=roles, username=username)
    return token_payload
