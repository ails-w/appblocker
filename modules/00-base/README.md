# Módulo 00 — Base

El fundamento compartido: la **configuración global** del daemon.

## Prerrequisitos

- `python3 >= 3.11` (por `tomllib`)

## Archivos

| Archivo | Destino | Qué hace |
|---|---|---|
| `files/etc/appblocker/config.toml` | `/etc/appblocker/config.toml` | `timezone`, intervalo de sondeo, logging |

## Aplicar

```bash
sudo install -d /etc/appblocker
sudo install -m 0644 files/etc/appblocker/config.toml /etc/appblocker/config.toml
```

## Verificar

```bash
python3 -c "import tomllib; print(tomllib.load(open('/etc/appblocker/config.toml','rb')))"
```

**Esperado:** imprime un dict con `timezone`, `poll_interval_seconds` y `log_attempts`.

## Rollback

```bash
sudo rm -f /etc/appblocker/config.toml
```

## Notas

- Permisos **`644 root:root`**, no `600`. El CLI corre como **usuario** y necesita **leer**.
  El candado es la propiedad `root:root`, no el modo. Ver [`../../docs/threat-model.md`](../../docs/threat-model.md).
- Todos los módulos asumen este archivo. Instala este módulo **primero**.
