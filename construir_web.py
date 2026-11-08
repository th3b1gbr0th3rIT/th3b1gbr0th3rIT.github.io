#!/usr/bin/env python3
"""Genera la web pública estática de th3b1gbr0th3r IT en sitio/ (GitHub Pages).

Estilo corporativo sobrio (WEB-006): un mensaje por bloque, servicios en tarjetas, diagrama del flujo en
HTML+CSS, caso de éxito «esta misma web» (WEB-005) y pie legal completo con sus páginas.
Sin cifras, sin precios, sin clientes nombrados. Sin recursos externos ni cookies: la única tipografía
(Source Serif 4, OFL) se sirve desde la propia web, en fuentes/.
Uso: python3 construir_web.py [--capturas] [--imagenes]
  --capturas  capturas de revisión en capturas/ (necesita google-chrome; Pillow opcional para recortar)
  --imagenes  regenera recursos/og.png y recursos/apple-touch-icon.png (necesita google-chrome y Pillow)
La construcción solo usa la biblioteca estándar de Python 3 (funciona tal cual en un runner de GitHub).
"""
import datetime
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
    dict(nombre="Jordi", rol="Fundador y CTO", icono="persona",
         frase="Analiza las necesidades de tu empresa, toma las decisiones y responde de cada entrega."),
    dict(nombre="Coordinación", rol="agente de IA", icono="lista",
         frase="Gestiona las prioridades y te informa de cada avance con claridad."),
    dict(nombre="Desarrollo", rol="agente de IA", icono="codigo",
         frase="Implementa cada mejora y la prueba a fondo antes de entregarla."),
    dict(nombre="Operación", rol="agente de IA", icono="escudo",
         frase="Realiza las copias de seguridad, publica los cambios y supervisa el funcionamiento."),
]

# Monograma «IT» (favicon y apple-touch-icon): sustituye al antiguo icono de marca.
MONOGRAMA = ('<svg class="icono-marca" viewBox="0 0 110 110" aria-hidden="true" focusable="false">'
             '<rect width="110" height="110" rx="24" fill="#111111"/>'
             f'<path transform="translate(-415.40 31.12) scale(0.06)" d="{logotipo.ACENTO_TRAZOS}" fill="#f59e0b"/></svg>')
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
    }[nombre]
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{d}</svg>'


def retrato(c):
    return f'<span class="retrato{" jefe" if c["nombre"] == "Jordi" else ""}">{icono(c["icono"])}</span>'


# ── Ilustraciones propias (SVG geométrico, misma paleta en todas) ───────────
C, N, G1, G2, A, B = "#fdf6ec", "#111111", "#e7e1d6", "#a8a29e", "#d97706", "#ffffff"


def _ilus(cuerpo, alt):
    return (f'<svg class="ilus" viewBox="0 0 320 200" role="img" aria-label="{alt}" focusable="false"><rect width="320" height="200" fill="{C}"/>'
            f'<circle cx="292" cy="26" r="64" fill="none" stroke="#efe4d2" stroke-width="2"/>'
            f'<circle cx="24" cy="186" r="38" fill="none" stroke="#efe4d2" stroke-width="2"/>{cuerpo}</svg>')


ILUS = {
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
    ("webs", "Webs", "Webs rápidas, accesibles y en varios idiomas, orientadas a convertir visitas en contactos y reservas.",
     ["Diseño a la medida de tu marca", "Versiones en varios idiomas", "Contenido fácil de actualizar"]),
    ("gestion", "Herramientas de gestión", "Clientes, pedidos, visitas o expedientes en una aplicación hecha a tu medida, con acceso según el perfil de cada usuario.",
     ["Diseñada sobre tus procesos reales", "Permisos por persona y por equipo", "Los datos son siempre de tu empresa"]),
    ("reservas", "Reservas y citas", "Reserva en línea para tus clientes y una agenda centralizada, accesible desde cualquier dispositivo.",
     ["Reservas en línea para tus clientes", "Recordatorios automáticos", "Agenda compartida para todo el equipo"]),
    ("automatizacion", "Automatización", "Automatizamos avisos, correos, informes y recordatorios para que tu equipo dedique su tiempo a lo que aporta valor.",
     ["Correos y avisos automáticos", "Informes periódicos automáticos", "Integración con las herramientas que ya utilizas"]),
    ("cuidado", "Mantenimiento y soporte", "Copias de seguridad, actualizaciones y supervisión continua para que tus sistemas sigan funcionando con seguridad.",
     ["Copia de seguridad antes de cada cambio", "Actualizaciones y supervisión continua", "Informe de cada cambio realizado"]),
]

COMPROMISOS = [
    ("persona", "Interlocutor único", "Un responsable identificado para tu proyecto, de principio a fin."),
    ("candado", "Tus datos, bajo tu control", "Solo los utilizamos para prestarte el servicio y nunca se mezclan con los de otros clientes."),
    ("copia", "Copia de seguridad previa", "Antes de cada cambio hacemos una copia completa, de modo que siempre es posible volver al estado anterior."),
    ("charla", "Transparencia", "Te informamos de lo realizado, de cómo comprobarlo y de lo pendiente, también cuando surge un problema."),
]

FAQ = [
    ("¿Necesito conocimientos técnicos?",
     "No. Tú conoces tu negocio y nosotros nos encargamos de la parte técnica. Te lo explicamos todo sin tecnicismos y te formamos en el uso de cada herramienta."),
    ("¿Trabajáis con empresas pequeñas?",
     "Sí, es nuestro foco. Empezamos por lo más prioritario y ampliamos la solución a medida que crece tu empresa."),
    ("Ya tengo una web o un programa. ¿Hay que sustituirlo?",
     "No necesariamente. Primero analizamos lo que tienes; si es aprovechable, lo mejoramos. Solo proponemos empezar de cero cuando está justificado."),
    ("¿Quién hace el trabajo: personas o inteligencia artificial?",
     "Ambos. Los agentes de IA desarrollan, prueban y supervisan; Jordi revisa, decide y es tu interlocutor."),
    ("¿Cuál es el coste?",
     "Depende del alcance del proyecto. Tras una primera conversación, sin compromiso, te enviamos una propuesta detallada."),
]

# WEB-005: un cambio de esta web, estado a estado. Se rotula «Ejemplo» mientras no esté publicado y validado.
CASO_PUNTOS = [
    ("hoja", "Cada cambio queda registrado", "Todo empieza en la hoja de cambios: qué se solicita, quién se encarga y en qué estado se encuentra."),
    ("lupa", "La información interna no se publica", "Una verificación automática revisa cada versión antes de publicarla."),
    ("mano", "Ningún cambio sin pasar por pruebas", "Desarrollo implementa y prueba; Operación publica mediante un proceso automatizado."),
    ("ojo", "Validación final humana", "Jordi revisa el resultado publicado y lo valida."),
]
CASO_TITULO = "Añadir a la web el diagrama del proceso"  # texto plano
CASO_TITULO_HTML = "Añadir a la web el diagrama del&nbsp;proceso"  # mini tarjeta y ticket: sin viuda
CASO_ESTADOS = [
    ("Pedido", "Pedido", "Jordi lo pide y Coordinación lo registra en la hoja de cambios."),
    ("En desarrollo", "Desarrollo", "Desarrollo lo implementa y lo prueba en un entorno aislado."),
    ("En revisión", "Revisión", "Pasa la verificación automática y una revisión independiente."),
    ("Publicado", "Publicado", "Operación lo publica con el proceso automatizado de la web."),
    ("Validado", "Validado", "Jordi valida el resultado."),
]
CASO_ACTUAL = 2  # índice del estado en curso (En revisión)

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

