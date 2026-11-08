# Web corporativa de th3b1gbr0th3r IT

Web pública estática (GitHub Pages) de th3b1gbr0th3r IT: una sola página, sin cookies, sin analítica y sin recursos externos. La generan scripts de Python 3 que solo usan la biblioteca estándar.

## Ficheros

- `construir_web.py`: genera `sitio/` (`index.html`, `404.html`, `favicon.svg`, `flujo.svg`, `flujo-vertical.svg`, `.nojekyll`, `robots.txt`).
- `diagrama_flujo.py`: dibuja el diagrama del flujo de trabajo, con un carril propio por empresa.
- `verificar.py`: revisa `sitio/` antes de publicar y termina con código 1 si algo falla. Comprueba los ficheros esperados, `lang`, `<title>` y `description`, que no haya recursos externos, que cada enlace `#id` tenga su `id`, que el tamaño sea menor de 1 MB y que no salga contenido interno.
- `docker/test/`: test local con nginx.

## Construir y verificar

```bash
python3 construir_web.py            # genera sitio/
python3 verificar.py                # comprueba sitio/
python3 construir_web.py --capturas # además, capturas en capturas/ (necesita google-chrome)
```

## Probar en local

```bash
docker/test/test-up.sh               # construye, verifica y sirve en http://127.0.0.1:8088 (nginx:1.27-alpine)
docker/test/test-up.sh --sin-docker  # alternativa con el servidor de Python
docker/test/test-down.sh             # SIEMPRE al terminar
```

`test-up.sh` comprueba con curl `/`, `/404.html`, una ruta inexistente (404 con `404.html`), `/flujo.svg` y `/favicon.svg`. Solo escucha en `127.0.0.1`.

## Publicación

Se publica **solo** con el pipeline `.github/workflows/pages.yml`, que construye, ejecuta `verificar.py` y despliega en GitHub Pages. Nunca se sube nada a mano.
