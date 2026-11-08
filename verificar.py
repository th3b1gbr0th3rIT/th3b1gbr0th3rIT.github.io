#!/usr/bin/env python3
"""Verifica el sitio generado en sitio/ antes de publicarlo (lo ejecuta el pipeline tras construir).

Comprueba: ficheros esperados, cabecera de cada página (lang, title, description, un solo h1), que no hay
recursos externos (salvo el propio dominio en canonical/og y los enlaces de ENLACES_PERMITIDOS), que los enlaces internos (#id, x.html, x.html#id y
rutas desde la raíz /x) y los recursos locales (fuentes, iconos) existen, los presupuestos de peso y que no sale
contenido interno. Avisa (sin fallar) de los marcadores [PENDIENTE: …] que queden en las páginas.
Solo biblioteca estándar. Uso: python3 verificar.py [carpeta]   (por defecto sitio/)
Sale con código 1 si algo falla.
"""
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGINAS_LEGALES = ["aviso-legal.html", "privacidad.html", "cookies.html"]
FUENTES = ["fuentes/source-serif-4-latin-400-normal.woff2", "fuentes/source-serif-4-latin-400-italic.woff2"]
ESPERADOS = ["index.html", "404.html", *PAGINAS_LEGALES, "favicon.svg", "favicon-32.png", "favicon-16.png", "favicon.ico",
             "apple-touch-icon.png", "og.png", *(f"og-{n.removesuffix('.html')}.png" for n in PAGINAS_LEGALES), *FUENTES, "fuentes/OFL.txt",
             ".nojekyll", "robots.txt", "sitemap.xml", "site.webmanifest", "icono-192.png", "icono-512.png"]
NO_PUBLICAR = ["flujo.svg", "flujo-vertical.svg"]  # el diagrama es HTML+CSS desde la ronda 2 de WEB-006
TAMANO_MAX = 1024 * 1024  # 1 MB en total
# Pares texto/fondo que deben cumplir WCAG AA en los DOS esquemas (claro y oscuro), con los tokens de :root de la hoja
# de estilos (o colores literales): (texto, fondo, mínimo). 4,5:1 para texto; 3:1 para el foco y los elementos gráficos.
PARES_CONTRASTE = [
    # Texto sobre los fondos de página, secciones alternas, tarjetas y pie
    *[(t, f, 4.5) for t in ("tinta", "texto", "apoyo", "acento")
      for f in ("fondo", "fondo-alt", "fondo-pie", "superficie", "superficie-alt")
      if (t, f) != ("acento", "fondo-pie")],  # el tostado de marca no se usa sobre el gris del pie (4,46:1)
    ("acento-suave", "superficie-alt", 4.5), ("acento-suave", "fondo-pie", 4.5), ("acento-suave", "fondo-alt", 4.5),
    ("etq-texto", "etq-fondo", 4.5), ("btn-texto", "btn-fondo", 4.5), ("btn-texto", "btn-hover", 4.5),
    ("apoyo", "etq-fondo", 4.5),
    # Estados «hecho» (mini tarjeta del hero y ticket del caso): texto y marca de verificación (WEB-019)
    ("hecho-texto", "hecho-fondo", 4.5), ("hecho-marca", "hecho-fondo", 3.0),
    # Foco (anillo exterior) y trazos decorativos
    ("foco", "fondo", 3.0), ("foco", "fondo-alt", 3.0), ("foco", "superficie", 3.0), ("ambar", "fondo", 3.0), ("ambar", "superficie", 3.0),
    # Secciones oscuras (hero, contacto, tarjeta de llamada): oscuras en los dos esquemas
    *[(t, "oscuro-fondo", 4.5) for t in ("crema", "ambar2", "oscuro-texto", "oscuro-claro", "blanco")],
    ("negro", "ambar2", 4.5), ("negro", "#fbbf24", 4.5), ("ambar", "oscuro-fondo", 3.0), ("crema", "oscuro-fondo", 3.0),
]
ESQUEMA_OSCURO = re.compile(r"@media screen and \(prefers-color-scheme:dark\)\s*\{\s*:root\{([^}]*)\}")
CSP_REQUERIDA = ("default-src 'none'", "base-uri 'none'", "form-action 'none'")


