import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import ConfigManager
from app.core.systemd_mgr import SystemdManager, UnitDetail
from app.core.cleaner import ResourceCleaner

router = APIRouter(prefix="/api/services", tags=["Services Control"])

class ActionRequest(BaseModel):
    unit_name: str
    action: str # start, stop, restart, enable, disable
    scope: str = "system"

class ManagedServiceStatus(BaseModel):
    unit_name: str
    display_name: str
    description: str
    category: str
    scope: str
    is_custom: bool
    status: UnitDetail

@router.get("/status", response_model=List[ManagedServiceStatus])
async def get_all_services_status():
    """Retrieve runtime status of all user-selected managed services"""
    cfg = ConfigManager.get_config()
    results = []
    
    # Query statuses concurrently
    tasks = [
        SystemdManager.get_unit_status(unit.unit_name, scope=unit.scope)
        for unit in cfg.units if unit.enabled
    ]
    statuses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for unit, stat in zip([u for u in cfg.units if u.enabled], statuses):
        if isinstance(stat, Exception):
            stat = UnitDetail(unit_name=unit.unit_name, scope=unit.scope)
        stat.display_name = unit.display_name
        results.append(ManagedServiceStatus(
            unit_name=unit.unit_name,
            display_name=unit.display_name,
            description=unit.description or "",
            category=unit.category or "AI & Apps",
            scope=unit.scope,
            is_custom=unit.is_custom,
            status=stat
        ))
    return results

@router.post("/action")
async def execute_action(req: ActionRequest):
    """Execute single action (start, stop, restart, enable, disable)"""
    cfg = ConfigManager.get_config()
    unit = next((u for u in cfg.units if u.unit_name == req.unit_name), None)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit {req.unit_name} is not in managed list")
    
    timeout = cfg.settings.kill_timeout_seconds if cfg.settings.enable_force_kill else 0
    try:
        res = await SystemdManager.control_unit(
            unit_name=req.unit_name,
            action=req.action,
            scope=req.scope,
            force_kill_timeout=timeout
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-all")
async def stop_all_services():
    """Stop all managed services at once to completely clear GPU VRAM, RAM & CPU"""
    cfg = ConfigManager.get_config()
    units_to_stop = [u for u in cfg.units if u.enabled]
    timeout = cfg.settings.kill_timeout_seconds if cfg.settings.enable_force_kill else 0
    
    # Check current active statuses
    status_tasks = [SystemdManager.get_unit_status(u.unit_name, u.scope) for u in units_to_stop]
    statuses = await asyncio.gather(*status_tasks, return_exceptions=True)
    
    active_units = []
    for u, st in zip(units_to_stop, statuses):
        if not isinstance(st, Exception) and st.active_state in ["active", "activating"]:
            active_units.append(u)
            
    # Concurrently stop all active units
    stop_tasks = [
        SystemdManager.control_unit(u.unit_name, "stop", u.scope, force_kill_timeout=timeout)
        for u in active_units
    ]
    stop_results = await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    # Perform ghost cleaning if enabled in settings
    clean_summary = None
    if cfg.settings.enable_ghost_cleaning:
        clean_summary = await ResourceCleaner.perform_deep_clean(active_unit_pids=[])
        
    return {
        "status": "success",
        "stopped_count": len(active_units),
        "results": [
            r if not isinstance(r, Exception) else {"error": str(r)}
            for r in stop_results
        ],
        "cleaning": clean_summary
    }

@router.post("/clean")
async def clean_resources():
    """Manually trigger deep cleaning of GPU memory, RAM and CPU leftovers"""
    cfg = ConfigManager.get_config()
    # Find PIDs of any still active managed services so we don't accidentally kill them
    status_tasks = [SystemdManager.get_unit_status(u.unit_name, u.scope) for u in cfg.units if u.enabled]
    statuses = await asyncio.gather(*status_tasks, return_exceptions=True)
    active_pids = [st.main_pid for st in statuses if not isinstance(st, Exception) and st.main_pid > 0]
    
    result = await ResourceCleaner.perform_deep_clean(active_unit_pids=active_pids)
    return result

