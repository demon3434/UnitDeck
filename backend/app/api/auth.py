from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.core.auth_mgr import AuthManager

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/login")
def login(req: LoginRequest):
    token = AuthManager.verify_login(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": token, "username": req.username}

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

