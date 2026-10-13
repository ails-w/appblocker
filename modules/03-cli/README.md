# Módulo 03 — CLI

El punto de inspección: `appblocker status / windows / check / test / reload`. Corre como
**usuario** (no root) y solo **lee**.

## Prerrequisitos

- `python3 >= 3.11`.
- Módulo `02-daemon` instalado (el CLI importa `core.*`).

## Archivos

| Archivo | Destino | Qué hace |
|---|---|---|
| `files/usr/local/bin/appblocker` | `/usr/local/bin/appblocker` | wrapper shell que ejecuta `cli.py` |
| `files/usr/local/lib/appblocker/cli.py` | `/usr/local/lib/appblocker/cli.py` | el CLI en sí (importa `core.*`) |

## Aplicar

```bash
sudo install -d /usr/local/lib/appblocker
sudo install -m 0644 files/usr/local/lib/appblocker/cli.py /usr/local/lib/appblocker/cli.py
sudo install -m 0755 files/usr/local/bin/appblocker /usr/local/bin/appblocker
```

## Verificar

```bash
appblocker status
```

**Esperado:** corre **sin `sudo`**. Si da `Permission denied`, la config quedó en `600`: ver
[`../../docs/troubleshooting.md`](../../docs/troubleshooting.md).

## Rollback

```bash
sudo rm -f /usr/local/bin/appblocker
```

## Comandos

| Comando | Qué hace |
|---|---|
| `appblocker status` | estado actual + ventanas (marca `*` la activa) |
| `appblocker windows` | lista las ventanas configuradas |
| `appblocker check` | PIDs que matchean cada objetivo **ahora** |
| `appblocker test` | dry-run: qué mataría en este instante, sin matar |
| `appblocker reload` | reinicia el servicio (`systemctl restart`) |
