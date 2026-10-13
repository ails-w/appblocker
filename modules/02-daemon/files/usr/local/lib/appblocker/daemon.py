#!/usr/bin/env python3
"""AppBlocker: daemon que aplica el bloqueo por horario."""
from __future__ import annotations

import signal
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, "/usr/local/lib/appblocker")

from core import enforcer  # noqa: E402
from core.config import CONFIG_PATH, POLICY_DIR, load  # noqa: E402
from core.scheduler import active_targets  # noqa: E402

_running = True


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{stamp} appblocker: {message}", flush=True)


def resolve_tz(config):
    name = config.get("timezone", "local")
    if name in ("local", "", None):
        return None
    try:
        return ZoneInfo(name)
    except Exception:
        log(f"zona horaria desconocida {name!r}, uso la local")
        return None


def fingerprint():
    paths = [CONFIG_PATH, *sorted(POLICY_DIR.glob("*.toml"))]
    stamps = []
    for path in paths:
        try:
            stamps.append((str(path), path.stat().st_mtime_ns))
        except OSError:
            stamps.append((str(path), 0))
    return stamps


def _stop(_signum, _frame):
    global _running
    _running = False


def main():
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    try:
        policy = load()
    except Exception as exc:
        log(f"FATAL: politica invalida: {exc}")
        return 2

    stamp = fingerprint()
    tz = resolve_tz(policy.config)
    poll = max(0.2, float(policy.config.get("poll_interval_seconds", 1)))
    log_attempts = bool(policy.config.get("log_attempts", True))
    log(f"iniciado: {len(policy.targets)} objetivo(s), {len(policy.windows)} ventana(s)")

    while _running:
        try:
            fresh = fingerprint()
            if fresh != stamp:
                policy = load()
                stamp = fresh
                tz = resolve_tz(policy.config)
                poll = max(0.2, float(policy.config.get("poll_interval_seconds", 1)))
                log_attempts = bool(policy.config.get("log_attempts", True))
                log("politica recargada")
        except Exception as exc:
            log(f"recarga fallida, sigo con la anterior: {exc}")

        now = datetime.now(tz)
        for target in active_targets(policy, now):
            try:
                handler = enforcer.get_enforcer(target.kind)
                handler.enforce(target, log=log if log_attempts else None)
            except Exception as exc:
                log(f"error aplicando {target.name}: {exc}")

        time.sleep(poll)

    log("detenido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
