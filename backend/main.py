from fastapi import FastAPI
from sqlalchemy import text

from app.database.database import engine
from app.routers.accidents import router as accidents_router
from app.routers.hotspots import router as hotspots_router
from app.routers.predict import router as predict_router

app = FastAPI(
    title="AegisAI Backend",
    version="1.0.0"
)

# Include Accident APIs
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