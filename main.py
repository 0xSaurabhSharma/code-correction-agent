#
import uvicorn
import os
import logging
from fastapi import FastAPI
from app.settings_loader import settings
from app.api import router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Self-Healing Code Agent",
    description="An API to run and self-heal Python functions.",
    version="1.0.0",
)


app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to the Self-Healing Code Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "I am on!!"}

if __name__ == "__main__":
    
    os.environ['LANGSMITH_TRACING_V2'] = settings.LANGSMITH_TRACING_V2
    os.environ['LANGSMITH_ENDPOINT'] = settings.LANGSMITH_ENDPOINT
    os.environ['LANGSMITH_API_KEY'] = settings.LANGSMITH_API_KEY
    os.environ['LANGSMITH_PROJECT'] = settings.LANGSMITH_PROJECT
    
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