NAV = [("servicios", "Servicios"), ("por-dentro", "Método"), ("caso", "Caso de éxito"), ("equipo", "Equipo"), ("preguntas", "Preguntas")]
LEGALES = [("aviso-legal.html", "Aviso legal"), ("privacidad.html", "Privacidad"), ("cookies.html", "Cookies")]

# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = r"""
@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:400;font-display:swap;src:url(@RAIZ@fuentes/@NORMAL@) format("woff2");
unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Source Serif 4";font-style:italic;font-weight:400;font-display:swap;src:url(@RAIZ@fuentes/@CURSIVA@) format("woff2");
unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
:root{--negro:#111;--carbon:#1c1917;--ambar:#d97706;--ambar2:#f59e0b;--tostado:#b45309;--crema:#fdf6ec;--blanco:#fff;
--gris1:#f4f1ec;--gris2:#e7e1d6;--gris3:#a8a29e;--texto:#44403c;--apoyo:#57534e;--linea:#e7e1d6;--borde-calido:#ecdcc4;
--serif:"Source Serif 4",Georgia,"DejaVu Serif","Times New Roman",serif;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"DejaVu Sans",Helvetica,Arial,sans-serif;
--ancho:1200px;--gutter:24px;--ritmo:8px;--cab:72px}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:calc(var(--cab) + 16px);background:var(--gris1)}
body{margin:0;background:var(--blanco);color:var(--negro);font:17px/1.65 var(--sans);-webkit-font-smoothing:antialiased;overflow-x:hidden}
img,svg{max-width:100%}
a{color:inherit}
h1,h2,h3{font-family:var(--serif);font-weight:400;line-height:1.12;margin:0;letter-spacing:-.01em;text-wrap:balance;font-variant-numeric:lining-nums}
h2{font-size:clamp(2rem,4vw,3rem)}
h3{font-size:1.35rem}
p{margin:0;text-wrap:pretty}
em{font-style:italic}
.sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}

/* Foco visible: anillo ámbar pegado al elemento y contorno negro por fuera (≥3:1 sobre blanco, crema y gris del pie).
   En fondos oscuros el contorno exterior pasa a crema. */
:focus{outline:none}
:focus-visible{outline:2px solid var(--negro);outline-offset:3px;box-shadow:0 0 0 3px var(--ambar2);border-radius:2px}
.oscuro :focus-visible{outline-color:var(--crema)}
.saltar{position:absolute;left:16px;top:-100px;z-index:100;background:var(--negro);color:var(--blanco);padding:12px 18px;text-decoration:none}
.saltar:focus{top:12px}
.contenedor{max-width:var(--ancho);margin:0 auto;padding:0 var(--gutter)}
.reticula{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:var(--gutter)}
.bloque{padding:calc(var(--ritmo)*13) 0}
.alterno{background:var(--crema)}
.sobre{display:block;font:700 .78rem/1.2 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--tostado);margin-bottom:calc(var(--ritmo)*2)}
.titular{max-width:900px;margin-bottom:calc(var(--ritmo)*6)}
.titular p{margin-top:calc(var(--ritmo)*2.5);font-size:1.15rem;color:var(--apoyo);max-width:60ch}
.titular .mas{margin-top:calc(var(--ritmo)*3)}
.mas{display:inline-flex;align-items:center;gap:8px;font-weight:700;text-decoration:none;color:var(--negro);border-bottom:2px solid var(--ambar);padding-bottom:3px}
.mas span{transition:transform .25s ease}.mas:hover span,.mas:focus-visible span{transform:translateX(4px)}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--negro);color:var(--blanco);padding:15px 26px;border-radius:4px;
font-weight:700;text-decoration:none;border:2px solid var(--negro);transition:background .2s,color .2s,border-color .2s;cursor:pointer;font-family:var(--sans);font-size:1rem}
.btn:hover{background:var(--carbon);border-color:var(--ambar)}
.btn.claro{background:var(--ambar2);border-color:var(--ambar2);color:var(--negro)}
.btn.claro:hover{background:#fbbf24;border-color:#fbbf24}

/* Logotipo (trazos SVG) */
.marca{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--negro)}
.logotipo{display:block;height:26px;width:auto}

/* Cabecera fija */
.cab{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.97);border-bottom:1px solid transparent;transition:border-color .3s,box-shadow .3s}
.cab.scroll{border-color:var(--linea);box-shadow:0 8px 24px -20px rgba(17,17,17,.4)}
.cab .contenedor{display:flex;align-items:center;justify-content:space-between;gap:24px;height:var(--cab)}
.menu ul{display:flex;align-items:center;gap:32px;list-style:none;margin:0;padding:0}
.menu a{text-decoration:none;font-weight:600;font-size:.95rem;color:var(--texto)}
.menu a:hover{color:var(--negro);text-decoration:underline;text-decoration-color:var(--ambar);text-underline-offset:6px;text-decoration-thickness:2px}
.menu .solo-movil{display:none}
.cab .btn{padding:10px 20px;font-size:.92rem}
.menu-boton{display:none;align-items:center;gap:10px;background:none;border:1px solid var(--linea);border-radius:4px;padding:9px 12px;
font:600 .92rem var(--sans);color:var(--negro);cursor:pointer}
.menu-boton .barras{position:relative;width:20px;height:14px}
.menu-boton .barras i{position:absolute;left:0;width:100%;height:2px;background:var(--negro);transition:transform .25s,opacity .25s}
.menu-boton .barras i:nth-child(1){top:0}.menu-boton .barras i:nth-child(2){top:6px}.menu-boton .barras i:nth-child(3){top:12px}
.menu-boton[aria-expanded="true"] .barras i:nth-child(1){transform:translateY(6px) rotate(45deg)}
.menu-boton[aria-expanded="true"] .barras i:nth-child(2){opacity:0}
.menu-boton[aria-expanded="true"] .barras i:nth-child(3){transform:translateY(-6px) rotate(-45deg)}

