#!/usr/bin/env python3
"""Genera la web pública estática de th3b1gbr0th3r IT en sitio/ (GitHub Pages).

Estilo corporativo sobrio (WEB-006): un mensaje por bloque, servicios en tarjetas, diagrama del flujo en
HTML+CSS, caso de éxito real de DBM Real Invest (WEB-012, con permiso del cliente) y pie legal completo con sus páginas.
Sin cifras ni precios; el único cliente nombrado es DBM (CASO_CON_NOMBRE). Sin recursos externos ni cookies: la única tipografía
(Source Serif 4, OFL) se sirve desde la propia web, en fuentes/.
Uso: python3 construir_web.py [--capturas] [--imagenes]
  --capturas  capturas de revisión en capturas/ (necesita google-chrome; Pillow opcional para recortar)
  --imagenes  regenera las imágenes de recursos/ (og, iconos y favicons; necesita google-chrome y Pillow)
La construcción solo usa la biblioteca estándar de Python 3 (funciona tal cual en un runner de GitHub).
"""
import base64
import datetime
import hashlib
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logotipo  # noqa: E402

HERE = Path(__file__).resolve().parent
SITIO = HERE / "sitio"
CAPTURAS = HERE / "capturas"
FUENTES = HERE / "fuentes"
RECURSOS = HERE / "recursos"
URL_BASE = "https://th3b1gbr0th3rit.github.io/"
MAIL = "jordi.gonzalez.roig@gmail.com"
MAILTO = f"mailto:{MAIL}?subject=Quiero%20hablar%20de%20mi%20negocio"
MAILTO_DERECHOS = f"mailto:{MAIL}?subject=Ejercicio%20de%20derechos%20de%20protecci%C3%B3n%20de%20datos"
HOY = datetime.date.today()
ANIO = HOY.year
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ACTUALIZADO = f"{HOY.day} de {MESES[HOY.month - 1]} de {HOY.year}"
FUENTE_NORMAL = "source-serif-4-latin-400-normal.woff2"
FUENTE_CURSIVA = "source-serif-4-latin-400-italic.woff2"

# ── El equipo: Jordi y los agentes (iconos lineales) ─────────────────────────
EQUIPO = [
    dict(nombre="Jordi Gonzalez Roig", corto="Jordi", rol="Fundador", icono="persona",
         frase="Escucha tu negocio, decide y responde de cada entrega."),
    dict(nombre="Coordinación", corto="Coordinación", rol="agente de IA", icono="lista",
         frase="Gestiona las prioridades y te informa de cada avance con claridad."),
    dict(nombre="Desarrollo", corto="Desarrollo", rol="agente de IA", icono="codigo",
         frase="Implementa cada mejora y la prueba a fondo antes de entregarla."),
    dict(nombre="Operación", corto="Operación", rol="agente de IA", icono="escudo",
         frase="Realiza las copias de seguridad, publica los cambios y supervisa el funcionamiento."),
    dict(nombre="Cumplimiento", corto="Cumplimiento", rol="agente de IA", icono="balanza",
         frase="Mantiene al día la documentación, la protección de datos y las condiciones de cada servicio."),
    dict(nombre="Diseño", corto="Diseño", rol="agente de IA", icono="paleta",
         frase="Cuida la imagen, los textos y la experiencia de uso de cada web."),
]

# Monograma «IT» (favicon y apple-touch-icon): sustituye al antiguo icono de marca.
MONOGRAMA = ('<svg class="icono-marca" viewBox="0 0 110 110" aria-hidden="true" focusable="false">'
             '<rect width="110" height="110" rx="24" fill="#111111"/>'
             f'<path transform="{logotipo.MONO_TRANSFORM}" d="{logotipo.ACENTO_TRAZOS}" fill="#f59e0b"/></svg>')
LOGOTIPO = logotipo.svg()


def icono(nombre):
    d = {
        "persona": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
        "candado": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
        "copia": '<path d="M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z"/><path d="M4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
        "charla": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>',
        "charla-ok": '<path d="M4 5h16v11H9l-5 4z"/><path d="m9 10.5 2 2 4-4"/>',
        "mano": '<path d="M4 20l1-4L15.5 5.5a2.1 2.1 0 0 1 3 3L8 19z"/><path d="M3 3l18 18"/>',
        "lupa": '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
        "ojo": '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z"/><circle cx="12" cy="12" r="2.5"/>',
        "hoja": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
        "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "repo": '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 8.2v7.6M18 10.2c0 4-6 3-11 6"/>',
        "pruebas": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3"/><path d="M8 15h8"/>',
        "publicar": '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
        "servidor": '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
        "lista": '<path d="M10 6h10M10 12h10M10 18h10"/><path d="m3.5 6 1.5 1.5L7.5 5M3.5 12l1.5 1.5L7.5 11M3.5 18l1.5 1.5L7.5 17"/>',
        "codigo": '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16"/>',
        "escudo": '<path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
        "balanza": '<path d="M12 4v16M8 20h8M5 7h14"/><circle cx="12" cy="4" r="1"/><path d="M5 7 2 13a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0z"/>',
        "paleta": '<path d="M12 3a9 9 0 0 0 0 18c1.4 0 2-1 2-2s-1-1.5-1-2.5 1-1.5 2-1.5h2a4 4 0 0 0 4-4c0-4.4-4-8-9-8z"/><circle cx="7.5" cy="11" r="1.1"/><circle cx="10" cy="7" r="1.1"/><circle cx="15" cy="7.5" r="1.1"/>',
        "nube": '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.1 4.5 4.5 0 0 0 7 18z"/>',
        "contenedor": '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9z"/><path d="M4 7.5 12 12l8-4.5M12 12v9"/>',
        "pipeline": '<circle cx="5" cy="12" r="2.2"/><circle cx="12" cy="12" r="2.2"/><circle cx="19" cy="12" r="2.2"/><path d="M7.2 12h2.6M14.2 12h2.6"/>',
        "pulso": '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
        "casa": '<path d="M3 11 12 4l9 7"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-5.5h4V20"/>',
        "calendario": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8.5 3v4M15.5 3v4"/><path d="m9.5 14.5 2 2 3.5-3.5"/>',
    }[nombre]
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{d}</svg>'


def retrato(c):
    return f'<span class="retrato{" jefe" if c["corto"] == "Jordi" else ""}">{icono(c["icono"])}</span>'


# ── Ilustraciones propias (SVG geométrico, misma paleta en todas) ───────────
C, N, G1, G2, A, B = "#fdf6ec", "#111111", "#e7e1d6", "#a8a29e", "#d97706", "#ffffff"


def _ilus(cuerpo, alt):
    return (f'<svg class="ilus" viewBox="0 0 320 200" role="img" aria-label="{alt}" focusable="false"><rect width="320" height="200" fill="{C}"/>'
            f'<circle cx="292" cy="26" r="64" fill="none" stroke="#efe4d2" stroke-width="2"/>'
            f'<circle cx="24" cy="186" r="38" fill="none" stroke="#efe4d2" stroke-width="2"/>{cuerpo}</svg>')


