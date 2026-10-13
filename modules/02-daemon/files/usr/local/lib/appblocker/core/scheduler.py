"""Decide que objetivos estan bloqueados en este momento."""
from __future__ import annotations

from .config import DAYS


def _clock(dt):
    # now.time() de un datetime con zona devuelve un time "aware"; comparar
    # contra un time naive lanza TypeError. Lo volvemos naive.
    return dt.time().replace(tzinfo=None)


def window_active(window, now):
    today = DAYS[now.weekday()]
    clock = _clock(now)

    if not window.crossing:
        return today in window.days and window.start <= clock < window.end

    # Cruza medianoche: o arranco hoy, o es la cola de ayer.
    if today in window.days and clock >= window.start:
        return True

    yesterday = DAYS[(now.weekday() - 1) % 7]
    return yesterday in window.days and clock < window.end


def active_targets(policy, now):
    names = []
    for window in policy.windows:
        if window_active(window, now):
            for app in window.apps:
                if app not in names:
                    names.append(app)
    return [policy.targets[n] for n in names]
