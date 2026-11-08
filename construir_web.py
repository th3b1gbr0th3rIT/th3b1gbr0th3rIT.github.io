#!/usr/bin/env python3
"""Genera la web pública estática de th3b1gbr0th3r IT en sitio/ (GitHub Pages).

Sin cifras, sin precios, sin clientes nombrados: profesionalidad y cercanía.
Sin recursos externos (ni fuentes, ni analítica, ni cookies).
Uso: python3 construir_web.py [--capturas]
Solo usa la biblioteca estándar de Python 3 (funciona tal cual en un runner de GitHub).
Las capturas (opcionales) necesitan google-chrome y se guardan en capturas/.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrama_flujo import flujo_ancho, flujo_vertical  # noqa: E402

HERE = Path(__file__).resolve().parent
SITIO = HERE / "sitio"
CAPTURAS = HERE / "capturas"
MAIL = "jordi.gonzalez.roig@gmail.com"
ASUNTO = "Quiero%20hablar%20de%20mi%20negocio"
MAILTO = f"mailto:{MAIL}?subject={ASUNTO}"

# ── La manada (mismos gatos que docs/marca/generar_marca.py) ─────────────────
EQUIPO = [
    dict(nombre="Jordi", rol="CTO · el responsable", cuerpo="#111111", interior="#3b2f2f", ojos="#f59e0b", pecho=None, extra="corona",
         frase="Escucha tu negocio, decide lo importante y responde ante ti de todo lo que hacemos."),
    dict(nombre="Coordinación", rol="agente de IA", cuerpo="#e07b24", interior="#f2b07a", ojos="#2f855a", pecho="#fde7cf", extra="rayas",
         frase="Ordena prioridades y te cuenta cada avance con palabras claras. No se le escapa ni un correo."),
    dict(nombre="Desarrollo", rol="agente de IA", cuerpo="#7b8794", interior="#b8c1cc", ojos="#38bdf8", pecho="#d9dee4", extra="gafas",
         frase="Construye cada mejora y la prueba a fondo antes de que llegue a tus manos."),
    dict(nombre="Operación", rol="agente de IA", cuerpo="#f4f1ea", interior="#f3c1c1", ojos="#3b82f6", pecho=None, extra="manchas",
         frase="Copias de seguridad, publicaciones y vigilancia nocturna. Ve en la oscuridad: es un gato."),
]


def gato(c, cls=""):
    t = ' stroke="#cbd5e1" stroke-width="6"' if c["cuerpo"] == "#f4f1ea" else ""
    p = [
        f'<path class="cola" d="M330 420 C 420 410, 440 330, 400 290 C 380 270, 360 285, 372 300 C 395 330, 380 385, 320 392 Z" fill="{c["cuerpo"]}"{t}/>',
        f'<path d="M170 430 C 150 360, 165 290, 215 255 L 300 255 C 350 290, 365 360, 345 430 Z" fill="{c["cuerpo"]}"{t}/>',
        f'<path d="M182 168 L 176 88 L 236 140 Z" fill="{c["cuerpo"]}"{t}/>',
        f'<path d="M330 168 L 336 88 L 276 140 Z" fill="{c["cuerpo"]}"{t}/>',
        f'<ellipse cx="256" cy="205" rx="88" ry="78" fill="{c["cuerpo"]}"{t}/>',
        f'<path d="M190 150 L 187 108 L 220 137 Z" fill="{c["interior"]}"/>',
        f'<path d="M322 150 L 325 108 L 292 137 Z" fill="{c["interior"]}"/>',
    ]
    if c["pecho"]:
        p.append(f'<path d="M225 300 C 235 360, 278 360, 288 300 C 270 320, 243 320, 225 300 Z" fill="{c["pecho"]}"/>')
    if c["extra"] == "rayas":
        p += [f'<path d="M{a} 140 q 6 22 0 40" stroke="#a24f10" stroke-width="9" fill="none" stroke-linecap="round"/>' for a in (240, 256, 272)]
        p += [f'<path d="M{a} 330 q 18 6 34 0" stroke="#a24f10" stroke-width="9" fill="none" stroke-linecap="round"/>' for a in (180, 300)]
    if c["extra"] == "manchas":
        p += ['<ellipse cx="300" cy="170" rx="34" ry="26" fill="#111111"/>', '<ellipse cx="200" cy="360" rx="30" ry="40" fill="#111111"/>',
              '<ellipse cx="380" cy="300" rx="16" ry="20" fill="#111111"/>']
    p.append(f'<g class="ojos"><ellipse cx="224" cy="205" rx="20" ry="16" fill="{c["ojos"]}"/><ellipse cx="288" cy="205" rx="20" ry="16" fill="{c["ojos"]}"/>'
             '<ellipse cx="224" cy="205" rx="5" ry="13" fill="#111"/><ellipse cx="288" cy="205" rx="5" ry="13" fill="#111"/></g>')
    p += ['<path d="M248 232 L 264 232 L 256 242 Z" fill="#e8a0a0"/>',
          f'<ellipse cx="225" cy="430" rx="26" ry="12" fill="{c["cuerpo"]}"{t}/>', f'<ellipse cx="290" cy="430" rx="26" ry="12" fill="{c["cuerpo"]}"{t}/>']
    if c["extra"] == "gafas":
        p += ['<circle cx="224" cy="205" r="30" fill="none" stroke="#0f172a" stroke-width="8"/>',
              '<circle cx="288" cy="205" r="30" fill="none" stroke="#0f172a" stroke-width="8"/>',
              '<line x1="254" y1="205" x2="258" y2="205" stroke="#0f172a" stroke-width="8"/>']
    if c["extra"] == "corona":
        p.append('<path d="M206 118 L 216 78 L 236 104 L 256 70 L 276 104 L 296 78 L 306 118 Z" fill="#f59e0b" stroke="#b45309" stroke-width="4"/>')
    return f'<svg class="gato {cls}" viewBox="120 60 320 390" role="img" aria-label="Gato {c["nombre"]}">' + "".join(p) + "</svg>"


JEFE = EQUIPO[0]
HUELLA = ('<svg class="huella" viewBox="0 0 40 40" aria-hidden="true"><ellipse cx="20" cy="27" rx="9" ry="8"/>'
          '<ellipse cx="8" cy="16" rx="3.6" ry="5"/><ellipse cx="16" cy="9" rx="3.6" ry="5"/><ellipse cx="25" cy="9" rx="3.6" ry="5"/>'
          '<ellipse cx="33" cy="16" rx="3.6" ry="5"/></svg>')
ICONO_MARCA = ('<svg viewBox="0 0 110 110" aria-hidden="true"><circle cx="55" cy="55" r="55" fill="#fdf6ec"/>'
               '<g transform="scale(0.215)">' + gato(JEFE)[gato(JEFE).index('>') + 1:-6] + '</g></svg>')


def icono(nombre):
    d = {
        "web": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 8h18"/><path d="M7 21h10"/><circle cx="6" cy="6" r=".6"/>',
        "gestion": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
        "reservas": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/><path d="m9 15 2 2 4-4"/>',
        "auto": '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/><circle cx="12" cy="12" r="3.5"/>',
        "cuidado": '<path d="M12 3 5 6v6c0 4.5 3 7.7 7 9 4-1.3 7-4.5 7-9V6z"/><path d="m9 12 2 2 4-4"/>',
        "idea": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
        "persona": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
        "candado": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
        "copia": '<path d="M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z"/><path d="M4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
        "charla": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>',
    }[nombre]
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">{d}</svg>'


# ── Contenido ────────────────────────────────────────────────────────────────
SECTORES = ["Comercios", "Restaurantes", "Inmobiliarias", "Talleres", "Despachos profesionales", "Clínicas",
            "Academias", "Tiendas online", "Alojamientos", "Asociaciones"]

SUENA = [
    ("Tengo un Excel que solo entiendo yo.", "Lo convertimos en una herramienta que entiende todo tu equipo."),
    ("El programa que compré me obliga a trabajar a su manera.", "Hacemos el software al revés: primero, cómo trabajas tú."),
    ("Mi web es bonita, pero no me trae clientes.", "Una web pensada para que te escriban, te llamen y te reserven."),
    ("Cuando algo falla, no sé a quién llamar.", "Nos tienes a nosotros: un nombre, un correo y una respuesta."),
]

SERVICIOS = [
    ("web", "Webs que trabajan por ti", "Rápidas, claras, en los idiomas de tus clientes y fáciles de mantener al día. Tu escaparate abierto a todas horas.", "grande"),
    ("gestion", "Tu herramienta de gestión", "Clientes, pedidos, visitas o expedientes, organizados a tu manera. Cada persona ve lo suyo.", ""),
    ("reservas", "Reservas y citas", "Que tus clientes reserven solos y tú lo veas todo en un único sitio.", ""),
    ("auto", "Automatización", "Avisos, correos, informes, recordatorios… Lo repetitivo, que lo haga la máquina.", ""),
    ("cuidado", "Cuidado continuo", "Copias de seguridad, actualizaciones y vigilancia. Tú a lo tuyo; nosotros, a lo nuestro.", "oscuro"),
    ("idea", "¿Algo distinto?", "Si nos lo puedes explicar, lo podemos construir. Cuéntanoslo y lo vemos juntos.", "abierto"),
]

PASOS = [
    ("Un café y tu historia", "Nos cuentas cómo funciona tu negocio, qué te quita tiempo y qué te gustaría. Escuchamos más de lo que hablamos."),
    ("Una propuesta clara", "Qué vamos a hacer, en qué orden y qué podrás ver en cada paso. Sin letra pequeña ni tecnicismos."),
    ("Lo construimos contigo", "Por partes y enseñándote cada avance. Cada mejora se prueba antes de llegar a tus manos."),
    ("Lo cuidamos", "Copia de seguridad antes de cada cambio, vigilancia continua y un aviso cada vez que hay algo nuevo."),
]

PALABRA = [
    ("persona", "Hablas con el responsable", "Siempre sabes quién está detrás de tu proyecto y a quién escribir."),
    ("candado", "Tus datos son tuyos", "No los usamos para nada más ni los mezclamos con los de nadie."),
    ("copia", "Primero, la copia de seguridad", "Antes de tocar nada, lo guardamos todo. Si algo sale mal, volvemos atrás."),
    ("charla", "Te lo contamos todo", "Qué hemos hecho, qué puedes comprobar y qué falta. También cuando no es buena noticia."),
]

FAQ = [
    ("No sé nada de tecnología. ¿Es un problema?",
     "Al contrario. Tú sabes de tu negocio y nosotros traducimos. Te hablamos claro, sin jerga, y te enseñamos a usar todo lo que hagamos."),
    ("¿Esto no es solo para empresas grandes?",
     "Justo al revés: trabajamos para pequeñas empresas. Empezamos por lo que más te urge y crecemos contigo, paso a paso."),
    ("Ya tengo una web o un programa. ¿Hay que tirarlo?",
     "No necesariamente. Primero miramos lo que tienes; si sirve, lo mejoramos. Solo proponemos empezar de cero cuando de verdad compensa."),
    ("¿Quién hace el trabajo: personas o inteligencia artificial?",
     "Los dos. Los agentes de IA desarrollan, prueban y vigilan; Jordi revisa, decide y responde ante ti. Los agentes siempre se presentan como lo que son."),
    ("¿Cuánto cuesta?",
     "Depende de lo que necesites, y por eso preferimos escucharte antes de dar una cifra. Tras la primera charla tendrás una propuesta clara, sin compromiso."),
]

FLOTANTES = [("Tu web", "c1"), ("Reservas", "c2"), ("Tus clientes", "c3"), ("Sin papeles", "c4")]

# ── HTML ─────────────────────────────────────────────────────────────────────
marquee = "".join(f"<li>{s}</li>" for s in SECTORES)
suena = "".join(f'<article class="suena revela"><p class="queja">«{q}»</p><p class="respuesta">{r}</p></article>' for q, r in SUENA)
servicios = "".join(f'<article class="serv {cls} revela">{icono(i)}<h3>{t}</h3><p>{d}</p></article>' for i, t, d, cls in SERVICIOS)
pasos = "".join(f'<li class="revela"><span class="num">{n + 1}</span><h3>{t}</h3><p>{d}</p></li>' for n, (t, d) in enumerate(PASOS))
manada = "".join(
    f'<article class="miembro revela{" jefe" if c is JEFE else ""}"><div class="foto">{gato(c)}</div>'
    f'<h3>{c["nombre"]}</h3><p class="rol">{c["rol"]}</p><p>{c["frase"]}</p></article>' for c in EQUIPO)
palabra = "".join(f'<li class="revela">{icono(i)}<div><h3>{t}</h3><p>{d}</p></div></li>' for i, t, d in PALABRA)
faq = "".join(f'<details class="revela"><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
GATOS = [gato(c) for c in EQUIPO]
FLUJO_ANCHO, FLUJO_VERTICAL = flujo_ancho(GATOS), flujo_vertical(GATOS)
flotantes = "".join(f'<span class="chip {c}"><i></i>{t}</span>' for t, c in FLOTANTES)

CSS = r"""
:root{--negro:#111;--carbon:#1c1917;--ambar:#d97706;--ambar2:#f59e0b;--tostado:#b45309;--crema:#fdf6ec;--crema2:#fffaf3;
--borde:#f1e4cf;--tinta:#475569;--serif:"DejaVu Serif",Georgia,"Times New Roman",serif;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"DejaVu Sans",Helvetica,Arial,sans-serif;--radio:26px}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:80px}
body{margin:0;background:var(--crema2);color:var(--negro);font:17px/1.65 var(--sans);overflow-x:hidden;-webkit-font-smoothing:antialiased}
img,svg{max-width:100%}a{color:inherit}
h1,h2,h3{font-family:var(--serif);line-height:1.15;margin:0 0 .45em;letter-spacing:-.01em}
h2{font-size:clamp(1.8rem,4.2vw,2.8rem)}h3{font-size:1.2rem}
em{font-style:italic;color:var(--ambar)}
.contenedor{max-width:1120px;margin:0 auto;padding:0 20px}
section{padding:96px 0}
.sobre{display:inline-block;font:700 .78rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--tostado);margin-bottom:14px}
.cabecera{max-width:780px;margin:0 auto 48px;text-align:center}.cabecera p{color:var(--tinta);font-size:1.1rem;margin:0}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--negro);color:var(--crema);padding:15px 28px;border-radius:999px;
font-weight:700;text-decoration:none;transition:transform .2s,box-shadow .2s,background .2s;box-shadow:0 6px 0 var(--ambar)}
.btn:hover,.btn:focus-visible{transform:translateY(-3px);box-shadow:0 9px 0 var(--ambar)}
.btn .flecha{transition:transform .2s}.btn:hover .flecha{transform:translateX(4px)}
.btn.ambar{background:var(--ambar2);color:var(--negro);box-shadow:0 6px 0 var(--tostado)}
.enlace{font-weight:700;text-decoration:none;border-bottom:2px solid var(--ambar2);padding-bottom:2px}
:focus-visible{outline:3px solid var(--ambar2);outline-offset:3px;border-radius:6px}