ILUS = {
    "inmobiliarias": _ilus(
        f'<path d="M58 172V96l46-36 46 36v76z" fill="{B}" stroke="{N}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M50 102 104 60l54 42" fill="none" stroke="{N}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<rect x="92" y="132" width="24" height="40" rx="2" fill="{N}"/><rect x="72" y="108" width="18" height="16" rx="2" fill="{G1}"/>'
        f'<rect x="118" y="108" width="18" height="16" rx="2" fill="{A}"/>'
        f'<rect x="168" y="52" width="104" height="120" rx="8" fill="{B}" stroke="{N}" stroke-width="2"/>'
        + "".join(f'<rect x="180" y="{y}" width="16" height="16" rx="3" fill="{G1}"/><rect x="204" y="{y + 2}" width="{w}" height="5" rx="2.5" fill="{N}"/>'
                  f'<rect x="204" y="{y + 10}" width="{w - 20}" height="4" rx="2" fill="{G2}"/>' for y, w in ((66, 52), (96, 44), (126, 56)))
        + f'<circle cx="252" cy="158" r="17" fill="{N}"/><circle cx="249" cy="155" r="7" fill="none" stroke="{C}" stroke-width="2.5"/>'
        f'<path d="m254 160 6 6" stroke="{C}" stroke-width="2.5" stroke-linecap="round"/>',
        "Ilustración: una vivienda junto a una ficha de inmuebles con un buscador"),
    "webs": _ilus(
        f'<rect x="62" y="34" width="196" height="138" rx="8" fill="{B}" stroke="{N}" stroke-width="2"/><path d="M62 56h196" stroke="{N}" stroke-width="2"/>'
        f'<circle cx="76" cy="45" r="3.5" fill="{N}"/><circle cx="88" cy="45" r="3.5" fill="{N}"/><circle cx="100" cy="45" r="3.5" fill="{G2}"/>'
        f'<rect x="76" y="68" width="168" height="52" rx="4" fill="{N}"/><rect x="88" y="80" width="84" height="7" rx="3.5" fill="{C}"/>'
        f'<rect x="88" y="94" width="56" height="6" rx="3" fill="{G2}"/><rect x="88" y="106" width="34" height="8" rx="4" fill="{A}"/>'
        f'<rect x="76" y="130" width="50" height="30" rx="4" fill="{G1}"/><rect x="135" y="130" width="50" height="30" rx="4" fill="{G1}"/>'
        f'<rect x="194" y="130" width="50" height="30" rx="4" fill="{G1}"/>', "Ilustración: ventana de navegador con una web clara y un botón de acción"),
    "gestion": _ilus(
        "".join(f'<rect x="{x}" y="32" width="66" height="142" rx="8" fill="{B}" stroke="{G1}" stroke-width="2"/>'
                f'<rect x="{x + 10}" y="42" width="30" height="6" rx="3" fill="{N}"/>' for x in (52, 127, 202))
        + "".join(f'<rect x="{x}" y="{y}" width="46" height="24" rx="4" fill="{G1}"/>'
                  for x, y in ((62, 58), (62, 90), (62, 122), (137, 58), (212, 58), (212, 90)))
        + f'<rect x="137" y="90" width="46" height="24" rx="4" fill="none" stroke="{G2}" stroke-width="1.5" stroke-dasharray="4 3"/>'
        + f'<g transform="rotate(-6 166 116)"><rect x="146" y="102" width="46" height="24" rx="4" fill="{A}"/>'
        f'<rect x="153" y="110" width="24" height="4" rx="2" fill="{B}"/></g>', "Ilustración: tablero de gestión en columnas con una tarea en movimiento"),
    "reservas": _ilus(
        f'<rect x="66" y="34" width="170" height="140" rx="8" fill="{B}" stroke="{N}" stroke-width="2"/>'
        f'<path d="M66 42a8 8 0 0 1 8-8h154a8 8 0 0 1 8 8v20H66z" fill="{N}"/>'
        f'<rect x="96" y="26" width="6" height="18" rx="3" fill="{G2}"/><rect x="200" y="26" width="6" height="18" rx="3" fill="{G2}"/>'
        + "".join(f'<rect x="{80 + c * 21}" y="{74 + f * 23}" width="15" height="15" rx="3" fill="{G1}"/>' for f in range(4) for c in range(7))
        + f'<rect x="143" y="97" width="15" height="15" rx="3" fill="{A}"/><path d="m146.5 104.5 3 3 5-6" stroke="{B}" stroke-width="2" fill="none" stroke-linecap="round"/>'
        f'<circle cx="244" cy="150" r="28" fill="{N}"/><circle cx="244" cy="150" r="21" fill="none" stroke="{G2}" stroke-width="1.5"/>'
        f'<path d="M244 136v14l10 6" stroke="{C}" stroke-width="3" fill="none" stroke-linecap="round"/>', "Ilustración: calendario con un día reservado y un reloj"),
    "automatizacion": _ilus(
        f'<path d="M92 100 H150 M170 100 L226 62 M170 100 L226 138" stroke="{N}" stroke-width="2" fill="none"/>'
        f'<path d="M108 100 H140" stroke="{A}" stroke-width="2" stroke-dasharray="5 5" fill="none"/>'
        f'<circle cx="74" cy="100" r="26" fill="{B}" stroke="{N}" stroke-width="2"/>'
        f'<rect x="62" y="91" width="24" height="18" rx="2" fill="none" stroke="{N}" stroke-width="2"/><path d="m62 93 12 9 12-9" stroke="{N}" stroke-width="2" fill="none"/>'
        f'<circle cx="160" cy="100" r="30" fill="{A}"/><path d="M151 88v24l20-12z" fill="{B}"/>'
        f'<circle cx="160" cy="100" r="40" fill="none" stroke="{G2}" stroke-width="1.5" stroke-dasharray="3 6"/>'
        f'<rect x="222" y="40" width="48" height="44" rx="8" fill="{N}"/><path d="m235 62 7 7 13-14" stroke="{C}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<rect x="222" y="116" width="48" height="44" rx="8" fill="{B}" stroke="{N}" stroke-width="2"/>'
        f'<path d="M234 130h24M234 138h24M234 146h14" stroke="{G2}" stroke-width="3" stroke-linecap="round"/>', "Ilustración: un correo que entra en un proceso automático y sale convertido en avisos e informes"),
    "cuidado": _ilus(
        f'<circle cx="160" cy="102" r="70" fill="none" stroke="{G2}" stroke-width="1.5" stroke-dasharray="4 6"/>'
        f'<path d="M226 78 A70 70 0 0 1 214 146" stroke="{A}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="m206 140 8 7 4-10" stroke="{A}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M160 52 122 66v30c0 26 16 44 38 52 22-8 38-26 38-52V66z" fill="{N}"/>'
        f'<path d="m144 100 11 11 21-22" stroke="{C}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        + "".join(f'<ellipse cx="74" cy="{y}" rx="22" ry="7" fill="{B}" stroke="{N}" stroke-width="2"/>' for y in (148, 136, 124))
        + f'<path d="M52 124v24M96 124v24" stroke="{N}" stroke-width="2"/>', "Ilustración: escudo con una marca de verificación junto a una pila de copias de seguridad"),
}

# ── Contenido ────────────────────────────────────────────────────────────────
# Cada línea de servicio con sus tres viñetas dentro de la tarjeta (la antigua sección «En detalle» ya no existe).
SERVICIOS = [
    ("inmobiliarias", "Plataforma para inmobiliarias", "Web con buscador y CRM de clientes, inmuebles y visitas. Lista para empezar y adaptada a tu forma de trabajar. Ya funciona en DBM Real Invest.",
     ["Buscador en lenguaje natural, en varios idiomas", "Fichas, visitas y permisos por perfil", "Páginas por ciudad e inmueble para aparecer en Google"]),
    ("webs", "Webs", "Webs rápidas y accesibles que convierten visitas en contactos.",
     ["Diseño a la medida de tu marca", "En varios idiomas", "Fácil de actualizar"]),
    ("gestion", "Herramientas de gestión", "Clientes, pedidos, visitas o expedientes en una aplicación hecha a tu medida, con acceso según el perfil de cada usuario.",
     ["Diseñada sobre tus procesos reales", "Permisos por persona y por equipo", "Los datos son siempre de tu empresa"]),
    ("reservas", "Reservas y citas", "Tus clientes reservan en línea. Tu equipo ve la agenda desde cualquier dispositivo.",
     ["Recordatorios automáticos", "Agenda compartida", "Desde el móvil"]),
    ("automatizacion", "Automatización con agentes de IA", "Agentes de IA hacen el trabajo repetitivo, siempre con una persona al mando. Tu equipo gana tiempo para lo importante.",
     ["Avisos y correos automáticos", "Informes periódicos", "Se conecta con lo que ya usas"]),
    ("cuidado", "Mantenimiento y soporte", "Tus sistemas, al día y vigilados. Sin que tengas que pensar en ello.",
     ["Copia de seguridad antes de cada cambio", "Actualizaciones al día", "Informe de cada cambio"]),
]

# P31: cuatro líneas al final de «Método», sin título propio (antes, la sección «Compromisos»).
COMPROMISOS = [
    ("persona", "Una persona responsable"),
    ("candado", "Tus datos, solo tuyos"),
    ("copia", "Copia antes de cada cambio"),
    ("charla", "Te contamos todo, también lo que falla"),
]

