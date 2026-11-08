import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional, Tuple
import bcrypt
from pydantic import BaseModel

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
AUTH_FILE = DATA_DIR / "auth.json"

class AuthUser(BaseModel):
    username: str = "admin"
    password_hash: str = ""
    salt: str = ""
    token_version: int = 1

class LoginRateLimiter:
    """Sliding-window IP rate limiter to block brute-force login attempts"""
    def __init__(self, max_attempts: int = 5, window_seconds: float = 60.0, lockout_seconds: float = 900.0):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lockouts: dict[str, float] = {}

    def is_locked(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        lock_until = self._lockouts.get(client_ip, 0.0)
        if lock_until > now:
            return True, int(lock_until - now)
        if client_ip in self._lockouts:
            del self._lockouts[client_ip]
        return False, 0

    def record_failure(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        attempts = [t for t in self._attempts.get(client_ip, []) if now - t <= self.window_seconds]
        attempts.append(now)
        self._attempts[client_ip] = attempts
        if len(attempts) >= self.max_attempts:
            lock_until = now + self.lockout_seconds
            self._lockouts[client_ip] = lock_until
            self._attempts.pop(client_ip, None)
            return True, int(self.lockout_seconds)
        return False, 0

    def record_success(self, client_ip: str):
        self._attempts.pop(client_ip, None)
        self._lockouts.pop(client_ip, None)

rate_limiter = LoginRateLimiter()

# Token Store: token -> dict with username, version, exp
_TOKEN_STORE: dict[str, dict] = {}

def hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt with automatic salt generation"""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def verify_password_hash(password: str, stored_hash: str, salt: str = "") -> Tuple[bool, bool]:
    """
    Verify password against stored hash.
    Returns: (is_valid, is_legacy)
    Supports backward-compatible SHA-256 with constant-time comparison.
    """
    if not stored_hash:
        return False, False
    
    # Check if modern bcrypt hash
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        try:
            is_valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            return is_valid, False
        except Exception:
            return False, False
    
    # Legacy SHA-256 verification with constant-time comparison
    legacy_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    if secrets.compare_digest(legacy_hash, stored_hash):
        return True, True
    return False, False

class AuthManager:
    @staticmethod
    def ensure_auth():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not AUTH_FILE.exists():
            pwd_hash = hash_password_bcrypt("admin123")
            user = AuthUser(username="admin", password_hash=pwd_hash, salt="", token_version=1)
            AuthManager.save_user(user)

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
    def save_user(user: AuthUser):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(user.model_dump(), f, indent=2)

    @staticmethod
    def clean_expired_tokens():
        now = time.time()
        expired_keys = [k for k, v in _TOKEN_STORE.items() if v.get("exp", 0) <= now]
        for k in expired_keys:
            _TOKEN_STORE.pop(k, None)

    @staticmethod
    def verify_login(username: str, password: str, client_ip: str = "127.0.0.1") -> Tuple[Optional[str], Optional[str]]:
        """
        Verify login credentials with rate-limiting and auto-upgrade of legacy hashes.
        Returns: (token, error_message)
        """
        locked, remaining = rate_limiter.is_locked(client_ip)
        if locked:
            return None, f"Too many failed attempts. Try again in {remaining} seconds."

        user = AuthManager.get_user()
        is_user_match = secrets.compare_digest(username, user.username)
        
        is_valid, is_legacy = verify_password_hash(password, user.password_hash, user.salt)

        if is_user_match and is_valid:
            rate_limiter.record_success(client_ip)
            
            # Auto-upgrade legacy SHA-256 hash to bcrypt transparently
            if is_legacy:
                user.password_hash = hash_password_bcrypt(password)
                user.salt = ""
                AuthManager.save_user(user)

            AuthManager.clean_expired_tokens()
            token = secrets.token_urlsafe(32)
            _TOKEN_STORE[token] = {
                "username": user.username,
                "version": user.token_version,
                "exp": time.time() + (7 * 86400) # 7 days validity
            }
            return token, None

        is_locked_now, lock_time = rate_limiter.record_failure(client_ip)
        if is_locked_now:
            return None, f"Too many failed attempts. Locked out for {lock_time} seconds."
        return None, "Invalid username or password"

    @staticmethod
    def verify_token(token: str) -> bool:
        if not token:
            return False
        AuthManager.clean_expired_tokens()
        token_info = _TOKEN_STORE.get(token)
        if not token_info:
            return False

        if token_info.get("exp", 0) <= time.time():
            _TOKEN_STORE.pop(token, None)
            return False

        user = AuthManager.get_user()
        # Verify token_version: if password changed, token_version changes, invalidating token
        if token_info.get("version") != user.token_version:
            _TOKEN_STORE.pop(token, None)
            return False

        return True

    @staticmethod
    def revoke_token(token: str) -> bool:
        """Revoke active token on explicit logout"""
        if token in _TOKEN_STORE:
            del _TOKEN_STORE[token]
            return True
        return False

    @staticmethod
    def update_password(old_pwd: str, new_pwd: str) -> bool:
        user = AuthManager.get_user()
        is_valid, _ = verify_password_hash(old_pwd, user.password_hash, user.salt)
        if not is_valid:
            return False

        user.password_hash = hash_password_bcrypt(new_pwd)
        user.salt = ""
        user.token_version += 1 # Invalidate all active tokens globally
        AuthManager.save_user(user)
        # Clear local token store to kick current sessions
        _TOKEN_STORE.clear()
        return True