/* Navegación */
.nav{position:sticky;top:0;z-index:50;background:rgba(255,250,243,.82);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
border-bottom:1px solid transparent;transition:border-color .3s}
.nav.scroll{border-color:var(--borde)}
.nav .contenedor{display:flex;align-items:center;justify-content:space-between;height:70px;gap:20px}
.marca{display:flex;align-items:center;gap:10px;text-decoration:none;font:700 1.15rem var(--serif)}
.marca span{white-space:nowrap}.marca svg{width:40px;height:40px;flex:none}.marca b{color:var(--ambar)}
.nav ul{display:flex;gap:28px;list-style:none;margin:0;padding:0}
.nav ul a{text-decoration:none;font-weight:600;font-size:.95rem;color:#334155}.nav ul a:hover{color:var(--ambar)}
.nav .btn{padding:10px 20px;font-size:.92rem;box-shadow:0 4px 0 var(--ambar)}

/* Hero */
.hero{position:relative;padding:72px 0 110px;overflow:hidden}
.hero::before{content:"";position:absolute;inset:-20% -10% auto auto;width:640px;height:640px;border-radius:50%;
background:radial-gradient(circle,rgba(245,158,11,.20),transparent 65%);pointer-events:none}
.hero .contenedor{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:40px;align-items:center}
.hero h1{font-size:clamp(2.4rem,5.4vw,4.1rem);margin-bottom:.35em}
.hero h1 .subrayado{position:relative;display:inline-block}
.hero h1 .subrayado svg{position:absolute;left:0;bottom:-.18em;width:100%;height:.35em;overflow:visible}
.hero h1 .subrayado path{fill:none;stroke:var(--ambar2);stroke-width:6;stroke-linecap:round;stroke-dasharray:420;stroke-dashoffset:420;animation:trazo 1.2s .5s ease-out forwards}
.hero .lead{font-size:1.2rem;color:var(--tinta);max-width:32em;margin:0 0 34px}
.acciones{display:flex;flex-wrap:wrap;align-items:center;gap:26px}
.confianza{display:flex;flex-wrap:wrap;gap:10px 24px;margin:38px 0 0;padding:0;list-style:none;color:var(--tinta);font-size:.95rem}
.confianza li{display:flex;align-items:center;gap:8px}.confianza li::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--ambar2)}
.escena{position:relative;aspect-ratio:1;max-width:440px;margin:0 auto;width:100%}
.circulo{position:absolute;inset:8%;border-radius:50%;background:var(--crema);box-shadow:inset 0 0 0 3px var(--borde)}
.anillo{position:absolute;inset:2%;border-radius:50%;border:2px dashed rgba(217,119,6,.45);animation:gira 60s linear infinite}
.escena .gato{position:absolute;inset:16% 18% 12%;width:64%;height:72%}
.chip{position:absolute;display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--borde);border-radius:14px;
padding:10px 16px;font-weight:700;font-size:.92rem;box-shadow:0 12px 30px -12px rgba(17,17,17,.25);animation:flota 6s ease-in-out infinite}
.chip i{width:10px;height:10px;border-radius:3px;background:var(--ambar2)}
.c1{top:6%;left:-4%}.c2{top:20%;right:-6%;animation-delay:-1.5s}.c2 i{background:#2f855a}
.c3{bottom:20%;left:-8%;animation-delay:-3s}.c3 i{background:#38bdf8}.c4{bottom:4%;right:0;animation-delay:-4.5s}.c4 i{background:#e07b24}

/* Gatos vivos */
.gato .ojos{transform-box:fill-box;transform-origin:center;animation:parpadeo 5s infinite}
.gato .cola{transform-box:fill-box;transform-origin:0% 100%;animation:cola 3.2s ease-in-out infinite}

/* Sectores */
.sectores{background:var(--negro);color:var(--crema);padding:22px 0;overflow:hidden;display:flex;align-items:center;gap:28px}
.sectores span{flex:none;padding-left:20px;font:italic 1rem var(--serif);color:var(--ambar2)}
.cinta{display:flex;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)}
.cinta ul{display:flex;flex:none;gap:0;margin:0;padding:0;list-style:none;animation:cinta 38s linear infinite}
.cinta li{padding:0 26px;font-weight:600;white-space:nowrap;position:relative}
.cinta li::after{content:"✦";position:absolute;right:-6px;color:var(--ambar)}

/* ¿Te suena? */
.rejilla-suena{display:grid;grid-template-columns:repeat(2,1fr);gap:22px}
.suena{background:#fff;border:1px solid var(--borde);border-radius:var(--radio);padding:30px 30px 26px;transition:transform .25s,box-shadow .25s}
.suena:hover{transform:translateY(-4px);box-shadow:0 22px 40px -24px rgba(17,17,17,.35)}
.queja{font:italic 1.3rem/1.4 var(--serif);margin:0 0 18px;color:#334155}
.respuesta{margin:0;padding-top:16px;border-top:2px dashed var(--borde);font-weight:600;display:flex;gap:10px}
.respuesta::before{content:"→";color:var(--ambar);font-weight:800}

/* Servicios */
.servicios{background:var(--crema)}
.bento{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.serv{background:#fff;border-radius:var(--radio);padding:30px;border:1px solid var(--borde);transition:transform .25s}
.serv:hover{transform:translateY(-4px)}
.serv p{margin:0;color:var(--tinta)}
.ico{width:44px;height:44px;padding:9px;border-radius:14px;background:var(--crema);fill:none;stroke:var(--tostado);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;margin-bottom:18px}
.serv.grande{grid-row:span 2;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(160deg,#fff 40%,#fef3c7);min-height:320px}
.serv.grande h3{font-size:1.7rem}.serv.grande .ico{width:56px;height:56px;margin-bottom:auto}
.serv.oscuro{background:var(--negro);color:var(--crema);border-color:var(--negro)}.serv.oscuro p{color:#cbd5e1}
.serv.oscuro .ico{background:#292524;stroke:var(--ambar2)}
.serv.abierto{background:transparent;border:2px dashed #e7cfa8;grid-column:1/-1;display:flex;align-items:center;gap:22px}
.serv.abierto .ico{margin:0;flex:none}.serv.abierto h3{margin:0;flex:none}

/* Proceso */
.pasos{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:26px;position:relative;counter-reset:p}
.pasos::before{content:"";position:absolute;top:27px;left:6%;right:6%;border-top:3px dotted #e7cfa8}
.pasos li{position:relative}
.num{display:grid;place-items:center;width:56px;height:56px;border-radius:50%;background:var(--negro);color:var(--ambar2);
font:700 1.35rem var(--serif);margin-bottom:20px;box-shadow:0 0 0 8px var(--crema2)}
.pasos p{color:var(--tinta);margin:0}

/* Por dentro: diagrama del flujo */
.por-dentro{padding-top:0}
.lienzo{background:#fff;border:1px solid var(--borde);border-radius:32px;padding:40px 36px 30px;box-shadow:0 30px 60px -40px rgba(17,17,17,.35)}
.flujo{display:block;width:100%;height:auto}.flujo-vertical{display:none}
.claves{display:flex;flex-wrap:wrap;justify-content:center;gap:12px 28px;list-style:none;margin:30px 0 0;padding:0;color:var(--tinta);font-size:.95rem}
.claves li::before{content:"✓ ";color:var(--ambar);font-weight:800}
@media (max-width:720px){.flujo-ancho{display:none}.flujo-vertical{display:block}.lienzo{padding:24px 16px}}

/* Manifiesto */
.manifiesto{background:var(--negro);color:var(--crema);text-align:center;position:relative;overflow:hidden}
.manifiesto blockquote{margin:0 auto;max-width:860px;font:400 clamp(1.7rem,4vw,2.9rem)/1.25 var(--serif)}
.manifiesto em{color:var(--ambar2)}
.manifiesto .firma{margin-top:28px;color:#a8a29e;font-size:1rem}
.manifiesto .huellas{position:absolute;inset:0;pointer-events:none;opacity:.10}
.huella{width:34px;fill:var(--ambar2);position:absolute}

/* Manada */
.equipo{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.miembro{background:#fff;border:1px solid var(--borde);border-radius:var(--radio);padding:26px 22px;text-align:center;transition:transform .25s,box-shadow .25s}
.miembro:hover{transform:translateY(-6px) rotate(-.6deg);box-shadow:0 26px 40px -26px rgba(17,17,17,.4)}
.foto{width:140px;height:140px;margin:0 auto 14px;border-radius:50%;background:var(--crema);display:grid;place-items:center;overflow:hidden}
.foto .gato{width:84%;height:84%;margin-top:14%}
.rol{display:inline-block;font-size:.8rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--tostado);
background:var(--crema);border-radius:999px;padding:4px 12px;margin:0 0 12px}
.miembro p:last-child{margin:0;color:var(--tinta);font-size:.96rem}
.miembro.jefe{background:var(--negro);color:var(--crema);border-color:var(--negro)}
.miembro.jefe .foto{background:var(--crema)}.miembro.jefe .rol{background:#292524;color:var(--ambar2)}.miembro.jefe p:last-child{color:#cbd5e1}

/* Nuestra palabra */
.palabra{background:var(--crema)}
.palabra .contenedor{display:grid;grid-template-columns:.9fr 1.1fr;gap:60px;align-items:start}
.palabra .cabecera{text-align:left;margin:0;position:sticky;top:110px}
.lista-palabra{list-style:none;margin:0;padding:0;display:grid;gap:16px}
.lista-palabra li{display:flex;gap:18px;background:#fff;border-radius:20px;padding:22px 24px;border:1px solid var(--borde)}
.lista-palabra .ico{flex:none;margin:0}.lista-palabra h3{margin-bottom:.2em}.lista-palabra p{margin:0;color:var(--tinta)}

/* FAQ */
.faq .contenedor{max-width:820px}
details{border-bottom:1px solid var(--borde);padding:6px 0}
summary{cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:18px 0;
font:700 1.15rem var(--serif)}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";flex:none;display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:var(--crema);
color:var(--tostado);font:400 1.5rem var(--sans);transition:transform .25s,background .25s}
details[open] summary::after{transform:rotate(45deg);background:var(--ambar2);color:var(--negro)}
details p{margin:0 0 20px;color:var(--tinta);max-width:44em}

/* Contacto */
.contacto{padding-top:40px}
.tarjeta-cta{position:relative;overflow:hidden;background:var(--negro);color:var(--crema);border-radius:36px;padding:72px 56px;
display:grid;grid-template-columns:1.3fr .7fr;gap:30px;align-items:center}
.tarjeta-cta::before{content:"";position:absolute;width:520px;height:520px;right:-140px;top:-160px;border-radius:50%;
background:radial-gradient(circle,rgba(245,158,11,.28),transparent 65%)}
.tarjeta-cta h2{color:var(--crema);font-size:clamp(2rem,4.6vw,3.2rem)}
.tarjeta-cta p{color:#d6d3d1;font-size:1.12rem;max-width:30em;margin:0 0 32px}
.tarjeta-cta .correo{display:block;margin-top:18px;color:#a8a29e;font-size:.95rem;word-break:break-all}
.asoma{position:relative;align-self:end;margin-bottom:-72px;height:260px}
.asoma .gato{position:absolute;bottom:-40px;left:50%;transform:translateX(-50%);width:240px;height:auto}

/* Pie */
footer{padding:56px 0 40px;color:var(--tinta);font-size:.92rem}
footer .contenedor{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:20px}
footer .lema{font:italic 1rem var(--serif);color:var(--tostado)}
footer p{margin:0}

/* Aparición al hacer scroll (solo con JS) */
.js .revela{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s ease}
.js .revela.visto{opacity:1;transform:none}

@keyframes trazo{to{stroke-dashoffset:0}}
@keyframes gira{to{transform:rotate(360deg)}}
@keyframes flota{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
@keyframes parpadeo{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes cola{0%,100%{transform:rotate(0)}50%{transform:rotate(7deg)}}
@keyframes cinta{to{transform:translateX(-100%)}}

@media (max-width:960px){
 .hero .contenedor,.palabra .contenedor,.tarjeta-cta{grid-template-columns:1fr}
 .escena{max-width:360px}.palabra .cabecera{position:static}
 .bento{grid-template-columns:1fr 1fr}.serv.abierto{flex-wrap:wrap}.serv.grande{grid-row:auto;grid-column:span 2;min-height:240px}
 .pasos{grid-template-columns:1fr 1fr}.pasos::before{display:none}
 .equipo{grid-template-columns:1fr 1fr}
 .asoma{height:200px;margin-bottom:-72px}.asoma .gato{width:190px}
}
@media (max-width:720px){
 .nav ul{display:none}.marca{font-size:1rem}.nav .btn{padding:9px 16px}section{padding:72px 0}.hero{padding:40px 0 80px}
 .rejilla-suena,.bento,.pasos{grid-template-columns:1fr}.serv.grande{grid-column:auto}.serv.abierto{display:block}.serv.abierto .ico{margin-bottom:18px}
 .tarjeta-cta{padding:52px 26px;border-radius:28px}
 .c1{left:0}.c2{right:0}.c3{left:0}
}
@media (max-width:480px){.equipo{grid-template-columns:1fr}.nav .btn span.largo{display:none}}
@media (prefers-reduced-motion:reduce){
 *,*::before,*::after{animation:none!important;transition:none!important}
 .hero h1 .subrayado path{stroke-dashoffset:0}.js .revela{opacity:1;transform:none}
}
"""

JS = r"""
document.documentElement.classList.add('js');
addEventListener('DOMContentLoaded',()=>{
 const nav=document.querySelector('.nav');
 const marca=()=>nav.classList.toggle('scroll',scrollY>10);marca();addEventListener('scroll',marca,{passive:true});
 const els=document.querySelectorAll('.revela');
 if(!('IntersectionObserver' in window)){els.forEach(e=>e.classList.add('visto'));return;}
 const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visto');io.unobserve(e.target);}}),{threshold:.12});
 els.forEach((e,i)=>{e.style.transitionDelay=(i%4)*80+'ms';io.observe(e);});
 document.getElementById('anio').textContent=new Date().getFullYear();
});
"""

huellas_fondo = "".join(
    HUELLA.replace('class="huella"', f'class="huella" style="left:{x}%;top:{y}%;transform:rotate({r}deg)"')
    for x, y, r in [(6, 18, -20), (11, 42, 15), (7, 66, -10), (88, 22, 25), (93, 48, -5), (86, 74, 20)])

SUBRAYADO = '<svg viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path d="M4 14 C 70 4, 150 4, 296 12"/></svg>'

html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>th3b1gbr0th3r IT · Software a la medida de tu negocio</title>
<meta name="description" content="Software a la medida para pequeñas empresas: webs, herramientas de gestión, reservas y automatización. Cercanos, claros y con alguien de verdad al otro lado.">
<meta name="theme-color" content="#111111">
<meta property="og:title" content="th3b1gbr0th3r IT · Software a la medida de tu negocio">
<meta property="og:description" content="Tu negocio es único. Tu software, también. Webs, gestión y automatización para pequeñas empresas.">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>{CSS}</style>
<script>{JS}</script>
</head>
<body>
<a class="enlace" href="#principal" style="position:absolute;left:-999px">Saltar al contenido</a>
<header class="nav">
 <div class="contenedor">
  <a class="marca" href="#" aria-label="th3b1gbr0th3r IT, inicio">{ICONO_MARCA}<span>th3b1gbr0th3r <b>IT</b></span></a>
  <nav aria-label="Principal"><ul>
   <li><a href="#que-hacemos">Qué hacemos</a></li><li><a href="#como">Cómo trabajamos</a></li>
   <li><a href="#por-dentro">Por dentro</a></li><li><a href="#manada">Quiénes somos</a></li><li><a href="#preguntas">Preguntas</a></li>
  </ul></nav>
  <a class="btn" href="{MAILTO}">Hablemos<span class="largo">&nbsp;de tu negocio</span></a>
 </div>
</header>

<main id="principal">
<section class="hero">
 <div class="contenedor">
  <div>
   <span class="sobre">Software para pequeñas empresas</span>
   <h1>Tu negocio es único. <em class="subrayado">Tu software, también.{SUBRAYADO}</em></h1>
   <p class="lead">Hacemos webs, herramientas de gestión y automatizaciones a la medida de cómo trabajas tú. Sin plantillas que te obligan a cambiar, sin jerga y con alguien de verdad al otro lado.</p>
   <div class="acciones">
    <a class="btn" href="{MAILTO}">Cuéntanos tu negocio <span class="flecha">→</span></a>
    <a class="enlace" href="#como">Así trabajamos</a>
   </div>
   <ul class="confianza"><li>Primera charla sin compromiso</li><li>Hablas siempre con el responsable</li><li>Te explicamos todo en claro</li></ul>
  </div>
  <div class="escena" aria-hidden="true">
   <div class="anillo"></div><div class="circulo"></div>{gato(JEFE)}{flotantes}
  </div>
 </div>
</section>

<div class="sectores" aria-label="Sectores con los que trabajamos"><span>Hecho para</span>
 <div class="cinta"><ul>{marquee}</ul><ul aria-hidden="true">{marquee}</ul></div>
</div>

<section class="te-suena">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">¿Te suena?</span><h2>Lo que nos cuentan <em>casi todos</em></h2>
   <p>Cada negocio es distinto, pero los dolores de cabeza se parecen mucho. Por ahí empezamos.</p></div>
  <div class="rejilla-suena">{suena}</div>
 </div>
</section>

<section class="servicios" id="que-hacemos">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Qué hacemos</span><h2>Tecnología que se adapta <em>a ti</em>, no al revés</h2>
   <p>Desde tu primera web hasta la herramienta con la que organizas el día a día. Todo pensado para tu forma de trabajar.</p></div>
  <div class="bento">{servicios}</div>
 </div>
</section>

<section id="como">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Cómo trabajamos</span><h2>Paso a paso, <em>y contigo</em></h2>
   <p>Nada de desaparecer tres meses y volver con algo que no pediste.</p></div>
  <ol class="pasos">{pasos}</ol>
 </div>
</section>

<section class="por-dentro" id="por-dentro">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Por dentro</span><h2>Cada empresa, <em>en su propio carril</em></h2>
   <p>Así viaja una mejora desde que nos escribes hasta que la tienes funcionando. Cada empresa tiene su propio repositorio, sus pruebas, sus copias y su servidor: nada se comparte ni se mezcla.</p></div>
  <figure class="lienzo revela" style="margin:0">{FLUJO_ANCHO}{FLUJO_VERTICAL}</figure>
  <ul class="claves"><li>Nada se publica sin pasar las pruebas</li><li>Siempre hay copia antes de un cambio</li><li>Si algo falla, volvemos atrás</li></ul>
 </div>
</section>

<section class="manifiesto">
 <div class="huellas" aria-hidden="true">{huellas_fondo}</div>
 <div class="contenedor">
  <blockquote class="revela">La inteligencia artificial hace el trabajo pesado.<br><em>Las decisiones importantes las toma una persona.</em></blockquote>
  <p class="firma">Así de simple. Así trabajamos.</p>
 </div>
</section>

<section id="manada">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Quiénes somos</span><h2>Un equipo pequeño, ágil y <em>con siete vidas</em></h2>
   <p>Una persona al mando y tres agentes de inteligencia artificial. Los agentes trabajan rápido y sin descanso; Jordi responde de todo lo que hacemos. Y sí: somos gatos.</p></div>
  <div class="equipo">{manada}</div>
 </div>
</section>

<section class="palabra">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Nuestra palabra</span><h2>Lo que puedes <em>esperar</em> de nosotros</h2>
   <p>No son promesas de folleto. Es cómo trabajamos cada día, con cada cliente.</p></div>
  <ul class="lista-palabra">{palabra}</ul>
 </div>
</section>

<section class="faq" id="preguntas">
 <div class="contenedor">
  <div class="cabecera"><span class="sobre">Preguntas</span><h2>Lo que <em>seguramente</em> te estás preguntando</h2></div>
  {faq}
 </div>
</section>

<section class="contacto" id="contacto">
 <div class="contenedor">
  <div class="tarjeta-cta revela">
   <div>
    <span class="sobre" style="color:var(--ambar2)">Hablemos</span>
    <h2>¿Nos cuentas tu negocio?</h2>
    <p>Escríbenos y cuéntanos qué te quita tiempo o qué te gustaría mejorar. Te respondemos para quedar a una primera charla, sin compromiso.</p>
    <a class="btn ambar" href="{MAILTO}">Escríbenos <span class="flecha">→</span></a>
    <span class="correo">{MAIL}</span>
   </div>
   <div class="asoma" aria-hidden="true">{gato(JEFE)}</div>
  </div>
 </div>
</section>
</main>

<footer>
 <div class="contenedor">
  <a class="marca" href="#">{ICONO_MARCA}<span>th3b1gbr0th3r <b>IT</b></span></a>
  <p class="lema">Software a la medida de tu negocio · Hecho por la manada</p>
  <p>© <span id="anio">2026</span> th3b1gbr0th3r IT · Esta web no usa cookies ni rastreadores.</p>
 </div>
</footer>
</body>
</html>
"""

NO_ENCONTRADA = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Página no encontrada · th3b1gbr0th3r IT</title><link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#fffaf3;color:#111;font:17px/1.6 system-ui,sans-serif;text-align:center;padding:20px}}
h1{{font:700 2.2rem Georgia,serif;margin:.4em 0}}svg{{width:180px}}a{{display:inline-block;margin-top:20px;background:#111;color:#fdf6ec;padding:13px 26px;border-radius:999px;text-decoration:none;font-weight:700}}</style>
</head><body><div>{gato(JEFE)}<h1>Esta página se ha escondido</h1><p>Los gatos somos así. Vuelve al inicio y te lo enseñamos todo.</p>
<a href="./">Volver al inicio</a></div></body></html>
"""


def construir():
    SITIO.mkdir(parents=True, exist_ok=True)
    (SITIO / "index.html").write_text(html, encoding="utf-8")
    (SITIO / "404.html").write_text(NO_ENCONTRADA, encoding="utf-8")
    (SITIO / "favicon.svg").write_text(ICONO_MARCA.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    (SITIO / ".nojekyll").write_text("", encoding="utf-8")
    estilo = '<rect width="100%" height="100%" fill="#fffaf3"/>'
    for nombre, svg in (("flujo.svg", FLUJO_ANCHO), ("flujo-vertical.svg", FLUJO_VERTICAL)):
        svg = svg.replace("</style>", "</style>" + estilo, 1).replace(' class="gato', ' xmlns="http://www.w3.org/2000/svg" class="gato')
        (SITIO / nombre).write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg, encoding="utf-8")
    (SITIO / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    print(f"OK: {SITIO}")


def base_temporal():
    """Primer ancestro con backup/tmp (repo de gestión: temporales solo ahí); si no hay (CI), el del sistema."""
    for ancestro in HERE.parents:
        candidato = ancestro / "backup" / "tmp"
        if candidato.is_dir():
            return str(candidato)
    return None  # tempfile usa el temporal del sistema


def capturas():
    tmp_base = base_temporal()
    salida = CAPTURAS
    salida.mkdir(exist_ok=True)
    for nombre, tam, src in [("flujo", "1200,720", "flujo.svg")]:
        with tempfile.TemporaryDirectory(dir=tmp_base) as perfil:
            subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                            f"--user-data-dir={perfil}", f"--screenshot={salida / (nombre + '.png')}", f"--window-size={tam}",
                            f"file://{SITIO / src}"], check=True, capture_output=True)
    for nombre, tam in [("escritorio", "1440,8200"), ("movil", "390,12800")]:
        with tempfile.TemporaryDirectory(dir=tmp_base) as perfil:
            subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                            f"--user-data-dir={perfil}", "--force-prefers-reduced-motion", "--virtual-time-budget=3000",
                            f"--screenshot={salida / (nombre + '.png')}", f"--window-size={tam}",
                            f"file://{SITIO / 'index.html'}"], check=True, capture_output=True)
    print(f"Capturas: {salida}")


if __name__ == "__main__":
    construir()
    if "--capturas" in sys.argv:
        capturas()
