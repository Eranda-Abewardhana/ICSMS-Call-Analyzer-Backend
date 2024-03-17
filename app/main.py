import os
import uvicorn
from fastapi import FastAPI
from app.routers.call import call_router
from app.routers.analytics import analytics_router
from app.routers.configuration import settings_configuration_router
from app.config.config import Configurations
from fastapi.middleware.cors import CORSMiddleware


os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Configurations.SAVED_FOLDER, exist_ok=True)

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(call_router)
app.include_router(analytics_router)
app.include_router(settings_configuration_router)


if __name__ == '__main__':
    uvicorn.run(app, port=8080)

