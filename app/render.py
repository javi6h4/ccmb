"""Construye el HTML del panel de detalle (clase / familia / componente).
Soporta mostrar el contenido del documento en espanol (traducido) o en el
ingles original del PDF, segun el parametro `lang` ('es' o 'en')."""
import html
import re

from . import theme

LINK_SCHEMES = {"class": "cls", "family": "fam", "component": "comp"}

LABELS = {
    "es": {
        "class_description": "Descripción de la clase",
        "general_notes": "Notas generales",
        "families": "Familias",
        "components": "Componentes",
        "family_behaviour": "Comportamiento de la familia",
        "leveling": "Nivelación y descripción de los componentes",
        "application_notes": "Notas de aplicación",
        "hierarchical_to": "Jerárquico a",
        "dependencies": "Dependencias",
        "elements": "Elementos",
        "no_elements": "Este componente no define elementos (ver nota arriba).",
        "management_of": "Gestión de",
        "audit_of": "Auditoría de",
        "who_depends": "Quién depende de este componente",
        "no_reverse_deps": "Ningún otro componente de esta Parte depende de este.",
        "outside_part": "(fuera de esta Parte)",
        "outside_part_dep": "(no está en esta Parte — ver CC Parte 3)",
    },
    "en": {
        "class_description": "Class description",
        "general_notes": "General notes",
        "families": "Families",
        "components": "Components",
        "family_behaviour": "Family behaviour",
        "leveling": "Components leveling and description",
        "application_notes": "Application notes",
        "hierarchical_to": "Hierarchical to",
        "dependencies": "Dependencies",
        "elements": "Elements",
        "no_elements": "This component defines no elements (see note above).",
        "management_of": "Management of",
        "audit_of": "Audit of",
        "who_depends": "Which components depend on this one",
        "no_reverse_deps": "No other component in this Part depends on this one.",
        "outside_part": "(outside this Part)",
        "outside_part_dep": "(not in this Part — see CC Part 3)",
    },
}


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


def pick(row, field, lang):
    """Devuelve row[field+'_es'] si lang='es' y existe, si no row[field]."""
    if lang == "es":
        es_val = row[f"{field}_es"] if f"{field}_es" in row.keys() else None
        if es_val:
            return es_val
    return row[field]


def ref_label(ref, lang):
    name = (ref.get("name_es") if lang == "es" else None) or ref.get("name") or ""
    return f'{ref["code"]} - {name}'


def row_label(row, lang):
    name = pick(row, "name", lang)
    return f'{row["code"]} - {name}'


def render_class(data, terms=None, lang="es"):
    terms = terms or []
    L = LABELS[lang]
    cls = data["class"]
    families = data["families"]
    parts = []
    parts.append(f'<h1>{esc(cls["code"])} <span class="badge">Clase</span></h1>')
    parts.append(f'<div class="subtitle">{esc(pick(cls, "name", lang))}</div>')
    parts.append(f'<div class="page-tag">Pagina {cls["page_pdf"]} del PDF &middot; CC:2022 Parte 2</div>')
    parts.append(
        f'<h2>{L["class_description"]}</h2><p>{highlight(esc(pick(cls, "description", lang)), terms)}</p>'
    )
    notes = pick(cls, "annex_general_notes", lang)
    if notes:
        parts.append(
            f'<h2>{L["general_notes"]} <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f"<p>{highlight(esc(notes), terms)}</p>"
        )
    parts.append(f'<h2>{L["families"]} ({len(families)})</h2><ul>')
    for f in families:
        parts.append(f'<li>{link("family", f["code"], row_label(f, lang))}</li>')
    parts.append("</ul>")
    return wrap("".join(parts))


def render_family(data, terms=None, lang="es"):
    terms = terms or []
    L = LABELS[lang]
    fam = data["family"]
    cls = data["class"]
    comps = data["components"]
    parts = []
    parts.append(f'<h1>{esc(fam["code"])} <span class="badge">Familia</span></h1>')
    parts.append(f'<div class="subtitle">{esc(pick(fam, "name", lang))}</div>')
    parts.append(f'<div class="meta">Clase: {link("class", cls["code"], row_label(cls, lang))}</div>')
    parts.append(f'<div class="page-tag">Pagina {fam["page_pdf"]} del PDF</div>')
    parts.append(
        f'<h2>{L["family_behaviour"]}</h2><p>{highlight(esc(pick(fam, "behaviour", lang)), terms)}</p>'
    )
    leveling = pick(fam, "leveling", lang)
    if leveling:
        parts.append(f'<h2>{L["leveling"]}</h2><p>{highlight(esc(leveling), terms)}</p>')
    annex_notes = pick(fam, "annex_notes", lang)
    if annex_notes:
        parts.append(
            f'<h2>{L["application_notes"]} <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f"<p>{highlight(esc(annex_notes), terms)}</p>"
        )
    parts.append(f'<h2>{L["components"]} ({len(comps)})</h2><ul>')
    for c in comps:
        parts.append(f'<li>{link("component", c["code"], row_label(c, lang))}</li>')
    parts.append("</ul>")
    return wrap("".join(parts))


