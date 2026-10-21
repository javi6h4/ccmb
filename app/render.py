"""Construye el HTML del panel de detalle (clase / familia / componente)."""
import html
import re

from . import theme

LINK_SCHEMES = {"class": "cls", "family": "fam", "component": "comp"}


def esc(text):
    return html.escape(text or "").replace("\n", "<br>")


def highlight(escaped_text, terms):
    if not terms:
        return escaped_text
    pattern = re.compile("|".join(re.escape(t) for t in terms if t), re.IGNORECASE)
    return pattern.sub(lambda m: f'<span class="hl">{m.group(0)}</span>', escaped_text)


def wrap(body_html):
    return f"<html><head><style>{theme.DETAIL_HTML_CSS}</style></head><body>{body_html}</body></html>"


def link(kind, code, label):
    scheme = LINK_SCHEMES[kind]
    return f'<a href="{scheme}:{esc(code)}">{esc(label)}</a>'


def render_class(data, terms=None):
    terms = terms or []
    cls = data["class"]
    families = data["families"]
    parts = []
    parts.append(f'<h1>{esc(cls["code"])} <span class="badge">Clase</span></h1>')
    parts.append(f'<div class="subtitle">{esc(cls["name"])}</div>')
    parts.append(f'<div class="page-tag">Pagina {cls["page_pdf"]} del PDF &middot; CC:2022 Parte 2</div>')
    parts.append(f'<h2>Class description</h2><p>{highlight(esc(cls["description"]), terms)}</p>')
    if cls["annex_general_notes"]:
        parts.append(
            f'<h2>Notas generales <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f'<p>{highlight(esc(cls["annex_general_notes"]), terms)}</p>'
        )
    parts.append(f"<h2>Familias ({len(families)})</h2><ul>")
    for f in families:
        label = f'{f["code"]} - {f["name"]}'
        parts.append(f'<li>{link("family", f["code"], label)}</li>')
    parts.append("</ul>")
    return wrap("".join(parts))


def render_family(data, terms=None):
    terms = terms or []
    fam = data["family"]
    cls = data["class"]
    comps = data["components"]
    parts = []
    parts.append(f'<h1>{esc(fam["code"])} <span class="badge">Familia</span></h1>')
    parts.append(f'<div class="subtitle">{esc(fam["name"])}</div>')
    cls_label2 = f'{cls["code"]} - {cls["name"]}'
    parts.append(f'<div class="meta">Clase: {link("class", cls["code"], cls_label2)}</div>')
    parts.append(f'<div class="page-tag">Pagina {fam["page_pdf"]} del PDF</div>')
    parts.append(f'<h2>Family behaviour</h2><p>{highlight(esc(fam["behaviour"]), terms)}</p>')
    if fam["leveling"]:
        parts.append(
            f'<h2>Components leveling and description</h2><p>{highlight(esc(fam["leveling"]), terms)}</p>'
        )
    if fam["annex_notes"]:
        parts.append(
            f'<h2>Application notes <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f'<p>{highlight(esc(fam["annex_notes"]), terms)}</p>'
        )
    parts.append(f"<h2>Componentes ({len(comps)})</h2><ul>")
    for c in comps:
        label = f'{c["code"]} - {c["name"]}'
        parts.append(f'<li>{link("component", c["code"], label)}</li>')
    parts.append("</ul>")
    return wrap("".join(parts))


