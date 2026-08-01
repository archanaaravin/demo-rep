from fastapi import APIRouter
from sqlalchemy import text
from app.database.database import engine

router = APIRouter(
    prefix="/accidents",
    tags=["Accidents"]
)

@router.get("/")
def get_accidents(limit: int = 100):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM accidents LIMIT :limit"),
            {"limit": limit}
        )

        accidents = []

        for row in result:
            accidents.append(dict(row._mapping))

        return accidents