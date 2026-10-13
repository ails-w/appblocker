# Sección 01 — Scheduler

> Cómo se decide si una ventana está activa *ahora*, y por qué el cruce de medianoche es el
> caso que rompe a los schedulers ingenuos.
> Implementación → `core/scheduler.py`

## Glosario de la sección

| Término | Qué significa (en una línea) |
|---|---|
| ventana | un rango horario con días asociados |
| cruce de medianoche | ventana donde `start > end` (ej. `20:00 → 02:00`) |
| naive vs aware | `datetime` sin zona vs con zona (`tzinfo`) |
| weekday | día de la semana como índice (lunes = 0) |

## Mapa de conceptos

```text
  days + start/end
        │
        ├─ start < end  ─▶ ventana del mismo día
        └─ start > end  ─▶ cruza medianoche ─▶ hay que mirar HOY y AYER
                                                     │
                              OJO: comparar horas aware vs naive ─▶ TypeError
```

---

## Ventanas y cruce de medianoche

### En una frase

Una ventana se define por `days`, `start` y `end`; si `start > end`, empieza hoy y termina
**mañana**.

### Fundamentos previos

- `datetime.weekday()` → lunes = 0 … domingo = 6.
- `datetime.time()` → la hora del día.

### Qué es

Dos formas de ventana:

- **Mismo día**: `start < end` (ej. `05:00 → 16:00`).
- **Cruce**: `start > end` (ej. `20:00 → 02:00`).

### Qué problema resuelve

Un bloqueo nocturno real (`20:00 → 02:00`) que un scheduler de un solo día **pierde**: cree
que la ventana terminó a medianoche y deja libre la madrugada.

### Cómo funciona paso a paso

1. `today` = día de la semana de `now`.
2. `clock` = hora **naive** de `now`.
3. Si **no** cruza: activo si `today ∈ days` y `start <= clock < end`.
4. Si **cruza**: activo si
   - `today ∈ days` **y** `clock >= start` (arranque de hoy), **o**
   - `ayer ∈ days` **y** `clock < end` (cola de ayer).

### Qué se rompería sin esto

El viernes `20:00 → 02:00` no alcanzaría el sábado 01:00. La madrugada del sábado quedaría
libre, que es justo cuando importa.

### Para qué sirve aquí

Es el corazón del horario. Ver el ejemplo completo en
[`../diagrams/schedule-lifecycle.md`](../diagrams/schedule-lifecycle.md).

### Cómo se usa (archivos reales)

```python
def window_active(window, now):
    today = DAYS[now.weekday()]
    clock = now.time().replace(tzinfo=None)
    if not window.crossing:
        return today in window.days and window.start <= clock < window.end
    if today in window.days and clock >= window.start:
        return True
    yesterday = DAYS[(now.weekday() - 1) % 7]
    return yesterday in window.days and clock < window.end
```

### Error común

Usar `now.time()` de un `datetime` **con zona horaria**. Devuelve un `time` *aware*, y
comparar `aware <= naive` lanza **`TypeError`**. Detección: el daemon revienta solo cuando
`timezone` no es `local`. Arreglo: `.replace(tzinfo=None)`.

### Para profundizar

`python3 -c "from datetime import datetime; help(datetime.weekday)"`.

---

## `timezone`

### En una frase

El scheduler compara horas, así que **qué reloj** usa importa.

### Qué es

Con `timezone = "local"` usa la hora local del sistema (`datetime.now()`).
Con `timezone = "America/Bogota"` fija la zona con `zoneinfo` (`datetime.now(ZoneInfo(...))`).

### Qué problema resuelve

Hacer el horario portable a un equipo con la zona mal configurada.

### Cómo se usa (archivos reales)

```toml
timezone = "local"        # o "America/Bogota"
```

### Error común

Poner `timezone = local` **sin comillas** (TOML inválido). Ver
[`00-fundamentos.md`](00-fundamentos.md).
