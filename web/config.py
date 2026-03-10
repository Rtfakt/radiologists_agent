from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8000

    enable_https_lan: bool = False
    enable_request_logging: bool = False
    ssl_certfile: Optional[Path] = None
    ssl_keyfile: Optional[Path] = None

    internet_mode: bool = False
    internet_ssl_certfile: Optional[Path] = None
    internet_ssl_keyfile: Optional[Path] = None


def _load_from_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def load_config() -> WebConfig:
    root = Path(__file__).resolve().parent.parent
    yaml_path = root / "web_config.yaml"
    raw = _load_from_yaml(yaml_path)

    def get_bool(key: str, default: bool) -> bool:
        if key in raw:
            return bool(raw[key])
        env_val = os.getenv(key.upper())
        if env_val is None:
            return default
        return env_val.lower() in {"1", "true", "yes", "on"}

    def get_int(key: str, default: int) -> int:
        if key in raw:
            try:
                return int(raw[key])
            except Exception:
                return default
        env_val = os.getenv(key.upper())
        if env_val is None:
            return default
        try:
            return int(env_val)
        except Exception:
            return default

    def get_str(key: str, default: str) -> str:
        if key in raw and isinstance(raw[key], (str, int, float)):
            return str(raw[key])
        env_val = os.getenv(key.upper())
        if env_val is None:
            return default
        return env_val

    cfg = WebConfig()
    cfg.host = get_str("host", cfg.host)
    cfg.port = get_int("port", cfg.port)

    cfg.enable_https_lan = get_bool("enable_https_lan", cfg.enable_https_lan)
    cfg.enable_request_logging = get_bool(
        "enable_request_logging",
        cfg.enable_request_logging,
    )

    cert = raw.get("ssl_certfile") or os.getenv("SSL_CERTFILE")
    key = raw.get("ssl_keyfile") or os.getenv("SSL_KEYFILE")
    if cert:
        cfg.ssl_certfile = Path(cert)
    if key:
        cfg.ssl_keyfile = Path(key)

    cfg.internet_mode = get_bool("internet_mode", cfg.internet_mode)
    internet_cert = raw.get("internet_ssl_certfile") or os.getenv("INTERNET_SSL_CERTFILE")
    internet_key = raw.get("internet_ssl_keyfile") or os.getenv("INTERNET_SSL_KEYFILE")
    if internet_cert:
        cfg.internet_ssl_certfile = Path(internet_cert)
    if internet_key:
        cfg.internet_ssl_keyfile = Path(internet_key)

    return cfg


__all__ = ["WebConfig", "load_config"]

