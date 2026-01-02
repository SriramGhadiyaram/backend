from app.models.user import UserActivityLogs
from app.database.deps import get_db

def log_activity(db, user_id, action):
    log = UserActivityLogs(UserId=user_id, Action=action)
    db.add(log)
    db.commit()
