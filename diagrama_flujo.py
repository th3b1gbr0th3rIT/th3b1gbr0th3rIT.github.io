"""Diagrama del flujo de trabajo de th3b1gbr0th3r IT para la web: de la petición del cliente a la publicación,
con un carril propio (repositorio, pruebas, copia, publicación y servidor) para cada empresa.
Sin datos internos: ni nombres de clientes, ni servidores, ni herramientas concretas."""

PATHS = {
    "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "charla": '<path d="M4 5h16v11H9l-5 4z"/><path d="m9 10.5 2 2 4-4"/>',
    "repo": '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 8.2v7.6M18 10.2c0 4-6 3-11 6"/>',
    "pruebas": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3"/><path d="M8 15h8"/>',
    "copia": '<path d="M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z"/><path d="M4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "publicar": '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    "servidor": '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    "candado": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
}

ESTILO = """<style>
.fl-t{font:700 20px "DejaVu Serif",Georgia,serif;fill:#111}.fl-s{font:15px system-ui,"DejaVu Sans",Arial,sans-serif;fill:#475569}
.fl-chip{font:600 14px system-ui,"DejaVu Sans",Arial,sans-serif;fill:#111}.fl-nota{font:italic 16px "DejaVu Serif",Georgia,serif;fill:#b45309}
.fl-carril{font:700 18px "DejaVu Serif",Georgia,serif;fill:#111}.fl-peq{font:700 11px system-ui,"DejaVu Sans",Arial,sans-serif;fill:#b45309;letter-spacing:.12em}
.fl-ico{fill:none;stroke:#b45309;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.fl-flecha{stroke:#d97706;stroke-width:2.5;stroke-dasharray:7 7;fill:none}
</style>"""

FLECHA_DEF = ('<defs><marker id="fl-punta" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
              '<path d="M0 0 L10 5 L0 10 z" fill="#d97706"/></marker></defs>')

CARRIL = [("repo", "Su repositorio"), ("pruebas", "Pruebas automáticas"), ("copia", "Copia de seguridad"),
          ("publicar", "Publicación"), ("servidor", "Su servidor")]


def ico(nombre, x, y, s=22, color=None):
    estilo = f' style="stroke:{color}"' if color else ""
    return f'<svg x="{x}" y="{y}" width="{s}" height="{s}" viewBox="0 0 24 24" class="fl-ico"{estilo}>{PATHS[nombre]}</svg>'


def gato_en(gato_svg, x, y, w, h):
    """Coloca un gato (svg de construir_web.gato) dentro del diagrama."""
    return gato_svg.replace("<svg ", f'<svg x="{x}" y="{y}" width="{w}" height="{h}" ', 1)


def etapas(gatos):
    """(icono|gato, título, línea 1, línea 2)."""
    return [
        (("ico", "correo"), "Nos escribes", "Por correo, con tus", "palabras, sin tickets"),
        (("gato", gatos[1]), "Coordinación", "Registra, prioriza", "y te confirma"),
        (("gato", gatos[2]), "Desarrollo", "Construye y prueba", "en un entorno aislado"),
        (("gato", gatos[3]), "Operación", "Copia de seguridad", "y publicación"),
        (("ico", "charla"), "Te lo contamos", "Qué hay nuevo y", "qué puedes comprobar"),
    ]


def _nodo(tipo, cx, cy, r):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fdf6ec" stroke="#f1e4cf" stroke-width="3"/>'
    if tipo[0] == "ico":
        s += ico(tipo[1], cx - r * .45, cy - r * .45, r * .9)
    else:
        s += gato_en(tipo[1], cx - r * .72, cy - r * .78, r * 1.44, r * 1.62)
    return s


def _carril(x, y, w, h, nombre, activo, vertical=False):
    borde = "#d97706" if activo else "#f1e4cf"
    op = "" if activo else ' opacity=".55"'
    s = f'<g{op}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="#fff" stroke="{borde}" stroke-width="{2.5 if activo else 2}"/>'
    if not vertical:
        s += f'<text x="{x + 26}" y="{y + 34}" class="fl-carril">{nombre}</text>'
        s += f'<text x="{x + 26}" y="{y + 56}" class="fl-peq">SU PROPIO CICLO</text>'
        cxi, gap = x + 190, 18
        for i, (ic, t) in enumerate(CARRIL):
            cw = round(40 + len(t) * 7.9 + 12)
            s += (f'<rect x="{cxi}" y="{y + 16}" width="{cw}" height="{h - 32}" rx="{(h - 32) / 2}" fill="#fdf6ec"/>'
                  + ico(ic, cxi + 12, y + h / 2 - 11) + f'<text x="{cxi + 40}" y="{y + h / 2 + 5}" class="fl-chip">{t}</text>')
            if i < len(CARRIL) - 1:
                s += f'<text x="{cxi + cw + 5}" y="{y + h / 2 + 6}" style="font:700 18px sans-serif;fill:#d97706">›</text>'
            cxi += cw + gap
    return s + "</g>"


