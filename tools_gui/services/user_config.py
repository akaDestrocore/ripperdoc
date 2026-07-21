#!/usr/bin/env python3

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from platformdirs import user_config_dir


APP_NAME = "ripperdoc"

DEFAULT_LAST_USED = {
    "priv_key_path": "",
    "pub_key_path": "",
    "aes_key_path": "",
    "input_dir": "",
    "output_dir": "",
}

DEFAULT_KEYGEN = {
    "algorithm": "AES",
    "key_size": 256,
    "format": "Hexadecimal",
}

DEFAULT_WINDOW = {
    "width": 1100,
    "height": 720,
}

@dataclass
class AppConfig:
    language: str = "en"
    theme: str = "acrylic"
    window: dict = field(default_factory=lambda: dict(DEFAULT_WINDOW))
    last_used: dict = field(default_factory=lambda: dict(DEFAULT_LAST_USED))
    keygen: dict = field(default_factory=lambda: dict(DEFAULT_KEYGEN))

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        cfg = cls()
        cfg.language = data.get("language", cfg.language)
        cfg.theme = data.get("theme", cfg.theme)
        cfg.window = {**cfg.window, **data.get("window", {})}
        cfg.last_used = {**cfg.last_used, **data.get("last_used", {})}
        cfg.keygen = {**cfg.keygen, **data.get("keygen", {})}
        return cfg
    

def get_config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or get_config_path()

    if not cfg_path.exists():
        return AppConfig()
    
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return AppConfig()

    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    cfg_path = path or get_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)


def reset_config(path: Path | None = None) -> AppConfig:
    defaults = AppConfig()
    save_config(defaults, path)
    return defaults