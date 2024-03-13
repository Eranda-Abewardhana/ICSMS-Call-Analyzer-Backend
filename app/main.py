import os
import uvicorn
from fastapi import FastAPI

from app.routers.analytics import analytics_router
from app.config.config import Configurations
# from app.routers.call import router

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()
# app.include_router(router)
app.include_router(analytics_router)

if __name__ == '__main__':
    uvicorn.run(app, port=8080)

