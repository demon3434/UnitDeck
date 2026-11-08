from fastapi import APIRouter, HTTPException, Query
from app.core.config import ConfigManager
from app.core.systemd_mgr import SystemdManager

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.get("/{unit_name}")
async def get_service_logs(
    unit_name: str,
    lines: int = Query(60, ge=10, le=500),
    scope: str = Query("system")
):
    """Fetch recent journalctl logs for specific unit - restricted to managed units"""
    cfg = ConfigManager.get_config()
    managed_names = {u.unit_name for u in cfg.units}
    if unit_name not in managed_names:
        raise HTTPException(status_code=403, detail=f"Access denied: unit '{unit_name}' is not in managed list.")

    logs = await SystemdManager.get_unit_logs(unit_name=unit_name, lines=lines, scope=scope)
    return {
        "unit_name": unit_name,
        "scope": scope,
        "lines_requested": lines,
        "content": logs
    }
