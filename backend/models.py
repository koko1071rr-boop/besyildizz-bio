from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from database import Base


class BioPage(Base):
    __tablename__ = "bio_pages"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    business_name = Column(String, nullable=False)
    tagline = Column(String, default="")
    logo_url = Column(String, default="")
    theme_color = Column(String, default="#22c55e")
    links = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
