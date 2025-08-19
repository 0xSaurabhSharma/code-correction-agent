#
import uvicorn
import os
import logging
from fastapi import FastAPI, Request     # <-- ensure Request is imported
from fastapi.templating import Jinja2Templates
from app.settings_loader import settings
from app.api import router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Self-Healing Code Agent",
    description="An API to run and self-heal Python functions.",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")

app.include_router(router)

@app.get("/")   # serve the UI on the root path
def root(request: Request):
    """
    Renders the single-file UI placed at templates/index.html.
    api_base and run_endpoint are passed so you can tweak without editing JS.
    """
    # Serve UI with empty API_BASE so frontend uses same-origin relative paths.
    return templates.TemplateResponse("index.html", {"request": request, "api_base": "", "run_endpoint": "/run_agent"})
    # return templates.TemplateResponse("index.html", {"request": request, "api_base": "", "run_endpoint": "/agent/run"})

# @app.get("/")
# def root():
#     return {"message": "Welcome to the Self-Healing Code Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "I am on!!"}

if __name__ == "__main__":
    
    os.environ['LANGSMITH_TRACING_V2'] = settings.LANGSMITH_TRACING_V2
    os.environ['LANGSMITH_ENDPOINT'] = settings.LANGSMITH_ENDPOINT
    os.environ['LANGSMITH_API_KEY'] = settings.LANGSMITH_API_KEY
    os.environ['LANGSMITH_PROJECT'] = settings.LANGSMITH_PROJECT
    
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

