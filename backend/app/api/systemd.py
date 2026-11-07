from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import ConfigManager, ManagedUnit, SystemSettings
from app.core.systemd_mgr import SystemdManager

router = APIRouter(prefix="/api/systemd", tags=["Systemd Discovery & Config"])

class SaveUnitsRequest(BaseModel):
    units: List[ManagedUnit]

class CustomUnitRequest(BaseModel):
    display_name: str
    unit_name: str
    description: Optional[str] = ""
    category: Optional[str] = "Custom"
    scope: str = "system"
    custom_start_cmd: Optional[str] = None
    custom_stop_cmd: Optional[str] = None

@router.get("/candidates")
async def get_candidates(include_core: bool = False):
    """List detected services from systemd, excluding OS core services by default"""
    services = await SystemdManager.list_candidate_services(include_system_core=include_core)
    current_managed = {u.unit_name for u in ConfigManager.get_config().units}
    
    # Enrich with managed status
    for s in services:
        s["is_managed"] = s["unit_name"] in current_managed
    return services

@router.get("/config")
def get_config():
    """Get active configuration (managed units and system settings)"""
    return ConfigManager.get_config()

@router.post("/config/units")
def save_managed_units(req: SaveUnitsRequest):
    """Save user-selected units to be managed on web dashboard"""
    ConfigManager.save_units(req.units)
    return {"status": "success", "count": len(req.units)}

@router.post("/config/custom")
def add_custom_unit(req: CustomUnitRequest):
    """Add a custom program (fallback solution requested by user)"""
    cfg = ConfigManager.get_config()
    new_unit = ManagedUnit(
        unit_name=req.unit_name,
        display_name=req.display_name,
        description=req.description,
        category=req.category or "Custom",
        scope=req.scope,
        is_custom=True,
        custom_start_cmd=req.custom_start_cmd,
        custom_stop_cmd=req.custom_stop_cmd,
        enabled=True
    )
    # Check if duplicate
    units = [u for u in cfg.units if u.unit_name != req.unit_name]
    units.append(new_unit)
    ConfigManager.save_units(units)
    return {"status": "success", "unit": new_unit}

@router.post("/config/settings")
def update_settings(settings: SystemSettings):
    """Update system settings (timeout kill, ghost cleaning, theme)"""
    ConfigManager.update_settings(settings)
    return {"status": "success", "settings": settings}