def render_component(data, terms=None):
    terms = terms or []
    comp = data["component"]
    fam = data["family"]
    cls = data["class"]
    code = comp["code"]
    parts = []

    cls_label = f'{cls["code"]} - {cls["name"]}'
    fam_label = f'{fam["code"]} - {fam["name"]}'
    parts.append(f'<h1>{esc(code)} <span class="badge">Componente</span></h1>')
    parts.append(f'<div class="subtitle">{esc(comp["name"])}</div>')
    parts.append(
        '<div class="meta">Clase: '
        + link("class", cls["code"], cls_label)
        + " &middot; Familia: "
        + link("family", fam["code"], fam_label)
        + "</div>"
    )
    parts.append(f'<div class="page-tag">Pagina {comp["page_pdf"]} del PDF &middot; CC:2022 Parte 2</div>')

    if comp["notes"]:
        parts.append(f'<div class="note">&#9888; {esc(comp["notes"])}</div>')

    hier = data["hierarchical_to"]
    parts.append("<h2>Hierarchical to</h2>")
    if hier is None:
        parts.append(f'<p>{esc(comp["hierarchical_to_text"])}</p>')
    elif hier["exists"]:
        hier_label = f'{hier["code"]} - {hier["name"]}'
        parts.append(f"<p>{link('component', hier['code'], hier_label)}</p>")
    else:
        parts.append(f'<p>{esc(hier["code"])} <span class="dep-missing">(fuera de esta Parte)</span></p>')

    parts.append("<h2>Dependencies</h2>")
    if data["dependencies"]:
        parts.append("<ul>")
        for d in data["dependencies"]:
            if d["exists"]:
                dep_label = f'{d["code"]} - {d["name"]}'
                parts.append(f"<li>{link('component', d['code'], dep_label)}</li>")
            else:
                parts.append(
                    f'<li>{esc(d["code"])} <span class="dep-missing">'
                    f"(no esta en esta Parte &mdash; ver CC Parte 3)</span></li>"
                )
        parts.append("</ul>")
    else:
        parts.append(f'<p>{esc(comp["dependencies_text"])}</p>')

    parts.append("<h2>Elementos</h2>")
    for e in data["elements"]:
        txt = highlight(esc(e["text"]), terms)
        parts.append(f'<p><span class="elem-code">{esc(e["element_code"])}</span><br>{txt}</p>')
    if not data["elements"]:
        parts.append('<p class="dep-missing">Este componente no define elementos (ver nota arriba).</p>')

    if comp["management_text"]:
        parts.append(
            f'<h2>Management of {esc(code)}</h2><p>{highlight(esc(comp["management_text"]), terms)}</p>'
        )
    if comp["audit_text"]:
        parts.append(f'<h2>Audit of {esc(code)}</h2><p>{highlight(esc(comp["audit_text"]), terms)}</p>')
    if comp["application_notes"]:
        parts.append(
            f'<h2>Application notes <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f'<p>{highlight(esc(comp["application_notes"]), terms)}</p>'
        )

    parts.append(f'<h2>Family behaviour <span class="badge">{esc(fam["code"])}</span></h2>')
    parts.append(f'<p>{esc(fam["behaviour"])}</p>')
    if fam["leveling"]:
        parts.append("<h2>Components leveling and description</h2>")
        parts.append(f'<p>{esc(fam["leveling"])}</p>')

    parts.append("<h2>Quien depende de este componente</h2>")
    if data["reverse_dependencies"]:
        parts.append("<ul>")
        for r in data["reverse_dependencies"]:
            rev_label = f'{r["code"]} - {r["name"]}'
            parts.append(f"<li>{link('component', r['code'], rev_label)}</li>")
        parts.append("</ul>")
    else:
        parts.append('<p class="dep-missing">Ningun otro componente de esta Parte depende de este.</p>')

    return wrap("".join(parts))


def render_search_results(query, ranked):
    parts = [f'<h1>Resultados para <span class="badge-violet">&ldquo;{esc(query)}&rdquo;</span></h1>']
    if not ranked:
        parts.append(
            '<p class="dep-missing">No se encontraron resultados. Proba con otro codigo '
            "(FAU, FAU_ARP, FAU_ARP.1), nombre o termino del contenido.</p>"
        )
        return wrap("".join(parts))

    n = len(ranked)
    parts.append(f'<div class="subtitle">{n} resultado{"s" if n != 1 else ""} encontrados</div>')
    type_label = {"class": "Clase", "family": "Familia", "component": "Componente"}
    shown = ranked[:80]
    parts.append("<ul>")
    for ref_type, ref_code, title in shown:
        badge_cls = "badge" if ref_type == "component" else "badge-violet"
        label_text = type_label.get(ref_type, ref_type)
        parts.append(
            f'<li>{link(ref_type, ref_code, title)} '
            f'<span class="{badge_cls}">{esc(label_text)}</span></li>'
        )
    parts.append("</ul>")
    if n > len(shown):
        parts.append(
            f'<p class="dep-missing">... y {n - len(shown)} resultados mas. '
            "Afina la busqueda para acotar la lista, o recorre el arbol de la izquierda.</p>"
        )
    return wrap("".join(parts))


def render_welcome(stats):
    parts = [
        '<h1>CCMB <span class="badge">Common Criteria</span></h1>',
        '<div class="subtitle">Base de consulta de CC:2022 Parte 2 &mdash; Security functional components</div>',
        f'<p class="meta">{stats["classes"]} clases &middot; {stats["families"]} familias &middot; '
        f'{stats["components"]} componentes cargados desde el PDF.</p>',
        "<h2>Como usar</h2>",
        "<p>Escribi en el buscador un codigo (FAU, FAU_ARP, FAU_ARP.1), un nombre "
        '("Security audit") o cualquier texto del contenido. El arbol de la izquierda '
        "se filtra automaticamente mostrando clases, familias y componentes relacionados.</p>",
        "<p>Hace clic en una clase o familia para ver su descripcion y desplegar sus hijos. "
        "Hace clic en un componente para ver su ficha completa, con sus dependencias "
        "como enlaces navegables.</p>",
    ]
    return wrap("".join(parts))