FAQ = [
    ("¿Necesito conocimientos técnicos?",
     "No. Tú conoces tu negocio; nosotros, la tecnología. Te lo explicamos sin tecnicismos y te enseñamos a usar cada herramienta."),
    ("Ya tengo una web o un programa. ¿Hay que sustituirlo?",
     "No necesariamente. Primero analizamos lo que tienes; si es aprovechable, lo mejoramos. Solo proponemos empezar de cero cuando está justificado."),
    ("¿Quién hace el trabajo: personas o inteligencia artificial?",
     "Las dos. Los agentes de IA desarrollan, prueban y publican. Jordi revisa, decide y habla contigo."),
    ("¿Cuál es el coste?",
     "Depende de lo que necesites. Después de hablar, te enviamos una propuesta detallada antes de empezar."),
    ("¿Y si algo falla después de un cambio?",
     "Volvemos atrás. Antes de cada cambio hacemos una copia completa, así que siempre hay un punto seguro al que volver."),
    # WEB-018: solo se promete la entrega de los datos y la documentación, no la del código (decisión del pmo, 2026-11-08).
    ("¿Me quedo atado a vosotros?",
     "No. Tus datos son siempre tuyos. Si cambias de proveedor, te entregamos los datos y la documentación en un formato estándar."),
    ("¿Cuánto se tarda en ver algo?",
     "Empezamos por lo más importante, en una entrega pequeña, para que veas resultados pronto. El plazo exacto va en la propuesta."),
]
# WEB-018: «Cómo empezar», tres pasos antes del contacto (icono, título, texto).
EMPEZAR = [
    ("correo", "Nos escribes", "Cuéntanos qué te hace perder tiempo."),
    ("charla", "Hablamos", "Una conversación sin compromiso para entender tu negocio."),
    ("hoja", "Recibes una propuesta", "Qué haremos, qué verás primero y cómo comprobarlo."),
]

# WEB-012: caso de éxito real. CASO_CON_NOMBRE=True (variante A) nombra a DBM Real Invest, con permiso del cliente
# (Jordi, 2026-11-08). Con False se vuelve a la variante B, anónima (reserva si DBM retirase el permiso).
CASO_CON_NOMBRE = True
CASO_TEXTOS = {
    "A": dict(
        titulo="Un pedido. Un cambio en&nbsp;producción.",
        entrada=('<a href="https://dbmrealinvest.com/" rel="noopener noreferrer">DBM Real Invest</a> es una inmobiliaria. '
                 'Creamos y mantenemos su web y su CRM. Cuando su CTO necesita algo, nos lo pide. Nosotros nos ocupamos del resto.'),
        informa="Informamos al CTO de DBM Real Invest.",
        ticket_cab="Hoja de cambios · DBM Real Invest",
        cierre="El mismo método para cada cliente. También para esta web."),
    "B": dict(
        titulo="Un pedido. Un cambio en&nbsp;producción.",
        entrada=('Una inmobiliaria. Creamos y mantenemos su web y su CRM. Cuando su responsable técnico necesita algo, nos lo pide. '
                 'Nosotros nos ocupamos del resto.'),
        informa="Informamos al cliente.",
        ticket_cab="Hoja de cambios · Inmobiliaria",
        cierre="El mismo método para cada cliente. También para esta web."),
}
CASO = CASO_TEXTOS["A" if CASO_CON_NOMBRE else "B"]
CASO_NOTA = "Si vemos un riesgo antes de publicar, paramos y lo consultamos con el cliente."
CASO_TICKET_TITULO_HTML = "Buscar una calle se escriba como se&nbsp;escriba"
# Calles públicas de ejemplo (DW-020-J2): sin datos de clientes ni de propietarios.
CASO_TICKET_DATOS = [
    ("Lo que pidió", "Que el CRM encuentre una calle se escriba como se escriba."),
    ("Lo que hicimos", "«C/», «Calle» y «Carrer» dan el mismo resultado, igual que «Avda.» y «Avinguda». "
                       "Da igual si hay acentos o mayúsculas. Cada comercial sigue viendo solo lo suyo."),
    ("Cómo lo comprobamos", "En producción, «Carrer de Sepúlveda», «C/ Sepúlveda» y «calle sepulveda» devuelven los mismos resultados."),
]
CASO_TICKET_ESTADOS = [
    ("Pedido por el cliente", "Con sus palabras."),
    ("Registrado", "En la hoja de cambios."),
    ("Probado", "En un entorno aislado."),
    ("Copia de seguridad y publicación", "Con vuelta atrás preparada."),
    ("Comprobado e informado", f"Validado en producción. {CASO['informa']}"),
]
# Mini tarjeta del hero: resumen del caso real (el mismo ticket que más abajo), todo «hecho».
MINI_ESTADOS = [("Pedido", "Pedido", ""), ("En desarrollo", "Desarrollo", ""), ("En revisión", "Revisión", ""),
                ("Publicado", "Publicado", ""), ("Validado", "Validado", "")]
MINI_ACTUAL = len(MINI_ESTADOS)  # ningún estado en curso: el cambio está validado
ICONO_SERVICIO = {"inmobiliarias": "casa", "webs": "nube", "gestion": "contenedor", "reservas": "calendario",
                  "automatizacion": "pipeline", "cuidado": "pulso"}  # icono de cada tarjeta de servicio

# Diagrama del flujo (HTML+CSS): pasos y carril propio de cada empresa.
FLUJO_PASOS = [
    ("correo", "Solicitud", "Por correo, al buzón dedicado de tu empresa"),
    ("lista", "Coordinación", "Registra la petición, la prioriza y confirma su recepción"),
    ("codigo", "Desarrollo", "Desarrolla y prueba en un entorno aislado"),
    ("escudo", "Operación", "Hace la copia de seguridad y publica el cambio"),
    ("charla-ok", "Informe", "Qué ha cambiado y cómo comprobarlo"),
]
CARRIL = [("repo", "Su repositorio"), ("pruebas", "Pruebas automáticas"), ("copia", "Copia de seguridad"),
          ("publicar", "Publicación"), ("servidor", "Su servidor")]

NAV = [("servicios", "Servicios"), ("caso", "Caso de éxito"), ("por-dentro", "Método"), ("equipo", "Equipo"), ("preguntas", "Preguntas")]
LEGALES = [("aviso-legal.html", "Aviso legal"), ("privacidad.html", "Privacidad"), ("cookies.html", "Cookies")]

# ── CSS ──────────────────────────────────────────────────────────────────────
# La hoja de estilos vive en estilos.css (WEB-017) y se publica con su hash en el nombre: el navegador la guarda
# en caché entre páginas y visitas, y un cambio de estilos cambia el nombre (nunca se sirve una versión vieja).
CSS = (HERE / "estilos.css").read_text(encoding="utf-8")
CSS_NOMBRE = f"estilos.{hashlib.sha256(CSS.encode('utf-8')).hexdigest()[:10]}.css"

JS = r"""
(function(){
 var d=document.documentElement,io=null,arrancado=false;
 // La clase .js solo se pone si el IntersectionObserver se ha podido crear: sin él, todo se ve sin animación.
 try{
  io=new IntersectionObserver(function(es){arrancado=true;es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('visto');io.unobserve(e.target);}});},{threshold:.1});
  d.classList.add('js');
 }catch(e){io=null;}
 function todo(){document.querySelectorAll('.revela').forEach(function(e){e.classList.add('visto');});}
 function alCambiar(mq,f){if(mq.addEventListener)mq.addEventListener('change',f);else if(mq.addListener)mq.addListener(f);}
 // Al imprimir: todo en su sitio y las preguntas abiertas; al terminar, las que estaban cerradas se vuelven a cerrar.
 var cerradas=[];
 addEventListener('beforeprint',function(){todo();cerradas=[].filter.call(document.querySelectorAll('details:not([open])'),function(x){x.open=true;return true;});});
 addEventListener('afterprint',function(){cerradas.forEach(function(x){x.open=false;});cerradas=[];});
 addEventListener('DOMContentLoaded',function(){
  try{
   var cab=document.querySelector('.cab');
   var anio=document.getElementById('anio');if(anio)anio.textContent=new Date().getFullYear();
   var copiar=document.querySelector('[data-copiar]'),aviso=document.getElementById('aviso-copia');
   if(copiar&&aviso&&navigator.clipboard&&window.isSecureContext){
    copiar.hidden=false;
    copiar.addEventListener('click',function(){var t=copiar.getAttribute('data-copiar');
     navigator.clipboard.writeText(t).then(function(){aviso.textContent='Dirección copiada.';},function(){aviso.textContent='No se ha podido copiar: la dirección es '+t+'.';});});
   }
   if(!io)return;
   var marca=function(){cab.classList.toggle('scroll',scrollY>8);};marca();addEventListener('scroll',marca,{passive:true});
   // Menú móvil: con teclado el foco va al primer enlace; Escape, salir del menú con el foco o tocar fuera lo cierran.
   var boton=document.querySelector('.menu-boton'),menu=document.getElementById('menu');
   if(boton&&menu){
    var abierto=function(){return boton.getAttribute('aria-expanded')==='true';};
    var abrir=function(a){boton.setAttribute('aria-expanded',String(a));boton.setAttribute('aria-label',a?'Cerrar el menú':'Abrir el menú');menu.classList.toggle('abierto',a);};
    boton.addEventListener('click',function(e){var a=!abierto();abrir(a);if(a&&e.detail===0){var p=menu.querySelector('a');if(p)p.focus();}});
    menu.addEventListener('click',function(e){if(e.target.closest('a'))abrir(false);});
    addEventListener('keydown',function(e){if(e.key==='Escape'&&abierto()){abrir(false);boton.focus();}});
    cab.addEventListener('focusout',function(e){if(abierto()&&e.relatedTarget&&!cab.contains(e.relatedTarget))abrir(false);});
    document.addEventListener('pointerdown',function(e){if(abierto()&&!cab.contains(e.target))abrir(false);});
    alCambiar(matchMedia('(min-width:901px)'),function(e){if(e.matches)abrir(false);});
   }
   // Botón fijo en móvil: aparece solo al subir (no tapa lo que se está leyendo).
   var cta=document.querySelector('.cta-movil'),hero=document.querySelector('.hero'),contacto=document.getElementById('contacto');
   if(cta&&hero&&contacto){
    document.body.classList.add('con-cta');var enContacto=false,ultimo=scrollY,subiendo=false;
    var ver=function(){var y=scrollY;if(Math.abs(y-ultimo)>6){subiendo=y<ultimo;ultimo=y;}
     var v=subiendo&&y>hero.offsetHeight&&!enContacto;cta.classList.toggle('visible',v);cta.setAttribute('aria-hidden',String(!v));cta.tabIndex=v?0:-1;};
    new IntersectionObserver(function(es){enContacto=es[0].isIntersecting;ver();}).observe(contacto);
    ver();addEventListener('scroll',ver,{passive:true});
   }
   document.querySelectorAll('.revela').forEach(function(e){io.observe(e);});
   // Red de seguridad: si el observador no ha respondido en 1,5 s, se muestra todo en su sitio.
   setTimeout(function(){if(!arrancado)todo();},1500);
  }catch(e){d.classList.remove('js');}
 });
})();
"""


