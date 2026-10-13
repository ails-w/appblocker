# Instalación

Orden por módulo. Cada uno es autocontenido y tiene su propio README con
**aplicar / verificar / rollback**.

> Automatización: `sudo scripts/install.sh` reproduce todo esto. Los pasos de abajo son para
> instalarlo a mano o entender qué toca cada módulo.

## Antes de empezar

- Requisitos: `bash`, `python3 >= 3.11` (por `tomllib`), `systemd`.
- El repo espeja el filesystem: `modules/NN-name/files/<ruta>` se instala **en `<ruta>`**.

## Orden

| Orden | Módulo | Instala en |
|---|---|---|
| 1 | [`00-base`](../modules/00-base/README.md) | `/etc/appblocker/config.toml` |
| 2 | [`01-policy`](../modules/01-policy/README.md) | `/etc/appblocker/policy.d/10-stremio.toml` |
| 3 | [`02-daemon`](../modules/02-daemon/README.md) | `/usr/local/lib/appblocker/`, `/etc/systemd/system/appblocker.service` |
| 4 | [`03-cli`](../modules/03-cli/README.md) | `/usr/local/bin/appblocker` |

## Resumen

```bash
# 1-2: configuración
sudo install -d /etc/appblocker/policy.d
sudo install -m 0644 modules/00-base/files/etc/appblocker/config.toml /etc/appblocker/config.toml
sudo install -m 0644 modules/01-policy/files/etc/appblocker/policy.d/10-stremio.toml \
                    /etc/appblocker/policy.d/10-stremio.toml

# 3: daemon + unit
sudo install -d /usr/local/lib/appblocker/core /usr/local/lib/appblocker/enforcers
# (copiar el paquete y el unit)
sudo systemctl daemon-reload
sudo systemctl enable --now appblocker.service

# 4: CLI
sudo install -m 0755 modules/03-cli/files/usr/local/bin/appblocker /usr/local/bin/appblocker
```

> **Antes de confiar en esto:** edita `policy.d/10-stremio.toml` y pon **tus** objetivos y
> **tus** horarios. Los valores del repo son de ejemplo.

## Verificar

```bash
systemctl status appblocker.service --no-pager
appblocker status
```

Sigue con [`verification.md`](verification.md).
