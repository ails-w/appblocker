# Sección 03 — Enforcement y señales

> Cómo se cierra el objetivo de forma confiable, y por qué matar un solo PID no alcanza.
> Implementación → `enforcers/kill.py`

## Glosario de la sección

| Término | Qué significa (en una línea) |
|---|---|
| señal | mensaje corto del kernel a un proceso |
| `SIGTERM` | "por favor, terminá" (se puede interceptar) |
| `SIGKILL` | "morí ya" (no se puede interceptar) |
| árbol de procesos | un proceso con hijos (y nietos) |
| `bwrap` | el sandbox de Flatpak que envuelve la app |

## Mapa de conceptos

```text
  match por cgroup  ─▶ lista de PIDs ─▶ SIGTERM a todos
                                              │
                                        espera 0.3 s
                                              │
                                     re-escanear ─▶ SIGKILL a los que queden
```

---

## Dos señales, no una

### En una frase

`SIGTERM` para cerrar bien, `SIGKILL` para garantizar que no quede nada.

### Fundamentos previos

- `os.kill(pid, sig)` envía una señal.
- `SIGTERM` es la petición cortés; `SIGKILL` es inapelable.

### Qué es

El enforcer: termina **todos** los PIDs coincidentes, primero con `SIGTERM`, espera, y remata
los sobrevivientes con `SIGKILL`.

### Qué problema resuelve

- `SIGTERM` solo: la app puede ignorarlo y quedarse viva.
- `SIGKILL` directo: corta sin dejar cerrar archivos.

### Cómo funciona paso a paso

1. `match_pids(target)` → lista de PIDs.
2. `SIGTERM` a todos.
3. `time.sleep(0.3)`.
4. **Re-escanear** y `SIGKILL` a lo que quede.

### Qué se rompería sin esto

Matar una sola vez dejaría el `bwrap` huérfano relanzando la app, o un proceso que ignoró el
`TERM` vivo dentro de la ventana.

### Para qué sirve aquí

Es el brazo ejecutor: el scheduler decide *cuándo*, el matcher *qué*, y esto *cómo*.

### Cómo se usa (archivos reales)

```python
def enforce(target, log=None):
    pids = match_pids(target)
    if not pids:
        return 0
    for pid in pids:
        _signal(pid, signal.SIGTERM)
    time.sleep(GRACE_SECONDS)
    for pid in match_pids(target):
        _signal(pid, signal.SIGKILL)
```

### Error común

Matar **solo el PID líder**. Un Flatpak corre `bwrap` + app; el líder no es el único. Y un
juego de Steam es un árbol (`reaper` → `proton` → juego). Detección: la app "se cierra" pero
reaparece sola. Arreglo: matar **el conjunto completo** de PIDs coincidentes.

### Para profundizar

`man 7 signal`.

---

## Por qué no `pkill -f`

### En una frase

`pkill -f` matchea por **línea de comandos**, que es frágil y se evade.

### Qué problema resuelve

`-f` coincide con cualquier proceso cuya *cmdline* contenga el patrón: falsos positivos (otro
proceso con la misma cadena) y bypass (renombrar o cambiar argumentos).

### Cómo funciona paso a paso

Por eso el matcher usa **cgroup** y el enforcer manda señales **por PID**, con el conjunto
controlado por nosotros.

### Error común

`pkill -f stremio` matando también un editor que tiene "stremio" abierto. Detección: se
cierran cosas que no pediste. Arreglo: matchear por cgroup y señalar PIDs concretos.

### Para profundizar

`man pkill` (opción `-f` y sus advertencias).
