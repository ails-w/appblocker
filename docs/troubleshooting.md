# Troubleshooting

Errores reales, con su causa y su arreglo.

## `appblocker.service` falla con `226/NAMESPACE`

```text
Process: ... ExecStart=... (code=exited, status=226/NAMESPACE)
```

**Causa:** el unit tiene `ReadWritePaths=` apuntando a una ruta que **no existe**. Con
`ProtectSystem=strict`, `systemd` monta un namespace y hace `bind-mount` de esas rutas; si la
ruta no existe, el montaje del namespace falla → `226`.

**Arreglo:** darle a `systemd` la propiedad del directorio, en vez de declararlo a mano:

```ini
RuntimeDirectory=appblocker     # systemd crea y limpia /run/appblocker solo
# y quitar: ReadWritePaths=/run/appblocker
```

## `TOMLDecodeError: Invalid value (at line N, column M)`

**Causa:** TOML inválido. Los dos sospechosos de siempre:

```toml
timezone = local        # ✗ literal sin comillas
fail = mode = open      # ✗ dos '=' en una línea
```

```toml
timezone = "local"      # ✓ string entre comillas
fail_mode = "open"      # ✓ un solo '=', y el nombre correcto
```

**Detección:** nunca a ojo. Siempre:

```bash
python3 -c "import tomllib; tomllib.load(open('<archivo>','rb'))"
```

## El daemon entra en bucle de reinicio cada 30 s

**Causa:** el unit declara `WatchdogSec=30` pero el daemon **no manda** el latido
(`sd_notify(WATCHDOG=1)`). `systemd` mata y reinicia.

**Arreglo:** en el MVP, **quitar** `WatchdogSec`. Si se quiere watchdog, el daemon debe
enviar el latido (implica `NotifyAccess=`).

## `appblocker status` da `Permission denied` leyendo la config

**Causa:** `config.toml` o `policy.d/` en modo `600`/`700`. El CLI corre como **usuario**, no
root, y necesita **leer**.

**Arreglo:**

```bash
sudo chmod 644 /etc/appblocker/config.toml /etc/appblocker/policy.d/*.toml
sudo chmod 755 /etc/appblocker /etc/appblocker/policy.d
```

El candado es la **propiedad `root:root`**, no el modo. Leer no es un riesgo; escribir sí.

## La app no se cierra aunque la ventana está activa

```bash
appblocker status     # ¿la ventana figura como activa? ¿aparece la '*'?
appblocker check      # ¿matchea algún PID con la app abierta?
```

- Si `status` no marca la ventana: revisa `days`/`start`/`end` (días en inglés, `HH:MM`).
- Si `check` da `0 procesos` con la app abierta: el `cgroup_match` no coincide. Verifica:

  ```bash
  grep -i <nombre-app> /proc/$(pgrep -f <nombre-app> | head -1)/cgroup
  ```

  y ajusta `cgroup_match` en el `target`.

## El error de `install` que parece grave y no lo es

```text
install: no se puede efectuar 'stat' sobre 'config.toml': No existe
```

**Causa:** `install` busca el **origen** en el directorio actual. Si corriste el comando
desde fuera del repo, no lo encuentra.

**Arreglo:** usar las rutas del repo (`modules/.../files/...`) o correr
`scripts/install.sh`, que las resuelve solo.