def _luz(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def tokens(css):
    """Tokens de color del esquema claro (primer :root) y del oscuro (claro + lo que redefine la media query)."""
    base = re.search(r":root\{([^}]*)\}", css)
    claro = dict(re.findall(r"--([a-z0-9-]+):(#[0-9a-fA-F]{3,6})\b", base.group(1) if base else ""))
    m = ESQUEMA_OSCURO.search(css)
    oscuro = {**claro, **dict(re.findall(r"--([a-z0-9-]+):(#[0-9a-fA-F]{3,6})\b", m.group(1)))} if m else None
    return claro, oscuro


def contraste(a, b):
    la, lb = sorted((_luz(a), _luz(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PRESUPUESTO = {  # bytes por fichero o grupo
    "index.html": 120 * 1024,
    "estilos (css)": 48 * 1024,
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
        self.meta_http = {}
        self.meta_name = {}
        self.landmarks = {}
        self.navs_sin_etiqueta = 0
        self.aria_current = 0
        self.manifest = False
        self.estilos = []  # hojas de estilo enlazadas
        self.style_attr = 0
        self.theme_color = []

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
        if tag == "meta":
            if a.get("http-equiv"):
                self.meta_http[a["http-equiv"].lower()] = a.get("content") or ""
            if a.get("name"):
                self.meta_name[a["name"].lower()] = a.get("content") or ""
        if tag == "link" and a.get("rel") == "manifest":
            self.manifest = True
        if tag == "link" and a.get("rel") == "stylesheet":
            self.estilos.append((a.get("href") or "").lstrip("/"))
        if "style" in a:
            self.style_attr += 1
        if tag == "meta" and (a.get("name") or "").lower() == "theme-color":
            self.theme_color.append(a.get("media") or "")
        if tag in ("header", "nav", "main", "footer"):
            self.landmarks[tag] = self.landmarks.get(tag, 0) + 1
            if tag == "nav" and not a.get("aria-label") and not a.get("aria-labelledby"):
                self.navs_sin_etiqueta += 1
        if a.get("aria-current"):
            self.aria_current += 1
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
             "og.png": (sitio / "og.png").stat().st_size if (sitio / "og.png").is_file() else 0, "estilos (css)": 0}

    # Hoja de estilos: una sola, con el hash de su contenido en el nombre (caché segura) y AA en los dos esquemas.
    hojas = sorted(sitio.glob("estilos.*.css"))
    hoja_css = hojas[0].name if len(hojas) == 1 else None
    if len(hojas) != 1:
        errores.append(f"debe haber exactamente una hoja estilos.<hash>.css (hay {len(hojas)})")
    else:
        css = hojas[0].read_text(encoding="utf-8")
        if hoja_css != f"estilos.{hashlib.sha256(css.encode('utf-8')).hexdigest()[:10]}.css":
            errores.append(f"{hoja_css}: el nombre no coincide con el hash de su contenido")
        claro, oscuro = tokens(css)
        if oscuro is None:
            errores.append(f"{hoja_css}: falta el esquema oscuro (@media screen and (prefers-color-scheme:dark) {{:root{{…}}}})")
        if "color-scheme:light dark" not in css:
            errores.append(f"{hoja_css}: falta color-scheme:light dark en :root")
        for esquema, var in (("claro", claro), ("oscuro", oscuro or {})):
            for t, f, minimo in PARES_CONTRASTE:
                ct, cf = var.get(t, t), var.get(f, f)
                if not (ct.startswith("#") and cf.startswith("#")):
                    errores.append(f"contraste ({esquema}): no se resuelve {t} / {f}")
                elif contraste(ct, cf) < minimo:
                    errores.append(f"contraste ({esquema}) {t} {ct} sobre {f} {cf}: {contraste(ct, cf):.2f}:1 (mínimo {minimo}:1)")
        pesos["estilos (css)"] = hojas[0].stat().st_size

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
                csp = lector.meta_http.get("content-security-policy", "")
                if not csp or not all(x in csp for x in CSP_REQUERIDA) or "unsafe-eval" in csp or re.search(r"script-src[^;]*unsafe-inline", csp):
                    errores.append(f"{rel}: falta la CSP por meta o es demasiado laxa")
                if not lector.meta_http.get("content-security-policy", "").strip() or not lector.meta_name.get("referrer"):
                    errores.append(f"{rel}: falta <meta name=\"referrer\"> o la CSP")
                if not lector.manifest:
                    errores.append(f"{rel}: falta <link rel=\"manifest\">")
                for lm in ("header", "main", "footer"):
                    if lector.landmarks.get(lm) != 1:
                        errores.append(f"{rel}: debe tener exactamente un <{lm}> (tiene {lector.landmarks.get(lm, 0)})")
                if not lector.landmarks.get("nav") or lector.navs_sin_etiqueta:
                    errores.append(f"{rel}: los <nav> deben existir y llevar aria-label")
                if rel.name in PAGINAS_LEGALES and lector.aria_current != 1:
                    errores.append(f"{rel}: debe marcar su enlace del pie con aria-current=\"page\" (tiene {lector.aria_current})")
                if lector.estilos != [hoja_css]:
                    errores.append(f"{rel}: debe enlazar solo la hoja {hoja_css} (enlaza {lector.estilos})")
                if lector.style_attr or "<style" in crudo:
                    errores.append(f"{rel}: estilos en línea (atributo style o <style>): la CSP solo admite la hoja propia")
                if re.search(r"unsafe-inline", csp) or not re.search(r"style-src 'self'(;|$)", csp):
                    errores.append(f"{rel}: la CSP debe tener style-src 'self' y ningún 'unsafe-inline'")
                if lector.meta_name.get("color-scheme") != "light dark":
                    errores.append(f"{rel}: falta <meta name=\"color-scheme\" content=\"light dark\">")
                if sorted(lector.theme_color) != ["(prefers-color-scheme: dark)", "(prefers-color-scheme: light)"]:
                    errores.append(f"{rel}: faltan los dos theme-color (claro y oscuro): {lector.theme_color}")
                if not {"favicon.svg", "favicon-32.png", "favicon-16.png"} <= {r.rsplit("/", 1)[-1] for r in lector.recursos}:
                    errores.append(f"{rel}: faltan los iconos (favicon.svg y PNG de 32 y 16)")
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

    errores += comprobar_caso(sitio)
    for clave, maximo in PRESUPUESTO.items():
        if pesos[clave] > maximo:
            errores.append(f"{clave} pesa {pesos[clave]} bytes (presupuesto {maximo})")
    print(f"Revisados {len(ficheros)} ficheros, {total} bytes en {sitio}")
    print("Pesos: " + ", ".join(f"{k} {v} B (máx. {PRESUPUESTO[k]})" for k, v in pesos.items()))
    for a in avisos:
        print(f"AVISO pendiente: {a}")
    return errores


def comprobar_caso(sitio: Path) -> list:
    """WEB-020: el caso se cuenta una vez (ticket de cinco estados «hecho» y tarjeta del hero) y la página tiene seis secciones."""
    errores = []
    index = sitio / "index.html"
    if not index.is_file():
        return errores
    crudo = index.read_text(encoding="utf-8")
    m = re.search(r'<article class="ticket[^"]*".*?</article>', crudo, re.S)
    if not m:
        return ["index.html: falta el ticket del caso"]
    ticket = m.group(0)
    if len(re.findall(r'<li class="hecho">', ticket)) != 5 or '<li class="actual"' in ticket or "<li>" in ticket:
        errores.append("index.html: el ticket del caso debe tener cinco estados y todos «hecho»")
    if not re.search(r'<div class="ticket-pie">.*?<b>Validado</b>', ticket, re.S):
        errores.append("index.html: el ticket del caso debe cerrar con «Validado»")
    if "Pedido por el cliente" not in ticket:
        errores.append("index.html: el caso debe empezar por «Pedido por el cliente» (DW-020-J2)")
    # Sin restos del caso antiguo (seis tarjetas, dibujo, lista de mejoras)
    for resto in ('class="caso-flujo"', 'class="caso-dibujo"', "Otras mejoras entregadas", "deploy ✓", "backup ✓"):
        if resto in crudo:
            errores.append(f"index.html: queda un resto del caso antiguo: {resto}")
    # La mini tarjeta del caso se quitó del hero (WEB-022): el caso vive solo en su sección
    if 'class="mini' in crudo or "Hoja de cambios · DBM" in crudo.split('id="caso"')[0]:
        errores.append("index.html: el hero no debe llevar la mini tarjeta del caso (WEB-022)")
    if 'class="pipeline"' in crudo:
        errores.append("index.html: el chip del proceso del hero se quitó (DW-020-J3)")
    # Estructura de ocho bloques: sin «Por qué ahora», «Compromisos» ni «Cómo empezar» como secciones (DW-020-J1, P31, P32)
    secciones = re.findall(r'<section[^>]*\bid="([^"]+)"', crudo)
    if secciones != ["servicios", "caso", "por-dentro", "equipo", "preguntas", "contacto"]:
        errores.append(f"index.html: secciones inesperadas: {secciones}")
    # Fundador con su nombre completo en Equipo y en el JSON-LD (WEB-020d)
    if '<span class="rol">CTO</span>' not in crudo or "<h3>Jordi Gonzalez Roig</h3>" not in crudo:
        errores.append("index.html: la tarjeta del CTO debe decir «Jordi Gonzalez Roig» y «CTO»")
    # El nombre corto «Jordi» no aparece en la portada: solo «Jordi Gonzalez Roig» (WEB-022)
    if re.search(r"Jordi(?! Gonzalez Roig)", re.sub(r"jordi\.gonzalez\.roig@gmail\.com", "", crudo)):
        errores.append("index.html: queda «Jordi» suelto; debe decir «el CTO» (WEB-022)")
    if '"founder": {"@type": "Person", "name": "Jordi Gonzalez Roig", "jobTitle": "CTO"' not in crudo:
        errores.append("index.html: el JSON-LD de la organización debe llevar founder «Jordi Gonzalez Roig»")
    # Ningún enlace ni id a las secciones retiradas, en ninguna página ni en el sitemap
    for f in sorted(sitio.iterdir()):
        if f.suffix in (".html", ".xml", ".webmanifest", ".txt", ".json"):
            texto = f.read_text(encoding="utf-8")
            if re.search(r'#(?:ahora|compromisos|empezar)\b|\bid="(?:ahora|compromisos|empezar)"', texto):
                errores.append(f"{f.name}: queda una referencia a #ahora, #compromisos o #empezar")
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
