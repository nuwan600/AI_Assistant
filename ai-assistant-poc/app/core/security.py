# pyrefly: ignore [missing-import]
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import settings
from app.models.schema import UserInDB, UserRole

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Hardcoded Users for RBAC testing
MOCK_USERS_DB = {
    "alice": {
        "username": "alice",
        "role": UserRole.VIEWER,
        "hashed_password": get_password_hash("viewer123"),
        "disabled": False
    },
    "bob": {
        "username": "bob",
        "role": UserRole.ANALYST,
        "hashed_password": get_password_hash("analyst123"),
        "disabled": False
    },
    "carol": {
        "username": "carol",
        "role": UserRole.ADMINISTRATOR,
        "hashed_password": get_password_hash("admin123"),
        "disabled": False
    }
}

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
