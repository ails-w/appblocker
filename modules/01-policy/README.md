# Módulo 01 — Policy

**Qué** se bloquea y **cuándo**. Un fragmento `.toml` por objetivo, dentro de `policy.d/`.

## Prerrequisitos

- Módulo `00-base` instalado (el directorio `/etc/appblocker` debe existir).

## Archivos

| Archivo | Destino | Qué hace |
|---|---|---|
| `files/etc/appblocker/policy.d/10-stremio.toml` | `/etc/appblocker/policy.d/10-stremio.toml` | define el target `stremio` y sus ventanas |

## Formato

```toml
[target.<nombre>]                # un objetivo: cómo detectarlo
kind = "flatpak"                 # tipo (hoy: flatpak | process)
cgroup_match = "<subcadena>"     # matchea /proc/<pid>/cgroup (ver docs/learning/02)
cmdline_match = "<subcadena>"    # opcional: matchea la línea de comandos

[[window]]                       # una ventana (repetible → [[...]] acumula)
days  = ["mon", "tue"]           # días en inglés: mon..sun
start = "20:00"
end   = "02:00"                  # start > end ⇒ cruza medianoche
apps  = ["<nombre>"]             # debe existir en [target.*]
```

## Aplicar

```bash
sudo install -d /etc/appblocker/policy.d
sudo install -m 0644 files/etc/appblocker/policy.d/10-stremio.toml \
                    /etc/appblocker/policy.d/10-stremio.toml
```

> **Antes de confiar en esto:** el archivo del repo es de **ejemplo** (Stremio). Edítalo con
> **tus** objetivos y **tus** horarios.

## Verificar

```bash
python3 -c "import tomllib; tomllib.load(open('/etc/appblocker/policy.d/10-stremio.toml','rb'))"
appblocker windows
```

**Esperado:** sin `TOMLDecodeError`, y las ventanas que escribiste.

## Rollback

```bash
sudo rm -f /etc/appblocker/policy.d/10-stremio.toml
```

## Notas

- El **nombre del archivo empieza con un número** (`10-`): los `.d` se leen en orden
  alfabético. Ver [`../../docs/learning/00-fundamentos.md`](../../docs/learning/00-fundamentos.md).
- Agregar un objetivo nuevo = **crear un archivo nuevo**, no editar éste.