def flujo_ancho(gatos):
    W, H = 1200, 720
    s = [f'<svg class="flujo flujo-ancho" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Flujo de trabajo: nos escribes, coordinación, desarrollo, operación y te lo contamos; '
         'cada empresa con su propio repositorio, pruebas, copia de seguridad, publicación y servidor.">', ESTILO, FLECHA_DEF]
    xs, cy, r = [110, 350, 600, 850, 1090], 160, 60
    # Jordi aprueba lo importante (sobre Coordinación → Operación)
    s.append('<path d="M350 70 V58 Q350 46 362 46 H838 Q850 46 850 58 V70" fill="none" stroke="#111" stroke-width="2"/>')
    s.append(gato_en(gatos[0], 470, 0, 40, 46))
    s.append('<text x="518" y="34" class="fl-nota">Jordi revisa y aprueba lo importante</text>')
    for i, (tipo, t, l1, l2) in enumerate(etapas(gatos)):
        x = xs[i]
        if i < 4:
            s.append(f'<line x1="{x + r + 8}" y1="{cy}" x2="{xs[i + 1] - r - 12}" y2="{cy}" class="fl-flecha" marker-end="url(#fl-punta)"/>')
        s.append(_nodo(tipo, x, cy, r))
        s.append(f'<text x="{x}" y="{cy + r + 36}" text-anchor="middle" class="fl-t">{t}</text>')
        s.append(f'<text x="{x}" y="{cy + r + 60}" text-anchor="middle" class="fl-s">{l1}</text>')
        s.append(f'<text x="{x}" y="{cy + r + 80}" text-anchor="middle" class="fl-s">{l2}</text>')
    # Operación → carriles
    s.append(f'<line x1="{xs[3]}" y1="{cy + r + 96}" x2="{xs[3]}" y2="390" class="fl-flecha" marker-end="url(#fl-punta)"/>')
    s.append(f'<text x="{xs[3] + 16}" y="375" class="fl-peq">CON EL CICLO DE CADA EMPRESA</text>')
    # carriles (detrás, los de otras empresas)
    s.append(_carril(40, 590, 1120, 76, "Empresa C", False))
    s.append(_carril(40, 497, 1120, 76, "Empresa B", False))
    s.append(_carril(40, 404, 1120, 76, "Tu empresa", True))
    s.append(ico("candado", 360, 686, 20, "#475569"))
    s.append('<text x="388" y="702" class="fl-s">Código, datos y credenciales de cada empresa nunca se mezclan.</text>')
    s.append("</svg>")
    return "".join(s)


def flujo_vertical(gatos):
    W = 600
    s = []
    # Jordi
    s.append(f'<rect x="20" y="10" width="{W - 40}" height="64" rx="32" fill="#111"/>')
    s.append(gato_en(gatos[0], 40, 14, 46, 54))
    s.append('<text x="98" y="50" style="font:italic 20px &quot;DejaVu Serif&quot;,Georgia,serif;fill:#fdf6ec">Jordi revisa y aprueba lo importante</text>')
    y0, paso, r = 160, 150, 56
    for i, (tipo, t, l1, l2) in enumerate(etapas(gatos)):
        cy = y0 + i * paso
        if i < 4:
            s.append(f'<line x1="90" y1="{cy + r + 8}" x2="90" y2="{cy + paso - r - 12}" class="fl-flecha" marker-end="url(#fl-punta)"/>')
        s.append(_nodo(tipo, 90, cy, r))
        s.append(f'<text x="172" y="{cy - 8}" class="fl-t" style="font-size:26px">{t}</text>')
        s.append(f'<text x="172" y="{cy + 22}" class="fl-s" style="font-size:20px">{l1} {l2}</text>' if len(l1 + l2) < 30 else
                 f'<text x="172" y="{cy + 22}" class="fl-s" style="font-size:20px">{l1}</text>'
                 f'<text x="172" y="{cy + 46}" class="fl-s" style="font-size:20px">{l2}</text>')
    yc = y0 + 4 * paso + r + 30
    s.append(f'<text x="20" y="{yc + 10}" class="fl-peq" style="font-size:15px">CON EL CICLO DE CADA EMPRESA</text>')
    yc += 40
    hc = 70 + len(CARRIL) * 66
    # pila de carriles: otras empresas detrás
    for k, nombre in ((2, "Empresa C"), (1, "Empresa B")):
        s.append(f'<g opacity=".5"><rect x="{20 + k * 14}" y="{yc - k * 14 + 10}" width="{W - 40 - k * 28}" height="{hc}" rx="24" '
                 f'fill="#fff" stroke="#f1e4cf" stroke-width="2"/></g>')
    yc += 30
    s.append(f'<rect x="20" y="{yc}" width="{W - 40}" height="{hc}" rx="24" fill="#fff" stroke="#d97706" stroke-width="2.5"/>')
    s.append(f'<text x="48" y="{yc + 44}" class="fl-carril" style="font-size:26px">Tu empresa</text>')
    s.append(f'<text x="{W - 48}" y="{yc + 42}" text-anchor="end" class="fl-peq" style="font-size:14px">SU PROPIO CICLO</text>')
    for i, (ic, t) in enumerate(CARRIL):
        y = yc + 70 + i * 66
        s.append(f'<rect x="44" y="{y}" width="{W - 88}" height="52" rx="26" fill="#fdf6ec"/>' + ico(ic, 62, y + 13, 26)
                 + f'<text x="104" y="{y + 34}" class="fl-chip" style="font-size:21px">{t}</text>')
    yf = yc + hc + 50
    s.append(ico("candado", 20, yf - 22, 26, "#475569"))
    s.append(f'<text x="56" y="{yf}" class="fl-s" style="font-size:19px">Código, datos y credenciales de cada</text>')
    s.append(f'<text x="56" y="{yf + 26}" class="fl-s" style="font-size:19px">empresa nunca se mezclan.</text>')
    H = yf + 50
    return (f'<svg class="flujo flujo-vertical" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Flujo de trabajo y carril propio de cada empresa">' + ESTILO
            + (FLECHA_DEF + "".join(s)).replace("fl-punta", "fl-punta-v") + "</svg>")