# ── Piezas comunes ───────────────────────────────────────────────────────────
def marca_html(inicio):
    return f'<a class="marca" href="{inicio}" aria-label="th3b1gbr0th3r IT, inicio">{logotipo.uso()}</a>'


def cabecera(base, inicio):
    """base: prefijo de las anclas de la página principal ("" en index.html, "index.html" o "/" en las demás)."""
    enlaces = "".join(f'<li><a href="{base}#{i}">{t}</a></li>' for i, t in NAV)
    return f"""<a class="saltar" href="#principal">Saltar al contenido</a>
<header class="cab">
 <div class="contenedor">
  {marca_html(inicio)}
  <button class="menu-boton" type="button" aria-expanded="false" aria-controls="menu" aria-label="Abrir el menú"><span class="barras" aria-hidden="true"><i></i><i></i><i></i></span>Menú</button>
  <nav class="menu" id="menu" aria-label="Principal"><ul>{enlaces}<li class="solo-movil"><a class="btn" href="{base}#contacto">Escríbenos</a></li></ul></nav>
  <a class="btn cab-cta" href="{base}#contacto">Escríbenos</a>
 </div>
</header>"""


def pie(base, inicio, raiz, actual=""):
    nav = "".join(f'<li><a href="{base}#{i}">{t}</a></li>' for i, t in NAV)
    legales = "".join(f'<li><a href="{raiz}{h}"{" aria-current=\"page\"" if h == actual else ""}>{t}</a></li>' for h, t in LEGALES)
    return f"""<footer class="pie">
 <div class="contenedor">
  <div class="reticula">
   <div class="col-marca">
    {marca_html(inicio)}
    <p>Desarrollo, mantenimiento y soporte de software para pequeñas empresas.</p>
   </div>
   <nav aria-label="Navegación del pie"><h2>Navegación</h2><ul>{nav}</ul></nav>
   <div class="col"><h2>Legal</h2><ul>{legales}</ul></div>
   <div class="col-contacto"><h2>Contacto</h2><ul><li><a class="correo" href="{MAILTO}">{MAIL}</a></li></ul></div>
  </div>
  <div class="base"><p>© <span id="anio">{ANIO}</span> th3b1gbr0th3r IT. Todos los derechos reservados.</p></div>
 </div>
</footer>"""


def sin_viudas(fragmento):
    """Une con espacio duro la última palabra de cada h1/h2 a la anterior (además de text-wrap:balance)."""
    def unir(m):
        dentro = m.group(2)
        dentro = "".join(t if t.startswith("<") else re.sub(r"(?<![\w&;])(\w{1,2}) (?=\w)", r"\1&nbsp;", t)
                         for t in re.split(r"(<[^>]+>)", dentro))
        cab, sep, cola = dentro.rpartition(" ")
        if not sep or '="' in cola or len(cola.strip()) > 18 or len(re.sub(r"<[^>]+>", "", dentro).split()) < 4:
            return f"{m.group(1)}{dentro}{m.group(3)}"
        return f"{m.group(1)}{cab}&nbsp;{cola}{m.group(3)}"
    return re.sub(r"(<h[12][^>]*>)(.*?)(</h[12]>)", unir, fragmento, flags=re.S)


HASH_JS = "sha256-" + base64.b64encode(hashlib.sha256(JS.encode("utf-8")).digest()).decode()
OG_ALT = "Logotipo de th3b1gbr0th3r IT junto al lema «Software a la medida de tu negocio»."

JSON_LD = json.dumps({"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "@id": URL_BASE + "#sitio", "url": URL_BASE, "name": "th3b1gbr0th3r IT", "inLanguage": "es",
     "publisher": {"@id": URL_BASE + "#empresa"}},
    {"@type": "Organization", "@id": URL_BASE + "#empresa", "name": "th3b1gbr0th3r IT", "url": URL_BASE,
     "logo": URL_BASE + "apple-touch-icon.png",
     "founder": {"@type": "Person", "name": "Jordi Gonzalez Roig", "jobTitle": "Fundador"},
     "contactPoint": {"@type": "ContactPoint", "contactType": "ventas", "email": MAIL, "availableLanguage": "es"}},
    {"@type": "ProfessionalService", "@id": URL_BASE + "#servicio", "name": "th3b1gbr0th3r IT", "url": URL_BASE,
     "image": URL_BASE + "og.png", "logo": URL_BASE + "apple-touch-icon.png", "parentOrganization": {"@id": URL_BASE + "#empresa"},
     "description": "Software a medida y automatización para pequeñas empresas.",
     "areaServed": {"@type": "Country", "name": "España"}, "knowsLanguage": "es"},
]}, ensure_ascii=False)


