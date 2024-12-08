from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)