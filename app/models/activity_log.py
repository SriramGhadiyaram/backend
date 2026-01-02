from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database.base import Base

class UserActivityLogs(Base):
    __tablename__ = "UserActivityLogs"

    LogId = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"))
    Action = Column(String(200))
    Timestamp = Column(DateTime, default=datetime.utcnow)
