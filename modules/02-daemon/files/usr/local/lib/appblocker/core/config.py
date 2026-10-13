"""Carga de configuracion: config.toml + fragmentos de policy.d/."""
from __future__ import annotations

import tomllib
from datetime import time
from pathlib import Path

CONFIG_PATH = Path("/etc/appblocker/config.toml")
POLICY_DIR = Path("/etc/appblocker/policy.d")

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

DEFAULTS = {
    "timezone": "local",
    "poll_interval_seconds": 1,
    "log_attempts": True,
}


def _parse_time(value):
    try:
        hh, mm = str(value).split(":")
        return time(int(hh), int(mm))
    except Exception:
        raise ValueError(f"hora invalida: {value!r} (se espera HH:MM)")


class Target:
    """Un objetivo a bloquear, con sus reglas de deteccion."""

    def __init__(self, name, spec):
        self.name = name
        self.kind = spec.get("kind", "flatpak")
        self.flatpak_id = spec.get("flatpak_id")
        self.cgroup_match = spec.get("cgroup_match") or self.flatpak_id
        self.cmdline_match = spec.get("cmdline_match")
        if not self.cgroup_match and not self.cmdline_match:
            raise ValueError(f"objetivo {name}: falta cgroup_match o cmdline_match")

    def __repr__(self):
        return f"<Target {self.name} kind={self.kind}>"


class Window:
    """Una ventana de bloqueo: dias + rango horario."""

    def __init__(self, spec):
        self.days = [str(d).lower() for d in spec["days"]]
        bad = [d for d in self.days if d not in DAYS]
        if bad:
            raise ValueError(f"dias invalidos: {bad} (validos: {DAYS})")
        self.apps = list(spec["apps"])
        self.start = _parse_time(spec["start"])
        self.end = _parse_time(spec["end"])
        if self.start == self.end:
            raise ValueError("start y end no pueden ser iguales")
        self.crossing = self.start > self.end

    def __repr__(self):
        return f"<Window {','.join(self.days)} {self.start:%H:%M}-{self.end:%H:%M}>"


class Policy:
    def __init__(self, config, targets, windows):
        self.config = config
        self.targets = targets
        self.windows = windows


def load():
    config = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as fh:
            config.update(tomllib.load(fh))

    targets, windows = {}, []
    for path in sorted(POLICY_DIR.glob("*.toml")):
        try:
            with path.open("rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"{path}: TOML invalido: {exc}") from exc

        for name, spec in doc.get("target", {}).items():
            try:
                targets[name] = Target(name, spec)
            except Exception as exc:
                raise ValueError(f"{path}: objetivo {name}: {exc}") from exc

        for spec in doc.get("window", []):
            try:
                windows.append(Window(spec))
            except Exception as exc:
                raise ValueError(f"{path}: ventana invalida: {exc}") from exc

    for window in windows:
        for app in window.apps:
            if app not in targets:
                raise ValueError(f"ventana referencia objetivo desconocido: {app!r}")

    return Policy(config, targets, windows)