def render_component(data, terms=None, lang="es"):
    terms = terms or []
    L = LABELS[lang]
    comp = data["component"]
    fam = data["family"]
    cls = data["class"]
    code = comp["code"]
    parts = []

    parts.append(f'<h1>{esc(code)} <span class="badge">Componente</span></h1>')
    parts.append(f'<div class="subtitle">{esc(pick(comp, "name", lang))}</div>')
    parts.append(
        '<div class="meta">Clase: '
        + link("class", cls["code"], row_label(cls, lang))
        + " &middot; Familia: "
        + link("family", fam["code"], row_label(fam, lang))
        + "</div>"
    )
    parts.append(f'<div class="page-tag">Pagina {comp["page_pdf"]} del PDF &middot; CC:2022 Parte 2</div>')

    notes = pick(comp, "notes", lang)
    if notes:
        parts.append(f'<div class="note">&#9888; {esc(notes)}</div>')

    hier = data["hierarchical_to"]
    parts.append(f"<h2>{L['hierarchical_to']}</h2>")
    if hier is None:
        parts.append(f'<p>{esc(pick(comp, "hierarchical_to_text", lang))}</p>')
    elif hier["exists"]:
        parts.append(f"<p>{link('component', hier['code'], ref_label(hier, lang))}</p>")
    else:
        parts.append(f'<p>{esc(hier["code"])} <span class="dep-missing">{L["outside_part"]}</span></p>')

    parts.append(f"<h2>{L['dependencies']}</h2>")
    if data["dependencies"]:
        parts.append("<ul>")
        for d in data["dependencies"]:
            if d["exists"]:
                parts.append(f"<li>{link('component', d['code'], ref_label(d, lang))}</li>")
            else:
                parts.append(
                    f'<li>{esc(d["code"])} <span class="dep-missing">{L["outside_part_dep"]}</span></li>'
                )
        parts.append("</ul>")
    else:
        parts.append(f'<p>{esc(pick(comp, "dependencies_text", lang))}</p>')

    parts.append(f"<h2>{L['elements']}</h2>")
    for e in data["elements"]:
        txt = highlight(esc(pick(e, "text", lang)), terms)
        parts.append(f'<p><span class="elem-code">{esc(e["element_code"])}</span><br>{txt}</p>')
    if not data["elements"]:
        parts.append(f'<p class="dep-missing">{L["no_elements"]}</p>')

    mgmt = pick(comp, "management_text", lang)
    if mgmt:
        parts.append(f'<h2>{L["management_of"]} {esc(code)}</h2><p>{highlight(esc(mgmt), terms)}</p>')
    audit = pick(comp, "audit_text", lang)
    if audit:
        parts.append(f'<h2>{L["audit_of"]} {esc(code)}</h2><p>{highlight(esc(audit), terms)}</p>')
    app_notes = pick(comp, "application_notes", lang)
    if app_notes:
        parts.append(
            f'<h2>{L["application_notes"]} <span class="badge-violet">Anexo {esc(cls["annex_letter"])}</span></h2>'
            f"<p>{highlight(esc(app_notes), terms)}</p>"
        )

    parts.append(f'<h2>{L["family_behaviour"]} <span class="badge">{esc(fam["code"])}</span></h2>')
    parts.append(f'<p>{esc(pick(fam, "behaviour", lang))}</p>')
    leveling = pick(fam, "leveling", lang)
    if leveling:
        parts.append(f"<h2>{L['leveling']}</h2>")
        parts.append(f"<p>{esc(leveling)}</p>")

    parts.append(f"<h2>{L['who_depends']}</h2>")
    if data["reverse_dependencies"]:
        parts.append("<ul>")
        for r in data["reverse_dependencies"]:
            parts.append(f"<li>{link('component', r['code'], ref_label(r, lang))}</li>")
        parts.append("</ul>")
    else:
        parts.append(f'<p class="dep-missing">{L["no_reverse_deps"]}</p>')

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
        '("Security audit") o cualquier texto del contenido, en espanol o en ingles. '
        "El arbol de la izquierda se filtra automaticamente mostrando clases, familias "
        "y componentes relacionados.</p>",
        "<p>Hace clic en una clase o familia para ver su descripcion y desplegar sus hijos. "
        "Hace clic en un componente para ver su ficha completa, con sus dependencias "
        "como enlaces navegables. El contenido se muestra en espanol; usa el boton "
        '"EN / ES" para ver el texto original en ingles tal cual el PDF.</p>',
    ]
    return wrap("".join(parts))
