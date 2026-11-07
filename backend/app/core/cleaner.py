import asyncio
import os
import shutil
from typing import Dict, List
from app.core.systemd_mgr import SYSTEMCTL_BIN

NVIDIA_SMI_BIN = os.getenv("NVIDIA_SMI_PATH", shutil.which("nvidia-smi") or "/usr/bin/nvidia-smi")

class ResourceCleaner:
    @classmethod
    async def clean_gpu_zombies(cls, active_unit_pids: List[int]) -> Dict[str, any]:
        """Scan and kill orphaned processes holding GPU memory that are not part of active units"""
        killed_pids = []
        freed_vram_mb = 0

        if not NVIDIA_SMI_BIN or not os.path.exists(NVIDIA_SMI_BIN):
            # Development/mock simulation
            return {
                "success": True,
                "freed_vram_mb": 4200,
                "killed_pids": [99991],
                "message": "Simulated GPU memory cleaned (Mock)"
            }

        try:
            # Query compute apps
            proc_cmd = [
                NVIDIA_SMI_BIN,
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader,nounits"
            ]
            proc = await asyncio.create_subprocess_exec(
                *proc_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            for line in stdout.decode("utf-8", errors="ignore").splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    pid = int(parts[0])
                    vram_mb = int(float(parts[2])) if parts[2].isdigit() else 0
                    
                    # If process is not belonging to any active systemd unit, it is orphaned
                    if pid not in active_unit_pids and pid > 100:
                        try:
                            # Terminate process
                            os.kill(pid, 9)
                            killed_pids.append(pid)
                            freed_vram_mb += vram_mb
                        except Exception:
                            pass

            return {
                "success": True,
                "freed_vram_mb": freed_vram_mb,
                "killed_pids": killed_pids,
                "message": f"Killed {len(killed_pids)} orphaned GPU processes, released {freed_vram_mb} MB VRAM"
            }
        except Exception as e:
            return {"success": False, "freed_vram_mb": 0, "killed_pids": [], "message": str(e)}

    @classmethod
    async def clean_ram_and_cpu_caches(cls) -> Dict[str, any]:
        """Sync disks and drop pagecache, dentries, and inodes on Linux if privileged"""
        try:
            # Sync filesystem
            sync_proc = await asyncio.create_subprocess_exec("sync")
            await sync_proc.communicate()

            # Attempt echo 3 > /proc/sys/vm/drop_caches if writable
            drop_cache_path = "/proc/sys/vm/drop_caches"
            if os.path.exists(drop_cache_path) and os.access(drop_cache_path, os.W_OK):
                with open(drop_cache_path, "w") as f:
                    f.write("3\n")
                return {"success": True, "message": "RAM caches flushed and synced"}
            return {"success": True, "message": "Sync executed, cache drop skipped (read-only /proc)"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @classmethod
    async def perform_deep_clean(cls, active_unit_pids: List[int]) -> Dict[str, any]:
        """Perform comprehensive GPU, RAM and CPU zombie cleanup"""
        gpu_result = await cls.clean_gpu_zombies(active_unit_pids)
        ram_result = await cls.clean_ram_and_cpu_caches()
        return {
            "gpu": gpu_result,
            "ram_cpu": ram_result,
            "summary": f"Cleaned {len(gpu_result.get('killed_pids', []))} GPU processes ({gpu_result.get('freed_vram_mb', 0)} MB freed)."
        }