def pagina(titulo, descripcion, cuerpo, ruta, base="index.html", raiz="", indexar=True, extra_head="",
           og_imagen="og.png", og_alt=OG_ALT):
    """ruta: nombre publicado (para og:url). raiz: "" (rutas relativas) o "/" (404: rutas desde la raíz del dominio)."""
    cuerpo = sin_viudas(cuerpo)
    inicio = raiz or "index.html"
    url = URL_BASE + ("" if ruta == "index.html" else ruta)
    robots = ('<meta name="robots" content="index,follow,max-image-preview:large">\n' if indexar
              else '<meta name="robots" content="noindex">\n')
    # CSP: sin 'unsafe-inline' en ningún sitio. El JS va en línea con su hash; los estilos, solo desde la hoja propia
    # (no hay atributos style ni <style> en las páginas). connect-src 'self' permite leer robots.txt a las herramientas
    # de auditoría (Lighthouse) sin abrir nada hacia fuera.
    csp = (f"default-src 'none'; script-src '{HASH_JS}'; style-src 'self'; img-src 'self' data:; "
           "font-src 'self'; manifest-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
{robots}<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111111" media="(prefers-color-scheme: dark)">
<link rel="preload" href="{raiz}fuentes/{FUENTE_NORMAL}" as="font" type="font/woff2" crossorigin fetchpriority="high">
<script>{JS}</script>
<link rel="stylesheet" href="{raiz}{CSS_NOMBRE}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="th3b1gbr0th3r IT">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{URL_BASE}{og_imagen}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titulo}">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="{URL_BASE}{og_imagen}">
<meta name="twitter:image:alt" content="{og_alt}">
<link rel="icon" href="{raiz}favicon.svg" type="image/svg+xml" sizes="any">
<link rel="icon" href="{raiz}favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="{raiz}favicon-16.png" type="image/png" sizes="16x16">
<link rel="apple-touch-icon" href="{raiz}apple-touch-icon.png">
<link rel="manifest" href="{raiz}site.webmanifest">
{extra_head}</head>
<body>
{logotipo.definicion()}
{cabecera(base, inicio)}
<main id="principal">
{cuerpo}
</main>
{pie(base, inicio, raiz, ruta)}
</body>
</html>
"""


# ── Página principal ─────────────────────────────────────────────────────────
hero_equipo = "".join(f'<li>{retrato(c)}<span class="nombre" aria-hidden="true">{c["corto"]}</span></li>' for c in EQUIPO)
mini_pasos = "".join(
    f'<li class="{"hecho" if i < MINI_ACTUAL else "actual" if i == MINI_ACTUAL else ""}"'
    f'{" aria-current=\"step\"" if i == MINI_ACTUAL else ""}>{corto}'
    f'<span class="sr">{": hecho" if i < MINI_ACTUAL else ": en curso" if i == MINI_ACTUAL else ": pendiente"}</span></li>'
    for i, (_, corto, _) in enumerate(MINI_ESTADOS)).replace(' class=""', "")

tarjetas = "".join(
    f'<article class="tarjeta revela"><div class="imagen">{ILUS[i]}</div><div class="cuerpo"><p class="etq">{icono(ICONO_SERVICIO[i])}</p><h3>{t}</h3><p>{d}</p>'
    f'<ul class="vinetas">{"".join(f"<li>{x}</li>" for x in v)}</ul></div></article>'
    for i, t, d, v in SERVICIOS) + (
    '<article class="tarjeta cta oscuro revela"><div class="cuerpo"><h3>¿Buscas otra cosa?</h3>'
    '<p>Cuéntanosla y te diremos cómo resolverla.</p>'
    '<a class="mas" href="#contacto">Escríbenos <span aria-hidden="true">→</span></a></div></article>')


def _nodo(x):
    return f'<span class="nodo">{icono(x)}</span>'


pasos = "".join(f'<li>{_nodo(x)}<span><b class="paso-t">{t}</b><span class="paso-d">{d}</span></span></li>' for x, t, d in FLUJO_PASOS)
carril = "".join(f'<li><span class="chip">{icono(i)}<span>{t}</span></span></li>' for i, t in CARRIL)
FLUJO = f"""<figure class="flujo revela" aria-labelledby="titulo-dentro">
   <div class="flujo-fila"><p class="flujo-aprueba">{icono("persona")}<span>Jordi revisa y aprueba las decisiones importantes</span></p></div>
   <ol class="pasos">{pasos}</ol>
   <div class="flujo-fila"><p class="flujo-apoyo">{icono("balanza")}{icono("paleta")}<span>Si hace falta, intervienen también Cumplimiento y Diseño.</span></p></div>
   <div class="flujo-fila"><p class="conector">Sobre la infraestructura de cada cliente</p></div>
   <div class="carriles">
    <div class="carril"><p class="carril-cab"><b>Tu empresa</b><span class="mono">entorno propio · aislado</span></p><ol class="carril-pasos">{carril}</ol></div>
   </div>
   <p class="flujo-nota">{icono("candado")}<span>Cada cliente tiene su propio entorno. Nada se comparte.</span></p>
  </figure>"""

compromisos = "".join(f'<li class="revela">{icono(i)}<span>{t}</span></li>' for i, t in COMPROMISOS)
equipo = "".join(f'<li class="revela">{retrato(c)}<h3>{c["nombre"]}</h3><span class="rol">{c["rol"]}</span><p>{c["frase"]}</p></li>' for c in EQUIPO)
empezar = "".join(f'<li class="revela"><span class="num" aria-hidden="true">{n}</span>{icono(i)}<h3>{t}</h3><p>{d}</p></li>'
                  for n, (i, t, d) in enumerate(EMPEZAR, 1))
faq = "".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
estados = "".join(
    f'<li class="hecho"><span class="punto" aria-hidden="true"></span>'
    f'<b>{e}<span class="sr">: hecho</span></b><span class="txt">{d}</span></li>' for e, d in CASO_TICKET_ESTADOS)
datos = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in CASO_TICKET_DATOS)

INDEX = f"""<section class="hero oscuro" aria-labelledby="titulo-hero">
 <div class="contenedor reticula">
  <div class="hero-texto">
   <span class="sobre">La automatización ya ha llegado a la pequeña&nbsp;empresa</span>
   <h1 id="titulo-hero">Software a la medida de tu&nbsp;negocio.</h1>
   <p class="apoyo">Webs y herramientas de gestión hechas para tu empresa. Una persona responde de cada cambio.</p>
   <div class="acciones"><a class="btn claro" href="#contacto">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a>
    <a class="enlace-sec" href="#caso">Ver el caso</a></div>
  </div>
  <div class="hero-visual">
   <div class="escena">
    <ul class="hero-equipo" aria-label="El equipo: Jordi, responsable, y los agentes de IA de Coordinación, Desarrollo, Operación, Cumplimiento y Diseño">{hero_equipo}</ul>
    <p class="hero-equipo-pie" aria-hidden="true">Jordi y cinco agentes de IA</p>
    <figure class="mini" aria-label="El caso real de nuestra hoja de cambios">
     <div class="mini-cab"><span>{CASO["ticket_cab"]}</span><span class="etiqueta">Caso real</span></div>
     <p class="mini-titulo">{CASO_TICKET_TITULO_HTML}</p>
     <ol class="mini-pasos">{mini_pasos}</ol>
     <p class="mini-pie">Estado: <b>Validado</b> · <a href="#caso">Ver el caso</a></p>
    </figure>
   </div>
  </div>
 </div>
</section>

<section class="bloque" id="servicios" aria-labelledby="titulo-servicios">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Servicios</span><h2 id="titulo-servicios">Hecho a partir de cómo trabajas.</h2>
   <p>Partimos de tus procesos, no de una plantilla.</p></div>
  <div class="tarjetas">{tarjetas}</div>
 </div>
</section>

<section class="bloque alterno caso" id="caso" aria-labelledby="titulo-caso">
 <div class="contenedor">
  <div class="reticula">
   <div class="caso-izq">
    <div class="titular"><span class="sobre">Caso real · DBM Real Invest</span><h2 id="titulo-caso">{CASO["titulo"]}</h2>
     <p>{CASO["entrada"]}</p></div>
    <p class="caso-nota">{icono("persona")}<span>{CASO_NOTA}</span></p>
   </div>
   <div class="caso-lado">
    <article class="ticket revela" aria-labelledby="titulo-ticket">
     <div class="ticket-cab"><span>{CASO["ticket_cab"]}</span><span class="etiqueta">Caso real</span></div>
     <div class="ticket-cuerpo">
      <h3 id="titulo-ticket">{CASO_TICKET_TITULO_HTML}</h3>
      <dl class="ticket-datos">{datos}</dl>
      <ol class="estados">{estados}</ol>
     </div>
     <div class="ticket-pie"><span><b>Validado</b> en producción</span></div>
    </article>
   </div>
  </div>
  <div class="cierre revela"><p>{CASO["cierre"]}</p>
   <a class="btn" href="#contacto">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a></div>
 </div>
</section>

<section class="bloque" id="por-dentro" aria-labelledby="titulo-dentro">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Método de trabajo</span><h2 id="titulo-dentro">Cada cambio, a la vista. Cada cliente, aparte.</h2>
   <p>Así llega cada petición desde tu correo hasta producción.</p></div>
  {FLUJO}
  <ul class="promesas" aria-label="Nuestros compromisos">{compromisos}</ul>
 </div>
</section>

<section class="bloque alterno" id="equipo" aria-labelledby="titulo-equipo">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Equipo</span><h2 id="titulo-equipo">Un responsable humano, apoyado por agentes de IA.</h2>
   <p>Jordi Gonzalez Roig, el fundador, dirige cada proyecto y decide. Cinco agentes de IA hacen el trabajo. Siempre se presentan como lo que son.</p></div>
  <ul class="equipo">{equipo}</ul>
 </div>
</section>

<section class="bloque faq" id="preguntas" aria-labelledby="titulo-preguntas">
 <div class="contenedor reticula">
  <div class="titular"><span class="sobre">Preguntas</span><h2 id="titulo-preguntas">Preguntas frecuentes</h2>
   <p>Si tienes otra duda, escríbenos.</p></div>
  <div class="lista">{faq}</div>
 </div>
</section>

<section class="bloque contacto oscuro" id="contacto" aria-labelledby="titulo-contacto">
 <div class="contenedor reticula">
  <div class="titular"><span class="sobre">Contacto</span><h2 id="titulo-contacto">Hablemos de tu proyecto.</h2>
   <p>Cuéntanos cómo funciona tu negocio. Te diremos cómo hacerlo más fácil.</p></div>
  <ol class="empezar" aria-label="Cómo empezar">{empezar}</ol>
  <div class="accion">
   <a class="btn claro" href="{MAILTO}">Escríbenos <span aria-hidden="true">→</span></a>
   <p class="correo-fila"><a class="correo" href="{MAILTO}">{MAIL}</a><button class="copiar" type="button" data-copiar="{MAIL}" hidden>Copiar dirección</button></p>
   <p class="aviso-copia" id="aviso-copia" aria-live="polite"></p>
   <p class="firma">{icono("persona")}<span>Jordi atiende personalmente cada mensaje.</span></p>
   <p class="privacidad-linea">Esta web no usa <a href="cookies.html">cookies ni analítica</a>. Tus datos, igual de protegidos.</p>
  </div>
 </div>
</section>
<a class="cta-movil btn claro" href="#contacto" aria-hidden="true" tabindex="-1">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a>"""

TITULO_INDEX = "Software a medida para pequeñas empresas · th3b1gbr0th3r IT"
DESC_INDEX = ("La automatización ya ha llegado a la pequeña empresa. Webs y herramientas de gestión a medida, "
              "con una persona responsable de cada cambio.")
html = pagina(TITULO_INDEX, DESC_INDEX, INDEX, "index.html", base="",
              extra_head=f'<script type="application/ld+json">{JSON_LD}</script>\n')


# ── Páginas legales ──────────────────────────────────────────────────────────
def pend(texto):
    return f'<span class="pendiente">[PENDIENTE: {texto}]</span>'


# Datos del titular (los aporta Jordi, 2026-11-08). Solo se muestran en las páginas legales.
TITULAR = "Jordi Gonzalez Roig"
NIF = "37327892L"
DOMICILIO = "Carrer de Jordi de Sant Jordi, 11, 2º 4ª, 08027 Barcelona (España)"
DATOS_TITULAR = (f"<dt>Titular</dt><dd>{TITULAR}, persona física, que opera con el nombre comercial th3b1gbr0th3r IT</dd>"
                 f"<dt>NIF</dt><dd>{NIF}</dd><dt>Domicilio</dt><dd>{DOMICILIO}</dd>")


def legal(titulo, cuerpo):
    return (f'<article class="legal"><div class="contenedor"><span class="sobre">Legal</span><h1>{titulo}</h1>'
            f'<p class="fecha">Última actualización: {ACTUALIZADO}</p>{cuerpo}</div></article>')


AVISO = legal("Aviso legal", f"""
<p>En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de servicios de la sociedad de la información y de comercio electrónico (LSSI-CE), estos son los datos del titular de esta web.</p>
<h2>Datos identificativos</h2>
<dl>
 {DATOS_TITULAR}
 <dt>Correo electrónico</dt><dd><a href="{MAILTO}">{MAIL}</a></dd>
 <dt>Web</dt><dd>{URL_BASE.rstrip("/")}</dd>
</dl>
<h2>Objeto</h2>
<p>Esta web presenta los servicios de desarrollo de software a la medida de th3b1gbr0th3r IT y explica cómo contactar con nosotros. Navegar por ella te da la condición de usuario e implica que aceptas este aviso legal. La web es informativa: no se puede contratar ni pagar nada a través de ella.</p>
<h2>Condiciones de uso</h2>
<p>Te comprometes a usar la web y sus contenidos de forma lícita, sin dañar su funcionamiento ni los derechos de terceros.</p>
<h2>Propiedad intelectual e industrial</h2>
<p>Los textos, diseños, ilustraciones, logotipos y el código de esta web pertenecen a su titular o se usan con autorización o con licencia. Las tipografías se usan bajo su licencia libre (SIL Open Font License): la tipografía Source Serif 4, de Adobe, se distribuye con el texto de esa licencia en <a href="fuentes/OFL.txt">fuentes/OFL.txt</a>. El logotipo está trazado a partir de la tipografía Inter (Rasmus Andersson, también SIL Open Font License) y no incorpora archivos de fuente. No se permite reproducir, distribuir, comunicar públicamente ni transformar los contenidos sin permiso previo y por escrito, salvo para uso personal y privado. «th3b1gbr0th3r IT» es un nombre comercial.</p>
<h2>Enlaces</h2>
<p>Si la web enlaza a sitios de terceros, no somos responsables de su contenido. Retiraremos un enlace en cuanto sepamos que lleva a contenido ilícito.</p>
<h2>Responsabilidad</h2>
<p>Cuidamos que la información de la web sea correcta y esté al día, pero no podemos garantizar que no haya errores ni que el sitio esté siempre disponible. El titular no responde de los daños causados por un uso indebido de la web.</p>
<h2>Inteligencia artificial</h2>
<p>Parte de nuestro trabajo lo hacen agentes de inteligencia artificial que supervisa Jordi. Cuando un agente se comunica contigo, se identifica como tal. Lo explicamos en la <a href="privacidad.html">política de privacidad</a>.</p>
<h2>Protección de datos y cookies</h2>
<p>El tratamiento de tus datos se explica en la <a href="privacidad.html">política de privacidad</a>. Esta web no usa cookies: lo detallamos en la <a href="cookies.html">política de cookies</a>.</p>
<h2>Legislación aplicable y jurisdicción</h2>
<p>Este aviso legal se rige por la legislación española. Si eres consumidor, en caso de controversia serán competentes los juzgados y tribunales de tu domicilio. En los demás casos, las partes se someten a los juzgados y tribunales de Barcelona.</p>
""")

PRIVACIDAD = legal("Política de privacidad", f"""
<p>Aquí te contamos qué datos personales tratamos, para qué y qué derechos tienes, conforme al Reglamento (UE) 2016/679 (RGPD) y a la Ley Orgánica 3/2018, de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD).</p>
<h2>Responsable del tratamiento</h2>
<dl>
 {DATOS_TITULAR.replace("<dt>Titular</dt>", "<dt>Responsable</dt>")}
 <dt>Contacto</dt><dd><a href="{MAILTO_DERECHOS}">{MAIL}</a></dd>
