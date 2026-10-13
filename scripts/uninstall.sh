#!/usr/bin/env bash
# Desinstala appblocker. Conserva la configuración por defecto.
# Uso: sudo scripts/uninstall.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta con sudo." >&2
  exit 1
fi

echo "== detener y deshabilitar =="
systemctl disable --now appblocker.service 2>/dev/null || true

echo "== quitar programa y unit =="
rm -f /usr/local/bin/appblocker
rm -rf /usr/local/lib/appblocker
rm -f /etc/systemd/system/appblocker.service
systemctl daemon-reload

echo
echo "Desinstalado."
echo "La configuración (/etc/appblocker) NO se borró. Para quitarla también:"
echo "  sudo rm -rf /etc/appblocker"
