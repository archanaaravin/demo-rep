from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database.database import engine
from app.routers.accidents import router as accidents_router
from app.routers.hotspots import router as hotspots_router
from app.routers.predict import router as predict_router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

app = FastAPI(
    title="AegisAI Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Accident APIs
app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')

@app.get('/frontend', response_class=FileResponse)
def serve_frontend():
    return FRONTEND_DIR / 'index.html'

@app.get('/app', response_class=FileResponse)
def serve_app():
    return FRONTEND_DIR / 'index.html'

app.include_router(accidents_router)
app.include_router(hotspots_router)
app.include_router(predict_router)

@app.get("/")
def home():
    return {
        "message": "AegisAI Backend Running Successfully"
    }

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "Database Connected Successfully"}
    except Exception as e:
        return {"status": "Database Connection Failed", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
