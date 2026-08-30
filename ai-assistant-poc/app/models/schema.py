from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class UserRole(str, Enum):
    VIEWER = "Viewer"
    ANALYST = "Analyst"
    ADMINISTRATOR = "Administrator"

class User(BaseModel):
    username: str
    role: UserRole
    disabled: bool = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None