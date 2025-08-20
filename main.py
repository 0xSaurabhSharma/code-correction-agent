import uvicorn
import os
import logging
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.settings_loader import settings
from app.api import router

# --- Environment Variable Setup ---
# It's good practice to set these up early.
os.environ['LANGSMITH_TRACING_V2'] = settings.LANGSMITH_TRACING_V2
os.environ['LANGSMITH_ENDPOINT'] = settings.LANGSMITH_ENDPOINT
os.environ['LANGSMITH_API_KEY'] = settings.LANGSMITH_API_KEY
os.environ['LANGSMITH_PROJECT'] = settings.LANGSMITH_PROJECT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Self-Healing Code Agent",
    description="An API to run and self-heal Python functions.",
    version="1.0.0",
)

# --- THE FIX: Use an absolute path for the templates directory ---
# This makes your app's location independent of the working directory.
# __file__ refers to the current file (main.py)
# os.path.dirname(__file__) gets the directory of main.py (/app in Docker)
# os.path.join combines them to create a full, unambiguous path.
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# --- Router and Routes ---
app.include_router(router)

@app.get("/")
def root(request: Request):
    """
    Renders the single-file UI placed at templates/index.html.
    """
    return templates.TemplateResponse("index.html", {"request": request, "api_base": "", "run_endpoint": "/run_agent"})

@app.get("/health")
def health_check():
    return {"status": "I am on!!"}

# --- Main execution block ---
if __name__ == "__main__":
    port = int(settings.PORT)
    # Use 0.0.0.0 to be accessible within Docker and from the outside.
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
