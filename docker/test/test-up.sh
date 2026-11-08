#!/usr/bin/env bash
# Test local de la web: construye sitio/, lo verifica y lo sirve en http://127.0.0.1:8088
# con nginx:1.27-alpine (contenedor web-test, sitio/ montado en solo lectura, sin volúmenes con nombre).
# Después comprueba con curl las rutas principales (incluidas las páginas legales).
#   docker/test/test-up.sh              -> nginx en docker
#   docker/test/test-up.sh --sin-docker -> servidor de Python (si no se puede usar docker o bajar la imagen)
# Al terminar las pruebas, SIEMPRE: docker/test/test-down.sh
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
SITIO="$RAIZ/sitio"
IMAGEN="nginx:1.27-alpine"
NOMBRE="web-test"
PUERTO=8088
URL="http://127.0.0.1:$PUERTO"
PIDFILE="$AQUI/.web-test.pid"
MODO="docker"
[ "${1:-}" = "--sin-docker" ] && MODO="python"

# docker directo o, si la sesión aún no tiene el grupo, con sg docker
dk() {
  if docker info >/dev/null 2>&1; then docker "$@"
  else sg docker -c "docker $(printf '%q ' "$@")"; fi
}

echo "== Construir y verificar"
python3 "$RAIZ/construir_web.py"
python3 "$RAIZ/verificar.py"

arrancar_python() {
  echo "== Servidor de Python en $URL (sirve 404.html en rutas inexistentes, como GitHub Pages)"
  python3 -I - "$SITIO" "$PUERTO" >/dev/null 2>&1 <<'PY' &
import functools, http.server, sys
sitio, puerto = sys.argv[1], int(sys.argv[2])
class H(http.server.SimpleHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if code == 404:
            cuerpo = open(f"{sitio}/404.html", "rb").read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(cuerpo)
        else:
            super().send_error(code, message, explain)
H.extensions_map[".svg"] = "image/svg+xml"
H.extensions_map[".woff2"] = "font/woff2"
http.server.ThreadingHTTPServer(("127.0.0.1", puerto), functools.partial(H, directory=sitio)).serve_forever()
PY
  echo $! > "$PIDFILE"
}

if [ "$MODO" = "docker" ]; then
  echo "== nginx en docker ($IMAGEN) en $URL"
  dk rm -f "$NOMBRE" >/dev/null 2>&1 || true
  if ! dk image inspect "$IMAGEN" >/dev/null 2>&1 && ! dk pull "$IMAGEN"; then
    echo "AVISO: no se ha podido bajar $IMAGEN (¿Netskope bloquea la descarga?). Sigo con --sin-docker." >&2
    MODO="python"
  fi
fi

# espera a que la web responda (máx. ~15 s)
responde() {
  curl -s --noproxy '*' --retry 5 --retry-connrefused --retry-delay 1 --max-time 3 -o /dev/null "$URL/"
}

if [ "$MODO" = "docker" ]; then
  # 1) red puente con el puerto publicado solo en 127.0.0.1
  dk run -d --name "$NOMBRE" -p "127.0.0.1:$PUERTO:80" \
    -v "$SITIO:/usr/share/nginx/html:ro" \
    -v "$AQUI/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
    "$IMAGEN" >/dev/null
  if ! responde; then
    # 2) En este equipo el tráfico del host hacia la red puente de docker se queda colgado
    #    (conecta pero no responde; cortafuegos/Netskope). Red del host con nginx solo en 127.0.0.1.
    echo "AVISO: el puerto publicado no responde; uso --network host con nginx en 127.0.0.1:$PUERTO" >&2
    dk rm -f "$NOMBRE" >/dev/null
    dk run -d --name "$NOMBRE" --network host \
      -v "$SITIO:/usr/share/nginx/html:ro" \
      -v "$AQUI/nginx-host.conf:/etc/nginx/conf.d/default.conf:ro" \
      "$IMAGEN" >/dev/null
    responde || echo "AVISO: nginx tampoco responde con la red del host" >&2
  fi
else
  arrancar_python
  responde || echo "AVISO: el servidor de Python no responde" >&2
fi

echo "== Pruebas con curl ($MODO)"
FALLOS=0
# comprobar RUTA CODIGO [TEXTO_EN_CUERPO] [TIPO]
comprobar() {
  local ruta="$1" codigo="$2" texto="${3:-}" tipo="${4:-}" salida cuerpo estado ctype
  local destino=-; [ -n "$texto" ] || destino=/dev/null  # binarios (fuentes, png): solo código y tipo
  salida="$(curl -s --noproxy '*' --max-time 5 -o "$destino" -w $'\n%{http_code} %{content_type}' "$URL$ruta" || true)"
  cuerpo="${salida%$'\n'*}"; estado="${salida##*$'\n'}"; ctype="${estado#* }"; estado="${estado%% *}"
  local ok=1
  [ "$estado" = "$codigo" ] || ok=0
  [ -z "$texto" ] || grep -qF -- "$texto" <<<"$cuerpo" || ok=0
  [ -z "$tipo" ] || [[ "$ctype" == "$tipo"* ]] || ok=0
  if [ $ok = 1 ]; then echo "  OK    $ruta -> $estado $ctype"
  else echo "  FALLA $ruta -> $estado $ctype (esperado $codigo ${tipo:-} ${texto:+con «$texto»})"; FALLOS=$((FALLOS+1)); fi
}
comprobar /               200 'lang="es"'                     text/html
comprobar /               200 'id="caso"'                     text/html
comprobar /               200 'Gestión y cumplimiento'        text/html
comprobar /               200 'DBM Real Invest'               text/html
comprobar /404.html       200 'no existe o ha cambiado'       text/html
comprobar /no-existe      404 'no existe o ha cambiado'       text/html
comprobar /favicon.svg    200 '<svg'                          image/svg+xml
comprobar /fuentes/source-serif-4-latin-400-normal.woff2 200 '' font/woff2
comprobar /og.png         200 ''                              image/png
comprobar /apple-touch-icon.png 200 ''                        image/png
comprobar /una/carpeta/inexistente 404 'href="/fuentes/'      text/html
comprobar /flujo.svg      404 ''
comprobar /aviso-legal.html 200 'Aviso legal'                   text/html
comprobar /privacidad.html  200 'Política de privacidad'        text/html
comprobar /cookies.html     200 'Esta web no usa cookies'       text/html
# WEB-017: hoja de estilos con hash (la de la portada), iconos PNG/ICO, og por página legal y manifest
CSS="$(grep -o 'estilos\.[0-9a-f]*\.css' "$SITIO/index.html" | head -1)"
comprobar "/$CSS"            200 'prefers-color-scheme:dark'    text/css
comprobar /una/carpeta/inexistente 404 "href=\"/$CSS\""     text/html
comprobar /favicon-32.png   200 ''                              image/png
comprobar /favicon-16.png   200 ''                              image/png
comprobar /favicon.ico      200 ''                              image/
comprobar /og-privacidad.png 200 ''                             image/png
comprobar /site.webmanifest 200 'icono-512.png'                 application/manifest+json
comprobar /aviso-legal.html 200 'og-aviso-legal.png'            text/html

if [ "$FALLOS" -gt 0 ]; then
  echo "FALLA: $FALLOS prueba(s). Recuerda: docker/test/test-down.sh"; exit 1
fi
echo "OK: web servida en $URL ($MODO). Al terminar: docker/test/test-down.sh"
