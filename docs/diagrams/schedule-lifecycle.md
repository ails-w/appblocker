# Ciclo de vida del horario

Cómo se evalúa una semana, y por qué el **cruce de medianoche** es el caso que rompe a los
schedulers ingenuos.

## Reglas

- Una ventana se define por `days`, `start` y `end`.
- Si `start < end` → ventana **del mismo día**.
- Si `start > end` → ventana que **cruza medianoche**: empieza hoy y termina **mañana**.

## Semana de ejemplo

```mermaid
gantt
    title Stremio (ejemplo del repo)
    dateFormat HH:mm
    axisFormat %H:%M
    section Lunes–Viernes
    mañana 05:00–16:00   :05:00, 11h
    noche 20:00–02:00    :20:00, 6h
    section Domingo
    noche 19:00–02:00    :19:00, 7h
```

> En el diagrama, la barra de "noche" de un día se **dibuja** hasta las 24:00; en la práctica
> sigue hasta las 02:00 del día siguiente.

## Cómo se decide "activo ahora"

Para una ventana que cruza medianoche, estar activo **ahora** significa:

```text
activo si  (hoy ∈ days  y  ahora >= start)      ← arranque de hoy
        o  (ayer ∈ days y  ahora <  end)        ← cola de ayer
```

Ejemplo concreto, ventana `20:00 → 02:00` los `[mon..fri]`:

| Momento | ¿activo? | Por qué |
|---|---|---|
| Viernes 21:00 | sí | hoy = vie ∈ days y 21:00 ≥ 20:00 |
| **Sábado 01:00** | **sí** | hoy = sáb ∉ days, pero **ayer = vie** ∈ days y 01:00 < 02:00 |
| Sábado 03:00 | no | ayer = vie pero 03:00 ≥ 02:00 (se acabó la cola) |
| Lunes 01:00 | no | hoy = lun ∈ days, pero 01:00 < 20:00; ayer = dom ∉ days |

Ese **Sábado 01:00 = sí** es exactamente lo que un scheduler de un solo día perdería.
