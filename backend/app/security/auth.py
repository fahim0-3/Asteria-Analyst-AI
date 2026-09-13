import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Role, User
from app.db.session import get_db

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    """Hash a password with salted PBKDF2-SHA256."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        _, salt, expected = hashed.split("$", 2)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def create_token(user: User) -> str:
    settings = get_settings()
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return jwt.encode({"sub": user.id, "role": user.role.value, "exp": expires}, settings.jwt_secret_key, algorithm="HS256")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        subject = jwt.decode(token, get_settings().jwt_secret_key, algorithms=["HS256"])["sub"]
    except (jwt.PyJWTError, KeyError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc
    user = db.get(User, subject)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive user")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


def seed_users(db: Session) -> None:
    if db.scalar(select(User).limit(1)):
        return
    db.add_all([
        User(name="Asteria Analyst", email="analyst@asteria.demo", role=Role.analyst, password_hash=hash_password("Analyst123!")),
        User(name="Asteria Admin", email="admin@asteria.demo", role=Role.admin, password_hash=hash_password("Admin123!")),
    ])
    db.commit()
