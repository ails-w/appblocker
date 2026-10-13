# Módulo 02 — Daemon

El motor: el paquete Python que lee el reloj, matchea `/proc` y cierra lo bloqueado — más su
unit de `systemd`.

## Prerrequisitos

- `python3 >= 3.11`, `systemd`.
- Módulos `00-base` y `01-policy` instalados (el daemon lee su config).

## Archivos

| Archivo | Destino | Qué hace |
|---|---|---|
| `files/usr/local/lib/appblocker/daemon.py` | `/usr/local/lib/appblocker/daemon.py` | bucle principal + recarga de config |
| `files/usr/local/lib/appblocker/core/config.py` | `…/core/config.py` | carga `config.toml` + `policy.d/*.toml` |
| `files/usr/local/lib/appblocker/core/scheduler.py` | `…/core/scheduler.py` | ¿ventana activa? (incluye cruce de medianoche) |
| `files/usr/local/lib/appblocker/core/matcher.py` | `…/core/matcher.py` | PIDs de un objetivo (`/proc` · cgroup) |
| `files/usr/local/lib/appblocker/core/enforcer.py` | `…/core/enforcer.py` | selecciona el enforcer por `kind` |
| `files/usr/local/lib/appblocker/enforcers/kill.py` | `…/enforcers/kill.py` | `SIGTERM` → `SIGKILL` |
| `files/etc/systemd/system/appblocker.service` | `/etc/systemd/system/appblocker.service` | la unit |

## Aplicar

```bash
sudo install -d /usr/local/lib/appblocker/core /usr/local/lib/appblocker/enforcers
sudo install -m 0644 files/usr/local/lib/appblocker/daemon.py /usr/local/lib/appblocker/daemon.py
sudo install -m 0644 files/usr/local/lib/appblocker/core/*.py /usr/local/lib/appblocker/core/
sudo install -m 0644 files/usr/local/lib/appblocker/enforcers/*.py /usr/local/lib/appblocker/enforcers/
sudo install -m 0644 files/etc/systemd/system/appblocker.service /etc/systemd/system/appblocker.service
sudo systemctl daemon-reload
sudo systemctl enable --now appblocker.service
```

## Verificar

```bash
systemctl status appblocker.service --no-pager
journalctl -u appblocker -n 20 --no-pager     # "iniciado: N objetivo(s), M ventana(s)"
```

## Rollback

```bash
sudo systemctl disable --now appblocker.service
sudo rm -rf /usr/local/lib/appblocker
sudo rm -f /etc/systemd/system/appblocker.service
sudo systemctl daemon-reload
```

## Notas

- La unit trae **`RuntimeDirectory=appblocker`**. Es lo que evita el `226/NAMESPACE` cuando se
  usa `ProtectSystem=strict`. Ver [`../../docs/troubleshooting.md`](../../docs/troubleshooting.md).
- **Sin `WatchdogSec`**: exigiría que el daemon mande latidos (`sd_notify`), que este MVP no
  implementa.
- El daemon **recarga** la policy sola cuando cambian sus archivos; no hay que reiniciarlo
  para cambiar un horario.