</dl>
<p>No hemos nombrado delegado de protección de datos porque no estamos obligados (art. 37 RGPD y art. 34 LOPDGDD).</p>
<h2>Qué datos tratamos</h2>
<p>La web no tiene formularios, no pide registro y no usa cookies ni analítica. Solo tratamos los datos que nos mandas si nos escribes: tu correo electrónico, tu nombre si nos lo das y lo que nos cuentes en el mensaje. Te pedimos que no nos envíes datos sensibles (salud, ideología, etc.) ni datos de otras personas sin su permiso.</p>
<h2>Para qué los usamos</h2>
<p>Para contestarte, atender tu consulta y, si nos lo pides, prepararte una propuesta. No los usamos para enviarte publicidad, no elaboramos perfiles y no tomamos decisiones automatizadas sobre ti.</p>
<h2>Quién lee tus mensajes</h2>
<p>Los correos que nos envías a esta dirección <strong>los lee y los contesta Jordi</strong>, una persona. Nuestros agentes de inteligencia artificial <strong>no procesan este buzón</strong>. Esos agentes trabajan solo en los proyectos de nuestros clientes, con las condiciones que pactamos con cada uno.</p>
<h2>Base legal</h2>
<ul>
 <li><strong>Tu consentimiento</strong> (art. 6.1.a RGPD), que nos das al escribirnos. Puedes retirarlo cuando quieras.</li>
 <li><strong>Medidas precontractuales a petición tuya</strong> (art. 6.1.b RGPD), si después hablamos de un proyecto.</li>
</ul>
<h2>Cuánto tiempo los conservamos</h2>
<p>El tiempo necesario para atender tu consulta y, como máximo, <strong>12 meses</strong> desde el último contacto si no llegamos a trabajar juntos. Si llegamos a trabajar juntos, los conservamos durante la relación y los plazos que exija la ley (por ejemplo, la normativa fiscal). Después, se eliminan.</p>
<h2>A quién se comunican</h2>
<p>No cedemos tus datos a terceros salvo obligación legal. Usamos estos proveedores, que actúan como encargados del tratamiento o, en lo que se indica, según su propia política:</p>
<div class="tabla"><table>
 <thead><tr><th scope="col">Proveedor</th><th scope="col">Para qué</th><th scope="col">Dónde</th><th scope="col">Garantía</th></tr></thead>
 <tbody>
  <tr><td>Google (Gmail)</td><td>Buzón de correo de contacto</td><td>UE y EE. UU.</td><td>Marco de Privacidad de Datos UE-EE. UU. y cláusulas contractuales tipo</td></tr>
  <tr><td>GitHub (GitHub Pages)</td><td>Alojamiento de la web</td><td>EE. UU.</td><td>Marco de Privacidad de Datos UE-EE. UU. y cláusulas contractuales tipo</td></tr>
 </tbody>
