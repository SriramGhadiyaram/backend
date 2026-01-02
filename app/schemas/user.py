from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    UserId: int
    FullName: str
    Email: str
    Role: str
    Department: str | None
    IsActive: bool
    CreatedAt: datetime
    LastLogin: datetime | None

    class Config:
        from_attributes = True

class CreateUserSchema(BaseModel):
    FullName: str
    Email: str
    Role: str
    Department: str | None
    Password: str


class UpdateUserSchema(BaseModel):
    Role: str | None = None
    Department: str | None = None

class ResetPasswordSchema(BaseModel):
    NewPassword: str

