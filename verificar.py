#!/usr/bin/env python3
"""Verifica el sitio generado en sitio/ antes de publicarlo (lo ejecuta el pipeline tras construir).

Comprueba: ficheros esperados, cabecera de index.html (lang, title, description), que no hay recursos
externos, que los enlaces internos #id existen, el tamaño total y que no sale contenido interno.
Solo biblioteca estándar. Uso: python3 verificar.py [carpeta]   (por defecto sitio/)
Sale con código 1 si algo falla.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ESPERADOS = ["index.html", "404.html", "favicon.svg", "flujo.svg", "flujo-vertical.svg", ".nojekyll", "robots.txt"]
TAMANO_MAX = 1024 * 1024  # 1 MB
CORREO_PUBLICO = "jordi.gonzalez.roig@gmail.com"

# Contenido interno que nunca puede salir en lo público (regla de la empresa: «lo interno no sale»).
# Se busca como palabra completa (sin distinguir mayúsculas) para no dar falsos positivos con palabras
# que las contienen: «aprecio» no es «precio», «ssh» no salta dentro de otra palabra.
# «precio» admite el plural («precios»); «bares» se busca solo como palabra suelta.
PROHIBIDO = {
    "símbolo €": re.compile(r"€"),
    "DBM": re.compile(r"\bdbm\b", re.I),
    "dbmrealinvest": re.compile(r"dbmrealinvest", re.I),
    "VPS": re.compile(r"\bvps\b", re.I),
    "bares": re.compile(r"\bbares\b", re.I),
    "precio": re.compile(r"\bprecios?\b", re.I),
    "licencia": re.compile(r"\blicencias?\b", re.I),
    "GHCR": re.compile(r"\bghcr\b", re.I),
    "ssh": re.compile(r"\bssh\b", re.I),
}
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Recursos externos: src=, href=, srcset=, action=, url( y @import hacia http(s):// o //.
EXTERNO = re.compile(
    r"""(?:\b(?:src|href|srcset|action|poster|data)\s*=\s*["']?\s*|url\(\s*["']?\s*|@import\s+["']?\s*)(?:https?:)?//""",
    re.I,
)


class Lector(HTMLParser):
    """Reúne el texto visible, los valores de los atributos, los id y los enlaces #id de un HTML/SVG."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.textos = []
        self.ids = set()
        self.anclas = []
        self.lang = None
        self.titulo = ""
        self.description = None
        self._en_title = False

    def handle_starttag(self, tag, attrs):
        for nombre, valor in attrs:
            if valor is None:
                continue
            if nombre != "xmlns" and not nombre.startswith("xmlns:"):
                self.textos.append(valor)
            if nombre == "id":
                self.ids.add(valor)
            if nombre in ("href", "xlink:href") and valor.startswith("#"):
                self.anclas.append(valor[1:])
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._en_title = True
        if tag == "meta" and (a.get("name") or "").lower() == "description":
            self.description = a.get("content") or ""

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "title":
            self._en_title = False

    def handle_data(self, data):
        self.textos.append(data)
        if self._en_title:
            self.titulo += data

    def handle_comment(self, data):
        self.textos.append(data)


def verificar(sitio: Path) -> list:
    errores = []
    if not sitio.is_dir():
        return [f"no existe la carpeta {sitio} (¿has ejecutado construir_web.py?)"]

    for nombre in ESPERADOS:
        if not (sitio / nombre).is_file():
            errores.append(f"falta el fichero esperado: {nombre}")

    ficheros = sorted(p for p in sitio.rglob("*") if p.is_file())
    total = sum(p.stat().st_size for p in ficheros)
    if total >= TAMANO_MAX:
        errores.append(f"el sitio ocupa {total} bytes (máximo {TAMANO_MAX})")

    for p in ficheros:
        rel = p.relative_to(sitio)
        try:
            crudo = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binario (imágenes): sin texto que revisar
        for m in EXTERNO.finditer(crudo):
            linea = crudo.count("\n", 0, m.start()) + 1
            errores.append(f"{rel}:{linea}: recurso externo: {crudo[m.start():m.end() + 40].splitlines()[0]}")

        if p.suffix in (".html", ".svg"):
            lector = Lector()
            lector.feed(crudo)
            lector.close()
            texto = "\n".join(lector.textos)
            for ancla in lector.anclas:
                # href="#" (la marca) vuelve al inicio de la página: es válido sin id.
                if ancla and ancla not in lector.ids:
                    errores.append(f"{rel}: el enlace #{ancla} no tiene su id")
            if rel.as_posix() == "index.html":
                if lector.lang != "es":
                    errores.append(f"index.html: lang={lector.lang!r}, se esperaba 'es'")
                if not lector.titulo.strip():
                    errores.append("index.html: falta <title> o está vacío")
                if not (lector.description or "").strip():
                    errores.append("index.html: falta <meta name=\"description\"> o está vacía")
        else:
            texto = crudo

        for etiqueta, patron in PROHIBIDO.items():
            for m in patron.finditer(texto):
                contexto = texto[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
                errores.append(f"{rel}: contenido interno prohibido ({etiqueta}): «…{contexto}…»")
        for m in CORREO.finditer(texto):
            if m.group(0).lower() != CORREO_PUBLICO:
                errores.append(f"{rel}: correo no permitido: {m.group(0)}")

    print(f"Revisados {len(ficheros)} ficheros, {total} bytes en {sitio}")
    return errores


def main():
    sitio = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "sitio"
    errores = verificar(sitio)
    if errores:
        print(f"FALLA: {len(errores)} problema(s)")
        for e in errores:
            print(f"  - {e}")
        sys.exit(1)
    print("OK: el sitio cumple todas las comprobaciones")


if __name__ == "__main__":
    main()
