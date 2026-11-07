from fastapi import APIRouter, Query
from app.core.systemd_mgr import SystemdManager

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.get("/{unit_name}")
async def get_service_logs(
    unit_name: str,
    lines: int = Query(60, ge=10, le=500),
    scope: str = Query("system")
):
    """Fetch recent journalctl logs for specific unit"""
    logs = await SystemdManager.get_unit_logs(unit_name=unit_name, lines=lines, scope=scope)
    return {
        "unit_name": unit_name,
        "scope": scope,
        "lines_requested": lines,
        "content": logs
    }

