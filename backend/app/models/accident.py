from sqlalchemy import Column, Integer, String, Float, Date, Time
from app.database.database import engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Accident(Base):
    __tablename__ = "accidents"

    accident_id = Column(Integer, primary_key=True, index=True)
    accident_date = Column(Date)
    accident_time = Column(Time)
    latitude = Column(Float)
    longitude = Column(Float)
    road_name = Column(String)
    junction = Column(String)
    weather = Column(String)
    rainfall_mm = Column(Float)
    temperature_c = Column(Float)
    visibility = Column(String)
    traffic_density = Column(String)
    road_type = Column(String)
    speed_limit = Column(Integer)
    lanes = Column(Integer)
    vehicle_1 = Column(String)
    vehicle_2 = Column(String)
    cause = Column(String)
    severity = Column(String)
    casualties = Column(Integer)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)