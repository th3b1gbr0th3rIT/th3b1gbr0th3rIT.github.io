#!/usr/bin/env python3
"""Verifica el sitio generado en sitio/ antes de publicarlo (lo ejecuta el pipeline tras construir).

Comprueba: ficheros esperados, cabecera de cada página (lang, title, description, un solo h1), que no hay
recursos externos (salvo el propio dominio en canonical/og y los enlaces de ENLACES_PERMITIDOS), que los enlaces internos (#id, x.html, x.html#id y
rutas desde la raíz /x) y los recursos locales (fuentes, iconos) existen, los presupuestos de peso y que no sale
contenido interno. Avisa (sin fallar) de los marcadores [PENDIENTE: …] que queden en las páginas.
Solo biblioteca estándar. Uso: python3 verificar.py [carpeta]   (por defecto sitio/)
Sale con código 1 si algo falla.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGINAS_LEGALES = ["aviso-legal.html", "privacidad.html", "cookies.html"]
FUENTES = ["fuentes/source-serif-4-latin-400-normal.woff2", "fuentes/source-serif-4-latin-400-italic.woff2"]
ESPERADOS = ["index.html", "404.html", *PAGINAS_LEGALES, "favicon.svg", "apple-touch-icon.png", "og.png", *FUENTES, "fuentes/OFL.txt",
             ".nojekyll", "robots.txt", "sitemap.xml"]
NO_PUBLICAR = ["flujo.svg", "flujo-vertical.svg"]  # el diagrama es HTML+CSS desde la ronda 2 de WEB-006
TAMANO_MAX = 1024 * 1024  # 1 MB en total
PRESUPUESTO = {  # bytes por fichero o grupo
    "index.html": 120 * 1024,
    "fuentes (woff2)": 60 * 1024,
    "og.png": 150 * 1024,
}
DOMINIO_PROPIO = "th3b1gbr0th3rit.github.io"
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
    "JuanJo": re.compile(r"\bjuanjo\b", re.I),  # el CTO de DBM no se nombra (Jordi, 2026-11-08, WEB-013)
    "manada": re.compile(r"\bmanada\b", re.I),  # retirada de toda la marca (cto, 2026-11-08)
    # Web sin gatos (Jordi, 2026-11-08, WEB-011): «gato», «gata», «gatos», «gatito»… también dentro de nombres
    # como «gato-404» o «hero-gatos». Palabra completa para no saltar con «navigator» del JS.
    "gato": re.compile(r"\bgat(?:[oa]s?|it[oa]s?)\b", re.I),
}
# Excepciones por página: el aviso legal cita la licencia libre de la tipografía (texto de cto, 2026-11-08) y la
# portada nombra a DBM Real Invest como caso de éxito, con permiso del cliente (Jordi, 2026-11-08, WEB-012).
# Ningún otro fichero (404, legales) puede nombrar a DBM.
PERMITIDO_EN = {"aviso-legal.html": {"licencia"}, "index.html": {"DBM", "dbmrealinvest"}}
# Lista blanca de enlaces de navegación externos (solo <a href> exacto y con rel="noopener noreferrer", sin Referer).
# src, url( e @import externos siguen prohibidos sin excepción.
ENLACES_PERMITIDOS = {"https://dbmrealinvest.com/"}
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Recursos externos: src=, href=, srcset=, action=, url( y @import hacia http(s):// o //.
EXTERNO = re.compile(
    r"""(?:\b(?:src|href|srcset|action|poster|data)\s*=\s*["']?\s*|url\(\s*["']?\s*|@import\s+["']?\s*)(?:https?:)?//(?!th3b1gbr0th3rit\.github\.io/)""",
    re.I,
)


avisos = []  # marcadores [PENDIENTE: …]: no bloquean, pero se listan para Jordi


