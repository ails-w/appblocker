# Sección 00 — Fundamentos

> Las decisiones de forma: dónde vive cada cosa y por qué. Sin esto, el resto del repo se
> siente arbitrario.
> Implementación → `modules/00-base/README.md`

## Glosario de la sección

| Término | Qué significa (en una línea) |
|---|---|
| FHS | Estándar que define qué va en cada carpeta del sistema |
| `/etc` | Configuración del sistema (texto editable, propiedad de root) |
| `.d` | Convención: "directorio de fragmentos que se fusionan" |
| TOML | Formato de configuración hecho para leer humanos |
| unit | Descripción declarativa de un recurso que `systemd` administra |

## Mapa de conceptos

```text
      dónde vive la config             cómo se declara
      ─────────────────────            ───────────────
      /etc  ─┐                         TOML ─┐
      .d    ─┼─▶ policy.d/10-*.toml           ├─▶ lo que el daemon lee
      NN-   ─┘                         ┌──────┘
                                       │
      cómo corre ─▶ systemd unit ──────┘
```

---

## `/etc` y el FHS

### En una frase

Linux reparte los archivos según su **naturaleza** (configuración, programa, datos), no al
azar.

### Fundamentos previos

Ninguno: es la primera capa.

### Qué es

El **Filesystem Hierarchy Standard** asigna un rol a cada carpeta:

| Carpeta | Rol |
|---|---|
| `/etc` | Configuración del sistema |
| `/usr` | Programas y librerías (del paquete) |
| `/var` | Datos variables (logs, colas) |
| `/run` | Estado efímero (RAM, se borra al reiniciar) |
| `/opt` | Software autocontenido de terceros |
| `/home` | Datos del usuario |

### Qué problema resuelve

Que el sistema y tú **sepan dónde buscar**. Además, en este proyecto hay un motivo extra:
`/etc` es `root:root`, así que poner la config ahí **es** el candado.

### Cómo funciona paso a paso

1. El código vive en `/usr/local/lib/appblocker/` (es *programa*).
2. La configuración vive en `/etc/appblocker/` (es *config*).
3. Un usuario sin `sudo` no puede escribir `root:root`.

### Qué se rompería sin esto

Si la config viviera en `~/.config/appblocker/`, la editarías sin `sudo` en dos segundos y el
bloqueo sería decorativo.

### Para qué sirve aquí

Es el mecanismo de fricción. Ver [`../threat-model.md`](../threat-model.md).

### Cómo se usa (archivos reales)

```bash
ls -la /etc/appblocker/            # config, root:root
ls -la /usr/local/lib/appblocker/  # código
```

### Error común

Poner la config en `~/.config` "porque es donde van mis dotfiles". Ahí es **por usuario** y
modificable: mata el propósito. Detección: si puedes editar el horario sin `sudo`, está mal
ubicado.

### Para profundizar

`man hier` (la página del FHS).

---

## La convención `.d`

### En una frase

`.d` = *directory*: una carpeta donde cada pieza de configuración vive aparte y nada pisa a
nada.

### Qué es

Un patrón de Unix de décadas: `/etc/pacman.d/`, `/etc/sysctl.d/`, `/etc/X11/xorg.conf.d/`,
`/etc/systemd/system/<svc>.service.d/`. Significa *"sueltas fragmentos aquí y el programa los
fusiona"*.

### Qué problema resuelve

Un archivo monolítico es frágil: para agregar un juego habría que editar el archivo compartido
por todos.
Con `.d`, **agregar es crear un archivo**.

### Para qué sirve aquí

`/etc/appblocker/policy.d/` — un `.toml` por objetivo. Sumar Steam mañana = un archivo nuevo,
sin tocar el daemon.

### Error común

Editar un archivo existente para agregar algo en vez de crear un fragmento nuevo. Detección:
si tu cambio haría que dos objetivos dependan del mismo archivo, está mal separado.