</table></div>
<h2>Alojamiento de la web</h2>
<p>La web se sirve como páginas estáticas desde GitHub Pages. Como cualquier servidor web, GitHub puede registrar datos técnicos de la conexión, como la dirección IP, por seguridad y para que el servicio funcione, según su propia política de privacidad. Nosotros no accedemos a esos registros ni los usamos.</p>
<h2>Tus derechos</h2>
<p>Puedes ejercer en cualquier momento tus derechos de acceso, rectificación, supresión, oposición, limitación del tratamiento y portabilidad, y retirar tu consentimiento. Escríbenos a <a href="{MAILTO_DERECHOS}">{MAIL}</a> indicando qué derecho quieres ejercer. Si tenemos dudas razonables sobre tu identidad, podremos pedirte que la acredites. Te contestaremos en un plazo máximo de un mes.</p>
<p>Si crees que no hemos tratado bien tus datos, puedes reclamar ante la Agencia Española de Protección de Datos (www.aepd.es).</p>
<h2>Menores</h2>
<p>La web va dirigida a empresas y profesionales. Si eres menor de 14 años, no nos envíes datos personales.</p>
<h2>Cambios en esta política</h2>
<p>Si cambia la forma en que tratamos los datos, actualizaremos esta página y su fecha.</p>
""")

COOKIES = legal("Política de cookies", f"""
<p>Una cookie es un pequeño fichero que una web guarda en tu navegador para recordar información sobre tu visita.</p>
<h2>Esta web no usa cookies</h2>
<p>No instalamos cookies propias ni de terceros. Tampoco usamos otras técnicas equivalentes de almacenamiento en tu navegador.</p>
<h2>Ni rastreadores ni recursos de terceros</h2>
<ul>
 <li>Sin analítica ni estadísticas de visitas.</li>
 <li>Sin publicidad ni píxeles de seguimiento.</li>
 <li>Sin botones de redes sociales, vídeos, mapas ni fuentes cargadas desde otros sitios.</li>
</ul>
<p>Todo lo que ves (textos, tipografía, ilustraciones y estilos) se sirve desde la propia web. Por eso no te mostramos ningún aviso de cookies: no hay nada que aceptar.</p>
<h2>Si esto cambia</h2>
<p>Si algún día incorporamos cookies que no sean estrictamente necesarias, actualizaremos esta política y te pediremos el consentimiento antes de usarlas.</p>
<p>Más información en el <a href="aviso-legal.html">aviso legal</a> y en la <a href="privacidad.html">política de privacidad</a>, o escribiéndonos a <a href="{MAILTO_DERECHOS}">{MAIL}</a>.</p>
""")

def og_legal(nombre):
    """Imagen para redes propia de cada página legal (recursos/og-<página>.png, se genera con --imagenes)."""
    return f"og-{nombre.removesuffix('.html')}.png"


PAGINAS_LEGALES = {
    "aviso-legal.html": ("Aviso legal · th3b1gbr0th3r IT", "Aviso legal de la web de th3b1gbr0th3r IT: datos del titular y condiciones de uso.", AVISO),
    "privacidad.html": ("Política de privacidad · th3b1gbr0th3r IT", "Qué datos personales tratamos, para qué, con qué proveedores y cuáles son tus derechos.", PRIVACIDAD),
    "cookies.html": ("Política de cookies · th3b1gbr0th3r IT", "Esta web no usa cookies ni rastreadores.", COOKIES),
}

IMAGENES_PUBLICADAS = ("og.png", "apple-touch-icon.png", "icono-192.png", "icono-512.png", "favicon-32.png", "favicon-16.png",
                       "favicon.ico", *(og_legal(n) for n in PAGINAS_LEGALES))

# 404: GitHub Pages la sirve en cualquier ruta inexistente, así que todo va desde la raíz del dominio.
NO_ENCONTRADA = pagina("Página no encontrada · th3b1gbr0th3r IT", "La página que buscas no existe.", f"""<section class="legal no-encontrada">
 <div class="contenedor">
  <div class="simbolo-404">{icono("lupa")}</div>
  <span class="sobre">Error 404</span>
  <h1>Página no encontrada</h1>
  <p class="subtitulo">Esta dirección no existe o ha cambiado.</p>
  <a class="btn" href="/">Volver al inicio</a>
 </div>
</section>""", "404.html", base="/", raiz="/", indexar=False)


def construir():
    if SITIO.exists():
        shutil.rmtree(SITIO)  # sin restos de versiones anteriores (p. ej. ficheros que ya no se publican)
    SITIO.mkdir(parents=True)
    (SITIO / "index.html").write_text(html, encoding="utf-8")
    (SITIO / "404.html").write_text(NO_ENCONTRADA, encoding="utf-8")
    for nombre, (titulo, desc, cuerpo) in PAGINAS_LEGALES.items():
        corto = titulo.split(" · ")[0]
        (SITIO / nombre).write_text(pagina(titulo, desc, cuerpo, nombre, og_imagen=og_legal(nombre),
                                           og_alt=f"th3b1gbr0th3r IT · {corto}"), encoding="utf-8")
    (SITIO / CSS_NOMBRE).write_text(CSS, encoding="utf-8")
    (SITIO / "favicon.svg").write_text(MONOGRAMA.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    (SITIO / "fuentes").mkdir()
    for f in (FUENTE_NORMAL, FUENTE_CURSIVA, "OFL.txt"):
        shutil.copy2(FUENTES / f, SITIO / "fuentes" / f)
    for f in IMAGENES_PUBLICADAS:
        shutil.copy2(RECURSOS / f, SITIO / f)
    (SITIO / "site.webmanifest").write_text(json.dumps({
        "name": "th3b1gbr0th3r IT", "short_name": "th3b1gbr0th3r", "lang": "es", "start_url": "./", "display": "browser",
        "background_color": "#111111", "theme_color": "#111111",
        "icons": [{"src": "icono-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icono-512.png", "sizes": "512x512", "type": "image/png"}]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (SITIO / ".nojekyll").write_text("", encoding="utf-8")
    (SITIO / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {URL_BASE}sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{URL_BASE}{'' if n == 'index.html' else n}</loc><lastmod>{datetime.date.today().isoformat()}</lastmod></url>" for n in ["index.html", *PAGINAS_LEGALES])
    (SITIO / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                       f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    print(f"OK: {SITIO}")


# ── Herramientas locales: servidor de prueba, capturas e imágenes (no las usa el pipeline) ──────────
def base_temporal():
    """Primer ancestro con backup/tmp (repo de gestión: temporales solo ahí); si no hay (CI), el del sistema."""
    for ancestro in HERE.parents:
        candidato = ancestro / "backup" / "tmp"
        if candidato.is_dir():
            return str(candidato)
    return None


def servidor(extra):
    """Sirve sitio/ en 127.0.0.1 (puerto libre) como GitHub Pages: 404.html en rutas inexistentes.
    extra: {ruta: html} páginas solo para capturas, servidas desde memoria (no se publican)."""
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path in extra:
                cuerpo = extra[self.path].encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            super().do_GET()

        def send_error(self, code, message=None, explain=None):
            if code != 404:
                return super().send_error(code, message, explain)
            cuerpo = (SITIO / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
    H.extensions_map = {**H.extensions_map, ".svg": "image/svg+xml", ".woff2": "font/woff2"}
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(SITIO)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _chrome(destino, tam, url, perfil, movimiento=False, oscuro=False, transparente=False):
    args = ["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--no-proxy-server",
            f"--user-data-dir={perfil}", "--virtual-time-budget=4000", f"--screenshot={destino}", f"--window-size={tam}", url]
    if not movimiento:
        args.insert(5, "--force-prefers-reduced-motion")
    if oscuro:  # prefers-color-scheme: dark
        args[5:5] = ["--force-dark-mode", "--blink-settings=preferredColorScheme=0"]
    if transparente:
        args.insert(5, "--default-background-color=00000000")
    subprocess.run(args, check=True, capture_output=True)


def _recortar(png):
    """Quita el fondo sobrante del final de una captura alta (si Pillow está disponible; si no, la deja tal cual)."""
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(png).convert("RGB")
    w, h = im.size
    fondo = im.getpixel((w - 1, h - 1))
    y = h - 1
    while y > 0 and all(im.getpixel((x, y)) == fondo for x in range(0, w, 7)):
        y -= 1
    if y < h - 1:
        im.crop((0, 0, w, min(h, y + 2))).save(png)


def sin_csp(pagina_html):
    """Solo para las páginas de captura (servidas en local desde /_captura/, nunca publicadas): sin la CSP, para poder
    inyectarles estilos y JS, y con la hoja de estilos y la fuente desde la raíz."""
    pagina_html = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n', "", pagina_html)
    return pagina_html.replace(f'href="{CSS_NOMBRE}"', f'href="/{CSS_NOMBRE}"').replace('href="fuentes/', 'href="/fuentes/')


def capturas():
    CAPTURAS.mkdir(exist_ok=True)
    extra = {
        # Menú móvil abierto con teclado (click() sin ratón: el foco va al primer enlace).
        "/_captura/menu.html": sin_csp(html).replace("</body>", "<script>addEventListener('load',()=>document.querySelector('.menu-boton').click())</script></body>"),
        # CTA fija en móvil tal como aparece al subir a media página.
        "/_captura/cta.html": sin_csp(html).replace("</head>", "<style>main>section:nth-of-type(-n+4){display:none}"
                                                      ".js .cta-movil{visibility:visible!important;transform:none!important}</style></head>"),
        # Solo el diagrama del flujo (imagen para redes, capturas/flujo.png).
        "/_captura/flujo.html": sin_csp(html).replace("</head>", "<style>.cab,.pie,.cta-movil,main>section:not(#por-dentro){display:none!important}"
                                                        "#por-dentro{padding:40px 0}#por-dentro .titular{margin-bottom:28px}</style></head>"),
    }
    trabajos = [("escritorio", "1440,12000", "/", True), ("tableta-1024", "1024,14000", "/", True), ("tableta-820", "820,15000", "/", True),
                ("movil-390", "390,20000", "/", True), ("movil-360", "360,21000", "/", True),
                ("movil-menu", "390,760", "/_captura/menu.html", False), ("movil-cta", "390,844", "/_captura/cta.html", False),
                ("flujo", "1240,1300", "/_captura/flujo.html", True),
                ("legal-privacidad-movil", "390,5200", "/privacidad.html", True),
                ("404", "1440,900", "/una/ruta/que/no-existe", False), ("404-movil", "360,780", "/otra/que/tampoco", False)]
    trabajos += [(f"legal-{n.removesuffix('.html')}", "1440,3200", f"/{n}", True) for n in PAGINAS_LEGALES]
    # Esquema oscuro (prefers-color-scheme: dark): portada, menú, una legal y la 404.
    trabajos += [(f"{n}-oscuro", tam, ruta, rec) for n, tam, ruta, rec in trabajos
                 if n in ("escritorio", "tableta-1024", "tableta-820", "movil-390", "movil-360", "movil-menu", "legal-privacidad-movil", "404")]
    srv, url = servidor(extra)
    try:
        with tempfile.TemporaryDirectory(dir=base_temporal()) as tmp:
            for i, (nombre, tam, ruta, recortar) in enumerate(trabajos):
                destino = CAPTURAS / f"{nombre}.png"
                _chrome(destino, tam, url + ruta, Path(tmp) / f"perfil{i}", oscuro=nombre.endswith("-oscuro"))
                if recortar:
                    _recortar(destino)
    finally:
        srv.shutdown()
    for f in ("og.png", "apple-touch-icon.png", *(og_legal(n) for n in PAGINAS_LEGALES)):
        shutil.copy2(RECURSOS / f, CAPTURAS / f)
    print(f"Capturas: {CAPTURAS}")


def _og_html(caras, titulo, lema, pasos=True):
    """Imagen para redes de 1200×630: logotipo, raya ámbar, titular y lema (y el flujo de estados en la portada)."""
    extra = ('<div class="pasos"><i class="ok"></i><b></b><i class="ok"></i><b></b><i class="ok"></i><b></b><i class="ok"></i><b></b><i></i></div>'
             '<p class="mono">petición → pruebas ✓ → copia ✓ → despliegue ✓ → validado</p>') if pasos else ""
    return f"""<!doctype html><meta charset="utf-8"><style>{caras}
