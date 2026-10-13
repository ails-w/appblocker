"""Selecciona el enforcer segun el tipo de objetivo."""
from __future__ import annotations

from enforcers import kill

_BY_KIND = {
    "flatpak": kill,
    "process": kill,
}


def get_enforcer(kind):
    return _BY_KIND.get(kind, kill)