### Para profundizar

`man systemd.unit` (sección *Drop-in*).

---

## La numeración `10-`, `20-`

### En una frase

Los `.d` se leen en **orden alfabético**, así que el número es la clave de ordenamiento.

### Qué es

No es decoración: `10-stremio.toml` se lee antes que `20-steam.toml`, siempre, aunque el
segundo se haya creado primero.

### Qué problema resuelve

1. **Orden determinista** (sin sorpresas).
2. **Espacio para insertar**: `15-algo.toml` queda en medio sin renombrar nada.
3. **Precedencia**: si el último gana, el número lo decide.

### Para qué sirve aquí

Agrupar y ordenar fragmentos en `policy.d/`. Se numera de 10 en 10 justamente para tener
huecos.

### Error común

Usar `1-`, `2-`, `3-` y luego necesitar algo "entre" 1 y 2. Detección: te ves obligado a
renombrar archivos para insertar uno.

---

## TOML

### En una frase

Un formato de configuración **hecho para leer humanos**, con comentarios, tipos y listas.

### Qué es

*Tom's Obvious Minimal Language*. Sus dos construcciones clave:

```toml
[target.stremio]         # [sección / tabla]
kind = "flatpak"         # clave = valor, con tipo

[[window]]               # [[doble corchete]] = LISTA de tablas
days = ["mon", "tue"]    # array de verdad
```

### Qué problema resuelve

JSON no admite comentarios; YAML rompe con un espacio de más (y convierte `NO` en `false`).
TOML evita ambos, y viene en la **stdlib** de Python (`tomllib`, 3.11+): cero dependencias.

### Cómo funciona paso a paso

1. `[[window]]` **acumula** en una lista: por eso cada ventana es un `[[window]]`.
2. El daemon parsea con `tomllib.load()`.
3. El header del espejo `modules/*/files/...` guarda el archivo ya parseable.

### Qué se rompería sin esto

Un TOML inválido revienta el parseo (`TOMLDecodeError`) y el daemon no arranca.

### Cómo se usa (archivos reales)

```bash
python3 -c "import tomllib; tomllib.load(open('policy.d/10-stremio.toml','rb'))"
```

### Error común

`timezone = local` (falta comillas) o `fail = mode = open` (dos `=` en una línea). **No se
detecta a ojo** — se detecta parseando. Ver
[`../troubleshooting.md`](../troubleshooting.md).

### Para profundizar

[`toml.io`](https://toml.io) · `python3 -c "import tomllib; help(tomllib)"`.

---

## Units de `systemd`

### En una frase

Una **unit** es una descripción declarativa de algo que `systemd` administra; `.service` es
la que describe un proceso.

### Fundamentos previos

`systemd` es el PID 1: arranca y **vigila** servicios.

### Qué es

| Extensión | Representa |
|---|---|
| `.service` | un proceso / daemon |
| `.timer` | un horario |
| `.socket` | un socket que activa bajo demanda |
| `.target` | un punto de agrupación |

Declarativo: tú describes el **estado deseado** (`Restart=always`), no el bucle.

### Qué problema resuelve

Supervisión: si el daemon cae, `systemd` lo revive; sobrevive a tu logout y arranca con la
máquina. Un `&` en una terminal no hace nada de eso.

### Qué se rompería sin esto

Sin `systemd`, el daemon muere al cerrar la sesión y no bloquea nada.

### Para qué sirve aquí

`appblocker.service` es el que mantiene vivo el bucle de enforcement.

### Cómo se usa (archivos reales)

```bash
systemctl cat appblocker.service
systemctl status appblocker.service --no-pager
```

### Error común

Creer que `Restart=always` cubre también `systemctl stop`. **No**: un `stop` es
*intencional* y `systemd` no reinicia. La fricción viene de la config `root:root`.

### Para profundizar

`man systemd.service` · `man systemd.exec`.
