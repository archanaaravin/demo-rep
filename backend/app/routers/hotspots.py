from fastapi import APIRouter
from sqlalchemy import text
from app.database.database import engine

router = APIRouter(
    prefix="/hotspots",
    tags=["Hotspots"]
)

@router.get("/")
def get_hotspots(limit: int = 10):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    road_name,
                    COUNT(*) AS total_accidents,
                    AVG(latitude) AS latitude,
                    AVG(longitude) AS longitude
                FROM accidents
                GROUP BY road_name
                ORDER BY total_accidents DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )

        hotspots = []

        for row in result:
            hotspots.append(dict(row._mapping))

        return hotspots