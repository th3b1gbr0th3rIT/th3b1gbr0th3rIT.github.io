# Web corporativa de th3b1gbr0th3r IT

Web pública estática (GitHub Pages) de th3b1gbr0th3r IT: página principal y páginas legales, sin cookies, sin analítica y sin recursos externos (la tipografía se sirve desde la propia web). La generan scripts de Python 3 que solo usan la biblioteca estándar.

## Ficheros

- `construir_web.py`: genera `sitio/` (`index.html`, `aviso-legal.html`, `privacidad.html`, `cookies.html`, `404.html`, `estilos.<hash>.css`, `favicon.svg`, `favicon-32.png`, `favicon-16.png`, `favicon.ico`, `apple-touch-icon.png`, `icono-192/512.png`, `og.png` y una `og-<página>.png` por página legal, `site.webmanifest`, `fuentes/`, `sitemap.xml`, `robots.txt`, `.nojekyll`). JS e ilustraciones SVG van en línea (el JS con su hash en la CSP); el diagrama del flujo es HTML+CSS.
- `estilos.css`: la hoja de estilos de todas las páginas. Se publica como `estilos.<hash>.css` (el nombre cambia con el contenido: caché segura entre páginas y visitas). Colores solo con los tokens de `:root`: esquema claro por defecto y oscuro con `prefers-color-scheme` (solo en pantalla; al imprimir, siempre claro).
- `logotipo.py`: el logotipo «th3b1gbr0th3r IT» en trazos SVG (generados una vez desde Source Serif 4 Semibold), idéntico en todos los sistemas.
- `fuentes/`: la única tipografía, Source Serif 4 (400 normal y cursiva, subconjunto latino, WOFF2) y su `OFL.txt`.
- `recursos/`: imágenes para redes (`og.png` y `og-<página legal>.png`, 1200×630), iconos (`apple-touch-icon.png`, `icono-192/512.png`, `favicon-32/16.png`, `favicon.ico`). Se regeneran con `--imagenes`.
- `verificar.py`: revisa `sitio/` antes de publicar y termina con código 1 si algo falla: ficheros esperados (y que no se publiquen los retirados), `lang`, `<title>`, `description` y un solo `h1` por página, sin recursos externos (salvo el propio dominio en `canonical`/`og`), enlaces y recursos locales existentes (también rutas desde la raíz, como en la 404), presupuestos de peso (`index.html` ≤ 120 KB, hoja de estilos ≤ 48 KB, fuentes ≤ 60 KB, `og.png` ≤ 150 KB, total < 1 MB), la CSP sin `'unsafe-inline'` (ni atributos `style` ni `<style>`), una sola hoja `estilos.<hash>.css` con el hash correcto, `color-scheme` y los dos `theme-color`, los iconos, el contraste AA de los pares de texto en los dos esquemas y que no salga contenido interno. Lista como AVISO los marcadores `[PENDIENTE: …]`.
- `docker/test/`: test local con nginx.

## Construir y verificar

```bash
python3 construir_web.py             # genera sitio/
python3 verificar.py                 # comprueba sitio/
python3 construir_web.py --capturas  # además, capturas en capturas/ (escritorio 1440, tableta 1024 y 820, móvil 390 y 360, menú, CTA, flujo, legales, 404, og y apple-touch-icon, y las variantes «-oscuro» de portada, menú, privacidad y 404); necesita google-chrome, Pillow opcional
python3 construir_web.py --imagenes  # regenera las imágenes de recursos/ (google-chrome y Pillow)
```

## Probar en local

```bash
docker/test/test-up.sh               # construye, verifica y sirve en http://127.0.0.1:8088 (nginx:1.27-alpine)
docker/test/test-up.sh --sin-docker  # alternativa con el servidor de Python
docker/test/test-down.sh             # SIEMPRE al terminar
```

`test-up.sh` sirve como GitHub Pages (gzip y `max-age=600`) y comprueba con curl `/`, la hoja de estilos, los iconos PNG/ICO, el manifest, `/404.html`, rutas inexistentes (404 con `404.html` y rutas desde la raíz), `favicon.svg`, la fuente, `og.png`, `apple-touch-icon.png`, que `flujo.svg` ya no se publica y las tres páginas legales. Solo escucha en `127.0.0.1`.

## Publicación

Se publica **solo** con el pipeline `.github/workflows/pages.yml`, que construye, ejecuta `verificar.py` y despliega en GitHub Pages. Nunca se sube nada a mano.