class Lector(HTMLParser):
    """Reúne el texto visible, los valores de los atributos, los id y los enlaces #id de un HTML/SVG."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.textos = []
        self.ids = set()
        self.anclas = []
        self.enlaces = []  # href a otros ficheros del sitio (relativos o desde la raíz)
        self.recursos = []  # link href / script src / img src locales
        self.h1 = 0
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
            elif nombre == "href" and tag == "a" and not re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", valor, re.I):
                self.enlaces.append(valor)
        a = dict(attrs)
        local = lambda v: v and not re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", v, re.I)
        if tag == "link" and local(a.get("href")):
            self.recursos.append(a["href"])
        if tag in ("script", "img", "source") and local(a.get("src")):
            self.recursos.append(a["src"])
        if tag == "h1":
            self.h1 += 1
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
    avisos.clear()
    if not sitio.is_dir():
        return [f"no existe la carpeta {sitio} (¿has ejecutado construir_web.py?)"]

    for nombre in ESPERADOS:
        if not (sitio / nombre).is_file():
            errores.append(f"falta el fichero esperado: {nombre}")

    for nombre in NO_PUBLICAR:
        if (sitio / nombre).exists():
            errores.append(f"{nombre} ya no se publica (la página no lo usa)")

    ficheros = sorted(p for p in sitio.rglob("*") if p.is_file())
    total = sum(p.stat().st_size for p in ficheros)
    if total >= TAMANO_MAX:
        errores.append(f"el sitio ocupa {total} bytes (máximo {TAMANO_MAX})")
    pesos = {"index.html": (sitio / "index.html").stat().st_size if (sitio / "index.html").is_file() else 0,
             "fuentes (woff2)": sum(p.stat().st_size for p in sitio.rglob("*.woff2")),
             "og.png": (sitio / "og.png").stat().st_size if (sitio / "og.png").is_file() else 0}
    for clave, maximo in PRESUPUESTO.items():
        if pesos[clave] > maximo:
            errores.append(f"{clave} pesa {pesos[clave]} bytes (presupuesto {maximo})")

    lectores = {}
    for p in ficheros:
        rel = p.relative_to(sitio)
        try:
            crudo = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binario (imágenes): sin texto que revisar
        for m in EXTERNO.finditer(crudo):
            linea = crudo.count("\n", 0, m.start()) + 1
            etiqueta_ini = crudo.rfind("<", 0, m.start())
            etiqueta = crudo[etiqueta_ini:crudo.find(">", m.end())] if etiqueta_ini >= 0 else ""
            if re.match(r"href\b", m.group(0), re.I) and re.match(r"<a\b", etiqueta, re.I):
                destino = re.search(r"""\bhref\s*=\s*["']([^"']*)["']""", etiqueta, re.I)
                if destino and destino.group(1) in ENLACES_PERMITIDOS:
                    rel_attr = re.search(r"""\brel\s*=\s*["']([^"']*)["']""", etiqueta, re.I)
                    palabras = set((rel_attr.group(1) if rel_attr else "").lower().split())
                    if not {"noopener", "noreferrer"} <= palabras:
                        errores.append(f"{rel}:{linea}: el enlace permitido {destino.group(1)} necesita rel=\"noopener noreferrer\"")
                    continue
            errores.append(f"{rel}:{linea}: recurso externo: {crudo[m.start():m.end() + 40].splitlines()[0]}")

        if p.suffix in (".html", ".svg"):
            lector = Lector()
            lector.feed(crudo)
            lector.close()
            texto = "\n".join(lector.textos)
            lectores[rel.as_posix()] = lector
            for ancla in lector.anclas:
                # href="#" (la marca) vuelve al inicio de la página: es válido sin id.
                if ancla and ancla not in lector.ids:
                    errores.append(f"{rel}: el enlace #{ancla} no tiene su id")
            if p.suffix == ".html":
                if lector.lang != "es":
                    errores.append(f"{rel}: lang={lector.lang!r}, se esperaba 'es'")
                if not lector.titulo.strip():
                    errores.append(f"{rel}: falta <title> o está vacío")
                if not (lector.description or "").strip():
                    errores.append(f"{rel}: falta <meta name=\"description\"> o está vacía")
                if lector.h1 != 1:
                    errores.append(f"{rel}: tiene {lector.h1} <h1>, debe tener exactamente uno")
                for m in re.finditer(r"\[PENDIENTE:[^\]]*\]", texto):
                    avisos.append(f"{rel}: {m.group(0)}")
        else:
            texto = crudo

        for etiqueta, patron in PROHIBIDO.items():
            if etiqueta in PERMITIDO_EN.get(rel.as_posix(), set()):
                continue
            for m in patron.finditer(texto):
                contexto = texto[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
                errores.append(f"{rel}: contenido interno prohibido ({etiqueta}): «…{contexto}…»")
        for m in CORREO.finditer(texto):
            if m.group(0).lower() != CORREO_PUBLICO:
                errores.append(f"{rel}: correo no permitido: {m.group(0)}")

    # Enlaces entre páginas: el fichero existe y, si llevan #id, el id existe en la página destino.
    for origen, lector in lectores.items():
        base = (sitio / origen).parent
        for href in lector.enlaces + lector.recursos:
            ruta, _, ancla = href.partition("#")
            ruta = ruta.split("?", 1)[0]
            if ruta.startswith("/"):  # desde la raíz del dominio (404.html)
                destino = (sitio / ruta.lstrip("/")).resolve()
            else:
                destino = (base / ruta).resolve() if ruta else (sitio / origen).resolve()
            if destino.is_dir():
                destino = destino / "index.html"
            try:
                destino_rel = destino.relative_to(sitio.resolve()).as_posix()
            except ValueError:
                errores.append(f"{origen}: el enlace {href} sale del sitio")
                continue
            if not destino.is_file():
                errores.append(f"{origen}: el enlace {href} apunta a un fichero que no existe")
            elif ancla and destino_rel in lectores and ancla not in lectores[destino_rel].ids:
                errores.append(f"{origen}: el enlace {href} apunta a #{ancla}, que no existe en {destino_rel}")

    print(f"Revisados {len(ficheros)} ficheros, {total} bytes en {sitio}")
    print("Pesos: " + ", ".join(f"{k} {v} B (máx. {PRESUPUESTO[k]})" for k, v in pesos.items()))
    for a in avisos:
        print(f"AVISO pendiente: {a}")
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
