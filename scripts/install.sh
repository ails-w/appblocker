#!/usr/bin/env bash
# Instala appblocker: config, policy, daemon y CLI.
# Uso: sudo scripts/install.sh [--dry-run]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta con sudo." >&2
  exit 1
fi

M="$REPO_DIR/modules"

echo "== Módulo 00: base =="
run install -d /etc/appblocker
run install -m 0644 "$M/00-base/files/etc/appblocker/config.toml" /etc/appblocker/config.toml

echo "== Módulo 01: policy =="
run install -d /etc/appblocker/policy.d
run install -m 0644 "$M/01-policy/files/etc/appblocker/policy.d/10-stremio.toml" \
                    /etc/appblocker/policy.d/10-stremio.toml
if grep -q 'com.stremio.Stremio' /etc/appblocker/policy.d/10-stremio.toml 2>/dev/null; then
  echo "  AVISO: la policy es el EJEMPLO (Stremio). Edítala con TUS objetivos y horarios."
fi

echo "== Módulo 02: daemon =="
run install -d /usr/local/lib/appblocker/core /usr/local/lib/appblocker/enforcers
run install -m 0644 "$M/02-daemon/files/usr/local/lib/appblocker/daemon.py" \
                    /usr/local/lib/appblocker/daemon.py
run install -m 0644 "$M"/02-daemon/files/usr/local/lib/appblocker/core/*.py \
                    /usr/local/lib/appblocker/core/
run install -m 0644 "$M"/02-daemon/files/usr/local/lib/appblocker/enforcers/*.py \
                    /usr/local/lib/appblocker/enforcers/
run install -m 0644 "$M/02-daemon/files/etc/systemd/system/appblocker.service" \
                    /etc/systemd/system/appblocker.service
run systemctl daemon-reload
run systemctl enable --now appblocker.service

echo "== Módulo 03: CLI =="
run install -m 0644 "$M/03-cli/files/usr/local/lib/appblocker/cli.py" \
                    /usr/local/lib/appblocker/cli.py
run install -m 0755 "$M/03-cli/files/usr/local/bin/appblocker" /usr/local/bin/appblocker

echo
echo "Instalado. Verifica con: sudo scripts/verify.sh"
