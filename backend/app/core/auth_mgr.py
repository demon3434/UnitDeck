import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
AUTH_FILE = DATA_DIR / "auth.json"

class AuthUser(BaseModel):
    username: str = "admin"
    password_hash: str = ""
    salt: str = ""

# Active token store: token -> expiry timestamp
_TOKEN_STORE: dict[str, float] = {}

def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

class AuthManager:
    @staticmethod
    def ensure_auth():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not AUTH_FILE.exists():
            salt = secrets.token_hex(16)
            pwd_hash = hash_password("admin123", salt)
            user = AuthUser(username="admin", password_hash=pwd_hash, salt=salt)
            with open(AUTH_FILE, "w", encoding="utf-8") as f:
                json.dump(user.model_dump(), f, indent=2)

    @staticmethod
    def get_user() -> AuthUser:
        AuthManager.ensure_auth()
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AuthUser(**data)
        except Exception:
            return AuthUser()

    @staticmethod
    def verify_login(username: str, password: str) -> Optional[str]:
        user = AuthManager.get_user()
        if username == user.username:
            computed = hash_password(password, user.salt)
            if computed == user.password_hash:
                token = secrets.token_urlsafe(32)
                _TOKEN_STORE[token] = time.time() + (30 * 86400) # 30 days valid
                return token
        return None

    @staticmethod
    def verify_token(token: str) -> bool:
        if not token:
            return False
        exp = _TOKEN_STORE.get(token)
        if exp and exp > time.time():
            return True
        return False

    @staticmethod
    def update_password(old_pwd: str, new_pwd: str) -> bool:
        user = AuthManager.get_user()
        if hash_password(old_pwd, user.salt) != user.password_hash:
            return False
        new_salt = secrets.token_hex(16)
        user.salt = new_salt
        user.password_hash = hash_password(new_pwd, new_salt)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(user.model_dump(), f, indent=2)
        return True

