import asyncio
import glob
import os
import shutil
from typing import Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.systemd_mgr import _MOCK_UNITS

router = APIRouter(prefix="/api/gpu", tags=["GPU"])

NVIDIA_SMI_BIN = os.getenv("NVIDIA_SMI_PATH", shutil.which("nvidia-smi") or "/usr/bin/nvidia-smi")

class GpuProcess(BaseModel):
    pid: int
    process_name: str
    used_memory_mb: int

class GpuInfo(BaseModel):
    available: bool
    name: str = "GPU"
    driver_version: str = "Kernel Driver"
    cuda_version: str = "N/A"
    total_memory_mb: int = 12288
    used_memory_mb: int = 0
    free_memory_mb: int = 12288
    memory_percent: float = 0.0
    gpu_utilization_percent: int = 0
    temperature_celsius: int = 45
    power_watts: Optional[float] = None
    processes: List[GpuProcess] = []

def read_amdgpu_sysfs() -> Optional[GpuInfo]:
    """Native Linux sysfs probe for AMD Radeon GPUs (e.g. RX 6700XT/6750XT 12GB)"""
    drm_cards = glob.glob("/sys/class/drm/card*/device/mem_info_vram_total")
    if not drm_cards:
        return None
    
    dev_dir = os.path.dirname(drm_cards[0])
    try:
        with open(os.path.join(dev_dir, "mem_info_vram_total"), "r") as f:
            total_bytes = int(f.read().strip())
        with open(os.path.join(dev_dir, "mem_info_vram_used"), "r") as f:
            used_bytes = int(f.read().strip())
            
        busy_pct = 0
        busy_path = os.path.join(dev_dir, "gpu_busy_percent")
        if os.path.exists(busy_path):
            with open(busy_path, "r") as f:
                busy_pct = int(f.read().strip())

        temp_c = 45
        temp_paths = glob.glob(os.path.join(dev_dir, "hwmon", "hwmon*", "temp1_input"))
        if temp_paths:
            with open(temp_paths[0], "r") as f:
                temp_c = int(int(f.read().strip()) / 1000)

        total_mb = int(total_bytes / (1024 * 1024))
        used_mb = int(used_bytes / (1024 * 1024))
        free_mb = max(0, total_mb - used_mb)
        pct = round((used_mb / total_mb * 100), 1) if total_mb > 0 else 0.0

        return GpuInfo(
            available=True,
            name="AMD Radeon RX 6700/6750 XT (12GB)",
            driver_version="amdgpu (Kernel)",
            cuda_version="ROCm/Sysfs",
            total_memory_mb=total_mb,
            used_memory_mb=used_mb,
            free_memory_mb=free_mb,
            memory_percent=pct,
            gpu_utilization_percent=busy_pct,
            temperature_celsius=temp_c,
            power_watts=None,
            processes=[]
        )
    except Exception:
        return None

@router.get("/status", response_model=GpuInfo)
async def get_gpu_status():
    """Retrieve GPU VRAM and statistics (Supports AMD sysfs & NVIDIA smi)"""
    # 1. Try AMD sysfs first (Linux native)
    amd_info = read_amdgpu_sysfs()
    if amd_info:
        return amd_info

    # 2. Try NVIDIA smi
    if NVIDIA_SMI_BIN and os.path.exists(NVIDIA_SMI_BIN):
        try:
            query_fields = "name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw"
            cmd = [NVIDIA_SMI_BIN, f"--query-gpu={query_fields}", "--format=csv,noheader,nounits"]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            lines = stdout.decode("utf-8", errors="ignore").strip().splitlines()
            if lines:
                parts = [p.strip() for p in lines[0].split(",")]
                total = int(float(parts[2]))
                used = int(float(parts[3]))
                free = int(float(parts[4]))
                util = int(float(parts[5])) if parts[5].isdigit() else 0
                temp = int(float(parts[6])) if parts[6].isdigit() else 0
                power = float(parts[7]) if len(parts) > 7 and parts[7].replace('.', '', 1).isdigit() else None
                pct = round((used / total * 100), 1) if total > 0 else 0.0
                return GpuInfo(
                    available=True,
                    name=parts[0],
                    driver_version=parts[1],
                    cuda_version="Detected",
                    total_memory_mb=total,
                    used_memory_mb=used,
                    free_memory_mb=free,
                    memory_percent=pct,
                    gpu_utilization_percent=util,
                    temperature_celsius=temp,
                    power_watts=power
                )
        except Exception:
            pass

    # 3. Fallback to realistic mock representation
    active_count = sum(1 for v in _MOCK_UNITS.values() if v.get("state") == "active")
    used_mb = 1200 + active_count * 6800 if active_count > 0 else 450
    used_mb = min(used_mb, 12288)
    free_mb = max(0, 12288 - used_mb)
    return GpuInfo(
        available=True,
        name="Radeon / GeForce (12GB Profile)",
        driver_version="Universal Driver (Mock)",
        cuda_version="Direct",
        total_memory_mb=12288,
        used_memory_mb=used_mb,
        free_memory_mb=free_mb,
        memory_percent=round((used_mb / 12288) * 100, 1),
        gpu_utilization_percent=active_count * 35 if active_count > 0 else 0,
        temperature_celsius=48 if active_count > 0 else 38
    )