/* Hero: texto + iconos de rol y la mini tarjeta del cambio */
.hero{background:var(--negro);color:var(--blanco);position:relative;overflow:hidden}
.hero .reticula{align-items:center;min-height:min(80vh,700px);padding-block:calc(var(--ritmo)*10);row-gap:48px}
.hero-texto{grid-column:1/span 6}
.hero .sobre{color:var(--ambar2)}
.hero h1{font-size:clamp(2.6rem,5.4vw,4.4rem);line-height:1.04;letter-spacing:-.02em}
.hero h1 em{color:var(--ambar2)}
.hero .apoyo{margin-top:calc(var(--ritmo)*3);font-size:clamp(1.1rem,1.6vw,1.3rem);color:#d6d3d1;max-width:30em}
.acciones{display:flex;flex-wrap:wrap;align-items:center;gap:16px 28px;margin-top:calc(var(--ritmo)*5)}
.hero-visual{grid-column:7/span 6}
.escena{background:var(--crema);color:var(--negro);border-radius:20px;padding:28px 26px 26px;box-shadow:0 40px 80px -40px rgba(0,0,0,.7)}
.hero-equipo{list-style:none;margin:0 0 20px;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;text-align:center}
.hero-equipo .retrato{width:72px;height:72px;margin:0 auto 8px}
.hero-equipo .nombre{display:block;font:600 .82rem/1.3 var(--sans);color:var(--apoyo)}
.hero-equipo-pie{display:none;margin:-8px 0 16px;font-size:.85rem;color:var(--apoyo);text-align:center}
.mini{margin:0;background:var(--blanco);border:1px solid var(--borde-calido);border-radius:12px;padding:16px 18px 14px}
.mini-cab{display:flex;justify-content:space-between;align-items:center;gap:12px;font:700 .8rem/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--apoyo)}
.etiqueta{display:inline-block;padding:4px 8px;border-radius:99px;background:#fef3c7;color:#7c2d12;border:1px solid #f5d08a;letter-spacing:.08em}
.mini-titulo{margin:12px 0 12px;font:400 1.2rem/1.25 var(--serif)}
.mini-titulo,.ticket h3{text-wrap:balance}
.mini-pasos{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.mini-pasos li{font:600 .82rem/1 var(--sans);padding:6px 10px;border-radius:99px;border:1px solid var(--gris2);color:var(--apoyo)}
.mini-pasos li.hecho{background:var(--negro);border-color:var(--negro);color:var(--blanco)}
.mini-pasos li.hecho::before{content:"✓ ";color:var(--ambar2)}
.mini-pasos li.actual{background:#fef3c7;border-color:var(--tostado);color:#7c2d12}
.mini-pie{margin-top:12px;font-size:.88rem;color:var(--apoyo)}
.mini-pie a{color:var(--negro);text-decoration-color:var(--ambar);text-underline-offset:3px}

/* Servicios en tarjetas, con las viñetas dentro */
.tarjetas{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:var(--gutter)}
.tarjeta{grid-column:span 4;display:flex;flex-direction:column;background:var(--blanco);border:1px solid var(--linea);
transition:transform .3s ease,box-shadow .3s ease,border-color .3s}
.tarjeta:hover{transform:translateY(-4px);box-shadow:0 28px 48px -32px rgba(17,17,17,.45);border-color:#d6cfc2}
.tarjeta .imagen{overflow:hidden;border-bottom:1px solid var(--linea);background:var(--crema)}
.ilus{display:block;width:100%;height:auto}
.tarjeta .cuerpo{padding:24px 26px 28px;display:flex;flex-direction:column;gap:12px;flex:1}
.tarjeta p{color:var(--apoyo)}
.vinetas{list-style:none;margin:4px 0 0;padding:14px 0 0;border-top:1px solid var(--linea);display:grid;gap:6px;font-size:.95rem;color:var(--texto)}
.vinetas li{padding-left:20px;position:relative}
.vinetas li::before{content:"";position:absolute;left:0;top:.72em;width:10px;height:2px;background:var(--ambar)}
.tarjeta.cta{background:var(--negro);color:var(--blanco);border-color:var(--negro);justify-content:flex-end}
.tarjeta.cta .cuerpo{justify-content:flex-end;padding:40px 32px}
.tarjeta.cta h3{font-size:1.8rem}.tarjeta.cta p{color:#d6d3d1}.tarjeta.cta .mas{color:var(--blanco);border-color:var(--ambar2);margin-top:12px;align-self:flex-start}

/* Misión */
.mision .reticula{align-items:end;row-gap:24px}
.mision .frase{grid-column:1/span 8;font-size:clamp(1.9rem,3.8vw,3rem);line-height:1.18}
.mision .frase em{color:var(--tostado)}
.mision .lado{grid-column:9/span 4;color:var(--apoyo);font-size:1.1rem}

/* Por dentro: diagrama del flujo en HTML+CSS (vertical por defecto, horizontal desde 1100 px) */
.flujo{margin:0;background:var(--blanco);border:1px solid var(--linea);padding:28px 20px 24px;font-size:15px}
.flujo-aprueba{display:flex;align-items:center;gap:12px;margin:0 0 24px;padding:10px 16px;background:var(--crema);border:1px solid var(--borde-calido);
border-radius:14px;font:italic 1.05rem/1.3 var(--serif);color:#92400e;position:relative}
.flujo-aprueba .ico{width:40px;height:40px;padding:9px;background:var(--negro);border-color:var(--negro);stroke:var(--ambar2)}
.pasos{list-style:none;margin:0;padding:0;display:grid;gap:0}
.pasos li{position:relative;display:grid;align-content:start;grid-template-columns:76px minmax(0,1fr);column-gap:16px;align-items:center;padding-bottom:22px}
.pasos li:not(:last-child)::after{content:"";position:absolute;left:37px;top:80px;bottom:4px;border-left:2.5px dashed var(--ambar)}
.nodo{width:76px;height:76px;border-radius:50%;background:var(--crema);border:3px solid #f1e4cf;display:grid;place-items:center;overflow:hidden}
.nodo .ico{width:34px;height:34px;padding:0;border:0;background:none;border-radius:0}
.paso-t{display:block;font:400 1.25rem/1.2 var(--serif);color:var(--negro)}
.paso-d{display:block;color:var(--apoyo);font-size:.95rem;line-height:1.4;margin-top:2px}
.conector{display:flex;align-items:center;gap:10px;margin:2px 0 14px;font:700 .82rem/1.2 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--tostado)}
.conector::before{content:"";width:2.5px;height:28px;margin-left:36px;border-left:2.5px dashed var(--ambar)}
.carriles{position:relative}
.carril{position:relative;z-index:2;background:var(--blanco);border:2.5px solid var(--ambar);border-radius:20px;padding:18px 16px 16px}
.carril-cab{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:12px}
.carril-cab b{font:400 1.3rem/1.2 var(--serif)}
.carril-cab span,.capa{font:700 .82rem/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--tostado)}
.carril-pasos{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.carril-pasos li{display:flex;align-items:center}
.chip{display:flex;align-items:center;gap:10px;flex:1;background:var(--crema);border-radius:99px;padding:8px 14px;font-weight:600;font-size:.95rem}
.carril-pasos .ico{width:22px;height:22px;padding:0;border:0;background:none;border-radius:0}
.capa{position:relative;margin:-16px 14px 0;padding:24px 18px 8px;background:var(--blanco);border:2px solid #f1e4cf;border-top:0;border-radius:0 0 18px 18px;color:var(--apoyo);z-index:1}
.capa+.capa{margin:-16px 28px 0;z-index:0;color:var(--apoyo)}
.flujo-nota{display:flex;align-items:center;gap:10px;margin-top:20px;color:var(--apoyo);font-size:.95rem}
.flujo-nota .ico{width:24px;height:24px;padding:0;border:0;background:none;border-radius:0;stroke:var(--apoyo)}
@media (min-width:1100px){
 .flujo{padding:36px 32px 28px}
 .flujo-fila{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));column-gap:24px}
 .flujo-aprueba{grid-column:2/5;justify-content:center;margin-bottom:30px;background:none;border:0;padding:0 0 4px}
 .flujo-aprueba::after{content:"";position:absolute;left:calc((100% - 48px)/6);right:calc((100% - 48px)/6);bottom:-18px;height:12px;
  border:2px solid var(--negro);border-bottom:0;border-radius:10px 10px 0 0}
 .pasos{grid-template-columns:repeat(5,minmax(0,1fr));column-gap:24px}
 .pasos li{grid-template-columns:1fr;justify-items:center;text-align:center;align-items:start;padding:0}
 .pasos li:not(:last-child)::after{left:calc(50% + 60px);right:calc(-50% + 36px);top:52px;bottom:auto;border-left:0;border-top:2.5px dashed var(--ambar)}
 .nodo{width:104px;height:104px;margin-bottom:14px}
 .nodo .ico{width:44px;height:44px}
 .paso-d{max-width:16em}
 .conector{grid-column:3/6;flex-direction:column;align-items:center;gap:6px;margin:16px 0 14px;text-align:center}
 .conector::before{margin:0;height:34px}
 .carril{padding:16px 24px 18px}
 .carril-cab{justify-content:flex-start;gap:16px}
 .carril-pasos{display:flex;flex-wrap:wrap;align-items:center;gap:8px 0}
 .chip{flex:none;padding:8px 12px;font-size:.9rem;gap:8px}
 .carril-pasos li+li::before{content:"›";margin:0 6px;color:var(--ambar);font-weight:700;font-size:1.2rem;line-height:1}
}

/* Caso de éxito */
.caso .reticula{row-gap:40px;align-items:start}
.caso .titular{grid-column:1/span 6;margin-bottom:0}
.puntos{grid-column:1/span 6;list-style:none;margin:0;padding:0;display:grid;gap:24px}
.puntos li{display:flex;gap:18px}
.ico{flex:none;width:44px;height:44px;padding:10px;border-radius:50%;background:var(--blanco);border:1px solid var(--borde-calido);
fill:none;stroke:var(--tostado);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.puntos h3,.compromisos h3{font-size:1.15rem;margin-bottom:6px}
.puntos p,.compromisos p{color:var(--apoyo)}
.ticket{grid-column:8/span 5;grid-row:1/span 2;background:var(--blanco);border:1px solid var(--linea);box-shadow:0 30px 60px -44px rgba(17,17,17,.5)}
.ticket-cab{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 24px;border-bottom:1px solid var(--linea);
font:700 .78rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--apoyo)}
.ticket-cuerpo{padding:22px 24px 6px}
.ticket h3{font-size:1.45rem;margin-bottom:8px}
.ticket .que{color:var(--apoyo);font-size:.98rem}
.estados{list-style:none;margin:22px 0 0;padding:0}
.estados li{position:relative;padding:0 0 20px 40px}
.estados li::before{content:"";position:absolute;left:9px;top:22px;bottom:0;width:2px;background:var(--gris2)}
.estados li:last-child::before{display:none}
.estados .punto{position:absolute;left:0;top:2px;width:20px;height:20px;border-radius:50%;border:2px solid var(--gris3);background:var(--blanco)}
.estados b{display:block;font-size:.98rem}
.estados .txt{display:block;color:var(--apoyo);font-size:.92rem}
.estados li.hecho .punto{background:var(--negro);border-color:var(--negro)}
.estados li.hecho .punto::after{content:"";position:absolute;left:5px;top:2px;width:5px;height:9px;border:solid var(--ambar2);border-width:0 2px 2px 0;transform:rotate(45deg)}
.estados li.actual .punto{border-color:var(--tostado);background:#fef3c7}
.estados li.actual .punto::after{content:"";position:absolute;left:4px;top:4px;width:8px;height:8px;border-radius:50%;background:var(--tostado)}
.ticket-pie{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px 12px;padding:14px 24px;border-top:1px solid var(--linea);background:var(--gris1);font-size:.9rem;color:var(--apoyo)}
.ticket-pie b{color:var(--negro)}
.cierre{margin-top:calc(var(--ritmo)*8);padding-top:calc(var(--ritmo)*5);border-top:1px solid #e6d6bd;display:flex;flex-wrap:wrap;
justify-content:space-between;align-items:center;gap:24px}
.cierre p{font:400 clamp(1.5rem,2.8vw,2.1rem)/1.2 var(--serif);max-width:24em}

/* Compromisos: títulos alineados con subgrid */
.compromisos{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));grid-template-rows:auto auto auto;gap:0 var(--gutter)}
.compromisos li{display:grid;grid-row:span 3;grid-template-rows:subgrid;align-content:start;border-top:2px solid var(--negro);padding-top:24px}
.compromisos .ico{margin-bottom:18px;background:var(--blanco);border-color:var(--borde-calido)}
.compromisos h3{align-self:end}

/* Equipo: dos por dos */
.equipo{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:40px var(--gutter)}
.equipo li{display:grid;grid-template-columns:96px minmax(0,1fr);grid-template-areas:"foto nombre" "foto rol" "foto frase";column-gap:24px;align-content:start;align-items:start}
.equipo .retrato{grid-area:foto;width:96px;height:96px}
.equipo h3{grid-area:nombre;font-size:1.35rem;align-self:end}
.equipo .rol{grid-area:rol}
.equipo p{grid-area:frase;color:var(--apoyo);max-width:36ch}
.retrato{display:grid;place-items:center;flex:none;border-radius:50%;background:var(--blanco);border:1px solid var(--borde-calido)}
.retrato .ico{width:44%;height:44%;padding:0;border:0;background:none;border-radius:0;stroke-width:1.6}
.retrato.jefe{background:var(--negro);border-color:var(--negro)}
.retrato.jefe .ico{stroke:var(--ambar2)}
.rol{display:block;font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--tostado);margin:4px 0 8px}

/* Preguntas */
.faq .reticula{row-gap:32px}
.faq .titular{grid-column:1/span 4;margin:0}
.faq h2{font-size:clamp(2rem,3vw,2.5rem)}
.faq .lista{grid-column:6/span 7;border-top:1px solid var(--linea)}
details{border-bottom:1px solid var(--linea)}
summary{cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:20px 0;font:400 1.25rem/1.3 var(--serif)}
summary::-webkit-details-marker{display:none}
summary::after{content:"";flex:none;width:14px;height:14px;margin-right:6px;border:solid var(--tostado);border-width:0 2px 2px 0;transform:rotate(45deg) translateY(-4px);transition:transform .25s}
details[open] summary::after{transform:rotate(-135deg) translateY(-4px)}
details p{padding:0 0 22px;color:var(--apoyo);max-width:42em}

/* Contacto */
.contacto{background:var(--negro);color:var(--blanco)}
.contacto .reticula{align-items:end;row-gap:32px}
.contacto .titular{grid-column:1/span 7;margin:0}
.contacto .sobre{color:var(--ambar2)}
.contacto h2{font-size:clamp(2.2rem,5vw,3.8rem)}
.contacto .titular p{color:#d6d3d1}
.contacto .accion{grid-column:8/span 5;display:flex;flex-direction:column;align-items:flex-start;gap:14px}
.correo-fila{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;color:#e7e5e4;font-size:1rem}
.correo-fila .correo{word-break:break-all;color:#e7e5e4;text-decoration-color:var(--ambar2);text-underline-offset:3px}
.copiar{background:none;border:1px solid #78716c;border-radius:4px;color:var(--blanco);font:600 .88rem var(--sans);padding:10px 14px;cursor:pointer}
.copiar:hover{border-color:var(--ambar2)}
.aviso-copia{min-height:1.3em;font-size:.9rem;color:var(--ambar2)}
.firma{display:flex;align-items:center;gap:14px;color:#d6d3d1;font-size:.95rem}
.firma .ico{width:44px;height:44px;background:transparent;border-color:#57534e;stroke:var(--ambar2)}
.privacidad-linea{margin-top:4px;padding-top:16px;border-top:1px solid #3a3530;color:#d6d3d1;font-size:.92rem;max-width:40ch}
.privacidad-linea a{color:var(--blanco);text-decoration-color:var(--ambar2);text-underline-offset:3px}

/* Pie */
.pie{background:var(--gris1);color:var(--texto);font-size:.95rem;padding:calc(var(--ritmo)*9) 0 calc(var(--ritmo)*4)}
.pie .reticula{row-gap:40px}
.pie .col-marca{grid-column:1/span 4}
.pie .col-marca p{margin-top:16px;font:italic 1.05rem var(--serif);color:#92400e}
.pie nav,.pie .col{grid-column:span 2}
.pie .col-contacto{grid-column:span 4}
.pie h2{font:700 .78rem/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--negro);margin-bottom:16px}
.pie ul{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.pie a{text-decoration:none;color:var(--texto)}
.pie a:hover{color:var(--negro);text-decoration:underline;text-decoration-color:var(--ambar);text-underline-offset:4px}
.pie .correo{word-break:break-all}
.pie .base{margin-top:calc(var(--ritmo)*7);padding-top:24px;border-top:1px solid #ddd5c8;color:var(--apoyo);font-size:.88rem}

/* CTA fija en móvil: solo al subir, pasado el hero y fuera de contacto */
.cta-movil{display:none}
@media (max-width:760px){
 .js .cta-movil{display:flex;justify-content:center;position:fixed;left:16px;right:16px;bottom:16px;z-index:40;
  box-shadow:0 16px 32px -12px rgba(17,17,17,.55);transform:translateY(140%);visibility:hidden;transition:transform .3s ease,visibility 0s linear .3s}
 .js .cta-movil.visible{transform:none;visibility:visible;transition:transform .3s ease}
 .js body.con-cta .pie{padding-bottom:110px}
}
/* Páginas legales y 404 */
.legal{padding:calc(var(--ritmo)*10) 0 calc(var(--ritmo)*12)}
.legal .contenedor{max-width:820px}
.legal h1{font-size:clamp(2.2rem,5vw,3.4rem);margin-bottom:12px}
.legal .fecha{color:var(--apoyo);font-size:.95rem;margin-bottom:48px}
.legal h2{font-size:1.5rem;margin:44px 0 14px}
.legal p,.legal li{color:var(--texto);max-width:68ch}
.legal p+p{margin-top:12px}
.legal ul{padding-left:22px;margin:12px 0 0}.legal li+li{margin-top:10px}
.legal dl{display:grid;grid-template-columns:minmax(0,180px) minmax(0,1fr);gap:10px 24px;margin:0;padding:24px;background:var(--crema)}
.legal dt{font-weight:700}.legal dd{margin:0}
.legal a:not(.btn){color:var(--negro);text-decoration-color:var(--ambar);text-underline-offset:3px}
.legal .tabla{overflow-x:auto;margin-top:16px;border:1px solid var(--linea)}
.legal table{border-collapse:collapse;width:100%;min-width:560px;font-size:.95rem}
.legal th,.legal td{text-align:left;vertical-align:top;padding:12px 14px;border-bottom:1px solid var(--linea)}
.legal th{background:var(--crema);font-weight:700}.legal tbody tr:last-child td{border-bottom:0}
.pendiente{background:#fef3c7;color:#7c2d12;padding:1px 6px;border:1px dashed #b45309;font-weight:600}
.no-encontrada .contenedor{text-align:center}
.simbolo-404 .ico{width:88px;height:88px;padding:22px;margin:0 auto 24px;background:var(--crema);stroke-width:1.5}
.no-encontrada .subtitulo{margin:16px auto 32px;color:var(--apoyo);font-size:1.15rem;max-width:32em}

/* Aparición al hacer scroll: solo desplazamiento (nada queda invisible si falla el JS) */
.js .revela{transform:translateY(28px);transition:transform .7s cubic-bezier(.2,.7,.2,1)}
.js .revela.visto{transform:none}

@media (max-width:1000px){
 .hero .reticula{min-height:0}
 .hero-texto,.hero-visual{grid-column:1/-1}
 .hero-visual{width:100%;max-width:560px}
 .tarjeta{grid-column:span 6}.tarjeta.cta{grid-column:span 12}
 .mision .frase,.mision .lado{grid-column:1/-1}
 .caso .titular,.puntos{grid-column:1/-1}.ticket{grid-column:1/-1;grid-row:auto;max-width:560px}
 .compromisos{grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:none;row-gap:40px}
 .compromisos li{grid-row:auto;grid-template-rows:none}
 .faq .titular,.faq .lista{grid-column:1/-1}
 .contacto .titular,.contacto .accion{grid-column:1/-1}
 .pie .col-marca{grid-column:1/-1}.pie nav,.pie .col{grid-column:span 4}.pie .col-contacto{grid-column:span 4}
}
@media (max-width:900px){
 .menu-boton{display:inline-flex}
 .cab .cab-cta{display:none}
 .js .menu{display:none;position:absolute;top:100%;left:0;right:0;background:var(--blanco);border-bottom:1px solid var(--linea);
  box-shadow:0 24px 32px -24px rgba(17,17,17,.35);padding:8px var(--gutter) 24px}
 .js .menu.abierto{display:block}
 .js .menu ul{flex-direction:column;align-items:stretch;gap:0}
 .js .menu li a{display:block;padding:14px 8px;border-bottom:1px solid var(--linea);font-size:1.05rem}
 .js .menu a:focus-visible{outline-offset:-2px;box-shadow:inset 0 0 0 5px var(--ambar2)}
 .js .menu .solo-movil{display:block;margin-top:20px}
 .js .menu .solo-movil a{display:flex;justify-content:center;border:2px solid var(--negro);color:var(--blanco)}
 html:not(.js) .menu-boton{display:none}
 html:not(.js) .cab .contenedor{height:auto;flex-wrap:wrap;padding-top:12px;padding-bottom:12px}
 html:not(.js) .menu ul{flex-wrap:wrap;gap:8px 20px}
}
@media (max-width:760px){
 :root{--gutter:16px;--cab:64px}
 body{font-size:16px}
 .bloque{padding:calc(var(--ritmo)*7) 0}
 .titular{margin-bottom:calc(var(--ritmo)*4)}
 .titular p{font-size:1.05rem}
 .hero .reticula{padding-block:calc(var(--ritmo)*6) calc(var(--ritmo)*6);row-gap:32px}
 .acciones{margin-top:calc(var(--ritmo)*4)}
 .escena{padding:20px 16px 16px;border-radius:16px}
 .tarjeta,.tarjeta.cta{grid-column:1/-1}
 .tarjeta .cuerpo{padding:20px 20px 22px}
 .ilus{height:104px}
 .vinetas{gap:4px;padding-top:12px;font-size:.92rem}
 .compromisos li{grid-template-columns:44px minmax(0,1fr);column-gap:14px;padding-top:18px}
 .compromisos .ico{grid-row:1/span 2;margin:0}
 .compromisos h3{align-self:center;margin:0 0 4px}
 .mision .reticula{row-gap:16px}
 .puntos{gap:18px}
 .estados li{padding-bottom:14px}
 .tarjeta.cta .cuerpo{padding:28px 20px}
 .flujo{padding:20px 14px 18px;margin:0 calc(var(--gutter)*-1);border-left:0;border-right:0}
 .compromisos{grid-template-columns:1fr;row-gap:28px}
 .equipo{grid-template-columns:1fr;row-gap:28px}
 .equipo li{grid-template-columns:72px minmax(0,1fr);grid-template-areas:"foto nombre" "foto rol" "frase frase";column-gap:16px}
 .equipo .retrato{width:72px;height:72px}
 .equipo p{margin-top:8px;max-width:none}
 .cierre{margin-top:calc(var(--ritmo)*6)}
 .pie nav,.pie .col,.pie .col-contacto{grid-column:span 6}.pie .col-contacto{grid-column:1/-1}
 .legal dl{grid-template-columns:1fr;gap:4px}.legal dd{margin-bottom:12px}
 .logotipo{height:22px}
}
@media (max-width:480px){
 .hero-equipo{gap:8px;margin-bottom:16px}
 .hero-equipo .retrato{width:56px;height:56px}
 .hero-equipo .nombre{display:none}
 .hero-equipo-pie{display:block}
 .tarjeta .imagen{display:none}
 .tarjeta .cuerpo{padding-top:22px;border-top:3px solid var(--ambar)}
 .pasos li{grid-template-columns:60px minmax(0,1fr);padding-bottom:16px}
 .nodo{width:60px;height:60px}.nodo .ico{width:28px;height:28px}
 .pasos li:not(:last-child)::after{left:29px;top:64px}
 .conector::before{margin-left:28px}
 .flujo-aprueba{margin-bottom:18px}
 .logotipo{height:20px}
}
@media (prefers-reduced-motion:reduce){
 html{scroll-behavior:auto}
 *,*::before,*::after{animation:none!important;transition:none!important}
 .js .revela{transform:none}
}
@media print{
 .revela{opacity:1!important;transform:none!important}
 .cab,.cta-movil,.menu-boton,.copiar{display:none!important}
 .hero,.contacto,.tarjeta.cta{background:#fff!important;color:#000!important}
}
"""

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
 addEventListener('beforeprint',todo);
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


def pie(base, inicio, raiz):
    nav = "".join(f'<li><a href="{base}#{i}">{t}</a></li>' for i, t in NAV)
    legales = "".join(f'<li><a href="{raiz}{h}">{t}</a></li>' for h, t in LEGALES)
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


JSON_LD = json.dumps({
    "@context": "https://schema.org", "@type": "ProfessionalService", "name": "th3b1gbr0th3r IT", "url": URL_BASE,
    "image": URL_BASE + "og.png", "logo": URL_BASE + "apple-touch-icon.png",
    "description": "Software a medida para pequeñas empresas: webs, herramientas de gestión, reservas y citas, automatización, mantenimiento y soporte.",
    "areaServed": {"@type": "Country", "name": "España"}, "knowsLanguage": "es",
}, ensure_ascii=False)


def pagina(titulo, descripcion, cuerpo, ruta, base="index.html", raiz="", indexar=True, extra_head=""):
    """ruta: nombre publicado (para og:url). raiz: "" (rutas relativas) o "/" (404: rutas desde la raíz del dominio)."""
    cuerpo = sin_viudas(cuerpo)
    inicio = raiz or "index.html"
    css = CSS.replace("@RAIZ@", raiz).replace("@NORMAL@", FUENTE_NORMAL).replace("@CURSIVA@", FUENTE_CURSIVA)
    url = URL_BASE + ("" if ruta == "index.html" else ruta)
    robots = "" if indexar else '<meta name="robots" content="noindex">\n'
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
{robots}<meta name="theme-color" content="#111111">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="th3b1gbr0th3r IT">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{URL_BASE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Logotipo de th3b1gbr0th3r IT junto al lema «Software a la medida de tu negocio».">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titulo}">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="{URL_BASE}og.png">
<link rel="icon" href="{raiz}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{raiz}apple-touch-icon.png">
<link rel="preload" href="{raiz}fuentes/{FUENTE_NORMAL}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{raiz}fuentes/{FUENTE_CURSIVA}" as="font" type="font/woff2" crossorigin>
{extra_head}<style>{css}</style>
<script>{JS}</script>
</head>
<body>
{logotipo.definicion()}
{cabecera(base, inicio)}
<main id="principal">
{cuerpo}
</main>
{pie(base, inicio, raiz)}
</body>
</html>
"""


# ── Página principal ─────────────────────────────────────────────────────────
hero_equipo = "".join(f'<li>{retrato(c)}<span class="nombre" aria-hidden="true">{c["nombre"]}</span></li>' for c in EQUIPO)
mini_pasos = "".join(
    f'<li class="{"hecho" if i < CASO_ACTUAL else "actual" if i == CASO_ACTUAL else ""}"'
    f'{" aria-current=\"step\"" if i == CASO_ACTUAL else ""}>{corto}'
    f'<span class="sr">{": hecho" if i < CASO_ACTUAL else ": en curso" if i == CASO_ACTUAL else ": pendiente"}</span></li>'
    for i, (_, corto, _) in enumerate(CASO_ESTADOS)).replace(' class=""', "")

tarjetas = "".join(
    f'<article class="tarjeta revela"><div class="imagen">{ILUS[i]}</div><div class="cuerpo"><h3>{t}</h3><p>{d}</p>'
    f'<ul class="vinetas">{"".join(f"<li>{x}</li>" for x in v)}</ul></div></article>'
    for i, t, d, v in SERVICIOS) + (
    '<article class="tarjeta cta oscuro revela"><div class="cuerpo"><h3>¿Necesitas otra solución?</h3>'
    '<p>Analizamos tu caso y te proponemos la solución más adecuada.</p>'
    '<a class="mas" href="#contacto">Consúltanos <span aria-hidden="true">→</span></a></div></article>')


def _nodo(x):
    return f'<span class="nodo">{icono(x)}</span>'


pasos = "".join(f'<li>{_nodo(x)}<span><b class="paso-t">{t}</b><span class="paso-d">{d}</span></span></li>' for x, t, d in FLUJO_PASOS)
carril = "".join(f'<li><span class="chip">{icono(i)}<span>{t}</span></span></li>' for i, t in CARRIL)
FLUJO = f"""<figure class="flujo revela" aria-labelledby="titulo-dentro">
   <div class="flujo-fila"><p class="flujo-aprueba">{icono("persona")}<span>Jordi revisa y aprueba las decisiones importantes</span></p></div>
   <ol class="pasos">{pasos}</ol>
   <div class="flujo-fila"><p class="conector">Sobre la infraestructura de cada cliente</p></div>
   <div class="carriles">
    <div class="carril"><p class="carril-cab"><b>Tu empresa</b><span>Entorno propio</span></p><ol class="carril-pasos">{carril}</ol></div>
    <p class="capa">Empresa B · entorno propio</p>
    <p class="capa">Empresa C · entorno propio</p>
   </div>
   <p class="flujo-nota">{icono("candado")}<span>El código, los datos y las credenciales de cada cliente están siempre separados.</span></p>
  </figure>"""

compromisos = "".join(f'<li class="revela">{icono(i)}<h3>{t}</h3><p>{d}</p></li>' for i, t, d in COMPROMISOS)
equipo = "".join(f'<li class="revela">{retrato(c)}<h3>{c["nombre"]}</h3><span class="rol">{c["rol"]}</span><p>{c["frase"]}</p></li>' for c in EQUIPO)
faq = "".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
puntos = "".join(f'<li class="revela">{icono(i)}<div><h3>{t}</h3><p>{d}</p></div></li>' for i, t, d in CASO_PUNTOS)
estados = "".join(
    f'<li class="{"hecho" if i < CASO_ACTUAL else "actual" if i == CASO_ACTUAL else "falta"}"'
    f'{" aria-current=\"step\"" if i == CASO_ACTUAL else ""}><span class="punto" aria-hidden="true"></span>'
    f'<b>{e}<span class="sr">{": hecho" if i < CASO_ACTUAL else ": en curso" if i == CASO_ACTUAL else ": pendiente"}</span></b><span class="txt">{d}</span></li>'
    for i, (e, _, d) in enumerate(CASO_ESTADOS))
ESTADO_ACTUAL = CASO_ESTADOS[CASO_ACTUAL][0]

INDEX = f"""<section class="hero oscuro" aria-labelledby="titulo-hero">
 <div class="contenedor reticula">
  <div class="hero-texto">
   <span class="sobre">Desarrollo y mantenimiento para pequeñas empresas</span>
   <h1 id="titulo-hero">Software a la medida <em>de tu negocio.</em></h1>
   <p class="apoyo">Desarrollamos y mantenemos webs y herramientas de gestión a medida, con un responsable único y un proceso trazable de principio a fin.</p>
   <div class="acciones"><a class="btn claro" href="#contacto">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a></div>
  </div>
  <div class="hero-visual">
   <div class="escena">
    <ul class="hero-equipo" aria-label="El equipo: Jordi, responsable, y los agentes de IA de Coordinación, Desarrollo y Operación">{hero_equipo}</ul>
    <p class="hero-equipo-pie" aria-hidden="true">Jordi y los agentes de Coordinación, Desarrollo y Operación</p>
    <figure class="mini" aria-label="Ejemplo de un cambio en nuestra hoja de cambios">
     <div class="mini-cab"><span>Hoja de cambios</span><span class="etiqueta">Ejemplo</span></div>
     <p class="mini-titulo">{CASO_TITULO_HTML}</p>
     <ol class="mini-pasos">{mini_pasos}</ol>
     <p class="mini-pie">Estado: <b>{ESTADO_ACTUAL}</b> · <a href="#caso">Ver el caso completo</a></p>
    </figure>
   </div>
  </div>
 </div>
</section>

<section class="bloque" id="servicios" aria-labelledby="titulo-servicios">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Servicios</span><h2 id="titulo-servicios">Tecnología adaptada a tu forma de trabajar.</h2>
   <p>Desde la web hasta las herramientas internas de gestión: soluciones diseñadas a partir de tus procesos, no de una plantilla.</p></div>
  <div class="tarjetas">{tarjetas}</div>
 </div>
</section>

<section class="bloque alterno mision" id="mision" aria-labelledby="titulo-mision">
 <div class="contenedor">
  <span class="sobre">Enfoque</span>
  <div class="reticula">
   <h2 class="frase revela" id="titulo-mision">Tecnología al servicio de tu negocio, <em>no al revés.</em></h2>
   <p class="lado revela">Analizamos cómo trabaja tu empresa y desarrollamos solo lo que aporta valor, sin funciones innecesarias.</p>
  </div>
 </div>
</section>

<section class="bloque" id="por-dentro" aria-labelledby="titulo-dentro">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Método de trabajo</span><h2 id="titulo-dentro">Un proceso trazable y un entorno aislado para cada cliente.</h2>
   <p>Así avanza cada petición de cambio, desde que la recibimos hasta que está en funcionamiento. Cada cliente dispone de su propio repositorio, pruebas, copias de seguridad y servidor: nada se comparte entre clientes.</p></div>
  {FLUJO}
 </div>
</section>

<section class="bloque alterno caso" id="caso" aria-labelledby="titulo-caso">
 <div class="contenedor">
  <div class="reticula">
   <div class="titular"><span class="sobre">Caso de éxito</span><h2 id="titulo-caso">Esta web, gestionada con nuestro método.</h2>
    <p>Gestionamos nuestra propia web como un cliente más, con el mismo proceso que aplicamos a cada proyecto.</p></div>
   <ul class="puntos">{puntos}</ul>
   <article class="ticket revela" aria-labelledby="titulo-ticket">
    <div class="ticket-cab"><span>Hoja de cambios · Web corporativa</span><span class="etiqueta">Ejemplo</span></div>
    <div class="ticket-cuerpo">
     <h3 id="titulo-ticket">{CASO_TITULO_HTML}</h3>
     <p class="que">Explicar cómo avanza una petición de cambio en el entorno propio de cada cliente.</p>
     <ol class="estados">{estados}</ol>
    </div>
    <div class="ticket-pie"><span>Estado: <b>{ESTADO_ACTUAL}</b></span><span>Probado antes de publicar</span></div>
   </article>
  </div>
  <div class="cierre revela"><p>Aplicamos este mismo método a cada proyecto.</p>
   <a class="btn" href="#contacto">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a></div>
 </div>
</section>

<section class="bloque" id="compromisos" aria-labelledby="titulo-compromisos">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Compromisos</span><h2 id="titulo-compromisos">Lo que puedes esperar de nosotros.</h2>
   <p>Principios que aplicamos en cada proyecto, sin excepciones.</p></div>
  <ul class="compromisos">{compromisos}</ul>
 </div>
</section>

<section class="bloque alterno" id="equipo" aria-labelledby="titulo-equipo">
 <div class="contenedor">
  <div class="titular"><span class="sobre">Equipo</span><h2 id="titulo-equipo">Un responsable humano, apoyado por agentes de IA.</h2>
   <p>Jordi dirige cada proyecto y toma las decisiones. Los agentes de IA se encargan de la coordinación, el desarrollo y la operación, y se identifican siempre como tales.</p></div>
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
   <p>Cuéntanos qué necesitas y te propondremos la mejor forma de abordarlo. La primera conversación no implica ningún compromiso.</p></div>
  <div class="accion">
   <a class="btn claro" href="{MAILTO}">Escríbenos <span aria-hidden="true">→</span></a>
   <p class="correo-fila"><a class="correo" href="{MAILTO}">{MAIL}</a><button class="copiar" type="button" data-copiar="{MAIL}" hidden>Copiar dirección</button></p>
   <p class="aviso-copia" id="aviso-copia" aria-live="polite"></p>
   <p class="firma">{icono("persona")}<span>Jordi atiende personalmente cada mensaje.</span></p>
   <p class="privacidad-linea">Esta web no utiliza <a href="cookies.html">cookies ni analítica</a>. Con tus datos aplicamos el mismo criterio.</p>
  </div>
 </div>
</section>
<a class="cta-movil btn claro" href="#contacto" aria-hidden="true" tabindex="-1">Cuéntanos tu proyecto <span aria-hidden="true">→</span></a>"""

TITULO_INDEX = "Software a medida para pequeñas empresas · th3b1gbr0th3r IT"
DESC_INDEX = ("Software a medida para pequeñas empresas en España: webs, herramientas de gestión, reservas y citas, "
              "automatización, mantenimiento y soporte. Un responsable único y un proceso trazable, con el apoyo de agentes de IA.")
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
<p>Los textos, diseños, ilustraciones, logotipos y el código de esta web pertenecen a su titular o se usan con autorización o con licencia. Las tipografías se usan bajo su licencia libre (SIL Open Font License): la tipografía Source Serif 4, de Adobe, se distribuye con el texto de esa licencia en <a href="fuentes/OFL.txt">fuentes/OFL.txt</a>. No se permite reproducir, distribuir, comunicar públicamente ni transformar los contenidos sin permiso previo y por escrito, salvo para uso personal y privado. «th3b1gbr0th3r IT» es un nombre comercial.</p>
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

PAGINAS_LEGALES = {
    "aviso-legal.html": ("Aviso legal · th3b1gbr0th3r IT", "Aviso legal de la web de th3b1gbr0th3r IT: datos del titular y condiciones de uso.", AVISO),
    "privacidad.html": ("Política de privacidad · th3b1gbr0th3r IT", "Qué datos personales tratamos, para qué, con qué proveedores y cuáles son tus derechos.", PRIVACIDAD),
    "cookies.html": ("Política de cookies · th3b1gbr0th3r IT", "Esta web no usa cookies ni rastreadores.", COOKIES),
}

# 404: GitHub Pages la sirve en cualquier ruta inexistente, así que todo va desde la raíz del dominio.
NO_ENCONTRADA = pagina("Página no encontrada · th3b1gbr0th3r IT", "La página que buscas no existe.", f"""<section class="legal no-encontrada">
 <div class="contenedor">
  <div class="simbolo-404">{icono("lupa")}</div>
  <span class="sobre">Error 404</span>
  <h1>Página no encontrada</h1>
  <p class="subtitulo">La dirección que has abierto no existe o ha cambiado. Desde la página de inicio encontrarás nuestros servicios y la forma de contactar con nosotros.</p>
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
        (SITIO / nombre).write_text(pagina(titulo, desc, cuerpo, nombre), encoding="utf-8")
    (SITIO / "favicon.svg").write_text(MONOGRAMA.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    (SITIO / "fuentes").mkdir()
    for f in (FUENTE_NORMAL, FUENTE_CURSIVA, "OFL.txt"):
        shutil.copy2(FUENTES / f, SITIO / "fuentes" / f)
    for f in ("og.png", "apple-touch-icon.png"):
        shutil.copy2(RECURSOS / f, SITIO / f)
    (SITIO / ".nojekyll").write_text("", encoding="utf-8")
    (SITIO / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {URL_BASE}sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{URL_BASE}{'' if n == 'index.html' else n}</loc></url>" for n in ["index.html", *PAGINAS_LEGALES])
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


def _chrome(destino, tam, url, perfil, movimiento=False):
    args = ["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--no-proxy-server",
            f"--user-data-dir={perfil}", "--virtual-time-budget=4000", f"--screenshot={destino}", f"--window-size={tam}", url]
    if not movimiento:
        args.insert(5, "--force-prefers-reduced-motion")
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


def capturas():
    CAPTURAS.mkdir(exist_ok=True)
    extra = {
        # Menú móvil abierto con teclado (click() sin ratón: el foco va al primer enlace).
        "/_captura/menu.html": html.replace("</body>", "<script>addEventListener('load',()=>document.querySelector('.menu-boton').click())</script></body>"),
        # CTA fija en móvil tal como aparece al subir a media página.
        "/_captura/cta.html": html.replace("</head>", "<style>main>section:nth-of-type(-n+4){display:none}"
                                                      ".js .cta-movil{visibility:visible!important;transform:none!important}</style></head>"),
        # Solo el diagrama del flujo (imagen para redes, capturas/flujo.png).
        "/_captura/flujo.html": html.replace("</head>", "<style>.cab,.pie,.cta-movil,main>section:not(#por-dentro){display:none!important}"
                                                        "#por-dentro{padding:40px 0}#por-dentro .titular{margin-bottom:28px}</style></head>"),
    }
    trabajos = [("escritorio", "1440,12000", "/", True), ("tableta-1024", "1024,14000", "/", True), ("tableta-820", "820,15000", "/", True),
                ("movil-390", "390,20000", "/", True), ("movil-360", "360,21000", "/", True),
                ("movil-menu", "390,760", "/_captura/menu.html", False), ("movil-cta", "390,844", "/_captura/cta.html", False),
                ("flujo", "1240,1300", "/_captura/flujo.html", True),
                ("legal-privacidad-movil", "390,5200", "/privacidad.html", True),
                ("404", "1440,900", "/una/ruta/que/no-existe", False), ("404-movil", "360,780", "/otra/que/tampoco", False)]
    trabajos += [(f"legal-{n.removesuffix('.html')}", "1440,3200", f"/{n}", True) for n in PAGINAS_LEGALES]
    srv, url = servidor(extra)
    try:
        with tempfile.TemporaryDirectory(dir=base_temporal()) as tmp:
            for i, (nombre, tam, ruta, recortar) in enumerate(trabajos):
                destino = CAPTURAS / f"{nombre}.png"
                _chrome(destino, tam, url + ruta, Path(tmp) / f"perfil{i}")
                if recortar:
                    _recortar(destino)
    finally:
        srv.shutdown()
    for f in ("og.png", "apple-touch-icon.png"):
        shutil.copy2(RECURSOS / f, CAPTURAS / f)
    print(f"Capturas: {CAPTURAS}")


def imagenes():
    """Regenera recursos/og.png (1200×630) y recursos/apple-touch-icon.png (180×180) con Chrome headless."""
    from PIL import Image
    fuente = (FUENTES / FUENTE_NORMAL).as_uri()
    cursiva = (FUENTES / FUENTE_CURSIVA).as_uri()
    caras = (f'@font-face{{font-family:S;src:url({fuente})}}@font-face{{font-family:S;font-style:italic;src:url({cursiva})}}'
             'html,body{margin:0}')
    og = f"""<!doctype html><meta charset="utf-8"><style>{caras}
body{{width:1200px;height:630px;background:#111;color:#fdf6ec;font-family:S,serif;box-sizing:border-box;padding:88px 96px;overflow:hidden;position:relative}}
.logotipo{{height:46px;width:auto;color:#fdf6ec;display:block}}.logo-it{{fill:#f59e0b}}
.raya{{width:120px;height:4px;background:#d97706;margin:44px 0 36px}}
h1{{font-weight:400;font-size:84px;line-height:1.02;margin:0 0 28px;letter-spacing:-.02em}}h1 em{{color:#f59e0b}}
p{{font:600 28px system-ui,sans-serif;color:#d6d3d1;margin:0}}
.pasos{{position:absolute;right:96px;bottom:88px;display:flex;align-items:center}}
.pasos i{{width:22px;height:22px;border-radius:50%;border:3px solid #d97706;box-sizing:border-box}}
.pasos i.ok{{background:#f59e0b;border-color:#f59e0b}}
.pasos b{{width:56px;border-top:3px dashed #d97706}}
</style>
<body>{LOGOTIPO}<div class="raya"></div><h1>Software a la medida<br><em>de tu negocio.</em></h1>
<p>Desarrollo y mantenimiento para pequeñas empresas</p>
<div class="pasos"><i class="ok"></i><b></b><i class="ok"></i><b></b><i class="ok"></i><b></b><i class="ok"></i><b></b><i></i></div></body>"""
    cuadrado = MONOGRAMA.replace('rx="24"', 'rx="0"')  # iOS ya redondea las esquinas
    icono_html = (f'<!doctype html><meta charset="utf-8"><style>{caras}body{{width:720px;height:720px;background:#111;display:grid;place-items:center;overflow:hidden}}'
                  f'svg{{width:720px;height:720px}}</style><body>{cuadrado}</body>')
    with tempfile.TemporaryDirectory(dir=base_temporal()) as tmp:
        for nombre, contenido, tam, final in (("og", og, "1200,630", (1200, 630)), ("icono", icono_html, "720,720", (180, 180))):
            pagina_tmp = Path(tmp) / f"{nombre}.html"
            pagina_tmp.write_text(contenido, encoding="utf-8")
            png = Path(tmp) / f"{nombre}.png"
            _chrome(png, tam, pagina_tmp.as_uri(), Path(tmp) / f"perfil-{nombre}")
            im = Image.open(png).convert("RGB")
            im = im.crop((0, 0, *[int(v) for v in tam.split(",")])) if im.size != final and nombre == "og" else im
            im = im.resize(final, Image.LANCZOS) if im.size != final else im
            destino = RECURSOS / ("og.png" if nombre == "og" else "apple-touch-icon.png")
            im.save(destino, optimize=True)
            print(f"{destino} {im.size}")


if __name__ == "__main__":
    if "--imagenes" in sys.argv:
        RECURSOS.mkdir(exist_ok=True)
        imagenes()
    construir()
    if "--capturas" in sys.argv:
        capturas()
