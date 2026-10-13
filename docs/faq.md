# Preguntas frecuentes

## ¿Por qué Python y no un binario compilado?

Porque es una **herramienta de uso diario**: cero build, cero dependencias (solo la stdlib),
y se lee de un tirón. `python3` ya está en cualquier Arch. Un binario no aportaría nada aquí.

## ¿Por qué matar y no impedir la ejecución?

Cerrar es simple, robusto y suficiente para una app de proceso único (Stremio). **Impedir**
el `exec` de verdad requiere `fanotify` con `FAN_OPEN_EXEC_PERM` — más código y más riesgo.
Se dejó como Tier 2 opcional, no como parte del MVP. Detalle:
[`threat-model.md`](threat-model.md).

## ¿Por qué el matcher va por `cgroup` y no por nombre?

Porque el nombre se rompe: renombrar el binario, o un Flatpak que **no tiene binario en
`$PATH`**. El cgroup (`app-flatpak-<id>.scope`) es estable en ambos casos. Ver
[`learning/02-matcher-cgroup.md`](learning/02-matcher-cgroup.md).

## ¿Puedo bloquear juegos de Steam?

Sí, pero el target es distinto: los juegos son un **árbol** bajo Steam (`reaper` → `proton` →
juego). Bloquear Steam entero es lo pragmático (los juegos no arrancan sin él). Si quieres un
juego suelto, apúntalo por su cgroup/Binario. El motor es el mismo; cambia el `target`.

## ¿Por qué las ventanas cruzan medianoche pero `focusguard` no?

Porque aquí **sí** hacía falta: un bloqueo `20:00 → 02:00` de lunes a viernes debe alcanzar
el sábado. El scheduler evalúa "el inicio de hoy" **y** "la cola de ayer", así no se pierde.
Ver [`learning/01-scheduler.md`](learning/01-scheduler.md).

## ¿`chattr +i` no es peligroso?

Es **fricción**, no una frontera. Un root puede quitarlo con `chattr -i`. Sirve para que
desactivar el bloqueo sea **deliberado**, se **revierta solo** (check de integridad cada
minuto) y quede **auditado**. Si te preocupa quedarte fuera: `chattr -i` siempre funciona como
root, y `scripts/uninstall.sh` lo hace por ti.

## ¿Por qué la config es `644` y no `600`?

Lo importante es la **propiedad `root:root`**: sin `sudo` nadie la escribe. El `600` además
rompería el CLI, que corre como usuario y necesita **leer**. Leer no es el riesgo.

## ¿`Restart=always` me protege de que alguien lo apague?

No del todo. `Restart=always` revive una caída **involuntaria**, pero `systemctl stop` es una
parada **intencional** y `systemd` la respeta. La fricción real es la config `root:root` y un
arranque deliberado con `sudo`.

## ¿En qué se diferencia de `focusguard` y `focusblock`?

Son tres niveles distintos del mismo tema:

- **`focusguard`**: limita una **cuenta** (PAM + `loginctl`). Bloquea *a la persona*.
- **`focusblock`**: app TUI en .NET con daemon, IPC y métricas. Es el proyecto de **aprendizaje backend**.
- **`appblocker`** (este): bloquear **aplicaciones** por horario con lo mínimo y auditable. Es una **herramienta**, no un proyecto de aprendizaje.

## ¿Sirve para control parental?

Sirve como **autocontrol y control doméstico suave**, no como barrera. Si el usuario tiene
`sudo`, está en `docker`, o tiene acceso físico, lo salta. Para control parental real: quita
privilegios y controla desde el router.
