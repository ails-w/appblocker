# Flujo de enforcement

Una pasada del daemon, de principio a fin.

```mermaid
flowchart TD
    A[bucle: cada poll_interval_seconds] --> B{¿cambió la config?}
    B -- sí --> B1[recargar config.toml + policy.d/*.toml]
    B -- no --> C
    B1 --> C[leer reloj: datetime.now tz]
    C --> D[para cada ventana: ¿está activa ahora?]
    D --> E{¿algún objetivo activo?}
    E -- no --> H[dormir]
    E -- sí --> F[escanear /proc · matchear por cgroup]
    F --> G{¿hay PIDs?}
    G -- no --> H
    G -- sí --> I[SIGTERM a todos]
    I --> J[esperar 0.3 s]
    J --> K[SIGKILL a los que queden]
    K --> L[log: bloqueado target · N procesos]
    L --> H
```

## Qué mirar en cada paso

| Paso | Archivo | Qué decide |
|---|---|---|
| ¿cambió la config? | `daemon.py` (`fingerprint`) | recargar sin reiniciar el servicio |
| ¿ventana activa? | `core/scheduler.py` | `days` + `start`/`end`, con cruce de medianoche |
| ¿es el objetivo? | `core/matcher.py` | `cgroup_match` (y `cmdline_match` opcional) |
| matar | `enforcers/kill.py` | `SIGTERM` → gracia → `SIGKILL` |

## Por qué dos señales

`SIGTERM` deja que la app cierre archivos; el `SIGKILL` posterior garantiza que no quede
nada vivo si ignora el `TERM`. Matar solo el líder NO basta en un Flatpak (hay `bwrap`): por
eso se recalcula el conjunto antes del `SIGKILL`.
