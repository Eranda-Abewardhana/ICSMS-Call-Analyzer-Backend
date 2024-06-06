import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import Configurations
from app.routers.filtering import filter_router
from app.routers.operators import operator_router
from app.routers.settings import settings_router
from app.routers.analytics import analytics_router
from app.routers.call import call_router

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Configurations.SAVED_FOLDER, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(operator_router)
app.include_router(filter_router)

if __name__ == '__main__':
    uvicorn.run(app, port=8080)
