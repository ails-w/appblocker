#!/usr/bin/env python3
"""appblocker: inspecciona y controla el daemon."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, "/usr/local/lib/appblocker")

from core.config import DAYS, load  # noqa: E402
from core.matcher import match_pids  # noqa: E402
from core.scheduler import active_targets, window_active  # noqa: E402


def resolve_tz(config):
    name = config.get("timezone", "local")
    if name in ("local", "", None):
        return None
    try:
        return ZoneInfo(name)
    except Exception:
        return None


def cmd_status(argv):
    policy = load()
    now = datetime.now(resolve_tz(policy.config))
    active = {t.name for t in active_targets(policy, now)}
    print(f"Ahora: {now:%Y-%m-%d %H:%M:%S} ({DAYS[now.weekday()]})")
    for name in sorted(policy.targets):
        state = "BLOQUEADO" if name in active else "libre"
        print(f"  {name:<12} {state}")
    print("\nVentanas:")
    for window in policy.windows:
        mark = "*" if window_active(window, now) else " "
        print(f"  [{mark}] {','.join(window.days):<28} "
              f"{window.start:%H:%M}-{window.end:%H:%M}  {','.join(window.apps)}")


def cmd_windows(argv):
    policy = load()
    for window in policy.windows:
        print(f"{','.join(window.days):<28} "
              f"{window.start:%H:%M}-{window.end:%H:%M}  {','.join(window.apps)}")


def cmd_check(argv):
    policy = load()
    for name in sorted(policy.targets):
        pids = match_pids(policy.targets[name])
        print(f"{name}: {len(pids)} proceso(s) -> {pids}")


def cmd_test(argv):
    policy = load()
    now = datetime.now(resolve_tz(policy.config))
    active = active_targets(policy, now)
    if not active:
        print("Ninguna ventana activa: no se bloquearia nada ahora.")
        return 0
    for target in active:
        pids = match_pids(target)
        print(f"se bloquearia {target.name}: {len(pids)} proceso(s) -> {pids}")
    return 0


def cmd_reload(argv):
    return subprocess.run(["systemctl", "restart", "appblocker.service"]).returncode


COMMANDS = {
    "status": cmd_status,
    "windows": cmd_windows,
    "check": cmd_check,
    "test": cmd_test,
    "reload": cmd_reload,
}


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print("uso: appblocker <status|windows|check|test|reload>")
        return 0 if len(argv) >= 2 else 1
    handler = COMMANDS.get(argv[1])
    if handler is None:
        print(f"comando desconocido: {argv[1]}")
        return 2
    result = handler(argv[2:])
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
