from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.deps import get_db
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    CreateUserSchema,
    UpdateUserSchema,
    ResetPasswordSchema
)
from typing import List
from app.core.password import hash_password
from app.core.roles import require_admin
import pandas as pd
from app.models.activity_log import UserActivityLogs
from fastapi.responses import FileResponse
from app.schemas.activity_log import ActivityLogResponse


router = APIRouter(prefix="/users", tags=["Users"])


# ---------------- GET USERS WITH SEARCH + FILTER ----------------

@router.get("/", response_model=List[UserResponse])
def get_users(
    search: str = "",
    role: str = "",
    department: str = "",
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    query = db.query(User)

    if search:
        query = query.filter(User.FullName.contains(search))

    if role:
        query = query.filter(User.Role == role)

    if department:
        query = query.filter(User.Department == department)

    return query.all()



# ---------------- CREATE USER ----------------

@router.post("/", response_model=UserResponse)
def create_user(user: CreateUserSchema, 
                db: Session = Depends(get_db), 
                admin=Depends(require_admin)):

    existing = db.query(User).filter(User.Email == user.Email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        FullName=user.FullName,
        Email=user.Email,
        Role=user.Role,
        Department=user.Department,
        PasswordHash=hash_password(user.Password)
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
        log = UserActivityLogs(
            UserId=new_user.UserId,
            Action=f"User created with email {new_user.Email}"
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return new_user




# ---------------- UPDATE USER ROLE / DEPARTMENT ----------------

@router.put("/{user_id}")
def update_user(user_id: int, 
                update: UpdateUserSchema, 
                db: Session = Depends(get_db),
                admin=Depends(require_admin)):

    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if update.Role:
        user.Role = update.Role

    if update.Department:
        user.Department = update.Department

    db.commit()
    return {"message": "User updated successfully"}



# ---------------- DELETE USER ----------------

@router.delete("/{user_id}")
def delete_user(user_id: int, 
                db: Session = Depends(get_db),
                admin=Depends(require_admin)):

    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}



# ---------------- ACTIVATE / DEACTIVATE ----------------

@router.patch("/{user_id}/toggle")
def toggle_user(user_id: int, 
                db: Session = Depends(get_db),
                admin=Depends(require_admin)):

    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.IsActive = not user.IsActive
    db.commit()

    return {
        "message": "Status updated",
        "IsActive": user.IsActive
    }



# ---------------- BULK UPLOAD CSV / EXCEL ----------------

@router.post("/upload-csv")
async def upload_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(400, "File must be CSV or Excel")

    df = pd.read_csv(file.file) if file.filename.endswith(".csv") else pd.read_excel(file.file)

    required_cols = {"FullName", "Email", "Role", "Department", "Password"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(400, detail=f"File must contain: {required_cols}")

    for _, row in df.iterrows():
        existing = db.query(User).filter(User.Email == row["Email"]).first()
        if existing:
            continue

        user = User(
            FullName=row["FullName"],
            Email=row["Email"],
            Role=row["Role"],
            Department=row["Department"],
            PasswordHash=hash_password(str(row["Password"]))
        )

        db.add(user)

    db.commit()
    return {"message": "Users uploaded successfully"}

@router.get("/{user_id}/logs")
def get_logs(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return db.query(UserActivityLogs).filter(UserActivityLogs.UserId == user_id).all()

@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    new_pass = "Reset@123"

    user.PasswordHash = hash_password(new_pass)
    db.commit()

    return {"message": "Password reset", "new_password": new_pass}

@router.get("/export")
def export_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    users = db.query(User).all()

    data = [
        {
            "Id": u.UserId,
            "Name": u.FullName,
            "Email": u.Email,
            "Role": u.Role,
            "Department": u.Department,
            "Active": u.IsActive
        }
        for u in users
    ]

    df = pd.DataFrame(data)
    path = "users_export.csv"
    df.to_csv(path, index=False)

    return FileResponse(path, filename="users.csv")

@router.get("/stats/roles")
def role_stats(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return {
        "students": db.query(User).filter(User.Role == "Student").count(),
        "faculty": db.query(User).filter(User.Role == "Faculty").count(),
        "admins": db.query(User).filter(User.Role == "Admin").count(),
    }
@router.get("/{user_id}/logs", response_model=list[ActivityLogResponse])
def get_user_logs(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    logs = db.query(UserActivityLogs)\
            .filter(UserActivityLogs.UserId == user_id)\
            .order_by(UserActivityLogs.Timestamp.desc())\
            .all()

    return logs

@router.patch("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    body: ResetPasswordSchema,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.PasswordHash = hash_password(body.NewPassword)

    db.add(UserActivityLogs(UserId=user.UserId, Action="Password Reset"))
    db.commit()

    return {"message": "Password Reset Successfully"}

@router.get("/stats/summary")
def summary(db: Session = Depends(get_db), admin=Depends(require_admin)):

    total = db.query(User).count()
    active = db.query(User).filter(User.IsActive == True).count()

    students = db.query(User).filter(User.Role == "Student").count()
    faculty = db.query(User).filter(User.Role == "Faculty").count()
    admins = db.query(User).filter(User.Role == "Admin").count()

    return {
        "total": total,
        "active": active,
        "students": students,
        "faculty": faculty,
        "admins": admins
    }
