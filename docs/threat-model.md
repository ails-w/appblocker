# Modelo de amenaza

Documentar lo que un sistema **no** protege es parte del contrato.

## Supuesto de diseño

Pensado para **autocontrol**: que *tú* no abras una app fuera de su horario. **No** está
pensado contra un atacante con root, y no pretende serlo.

## Qué protege

| Intento de bypass | Qué lo detiene | Capa |
|---|---|---|
| Abrir la app dentro de la ventana | el daemon la cierra en ≤1 intervalo de sondeo | 2 |
| Renombrar el binario | el matcher va por **cgroup**, no por nombre | 2 |
| Abrir Stremio desde Flatpak o desde la terminal | mismo cgroup en ambos casos | 2 |
| Volver a abrirla un segundo después | el daemon sigue corriendo dentro de la ventana | 2 |
| Editar el horario sin permiso | `config` y `policy.d` son `root:root` | 0/1 |
| Pararlo y olvidarse | `Restart=always` lo revive; `stop` queda registrado | 2 |

## Qué NO protege

| Límite | Por qué |
|---|---|
| **Root / `sudo`** | Puede `systemctl stop/disable`, borrar la config y editar todo. |
| **`sudo` sin contraseña (`NOPASSWD`)** | Bypass total. |
| **Grupos potentes** (`docker`, `libvirt`…) | `docker` ≈ root (montar `/` y editar desde afuera). |
| **Otro administrador** | Cualquier cuenta con `sudo` puede desarmar; queda auditado, pero puede. |
| **Acceso físico / live USB** | Puede editar el disco desde otro sistema. |
| **Cambiar el reloj del sistema** | El scheduler depende de la hora. |
| **Abrir la app y usarla <1 s** | El MVP cierra; **no impide** la ejecución (ver abajo). |

## La diferencia honesta: cerrar ≠ impedir

El MVP (Tier 1) **cierra** procesos: la app puede abrir y desaparecer en el siguiente
intervalo de sondeo. **No** deniega el `exec` a nivel kernel.

Impedir el lanzamiento de verdad requiere un `fanotify` con `FAN_OPEN_EXEC_PERM` (Tier 2),
que sí bloquea el `exec`. Es más código y más riesgo, y para una app Flatpak de proceso
único el Tier 1 sobra en la práctica. Se dejó fuera a propósito; no se promete.

## Fricción, no frontera

`Restart=always` + config `root:root` hacen que desactivarlo sea **deliberado**, no un
descuido. Con `sudo`, un `systemctl stop` sigue siendo posible — y está bien: no es una
cárcel, es una decisión que quieres tomar en frío.
