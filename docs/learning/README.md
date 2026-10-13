# Aprendizaje

Conceptos del proyecto, **un archivo por sección**. Se leen en orden: cada uno se entiende
solo, pero juntos explican todo el sistema.

| # | Archivo | Qué aprenderás |
|---|---|---|
| — | [`00-fundamentos.md`](00-fundamentos.md) | `/etc`, la convención `.d`, la numeración, TOML, las units de `systemd` |
| 1 | [`01-scheduler.md`](01-scheduler.md) | ventanas horarias, el cruce de medianoche, `timezone` |
| 2 | [`02-matcher-cgroup.md`](02-matcher-cgroup.md) | `/proc`, cgroups, scopes, por qué Flatpak complica el match |
| 3 | [`03-enforce-signals.md`](03-enforce-signals.md) | señales, árboles de procesos, por qué `pkill` no alcanza |

## Esquema de cada concepto

- **En una frase** — la idea mínima.
- **Fundamentos previos** — lo que hay que entender antes, explicado ahí mismo.
- **Qué es** / **Qué problema resuelve** / **Cómo funciona paso a paso**.
- **Qué se rompería sin esto** — contrafactual concreto de *este* proyecto.
- **Para qué sirve aquí** / **Cómo se usa (archivos reales)**.
- **Error común** — qué se hace mal y cómo detectarlo.
- **Para profundizar**.

## Reglas

- Se acumula: los conceptos aprendidos **nunca** se borran.
- Glosario + mapa de conceptos obligatorios al inicio de cada archivo.
- Cada concepto debe tener su **Error común**.
- Plantilla para una sección nueva: [`template.md`](template.md).
