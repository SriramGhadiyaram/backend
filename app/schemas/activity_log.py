from pydantic import BaseModel
from datetime import datetime

class ActivityLogResponse(BaseModel):
    LogId: int
    UserId: int
    Action: str
    Timestamp: datetime

    class Config:
        from_attributes = True
