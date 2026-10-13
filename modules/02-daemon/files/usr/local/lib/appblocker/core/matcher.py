"""Encuentra PIDs que pertenecen a un objetivo, leyendo /proc."""
from __future__ import annotations

import os

PROC = "/proc"
_SELF = os.getpid()


def _read(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(65536).decode("utf-8", "replace")
    except OSError:
        return ""


def match_pids(target):
    """PIDs cuyo cgroup (o cmdline) coincide con el objetivo.

    Se matchea por cgroup porque es estable: sobrevive a renombrar el binario
    y cubre Flatpak, que no tiene binario en $PATH.
    """
    pids = []
    try:
        entries = os.listdir(PROC)
    except OSError:
        return pids

    for name in entries:
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == 1 or pid == _SELF:
            continue

        if target.cgroup_match and target.cgroup_match in _read(f"{PROC}/{pid}/cgroup"):
            pids.append(pid)
            continue

        if target.cmdline_match:
            cmdline = _read(f"{PROC}/{pid}/cmdline").replace("\x00", " ")
            if target.cmdline_match in cmdline:
                pids.append(pid)

    return pids
