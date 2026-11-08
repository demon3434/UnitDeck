import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, gpu, logs, services, systemd, system
from app.core.auth_mgr import AuthManager
from app.core.config import ConfigManager

ConfigManager.ensure_dir()
AuthManager.ensure_auth()

app = FastAPI(title="UnitDeck", description="AI Service & System Resource Control Hub", version="1.0.0")

# Standardized CORS configuration
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    allow_unauth_docs = os.getenv("ENABLE_DOCS_NO_AUTH", "0") == "1"
    
    # Allow login, health check, and frontend static assets without token
    is_public = (
        path.startswith("/api/auth/login") or 
        path == "/api/health" or 
        (allow_unauth_docs and (path.startswith("/docs") or path.startswith("/openapi.json"))) or
        (not path.startswith("/api/") and not path.startswith("/docs") and not path.startswith("/openapi.json"))
    )
    if is_public:
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else ""
    if not AuthManager.verify_token(token):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized. Please login."})
    
    return await call_next(request)

# Include Routers
app.include_router(auth.router)
app.include_router(systemd.router)
app.include_router(services.router)
app.include_router(system.router)
app.include_router(gpu.router)
app.include_router(logs.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "UnitDeck"}

# Serve Frontend static build
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
