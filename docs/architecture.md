# Arquitectura

`appblocker` bloquea **aplicaciones concretas** dentro de **ventanas horarias**, con un
daemon root que corre bajo `systemd` y reevalúa el reloj cada segundo.

## Capas

| # | Capa | Actúa... | Módulo |
|---|------|----------|--------|
| 0 | Config | define el comportamiento global | `00-base` |
| 1 | Policy | define **qué** app y **cuándo** | `01-policy` |
| 2 | Daemon | mientras el servicio corre (siempre) | `02-daemon` |
| 3 | CLI | a demanda, por el usuario | `03-cli` |

## Mapa

```text
        ┌────────────────────────────────────────────────────────┐
        │  /etc/appblocker/config.toml          (global)         │
        │  /etc/appblocker/policy.d/10-*.toml   (targets+ventanas)│
        └───────────────────────────┬────────────────────────────┘
                                    │ los lee (y recarga si cambian)
                                    ▼
                    ┌──────────────────────────────┐
                    │  appblocker.service (root)   │
                    │  daemon.py · bucle cada 1 s  │
                    └───────────────┬──────────────┘
                                    │
             ¿hay ventana activa ahora?  ── scheduler.py
                                    │ sí
                                    ▼
             ¿qué PIDs son el objetivo?  ── matcher.py (/proc cgroup)
                                    │
                                    ▼
             SIGTERM ─▶ espera 0.3 s ─▶ SIGKILL   ── enforcers/kill.py

   appblocker (CLI) ── lee la misma config ──▶ status / check / test
```

## Una pasada del daemon

1. **Recarga si cambió.** Compara `mtime` de `config.toml` y de `policy.d/*.toml`. Si
   cambiaron, vuelve a parsear. No hay que reiniciar el servicio para cambiar un horario.
2. **Lee el reloj.** `datetime.now(tz)` (timezone `local` por defecto).
3. **Evalúa ventanas.** Para cada ventana, decide si está activa *ahora* — incluyendo el
   caso en que la ventana **cruzó medianoche** (`02-scheduler`).
4. **Resuelve objetivos.** De las ventanas activas salen los nombres de app; cada uno mapea
   a un `target` con sus reglas de detección.
5. **Aplica el enforcer.** Escanea `/proc`, matchea por **cgroup**, y termina el conjunto de
   procesos (`SIGTERM` → `SIGKILL`).
6. **Duerme** `poll_interval_seconds` (1 s por defecto) y repite.

## Decisiones clave

- **¿Por qué un daemon y no un `systemd` timer?** Un timer de `systemd` dispara en
  instantes, no *sostiene* un estado. El bloqueo es continuo ("mientras estés en la
  ventana"), y además necesitamos reevaluar en cada arranque y tras cambios de config.
- **¿Por qué el matcher va por cgroup?** Ver [`learning/02-matcher-cgroup.md`](learning/02-matcher-cgroup.md):
  es inmune a renombrar el binario y cubre Flatpak, que no tiene binario en `$PATH`.
- **¿Por qué matar **todos** los PIDs coincidentes?** Un Flatpak corre en un `scope` con
  `bwrap` + la app; matar solo el líder deja huérfanos. Se recorre el conjunto completo.
- **¿Por qué `SIGTERM` antes de `SIGKILL`?** Cortesía: permite cerrar archivos. El `SIGKILL`
  posterior garantiza que no quede nada si ignoró el `TERM`.
- **¿Por qué la config es `root:root`?** Es lo que convierte el bloqueo en fricción real: el
  usuario no la edita sin `sudo`. Ver [`threat-model.md`](threat-model.md).

## Por qué Python

El objetivo es una **herramienta de uso diario**: cero build, cero dependencias (solo la
stdlib — `tomllib`, `zoneinfo`, `os`, `signal`), y se lee de un tirón. Un binario compilado
no aportaría nada aquí. (El proyecto de aprendizaje equivalente, con IPC y persistencia, es
`focusblock`; éste no lo reemplaza.)
