from sqlalchemy import Column, String, Integer, Float, DateTime
from database import Base
import datetime

class Listing(Base):
    __tablename__ = "listings"

    # We use the source's native ID (e.g., as24_..., 2em_...) as our primary key
    id = Column(String, primary_key=True, index=True)
    source = Column(String, index=True)
    title = Column(String)
    price = Column(Float, index=True)
    year = Column(Integer, index=True, nullable=True)
    km = Column(Integer, index=True, nullable=True)
    city = Column(String, nullable=True)
    fuel_type = Column(String, index=True, nullable=True)
    transmission = Column(String, index=True, nullable=True)
    url = Column(String, unique=True, index=True)
    image_url = Column(String, nullable=True)
    date_scraped = Column(DateTime, default=datetime.datetime.utcnow)
    
    deal_score  = Column(Float, nullable=True)
    has_carpass = Column(String, nullable=True)


class AppConfig(Base):
    __tablename__ = "app_config"
    key   = Column(String, primary_key=True)
    value = Column(String)

class SeenId(Base):
    __tablename__ = "seen_ids"
    listing_id = Column(String, primary_key=True)
