import os

import uvicorn
from fastapi import FastAPI

from config.config import Configurations
from routers.call import router

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()
app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, port=8080)
