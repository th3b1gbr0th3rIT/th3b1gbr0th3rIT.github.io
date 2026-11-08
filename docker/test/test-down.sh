#!/usr/bin/env bash
# Para el test local: elimina el contenedor web-test y, si se usó --sin-docker, el servidor de Python.
set -uo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$AQUI/.web-test.pid"

dk() {
  if docker info >/dev/null 2>&1; then docker "$@"
  else sg docker -c "docker $(printf '%q ' "$@")"; fi
}

if command -v docker >/dev/null 2>&1 && dk ps -a --format '{{.Names}}' 2>/dev/null | grep -qx web-test; then
  dk rm -f web-test >/dev/null && echo "Contenedor web-test eliminado"
else
  echo "Sin contenedor web-test"
fi
if [ -f "$PIDFILE" ]; then
  kill "$(cat "$PIDFILE")" 2>/dev/null && echo "Servidor de Python parado"
  rm -f "$PIDFILE"
fi
echo "OK: test local parado"
