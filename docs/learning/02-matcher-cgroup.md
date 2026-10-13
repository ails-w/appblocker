# Sección 02 — Matcher por cgroup

> Cómo se identifica de forma confiable un proceso objetivo, y por qué el nombre del binario
> no sirve.
> Implementación → `core/matcher.py`

## Glosario de la sección

| Término | Qué significa (en una línea) |
|---|---|
| `/proc` | filesystem virtual con el estado de cada proceso |
| cgroup | agrupación de procesos del kernel (jerárquica) |
| scope | cgroup de `systemd` para un conjunto de procesos (ej. una app) |
| Flatpak | empaquetado sandbox que corre la app en su propio scope |
| `/proc/<pid>/cgroup` | el archivo que dice a qué cgroup pertenece un PID |

## Mapa de conceptos

```text
  nombre del binario          cgroup del proceso
  ──────────────────          ──────────────────
  se rompe si renombran  ✗    estable              ✓
  no existe en Flatpak   ✗    existe en Flatpak   ✓
        │                            │
        └──────────┬─────────────────┘
                   ▼
        appblocker matchea por /proc/<pid>/cgroup
```

---

## Matchear por cgroup

### En una frase

En vez de buscar "cómo se llama el proceso", buscamos "en qué cgroup vive", porque el cgroup
no miente.

### Fundamentos previos

- `/proc` es un filesystem virtual: cada `/proc/<pid>/` describe un proceso.
- `/proc/<pid>/cgroup` lista los cgroups del proceso, uno por línea.

### Qué es

Leer `/proc/<pid>/cgroup` y comprobar si contiene una subcadena (el `cgroup_match` del
target). Si la contiene, ese PID es del objetivo.

### Qué problema resuelve

**Dos dolores concretos:**

1. **Renombrar el binario.** Un matcher por nombre (`pgrep`) se burla renombrando; el cgroup
   no cambia porque lo asigna `systemd`, no el usuario.
2. **Flatpak.** Stremio (Flatpak) **no tiene binario en `$PATH`**: corre dentro de
   `app-flatpak-com.stremio.Stremio-*.scope`. Solo hay cgroup.

### Cómo funciona paso a paso

1. `os.listdir("/proc")`, quedarse con los nombres numéricos.
2. Saltar `pid == 1` y el propio PID del daemon.
3. Leer `/proc/<pid>/cgroup`.
4. Si `cgroup_match` está en el contenido → es un PID objetivo.
5. Opcional: si no, comprobar `cmdline_match` en `/proc/<pid>/cmdline`.

### Qué se rompería sin esto

`appblocker check` daría `0 procesos` con Stremio abierto, y no se bloquearía nada. Con un
matcher por nombre, renombrar el binario sería un bypass trivial.

### Para qué sirve aquí

Es cómo el daemon sabe *qué* matar. El `enforcer` recibe la lista de PIDs y los señala.

### Cómo se usa (archivos reales)

```toml
[target.stremio]
kind = "flatpak"
flatpak_id = "com.stremio.Stremio"
cgroup_match = "com.stremio.Stremio"
```

```bash
# verlo a mano con la app abierta:
pgrep -f stremio | head -1 | xargs -I{} cat /proc/{}/cgroup
```

### Error común

Usar el **nombre del ejecutable** como única clave. Detección: `check` falla con la app
abierta, o un rename lo evade. Arreglo: apuntar `cgroup_match` al id estable
(`com.<vendor>.<app>`).

### Para profundizar

`man 7 cgroups` · `man 5 proc` (sección `/proc/<pid>/cgroup`).

---

## Por qué `flatpak kill` no se usa desde el daemon

### En una frase

`flatpak kill` ve la **sesión del usuario que lo invoca**; el daemon es root y corre en otro
contexto, así que no vería la instancia de tu sesión.

### Qué es

El CLI de Flatpak habla con el `flatpak-session-helper` de la sesión del usuario. Como root,
`flatpak ps` no lista las apps de tu sesión.

### Qué problema resuelve

Evita un falso "ya lo maté" que no mata nada.

### Cómo funciona paso a paso

Por eso el matcher **lee `/proc` directo**: es **independiente de la sesión** y funciona igual
desde root.

### Error común

Llamar `flatpak kill <id>` desde un servicio root y creer que funcionó. Detección: el log dice
"maté" pero la app sigue abierta. Arreglo: matar por PIDs/scope leídos de `/proc`.

### Para profundizar

`man flatpak-kill` (y la nota sobre el helper de sesión).