body{{width:1200px;height:630px;background:radial-gradient(circle,rgba(253,246,236,.10) 1.4px,transparent 1.8px) 0 0/28px 28px,#111;color:#fdf6ec;font-family:S,serif;box-sizing:border-box;padding:88px 96px;overflow:hidden;position:relative}}
body::before{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#111 0,#111 45%,rgba(17,17,17,0) 85%)}}
.logotipo{{height:46px;width:auto;color:#fdf6ec;display:block;position:relative;z-index:1}}.logo-it{{fill:#f59e0b}}
.raya{{width:120px;height:4px;background:#d97706;margin:44px 0 36px;position:relative;z-index:1}}
h1{{font-weight:400;font-size:80px;line-height:1.04;margin:0 0 28px;letter-spacing:-.02em;max-width:880px;text-wrap:balance;color:#fdf6ec;position:relative;z-index:1}}
p{{font:600 28px system-ui,sans-serif;color:#d6d3d1;margin:0;position:relative;z-index:1}}
.mono{{position:absolute;right:96px;bottom:52px;font:500 20px ui-monospace,"DejaVu Sans Mono",monospace;color:#a8a29e}}
.pasos{{position:absolute;z-index:1;right:96px;bottom:96px;display:flex;align-items:center}}
.pasos i{{width:22px;height:22px;border-radius:50%;border:3px solid #d97706;box-sizing:border-box}}
.pasos i.ok{{background:#f59e0b;border-color:#f59e0b}}
.pasos b{{width:56px;border-top:3px dashed #d97706}}
</style>
<body>{LOGOTIPO}<div class="raya"></div><h1>{titulo}</h1>
<p>{lema}</p>{extra}</body>"""


def imagenes():
    """Regenera en recursos/ las imágenes con Chrome headless y Pillow: og.png y una og por página legal (1200×630),
    apple-touch-icon.png (180×180), icono-192/512.png (manifest), favicon-32/16.png y favicon.ico (16+32)."""
    from PIL import Image
    fuente = (FUENTES / FUENTE_NORMAL).as_uri()
    cursiva = (FUENTES / FUENTE_CURSIVA).as_uri()
    caras = (f'@font-face{{font-family:S;src:url({fuente})}}@font-face{{font-family:S;font-style:italic;src:url({cursiva})}}'
             'html,body{margin:0}')
    lema = "Desarrollo y mantenimiento para pequeñas empresas"
    ogs = {"og.png": _og_html(caras, "Software a la medida de tu&nbsp;negocio.", lema)}
    for nombre, (titulo, _, _) in PAGINAS_LEGALES.items():
        ogs[og_legal(nombre)] = _og_html(caras, titulo.split(" · ")[0], lema, pasos=False)
    cuadrado = MONOGRAMA.replace('rx="24"', 'rx="0"')  # iOS ya redondea las esquinas
    lienzo = '<!doctype html><meta charset="utf-8"><style>{c}html,body{{background:transparent}}body{{width:720px;height:720px;display:grid;place-items:center;overflow:hidden}}svg{{width:720px;height:720px}}</style><body>{s}</body>'
    with tempfile.TemporaryDirectory(dir=base_temporal()) as tmp:
        t = Path(tmp)

        def render(nombre, contenido, tam, transparente=False):
            pagina_tmp = t / f"{nombre}.html"
            pagina_tmp.write_text(contenido, encoding="utf-8")
            png = t / f"{nombre}.png"
            _chrome(png, tam, pagina_tmp.as_uri(), t / f"perfil-{nombre}", transparente=transparente)
            return Image.open(png)

        for destino, contenido in ogs.items():
            im = render(destino.removesuffix(".png"), contenido, "1200,630").convert("RGB")
            im = im.crop((0, 0, 1200, 630)) if im.size != (1200, 630) else im
            # Paleta de 256 colores: la imagen es plana (fondo, texto y ámbar) y pesa mucho menos sin pérdida visible.
            im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(RECURSOS / destino, optimize=True)
            print(f"{RECURSOS / destino} {im.size}")
        icono = render("icono", lienzo.format(c=caras, s=cuadrado), "720,720").convert("RGB")
        icono.resize((180, 180), Image.LANCZOS).save(RECURSOS / "apple-touch-icon.png", optimize=True)
        for lado in (192, 512):
            icono.resize((lado, lado), Image.LANCZOS).save(RECURSOS / f"icono-{lado}.png", optimize=True)
        # Favicon con las esquinas redondeadas del SVG, sobre fondo transparente.
        fav = render("favicon", lienzo.format(c=caras, s=MONOGRAMA), "720,720", transparente=True).convert("RGBA")
        for lado in (32, 16):
            fav.resize((lado, lado), Image.LANCZOS).save(RECURSOS / f"favicon-{lado}.png", optimize=True)
        fav.resize((64, 64), Image.LANCZOS).save(RECURSOS / "favicon.ico", sizes=[(16, 16), (32, 32)])
        print(f"{RECURSOS}: apple-touch-icon, icono-192/512, favicon-32/16 y favicon.ico")


if __name__ == "__main__":
    if "--imagenes" in sys.argv:
        RECURSOS.mkdir(exist_ok=True)
        imagenes()
    construir()
    if "--capturas" in sys.argv:
        capturas()
