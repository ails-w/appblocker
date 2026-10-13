"""Tier 1: termina todos los procesos de un objetivo bloqueado."""
from __future__ import annotations

import os
import signal
import time

from core.matcher import match_pids

GRACE_SECONDS = 0.3


def _signal(pid, sig):
    try:
        os.kill(pid, sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def enforce(target, log=None):
    """SIGTERM al conjunto, espera, y SIGKILL a lo que quede.

    Se recalcula el conjunto antes del SIGKILL: en un Flatpak o en un juego de
    Steam el lider no es el unico proceso vivo.
    """
    pids = match_pids(target)
    if not pids:
        return 0

    for pid in pids:
        _signal(pid, signal.SIGTERM)

    time.sleep(GRACE_SECONDS)

    for pid in match_pids(target):
        _signal(pid, signal.SIGKILL)

    if log is not None:
        log(f"bloqueado {target.name}: terminados {len(pids)} proceso(s)")

    return len(pids)
