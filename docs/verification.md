# Verificación

Cómo comprobar cada capa. Si una falla, no sigas.

> Automatización: `scripts/verify.sh` reproduce esta batería. Los comandos de abajo son
> para inspeccionar cada capa a mano cuando algo falla.

## Capa 0/1 — Configuración

```bash
# el TOML debe parsear (no confíes en la vista)
python3 -c "import tomllib; tomllib.load(open('/etc/appblocker/policy.d/10-stremio.toml','rb'))"
appblocker windows          # lista las ventanas tal como las entiende el parser
```

**Esperado:** sin `TOMLDecodeError` y las ventanas que escribiste (con el cruce de medianoche
correcto).

## Capa 2 — Daemon

```bash
systemctl is-active appblocker.service
journalctl -u appblocker -n 20 --no-pager
appblocker check            # ¿cuántos procesos matchea el target ahora?
```

**Esperado:** `active (running)`, log "iniciado: N objetivo(s), M ventana(s)", y `check`
muestra los PIDs de la app **si está abierta**.

Prueba real controlada:

1. Abre la app objetivo **dentro** de su ventana.
2. En otra terminal: `journalctl -u appblocker -f`
3. Debe aparecer `bloqueado <target>: terminados N proceso(s)` y la app debe cerrarse.
4. `appblocker test` confirma en dry-run qué mataría, sin matar nada.

## Capa 3 — CLI

```bash
appblocker status           # estado + ventanas (marca * la activa)
appblocker reload           # debe reiniciar el servicio sin error
```

**Esperado:** `status` corre como **tu usuario** (no root) y lee la config sin error — prueba
de que los permisos son `644 root:root` y no `600`.

## Checklist final

- [ ] El TOML parsea y `appblocker windows` coincide con lo que escribí.
- [ ] `appblocker.service` está `enabled` y `active (running)`.
- [ ] Abrir la app dentro de la ventana → se cierra, y queda en el journal.
- [ ] `appblocker check` detecta la app con `cgroup_match`.
- [ ] `appblocker status` corre como usuario sin `sudo`.
