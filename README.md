# Web corporativa de th3b1gbr0th3r IT

Web pública estática (GitHub Pages) de th3b1gbr0th3r IT: página principal y páginas legales, sin cookies, sin analítica y sin recursos externos (la tipografía se sirve desde la propia web). La generan scripts de Python 3 que solo usan la biblioteca estándar.

## Ficheros

- `construir_web.py`: genera `sitio/` (`index.html`, `aviso-legal.html`, `privacidad.html`, `cookies.html`, `404.html`, `favicon.svg`, `apple-touch-icon.png`, `og.png`, `fuentes/`, `sitemap.xml`, `robots.txt`, `.nojekyll`). HTML, CSS, JS e ilustraciones SVG van inline; el diagrama del flujo es HTML+CSS.
- `logotipo.py`: el logotipo «th3b1gbr0th3r IT» en trazos SVG (generados una vez desde Source Serif 4 Semibold), idéntico en todos los sistemas.
- `fuentes/`: la única tipografía, Source Serif 4 (400 normal y cursiva, subconjunto latino, WOFF2) y su `OFL.txt`.
- `recursos/`: `og.png` (1200×630, para redes) y `apple-touch-icon.png` (180×180). Se regeneran con `--imagenes`.
- `verificar.py`: revisa `sitio/` antes de publicar y termina con código 1 si algo falla: ficheros esperados (y que no se publiquen los retirados), `lang`, `<title>`, `description` y un solo `h1` por página, sin recursos externos (salvo el propio dominio en `canonical`/`og`), enlaces y recursos locales existentes (también rutas desde la raíz, como en la 404), presupuestos de peso (`index.html` ≤ 120 KB, fuentes ≤ 60 KB, `og.png` ≤ 150 KB, total < 1 MB) y que no salga contenido interno. Lista como AVISO los marcadores `[PENDIENTE: …]`.
- `docker/test/`: test local con nginx.

## Construir y verificar

```bash
python3 construir_web.py             # genera sitio/
python3 verificar.py                 # comprueba sitio/
python3 construir_web.py --capturas  # además, capturas en capturas/ (escritorio 1440, tableta 1024 y 820, móvil 390 y 360, menú, CTA, flujo, legales, 404, og); necesita google-chrome, Pillow opcional
python3 construir_web.py --imagenes  # regenera recursos/og.png y recursos/apple-touch-icon.png (google-chrome y Pillow)
```

## Probar en local

```bash
docker/test/test-up.sh               # construye, verifica y sirve en http://127.0.0.1:8088 (nginx:1.27-alpine)
docker/test/test-up.sh --sin-docker  # alternativa con el servidor de Python
docker/test/test-down.sh             # SIEMPRE al terminar
```

`test-up.sh` comprueba con curl `/`, `/404.html`, rutas inexistentes (404 con `404.html` y rutas desde la raíz), `favicon.svg`, la fuente, `og.png`, `apple-touch-icon.png`, que `flujo.svg` ya no se publica y las tres páginas legales. Solo escucha en `127.0.0.1`.

## Publicación

Se publica **solo** con el pipeline `.github/workflows/pages.yml`, que construye, ejecuta `verificar.py` y despliega en GitHub Pages. Nunca se sube nada a mano.
