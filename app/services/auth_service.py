from datetime import datetime, timezone, timedelta
from bson import ObjectId
import bcrypt
import jwt

from app.config.settings import settings
from app.database.mongodb import users_collection
from app.services.common import now_utc, to_object_id, serialize_user_document


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid authentication token")


class AuthService:

    @staticmethod
    def authenticate(email: str, password: str) -> dict:
        user = users_collection.find_one({"email": email.lower()})
        if not user:
            raise ValueError("Invalid email or password")
        if not verify_password(password, user.get("password", "")):
            raise ValueError("Invalid email or password")
        if not user.get("is_active", True):
            raise ValueError("User account is deactivated")
        return serialize_user_document(user)

    @staticmethod
    def login(email: str, password: str) -> dict:
        user = AuthService.authenticate(email, password)
        token = create_access_token({
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    def register(data) -> dict:
        from app.services.user_service import UserService
        user = UserService.create_user(data)
        token = create_access_token({
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    def get_current_user_from_token(token: str) -> dict:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Invalid token payload")
        user = users_collection.find_one({"_id": to_object_id(sub)})
        if not user:
            raise ValueError("User not found")
        if not user.get("is_active", True):
            raise ValueError("User account is deactivated")
        return serialize_user_document(user)
