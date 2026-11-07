import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
CONFIG_FILE = DATA_DIR / "config.json"

class ManagedUnit(BaseModel):
    unit_name: str = Field(..., description="Systemd unit name or custom identifier")
    display_name: str = Field(..., description="Friendly name")
    description: Optional[str] = Field("", description="Notes or details")
    category: Optional[str] = Field("AI & Apps", description="Category tag")
    scope: str = Field("system", description="system or user")
    is_custom: bool = Field(False, description="Whether this is a manually added program")
    custom_start_cmd: Optional[str] = Field(None, description="Custom start command if not standard systemd")
    custom_stop_cmd: Optional[str] = Field(None, description="Custom stop command")
    enabled: bool = Field(True, description="Whether to show in main dashboard")

class SystemSettings(BaseModel):
    # Kill & cleanup configurations
    enable_force_kill: bool = Field(True, description="Force kill (SIGKILL) if stop times out")
    kill_timeout_seconds: int = Field(8, description="Timeout seconds before SIGKILL")
    enable_ghost_cleaning: bool = Field(True, description="Clean zombie GPU/RAM/CPU processes on Stop All")
    
    # UI preferences
    theme: str = Field("night", description="Active DaisyUI theme")
    refresh_interval_sec: int = Field(3, description="Dashboard auto refresh interval in seconds")

class AppConfig(BaseModel):
    units: List[ManagedUnit] = Field(default_factory=list)
    settings: SystemSettings = Field(default_factory=SystemSettings)

class ConfigManager:
    @staticmethod
    def ensure_dir():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            default_config = AppConfig(
                units=[
                    ManagedUnit(unit_name="heartmula.service", display_name="HeartMuLa AI音乐生成", description="HeartMuLa AI Music Generation Web Service", scope="system"),
                    ManagedUnit(unit_name="comfyui.service", display_name="ComfyUI 绘画工具", description="ComfyUI Stable Diffusion GUI", scope="system"),
                    ManagedUnit(unit_name="diffrhythm2.service", display_name="DiffRhythm2 歌声合成", description="DiffRhythm2 AI Voice Engine", scope="system"),
                    ManagedUnit(unit_name="acestep.service", display_name="ACE-Step 伴奏生成", description="ACE-Step Music Production", scope="system"),
                    ManagedUnit(unit_name="voicestudio.service", display_name="VoiceStudio 声音工坊", description="VoiceStudio Speech & Vocal Suite", scope="system"),
                    ManagedUnit(unit_name="yue2-studio.service", display_name="Yue2-Studio 音乐创作", description="Yue2-Studio Music Inference", scope="system"),
                ],
                settings=SystemSettings()
            )
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config.model_dump(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def get_config() -> AppConfig:
        ConfigManager.ensure_dir()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            return AppConfig()

    @staticmethod
    def save_config(config: AppConfig):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def update_settings(settings: SystemSettings):
        cfg = ConfigManager.get_config()
        cfg.settings = settings
        ConfigManager.save_config(cfg)

    @staticmethod
    def save_units(units: List[ManagedUnit]):
        cfg = ConfigManager.get_config()
        cfg.units = units
        ConfigManager.save_config(cfg)
