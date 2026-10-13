# Módulo 04 — Integridad

Candado anti-manipulación de la configuración: una copia *golden*, `chattr +i` (inmutable) y
una verificación cada minuto que **restaura y re-bloquea** si algo cambió.

Va **después** de `00-base` y `01-policy`, porque congela el estado ya correcto.

## Prerrequisitos

- Módulos [`00-base`](../00-base/) y [`01-policy`](../01-policy/).
- `e2fsprogs` (`chattr` / `lsattr`).

## Archivos

| Archivo | Destino | Qué hace |
|---|---|---|
| `files/usr/local/bin/appblocker-lock` | `/usr/local/bin/` | copia live → golden y marca `+i` |
| `files/usr/local/bin/appblocker-integrity` | `/usr/local/bin/` | compara, restaura, re-bloquea |
| `files/etc/systemd/system/appblocker-integrity.service` | `/etc/systemd/system/` | corre el check |
| `files/etc/systemd/system/appblocker-integrity.timer` | `/etc/systemd/system/` | cada minuto (`:30`) |

Protege `/etc/appblocker/config.toml` y **todos** los `/etc/appblocker/policy.d/*.toml`. La
golden conserva la ruta relativa: `golden/config.toml`, `golden/policy.d/10-stremio.toml`.

## Aplicar

```bash
sudo install -m 0755 files/usr/local/bin/appblocker-lock files/usr/local/bin/appblocker-integrity /usr/local/bin/
sudo install -m 0644 files/etc/systemd/system/appblocker-integrity.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now appblocker-integrity.timer

sudo appblocker-lock        # primera foto del estado bueno + bloqueo
```

> `scripts/install.sh` instala el módulo pero **no bloquea**. Bloquear es un acto deliberado:
> hazlo con `sudo appblocker-lock` cuando tu configuración sea la definitiva.

## Flujo para cambiar la config

```bash
sudo chattr -i /etc/appblocker/config.toml /etc/appblocker/policy.d/*.toml
sudoedit /etc/appblocker/policy.d/10-stremio.toml
appblocker reload           # el daemon recarga la policy
sudo appblocker-lock        # nueva golden + re-bloquear
```

Al **agregar un fragmento nuevo** (p. ej. `20-steam.toml`), hay que re-ejecutar
`appblocker-lock`: los archivos sin golden no se protegen.

## Verificar

```bash
lsattr /etc/appblocker/config.toml /etc/appblocker/policy.d/*.toml   # con 'i'
ls -la /etc/appblocker/golden/

# Prueba de sabotaje controlado:
sudo chattr -i /etc/appblocker/config.toml
sudo sh -c 'echo "# sabotage" >> /etc/appblocker/config.toml'
sudo systemctl start appblocker-integrity.service
grep -c sabotage /etc/appblocker/config.toml   # debe ser 0
lsattr /etc/appblocker/config.toml             # vuelve a tener 'i'
journalctl -t appblocker -n 5 --no-pager
```

## Rollback

```bash
sudo systemctl disable --now appblocker-integrity.timer
find /etc/appblocker -name '*.toml' -exec chattr -i {} + 2>/dev/null || true
chattr -i /etc/appblocker/golden 2>/dev/null || true
sudo rm -f /etc/systemd/system/appblocker-integrity.service /etc/systemd/system/appblocker-integrity.timer
sudo rm -f /usr/local/bin/appblocker-lock /usr/local/bin/appblocker-integrity
sudo rm -rf /etc/appblocker/golden
sudo systemctl daemon-reload
```

## Notas

- **`chattr +i` es fricción, no frontera.** Un root decidido puede quitarlo; lo que aporta es
  que desactivar el bloqueo sea **deliberado**, se **revierta solo** y quede **auditado**.
- **Sin recarga de servicios.** El daemon relee la policy cuando cambia su `mtime`; al
  restaurar el archivo, el daemon recarga solo. No hay estado en memoria que refrescar.
- **Golden por ruta relativa**, no por `basename`: dos fragmentos en `policy.d/` nunca
  colisionan.
- El timer corre en `:30`. La unit de integridad usa `ProtectSystem=full` (no `strict`),
  porque necesita **escribir en `/etc`** para restaurar.
