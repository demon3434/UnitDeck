import asyncio
import logging
import os
import re
import shutil
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("unitdeck.systemd")

UNIT_NAME_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-\.@:]*(\.service|\.target|\.socket)?$")

CRITICAL_SYSTEM_SERVICES = {
    "ssh", "sshd", "ssh.service", "sshd.service",
    "docker", "docker.service", "dockerd", "dockerd.service", "containerd", "containerd.service",
    "systemd-networkd", "systemd-networkd.service",
    "networkmanager", "networkmanager.service", "networking", "networking.service",
    "systemd-resolved", "systemd-resolved.service",
    "systemd-journald", "systemd-journald.service",
    "dbus", "dbus.service",
    "systemd-logind", "systemd-logind.service",
    "polkit", "polkit.service",
    "apparmor", "apparmor.service",
    "firewalld", "firewalld.service", "ufw", "ufw.service"
}

NSENTER_BIN = shutil.which("nsenter") or "/usr/bin/nsenter"
USE_NSENTER = False

# Check if nsenter can target PID 1 (host systemd)
def check_nsenter():
    global USE_NSENTER
    if NSENTER_BIN and os.path.exists(NSENTER_BIN):
        try:
            import subprocess
            res = subprocess.run(
                [NSENTER_BIN, "-t", "1", "-m", "-u", "-i", "-n", "-p", "--", "systemctl", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            if res.returncode == 0:
                USE_NSENTER = True
        except Exception:
            USE_NSENTER = False

check_nsenter()

SYSTEMCTL_BIN = shutil.which("systemctl") or "/bin/systemctl"
JOURNALCTL_BIN = shutil.which("journalctl") or "/bin/journalctl"

SYSTEM_CORE_PREFIXES = (
    "systemd-", "sys-", "getty@", "serial-getty@", "dbus", "udev", 
    "user@", "emergency.", "rescue.", "plymouth-", "dracut-", "kmod-", 
    "apparmor", "auditd", "cron", "polkit", "rsyslog", "snapd.", "apt-daily",
    "ifupdown", "container-getty",
    # Audio, Bluetooth, Display, Printing
    "alsa-", "bluetooth", "pulseaudio", "pipewire", "wireplumber", "bluez",
    "cups", "cups-browsed", "colord", "saned", "speech-dispatcher", "gdm", "lightdm",
    # Power, thermal, hardware, disks
    "acpid", "thermald", "power-profiles-daemon", "upower", "udisks2", "smartmontools",
    "mdadm", "lvm2-", "dm-event", "blk-availability", "multipathd", "rtkit-daemon",
    # Networking and discovery
    "networkd-dispatcher", "networking", "NetworkManager", "wpa_supplicant", "modemmanager",
    "avahi-daemon", "irqbalance", "uuidd", "whoopsie", "kerneloops", "apport",
    # Maintenance, boot, packages
    "unattended-upgrades", "packagekit", "e2scrub", "fstrim", "man-db", "motd-news",
    "grub-", "finalrd", "dmesg", "console-setup", "keyboard-setup", "secureboot-db",
    "gpu-manager", "accounts-daemon"
)

USER_APP_KEYWORDS = (
    "ollama", "vllm", "comfy", "comfyui", "sd", "webui", "diff", "whisper",
    "voice", "audio", "model", "llm", "chat", "bot", "worker", "fastapi",
    "gradio", "streamlit", "open-webui", "text-generation", "kobold", "tabby",
    "heartmula", "acestep", "diffrhythm", "voicestudio", "jupyter", "torch", "rag"
)

class UnitDetail(BaseModel):
    unit_name: str
    display_name: Optional[str] = None
    scope: str = "system"
    load_state: str = "unknown"
    active_state: str = "unknown"
    sub_state: str = "unknown"
    is_enabled: bool = False
    main_pid: int = 0
    memory_current: Optional[str] = None
    started_at: Optional[str] = None
    description: str = ""

_MOCK_UNITS: Dict[str, Dict[str, any]] = {
    "heartmula.service": {"state": "active", "enabled": True, "pid": 10421, "mem": "4.8 GB", "scope": "system", "source_type": "custom", "is_recommended": True},
    "comfyui.service": {"state": "inactive", "enabled": False, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "custom", "is_recommended": True},
    "diffrhythm2.service": {"state": "inactive", "enabled": True, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "custom", "is_recommended": True},
    "acestep.service": {"state": "inactive", "enabled": False, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "custom", "is_recommended": True},
    "voicestudio.service": {"state": "inactive", "enabled": True, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "custom", "is_recommended": True},
    "cups.service": {"state": "inactive", "enabled": False, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "system_package", "is_recommended": False},
    "bluetooth.service": {"state": "inactive", "enabled": False, "pid": 0, "mem": "0 B", "scope": "system", "source_type": "system_package", "is_recommended": False},
}

def build_cmd(tool: str, args: List[str], scope: str = "system") -> List[str]:
    """Build command using nsenter if in host container, or direct binary"""
    scope_args = ["--user"] if scope == "user" else []
    if USE_NSENTER:
        return [NSENTER_BIN, "-t", "1", "-m", "-u", "-i", "-n", "-p", "--", tool] + scope_args + args
    bin_path = SYSTEMCTL_BIN if tool == "systemctl" else JOURNALCTL_BIN
    return [bin_path] + scope_args + args

class SystemdManager:
    @classmethod
    def is_available(cls) -> bool:
        return USE_NSENTER or bool(SYSTEMCTL_BIN and os.path.exists(SYSTEMCTL_BIN))

    @classmethod
    async def get_etc_custom_services(cls) -> set:
        """Detect user-created .service files placed in /etc/systemd/system/ (ignoring vendor symlinks)"""
        custom_units = set()
        try:
            if os.path.isdir("/etc/systemd/system"):
                for fname in os.listdir("/etc/systemd/system"):
                    if fname.endswith(".service"):
                        fpath = os.path.join("/etc/systemd/system", fname)
                        if os.path.isfile(fpath) and not os.path.islink(fpath):
                            custom_units.add(fname)
        except Exception:
            pass

        if USE_NSENTER and not custom_units:
            try:
                cmd = [NSENTER_BIN, "-t", "1", "-m", "-u", "-i", "-n", "-p", "--", "find", "/etc/systemd/system/", "-maxdepth", "1", "-name", "*.service", "-type", "f"]
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, _ = await proc.communicate()
                for line in stdout.decode("utf-8", errors="ignore").splitlines():
                    fname = os.path.basename(line.strip())
                    if fname.endswith(".service"):
                        custom_units.add(fname)
            except Exception:
                pass

        return custom_units

    @classmethod
    async def get_active_unit_names(cls, scope: str = "system") -> set:
        """Get set of unit names currently in active/running state"""
        active_units = set()
        try:
            cmd = build_cmd("systemctl", ["list-units", "--type=service", "--state=active", "--no-pager", "--no-legend"], scope=scope)
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            for line in stdout.decode("utf-8", errors="ignore").splitlines():
                parts = line.split()
                if parts and parts[0].endswith(".service"):
                    active_units.add(parts[0])
        except Exception:
            pass
        return active_units

    @classmethod
    async def list_candidate_services(cls, include_system_core: bool = False) -> List[Dict[str, any]]:
        if not cls.is_available():
            mock_items = []
            for k, v in _MOCK_UNITS.items():
                is_rec = v.get("is_recommended", True)
                if not include_system_core and not is_rec:
                    continue
                mock_items.append({
                    "unit_name": k,
                    "scope": v["scope"],
                    "status": "enabled" if v["enabled"] else "disabled",
                    "active_state": v.get("state", "inactive"),
                    "is_user_app": is_rec,
                    "source_type": v.get("source_type", "custom"),
                    "is_recommended": is_rec,
                    "description": ""
                })
            return sorted(mock_items, key=lambda x: (not x["is_recommended"], x["active_state"] != "active", x["unit_name"]))

        etc_custom_services = await cls.get_etc_custom_services()
        results = []
        seen = set()

        for scope in ["system", "user"]:
            try:
                active_units = await cls.get_active_unit_names(scope=scope)
                cmd = build_cmd("systemctl", ["list-unit-files", "--type=service", "--no-pager", "--no-legend"], scope=scope)
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, _ = await proc.communicate()
                lines = stdout.decode("utf-8", errors="ignore").splitlines()
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        uname = parts[0]
                        status = parts[1]
                        if not uname.endswith(".service") or (uname, scope) in seen:
                            continue
                        seen.add((uname, scope))

                        is_active = uname in active_units
                        is_etc_custom = uname in etc_custom_services
                        is_keyword_match = any(kw in uname.lower() for kw in USER_APP_KEYWORDS)
                        is_core = any(uname.startswith(prefix) for prefix in SYSTEM_CORE_PREFIXES)

                        if scope == "user":
                            source_type = "user_scope"
                            is_recommended = True
                        elif is_etc_custom:
                            source_type = "custom"
                            is_recommended = True
                        elif is_keyword_match:
                            source_type = "custom"
                            is_recommended = True
                        elif is_core:
                            source_type = "system_package"
                            is_recommended = False
                        else:
                            source_type = "system_package"
                            is_recommended = False

                        # If user didn't ask to include system core daemons, filter out core
                        if not include_system_core and not is_recommended and is_core:
                            continue

                        results.append({
                            "unit_name": uname,
                            "scope": scope,
                            "status": status,
                            "active_state": "active" if is_active else "inactive",
                            "is_user_app": is_recommended,
                            "source_type": source_type,
                            "is_recommended": is_recommended,
                            "description": ""
                        })
            except Exception:
                continue

        return sorted(results, key=lambda x: (not x["is_recommended"], x["active_state"] != "active", x["unit_name"]))

    @classmethod
    async def get_unit_status(cls, unit_name: str, scope: str = "system") -> UnitDetail:
        if not cls.is_available():
            data = _MOCK_UNITS.get(unit_name, {"state": "inactive", "enabled": False, "pid": 0, "mem": "0 B", "scope": scope})
            return UnitDetail(
                unit_name=unit_name, scope=scope, load_state="loaded",
                active_state=data["state"], sub_state="running" if data["state"] == "active" else "dead",
                is_enabled=data["enabled"], main_pid=data["pid"], memory_current=data["mem"], description=unit_name
            )

        try:
            # Check is-enabled
            en_cmd = build_cmd("systemctl", ["is-enabled", unit_name], scope=scope)
            en_proc = await asyncio.create_subprocess_exec(*en_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            en_stdout, _ = await en_proc.communicate()
            is_enabled = en_stdout.decode("utf-8", errors="ignore").strip() == "enabled"

            # Query show properties
            props = ["LoadState", "ActiveState", "SubState", "Description", "MainPID", "MemoryCurrent", "ActiveEnterTimestamp"]
            show_cmd = build_cmd("systemctl", ["show", unit_name, f"--property={','.join(props)}", "--no-pager"], scope=scope)
            proc = await asyncio.create_subprocess_exec(*show_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            
            p_dict = {}
            for line in stdout.decode("utf-8", errors="ignore").splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    p_dict[k] = v

            mem_bytes = p_dict.get("MemoryCurrent", "")
            mem_display = None
            if mem_bytes and mem_bytes.isdigit() and int(mem_bytes) < 18446744073709551615:
                mb = int(mem_bytes) / (1024 * 1024)
                mem_display = f"{mb:.1f} MB" if mb < 1024 else f"{(mb/1024):.2f} GB"

            return UnitDetail(
                unit_name=unit_name,
                scope=scope,
                load_state=p_dict.get("LoadState", "unknown"),
                active_state=p_dict.get("ActiveState", "unknown"),
                sub_state=p_dict.get("SubState", "unknown"),
                is_enabled=is_enabled,
                main_pid=int(p_dict.get("MainPID", 0) or 0),
                memory_current=mem_display,
                started_at=p_dict.get("ActiveEnterTimestamp", None),
                description=p_dict.get("Description", "")
            )
        except Exception:
            return UnitDetail(unit_name=unit_name, scope=scope)

    @classmethod
    async def control_unit(cls, unit_name: str, action: str, scope: str = "system", force_kill_timeout: int = 8) -> Dict[str, any]:
        if action not in ["start", "stop", "restart", "enable", "disable"]:
            raise ValueError(f"Unsupported action: {action}")

        if not UNIT_NAME_REGEX.match(unit_name):
            raise ValueError(f"Invalid unit name format: {unit_name}")

        # Guard critical system infrastructure services from being stopped or disabled
        if action in ["stop", "disable"]:
            clean_name = unit_name.lower().removesuffix(".service")
            if clean_name in CRITICAL_SYSTEM_SERVICES or unit_name.lower() in CRITICAL_SYSTEM_SERVICES:
                raise PermissionError(f"Operating critical infrastructure service '{unit_name}' is strictly prohibited.")

        if not cls.is_available():
            if unit_name in _MOCK_UNITS:
                if action == "start": _MOCK_UNITS[unit_name]["state"] = "active"
                elif action == "stop": _MOCK_UNITS[unit_name]["state"] = "inactive"
                elif action == "restart": _MOCK_UNITS[unit_name]["state"] = "active"
                elif action == "enable": _MOCK_UNITS[unit_name]["enabled"] = True
                elif action == "disable": _MOCK_UNITS[unit_name]["enabled"] = False
            return {"unit_name": unit_name, "action": action, "status": "success", "mock": True}

        cmd = build_cmd("systemctl", [action, "--", unit_name], scope=scope)
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(force_kill_timeout))
            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="ignore").strip()
                raise RuntimeError(f"Action {action} failed: {err}")
            return {"unit_name": unit_name, "action": action, "status": "success"}
        except asyncio.TimeoutError:
            if action == "stop" and force_kill_timeout > 0:
                kill_cmd = build_cmd("systemctl", ["kill", "-s", "SIGKILL", "--", unit_name], scope=scope)
                kill_p = await asyncio.create_subprocess_exec(*kill_cmd)
                await kill_p.communicate()
                return {"unit_name": unit_name, "action": action, "status": "force_killed"}
            raise RuntimeError(f"Action {action} timed out after {force_kill_timeout}s")

    @classmethod
    async def get_unit_logs(cls, unit_name: str, lines: int = 60, scope: str = "system") -> str:
        if not UNIT_NAME_REGEX.match(unit_name):
            raise ValueError(f"Invalid unit name format: {unit_name}")

        if not cls.is_available():
            return f"[{unit_name}] Mock service logs."
        cmd = build_cmd("journalctl", ["-u", unit_name, "-n", str(lines), "--no-pager"], scope=scope)
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8", errors="ignore")

    @classmethod
    async def execute_host_power(cls, action: str, operator: str = "admin") -> Dict[str, any]:
        """Safely trigger host-level reboot or poweroff via systemctl/shutdown."""
        if action not in ["reboot", "poweroff"]:
            raise ValueError(f"Unsupported host power action: {action}. Must be 'reboot' or 'poweroff'.")

        logger.warning(f"SECURITY AUDIT: Host power action '{action}' triggered by operator '{operator}'")

        if not cls.is_available():
            logger.info(f"Systemd not available in this environment. Simulating host power action: {action}")
            return {"action": action, "status": "scheduled", "mock": True}

        cmd = build_cmd("systemctl", [action])
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="ignore").strip()
                # Fallback to /sbin/shutdown if available
                if shutil.which("/sbin/shutdown") or os.path.exists("/sbin/shutdown"):
                    flag = "-r" if action == "reboot" else "-h"
                    fb_proc = await asyncio.create_subprocess_exec("/sbin/shutdown", flag, "now", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    _, fb_err = await asyncio.wait_for(fb_proc.communicate(), timeout=5.0)
                    if fb_proc.returncode == 0:
                        return {"action": action, "status": "scheduled", "fallback": True}
                raise RuntimeError(f"Host {action} execution failed: {err}")
            return {"action": action, "status": "scheduled"}
        except Exception as e:
            logger.error(f"Failed to execute host {action}: {e}")
            raise
