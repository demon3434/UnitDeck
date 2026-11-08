from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from app.core.auth_mgr import AuthManager

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post("/login")
def login(req: LoginRequest, request: Request):
    client_ip = get_client_ip(request)
    token, err = AuthManager.verify_login(req.username, req.password, client_ip=client_ip)
    if err and ("Too many" in err or "Locked out" in err):
        raise HTTPException(status_code=429, detail=err)
    if not token:
        raise HTTPException(status_code=401, detail=err or "Invalid username or password")
    return {"token": token, "username": req.username}

@router.post("/logout")
def logout(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else ""
    if token:
        AuthManager.revoke_token(token)
    return {"status": "success", "message": "Logged out successfully"}

@router.get("/me")
def get_current_user(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else ""
    if not AuthManager.verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = AuthManager.get_user()
    return {"username": user.username, "authenticated": True}

@router.post("/password")
def change_password(req: PasswordChangeRequest, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else ""
    if not AuthManager.verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    success = AuthManager.update_password(req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    return {"status": "success", "message": "Password changed successfully"}
