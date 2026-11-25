from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "configs" / "profiles"


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _set_dotted(d: dict, dotted: str, value: Any) -> None:
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def apply_overrides(d: dict, overrides: Iterable[str]) -> dict:
    """Apply CLI overrides of the form 'a.b.c=value' (value parsed as YAML)."""
    for item in overrides or ():
        key, sep, raw = item.partition("=")
        if not sep:
            raise ValueError(f"override must look like key=value, got {item!r}")
        _set_dotted(d, key.strip(), yaml.safe_load(raw))
    return d


def load_profile(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))
        raise FileNotFoundError(f"profile {name!r} not found; available: {available}")
    profile = yaml.safe_load(path.read_text())
    calibrated = PROFILES_DIR / f"{name}.size_thresholds.json"
    if calibrated.exists():
        profile.setdefault("severity", {}).setdefault("size_thresholds", {}).update(
            json.loads(calibrated.read_text())
        )
    return profile


@dataclass
class Config:
    app: dict
    profile: dict

    @property
    def profile_name(self) -> str:
        return self.profile["name"]

    def path(self, template: str | Path) -> Path:
        return resolve(str(template).format(profile=self.profile_name))

    def section(self, name: str) -> dict:
        return self.app.get(name, {})


def _merge(base: dict, extra: dict) -> dict:
    for k, v in extra.items():
        base[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return base


def load_config(app_path: str | Path | None = None, overrides: Iterable[str] = ()) -> Config:
    """configs/app.yaml < the profile's own `app:` section (e.g. its model input size) < CLI overrides."""
    app = yaml.safe_load(resolve(app_path or "configs/app.yaml").read_text())
    overrides = list(overrides or ())
    profile = load_profile(apply_overrides(copy.deepcopy(app), overrides)["profile"])
    app = _merge(app, copy.deepcopy(profile.get("app") or {}))
    return Config(app=apply_overrides(app, overrides), profile=profile)
