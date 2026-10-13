# appblocker

> Bloquea aplicaciones concretas por horario en Linux, con un daemon `systemd` que corre como
> root. Sin GUI, sin build, sin dependencias fuera de la stdlib de Python.

![Linux](https://img.shields.io/badge/OS-Linux-informational)
![systemd](https://img.shields.io/badge/init-systemd-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

## ¿Qué es?

`appblocker` cierra aplicaciones dentro de **ventanas horarias**, definidas por días y horas.
Un daemon mínimo lee el reloj cada segundo, decide si hay una ventana activa y, si la hay,
termina los procesos de las aplicaciones bloqueadas.

Resuelve tres cosas que un `cron` con `pkill` hace mal:

1. **Relanzar.** `cron` mata una vez; el usuario reabre la app un segundo después. Aquí el
   daemon **sigue** vigilando durante toda la ventana.
2. **Renombrar.** Un match por nombre de binario se evade renombrando. Aquí se matchea por
   **cgroup**, que el usuario no controla.
3. **Medianoche.** Un bloqueo `20:00 → 02:00` de lunes a viernes debe alcanzar el **sábado**.
   Muchos schedulers pierden esa cola; este no.

Es una herramienta de **autocontrol**, no un sistema de seguridad: ver
[Alcance y límites](#alcance-y-límites).

## Características

- Ventanas por día y rango horario, con **cruce de medianoche**.
- Match por **cgroup**: inmune a renombrar el binario y válido para **Flatpak**.
- **Recarga en caliente**: cambiar un horario no requiere reiniciar el servicio.
- **CLI** de inspección: `status`, `windows`, `check`, `test`, `reload`.
- **Integridad** opcional: copia golden + `chattr +i` + restauración cada minuto.
- **Cero dependencias**: solo la stdlib (`tomllib`, `zoneinfo`).

## Requisitos

| Requisito | Por qué |
|---|---|
| Linux con `systemd` | el daemon corre como unidad `.service` |
| `python3 >= 3.11` | `tomllib` entró en la stdlib en 3.11 |
| `e2fsprogs` (`chattr`) | solo para el módulo de integridad |
| `sudo` | instalar y gestionar el servicio |

## Instalación

```bash
git clone https://github.com/ails-w/appblocker.git
cd appblocker
sudo scripts/install.sh --dry-run   # ver el plan sin tocar nada
sudo scripts/install.sh             # config + daemon + CLI + integridad
scripts/verify.sh                   # comprobar cada capa
```

Después de instalar, **edita tu configuración** (ver [Configuración](#configuración)) y
recarga:

```bash
appblocker reload
```

## Uso

### CLI

| Comando | Qué hace |
|---|---|
| `appblocker status` | estado actual y ventanas (marca `*` la activa) |
| `appblocker windows` | lista las ventanas configuradas |
| `appblocker check` | PIDs que matchean cada objetivo **ahora** |
| `appblocker test` | dry-run: qué mataría en este instante, sin matar |
| `appblocker reload` | reinicia el servicio |

El CLI corre como **usuario** (no root) y solo **lee** la configuración.

### El servicio

```bash
systemctl status appblocker.service --no-pager
journalctl -u appblocker -f          # ver los bloqueos en vivo
```

### Como apagar el bloqueo (a propósito)

```bash
sudo systemctl stop appblocker.service
```

> Si aplicaste el módulo de integridad, la configuración está inmutable. Para editar:
> `sudo chattr -i /etc/appblocker/config.toml` y luego `sudo appblocker-lock` al terminar.

## Configuración

Todo vive en `/etc/appblocker/`, propiedad de `root:root`.

### `config.toml` — comportamiento global

```toml
timezone = "local"              # "local" o una zona IANA, ej. "America/Bogota"
poll_interval_seconds = 1       # cada cuánto reevalúa
log_attempts = true            # registrar cada cierre en el journal
```

### `policy.d/*.toml` — qué y cuándo

Un archivo por objetivo. El nombre empieza con un número (`10-`, `20-`) porque los `.d` se
leen en orden alfabético.

**Objetivo** (`[target.<nombre>]`):

| Campo | Obligatorio | Qué es |
|---|---|---|
| `kind` | no | `flatpak` (por defecto) o `process` |
| `flatpak_id` | si `kind = "flatpak"` | id del Flatpak, ej. `com.stremio.Stremio` |
| `cgroup_match` | sí* | subcadena a buscar en `/proc/<pid>/cgroup` |
| `cmdline_match` | no | subcadena alternativa en la línea de comandos |

\* si no pones `cgroup_match`, se usa `flatpak_id`.

**Ventana** (`[[window]]`, repetible):

| Campo | Qué es |
|---|---|
| `days` | días en inglés: `mon`…`sun` |
| `start` / `end` | horas `HH:MM` (24 h). Si `start > end`, **cruza medianoche** |
| `apps` | nombres de objetivos que aplica |

**Ejemplo completo** (bloquear Stremio):

```toml
[target.stremio]
kind = "flatpak"
flatpak_id = "com.stremio.Stremio"
cgroup_match = "com.stremio.Stremio"

[[window]]
days  = ["mon", "tue", "wed", "thu", "fri"]
start = "05:00"
end   = "16:00"
apps  = ["stremio"]

[[window]]
days  = ["mon", "tue", "wed", "thu", "fri"]
start = "20:00"
end   = "02:00"     # cruza medianoche: el viernes llega al sábado 02:00
apps  = ["stremio"]
```

> **Valida siempre el TOML**, no lo mires a ojo:
> `python3 -c "import tomllib; tomllib.load(open('10-stremio.toml','rb'))"`.

## Verificación

```bash
appblocker status          # ¿qué ventana está activa ahora?
appblocker check           # ¿detecta la app con ella abierta?
appblocker test            # dry-run de lo que se cerraría
```

Batería completa, capa por capa: [`docs/verification.md`](docs/verification.md).

## Desinstalación

```bash
sudo scripts/uninstall.sh          # conserva /etc/appblocker
sudo rm -rf /etc/appblocker        # solo si quieres borrar la config
```

## Estructura del repositorio

```text
modules/   una capacidad autocontenida por módulo (files/ + README de aplicar/verificar/rollback)
docs/      arquitectura, modelo de amenaza, instalación, verificación, conceptos y diagramas
scripts/   install.sh · uninstall.sh · verify.sh
```

**Regla del espejo:** cada módulo guarda sus archivos en
`modules/NN-nombre/files/<ruta-destino>`. La ruta dentro del repo **es** la ruta en el
sistema, así que instalar es copiar y **nada se transcribe a mano**.

| Módulo | Qué aporta |
|---|---|
| [`00-base`](modules/00-base/) | configuración global |
| [`01-policy`](modules/01-policy/) | objetivos y ventanas |
| [`02-daemon`](modules/02-daemon/) | el motor + su unit de `systemd` |
| [`03-cli`](modules/03-cli/) | el comando `appblocker` |
| [`04-integrity`](modules/04-integrity/) | golden + `chattr +i` + restauración |

## Alcance y límites

- **No es una frontera contra root.** Cualquiera con `sudo` (o el grupo `docker`, o acceso
  físico) puede desactivarlo. La promesa honesta es *deliberado, revertido y auditado*.
- **El MVP cierra, no impide.** Una app bloqueada puede abrir y desaparecer en el siguiente
  intervalo de sondeo. Denegar el `exec` (`fanotify`) es una opción futura, no una promesa.
- **Depende del reloj del sistema.** Cambiarlo afecta las ventanas.

Lista completa: [`docs/threat-model.md`](docs/threat-model.md).

## Documentación

| Área | Documento |
|---|---|
| Cómo encajan las capas | [`docs/architecture.md`](docs/architecture.md) |
| Qué protege y qué no | [`docs/threat-model.md`](docs/threat-model.md) |
| Orden de instalación | [`docs/install.md`](docs/install.md) |
| Cómo verificar | [`docs/verification.md`](docs/verification.md) |
| Algo se rompió | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Preguntas frecuentes | [`docs/faq.md`](docs/faq.md) |
| Conceptos, sección por sección | [`docs/learning/`](docs/learning/) |
| Diagramas | [`docs/diagrams/`](docs/diagrams/) |

## Licencia

MIT — ver [LICENSE](LICENSE).
