#!/usr/bin/env bash
# Verifica cada capa de appblocker. No modifica nada.
# Uso: scripts/verify.sh
set -uo pipefail

FALLOS=0
ok()   { printf '  [ok]    %s\n' "$1"; }
fail() { printf '  [FALLA] %s\n' "$1"; FALLOS=$((FALLOS + 1)); }

echo "== Configuración =="
for f in /etc/appblocker/config.toml /etc/appblocker/policy.d/10-stremio.toml; do
  if [ -f "$f" ]; then ok "existe $f"; else fail "falta $f"; fi
done

if python3 -c "
import glob, tomllib
for p in ['/etc/appblocker/config.toml'] + glob.glob('/etc/appblocker/policy.d/*.toml'):
    tomllib.load(open(p, 'rb'))
" 2>/dev/null; then
  ok "el TOML parsea"
else
  fail "TOML inválido (revisa comillas y '=' de más)"
fi

if [ -r /etc/appblocker/policy.d/10-stremio.toml ] && [ "$(stat -c '%U' /etc/appblocker/policy.d/10-stremio.toml)" = "root" ]; then
  ok "policy.d legible y propiedad de root"
else
  fail "policy.d no legible o no es de root"
fi

echo "== Daemon =="
if systemctl is-active --quiet appblocker.service; then
  ok "appblocker.service activo"
else
  fail "appblocker.service NO activo (systemctl status appblocker.service)"
fi
if systemctl is-enabled --quiet appblocker.service; then
  ok "appblocker.service habilitado"
else
  fail "appblocker.service NO habilitado"
fi

echo "== CLI =="
if command -v appblocker >/dev/null 2>&1; then
  ok "appblocker en PATH"
else
  fail "appblocker ausente de PATH"
fi

echo
if [ "$FALLOS" -eq 0 ]; then
  echo "Todo OK."
else
  echo "$FALLOS comprobación(es) fallida(s)."
  exit 1
fi
