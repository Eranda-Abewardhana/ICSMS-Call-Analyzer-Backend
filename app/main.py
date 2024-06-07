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
from app.tasks.celery_tasks import analyze_and_save_calls

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Configurations.SAVED_FOLDER, exist_ok=True)

app = FastAPI(title="ICSMS Call Analyzer REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router, tags=["Call Recordings"])
app.include_router(analytics_router, tags=["Call Analytics"])
app.include_router(settings_router, tags=["Call Settings"])
app.include_router(operator_router, tags=["Call Operators"])
app.include_router(filter_router)


@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = analyze_and_save_calls.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return {"result": result.result}
    return {"status": result.state}


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
