#!/usr/bin/env python3
"""
build_db.py - Construye ccmb.db (SQLite) a partir de CC2022PART2R1.pdf
(Common Criteria CC:2022 Parte 2 Rev.1 - Security functional components).

Uso:
    python build_db.py [ruta_pdf] [ruta_db_salida]

Por defecto usa CC2022PART2R1.pdf -> ccmb.db en el directorio actual.
"""
import sys
import re
import sqlite3
import unicodedata
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Falta PyMuPDF. Instalá con: pip install PyMuPDF")
    sys.exit(1)

# ----------------------------------------------------------------------------
# Constantes / regex
# ----------------------------------------------------------------------------

VALID_CLASS_CODES = {"FAU", "FCO", "FCS", "FDP", "FIA", "FMT", "FPR", "FPT", "FRU", "FTA", "FTP"}
ANNEX_LETTERS = "CDEFGHIJKLM"  # Anexos C..M, uno por clase en orden de aparicion

FOOTER_PAGE_RE = re.compile(r"^Page\s+\S+\s+of\s+297\.?$", re.IGNORECASE)
APPNOTES_TITLE_RE = re.compile(r"^Class\s+([A-Z]{3}):\s*.+?\s+[–—-]\s+Application notes\.?$")
CLASS_TITLE_RE = re.compile(r"^Class\s+([A-Z]{3}):\s*(.+)$")
FAMILY_TITLE_RE = re.compile(r"^(.+?)\s*\(([A-Z]{2,4}_[A-Z0-9]{2,10})\)\.?$")
COMPONENT_TITLE_RE = re.compile(r"^([A-Z]{2,4}_[A-Z0-9]{2,10}\.\d{1,2})\s+(.+)$")
MGMT_TITLE_RE = re.compile(r"^Management of (.+)$")
AUDIT_TITLE_RE = re.compile(r"^Audit of (.+)$")
ANNEX_LINE_RE = re.compile(r"^Annex\s+([A-M])$")

HEADING_BARE_RE = re.compile(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2}){0,3}|[A-M](?:\.[0-9]{1,2}){1,4})$")
HEADING_COMBINED_RE = re.compile(
    r"^((?:[0-9]{1,2}(?:\.[0-9]{1,2}){0,3})|(?:[A-M](?:\.[0-9]{1,2}){1,4}))\s+(\S.*)$"
)
ELEMENT_BARE_RE = re.compile(r"^([A-Z]{2,4}_[A-Z0-9]{2,10}\.\d{1,2}\.\d{1,2})$")
ELEMENT_COMBINED_RE = re.compile(r"^([A-Z]{2,4}_[A-Z0-9]{2,10}\.\d{1,2}\.\d{1,2})\s+(\S.*)$")
CODE_TOKEN_RE = re.compile(r"[A-Z]{2,4}_[A-Z0-9]{2,10}\.\d{1,2}")

HIER_LABEL_RE = re.compile(r"^Hierarchical to:\s*(.*)$")
DEPS_LABEL_RE = re.compile(r"^Dependencies:\s*(.*)$")


# ----------------------------------------------------------------------------
# Extraccion y limpieza de texto por pagina
# ----------------------------------------------------------------------------

def clean_page_lines(raw_lines):
    """Quita encabezados/pies de pagina repetidos, preservando los titulos
    reales de clase / anexo (que vienen inmediatamente despues de un numero
    de seccion 'suelto' o de la etiqueta '(normative)')."""
    out = []
    last_nonblank = ""
    for line in raw_lines:
        line = line.strip()
        if line == "":
            continue
        if FOOTER_PAGE_RE.match(line):
            continue
        if line in ("CC:2022", "November 2022"):
            continue
        if line == "Dependency tables for security functional components":
            continue
        if CLASS_TITLE_RE.match(line) or APPNOTES_TITLE_RE.match(line):
            # Puede ser un titulo real (precedido por numero de seccion suelto
            # o "(normative)") o un encabezado/pie repetido -> descartar el 2do caso.
            if re.match(r"^[0-9]+$", last_nonblank) or last_nonblank == "(normative)":
                out.append(line)
                last_nonblank = line
            continue
        out.append(line)
        last_nonblank = line
    return out


def iter_doc_lines(pdf_path):
    """Genera tuplas (pagina_pdf, texto_linea) para todo el documento, ya limpio
    de encabezados/pies de pagina."""
    doc = fitz.open(pdf_path)
    for pno in range(doc.page_count):
        page_num = pno + 1
        text = doc[pno].get_text("text")
        raw_lines = text.split("\n")
        for line in clean_page_lines(raw_lines):
            yield page_num, line
    doc.close()


def normalize_ws(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ----------------------------------------------------------------------------
# Tokenizacion de encabezados (numero + titulo), manejando el caso en que
# PyMuPDF los separa en dos lineas o los deja juntos en una sola.
# ----------------------------------------------------------------------------

def tokenize(lines_with_pages):
    """Convierte la lista de (pagina, linea) en una lista de tokens:
      ('heading', numero, titulo, pagina)
      ('element', codigo, texto_inicial, pagina)
      ('text', texto, pagina)
    """
    tokens = []
    n = len(lines_with_pages)
    i = 0
    while i < n:
        page, line = lines_with_pages[i]

        m = HEADING_BARE_RE.match(line)
        if m:
            # El titulo deberia venir en la siguiente linea no vacia
            if i + 1 < n:
                npage, nline = lines_with_pages[i + 1]
                tokens.append(("heading", line, nline, page))
                i += 2
                continue

        m = HEADING_COMBINED_RE.match(line)
        if m and m.group(2)[0:1].isupper():
            tokens.append(("heading", m.group(1), m.group(2), page))
            i += 1
            continue

        m = ELEMENT_BARE_RE.match(line)
        if m:
            if i + 1 < n:
                npage, nline = lines_with_pages[i + 1]
                tokens.append(("element", m.group(1), nline, page))
                i += 2
                continue

        m = ELEMENT_COMBINED_RE.match(line)
        if m:
            tokens.append(("element", m.group(1), m.group(2), page))
            i += 1
            continue

        tokens.append(("text", line, None, page))
        i += 1
    return tokens


def classify_heading(title):
    """Clasifica un titulo de encabezado. Devuelve (tipo, datos)."""
    m = CLASS_TITLE_RE.match(title)
    if m and m.group(1) in VALID_CLASS_CODES:
        return "class", (m.group(1), m.group(2).rstrip("."))
    if title == "Class description":
        return "class_description", None
    if title == "Family behaviour":
        return "family_behaviour", None
    if title == "Components leveling and description":
        return "family_leveling", None
    m = MGMT_TITLE_RE.match(title)
    if m:
        codes = CODE_TOKEN_RE.findall(m.group(1))
        return "management", codes
    m = AUDIT_TITLE_RE.match(title)
    if m:
        codes = CODE_TOKEN_RE.findall(m.group(1))
        return "audit", codes
    m = COMPONENT_TITLE_RE.match(title)
    if m:
        return "component", (m.group(1), m.group(2).rstrip("."))
    m = FAMILY_TITLE_RE.match(title)
    if m:
        return "family", (m.group(2), m.group(1).rstrip("."))
    return "generic", title


# ----------------------------------------------------------------------------
# Modelo de datos intermedio
# ----------------------------------------------------------------------------

class ClassRec:
    def __init__(self, code, name, page):
        self.code = code
        self.name = name
        self.page = page
        self.description = ""
        self.annex_letter = None
        self.annex_general_notes = ""
        self.family_order = []


class FamilyRec:
    def __init__(self, code, name, class_code, page):
        self.code = code
        self.name = name
        self.class_code = class_code
        self.page = page
        self.behaviour = ""
        self.leveling = ""
        self.annex_notes = ""
        self.component_order = []


class ComponentRec:
    def __init__(self, code, name, family_code, class_code, page):
        self.code = code
        self.name = name
        self.family_code = family_code
        self.class_code = class_code
        self.page = page
        self.hierarchical_to_text = "No other components."
        self.hierarchical_to_code = None
        self.dependencies_text = "No dependencies."
        self.dependencies_codes = []
        self.management_text = ""
        self.audit_text = ""
        self.application_notes = ""
        self.notes = ""  # texto suelto bajo el encabezado (p.ej. avisos de deprecacion)
        self.elements = []  # list of (code, text)


# ----------------------------------------------------------------------------
# Parser principal del cuerpo (clases/familias/componentes)
# ----------------------------------------------------------------------------

def parse_body(tokens):
    classes = {}
    families = {}
    components = {}

    cur_class = None
    cur_family = None
    cur_component = None
    buffer = []  # lineas de texto acumuladas para la seccion activa
    active = None  # ('class_description'|'family_behaviour'|'family_leveling'|None)
    mgmt_targets = []
    audit_targets = []

    # estado especial para parseo de "Component relationships"
    in_component_relations = False
    hier_buffer = None
    deps_buffer = None
    stage = None  # None | 'hier' | 'deps'
    relations_started = False  # True una vez vista "Hierarchical to:" o un elemento
    note_buffer = []

    def flush_note():
        nonlocal note_buffer
        if note_buffer and cur_component is not None:
            cur_component.notes = normalize_ws("\n".join(note_buffer))
        note_buffer = []

    def flush_active():
        nonlocal buffer, active
        text = normalize_ws("\n".join(buffer))
        if active == "class_description" and cur_class:
            cur_class.description = text
        elif active == "family_behaviour" and cur_family:
            cur_family.behaviour = text
        elif active == "family_leveling" and cur_family:
            cur_family.leveling = text
        elif active == "management":
            for code in mgmt_targets:
                if code in components:
                    components[code].management_text = text
        elif active == "audit":
            for code in audit_targets:
                if code in components:
                    components[code].audit_text = text
        buffer = []
        active = None

    def flush_hier_deps():
        nonlocal hier_buffer, deps_buffer, stage
        if cur_component is None:
            hier_buffer, deps_buffer, stage = None, None, None
            return
        if hier_buffer is not None:
            txt = normalize_ws(" ".join(hier_buffer)).rstrip(".") + "."
            cur_component.hierarchical_to_text = txt
            codes = CODE_TOKEN_RE.findall(txt)
            if codes:
                cur_component.hierarchical_to_code = codes[0]
        if deps_buffer is not None:
            txt = normalize_ws(" ".join(deps_buffer))
            cur_component.dependencies_text = txt if txt else "No dependencies."
            cur_component.dependencies_codes = list(dict.fromkeys(CODE_TOKEN_RE.findall(txt)))
        hier_buffer, deps_buffer, stage = None, None, None

    for tok in tokens:
        kind = tok[0]

        if kind == "heading":
            _, num, title, page = tok
            flush_hier_deps()
            flush_active()
            flush_note()
            ctype, data = classify_heading(title)

            if ctype == "class":
                code, name = data
                cur_class = ClassRec(code, name, page)
                classes[code] = cur_class
                cur_family = None
                cur_component = None
            elif ctype == "class_description":
                active = "class_description"
            elif ctype == "family":
                code, name = data
                if cur_class is None:
                    continue
                cur_family = FamilyRec(code, name, cur_class.code, page)
                families[code] = cur_family
                cur_class.family_order.append(code)
                cur_component = None
            elif ctype == "family_behaviour":
                active = "family_behaviour"
            elif ctype == "family_leveling":
                active = "family_leveling"
            elif ctype == "management":
                active = "management"
                mgmt_targets = data
            elif ctype == "audit":
                active = "audit"
                audit_targets = data
            elif ctype == "component":
                code, name = data
                if cur_family is None:
                    continue
                cur_component = ComponentRec(code, name, cur_family.code, cur_family.class_code, page)
                components[code] = cur_component
                cur_family.component_order.append(code)
                relations_started = False
            else:
                # generic: titulo no reconocido (p.ej. "Component relationships")
                if title == "Component relationships":
                    pass
                # cualquier otro titulo generico se ignora como encabezado,
                # su contenido (si lo hay) cae como texto suelto.

        elif kind == "element":
            _, code, text0, page = tok
            if stage is not None:
                flush_hier_deps()
            relations_started = True
            if cur_component is not None:
                cur_component.elements.append([code, text0])

        else:  # text
            _, text, _, page = tok

            m = HIER_LABEL_RE.match(text)
            if m and cur_component is not None:
                flush_active()
                relations_started = True
                stage = "hier"
                hier_buffer = []
                if m.group(1):
                    hier_buffer.append(m.group(1))
                continue

            m = DEPS_LABEL_RE.match(text)
            if m and cur_component is not None:
                stage = "deps"
                deps_buffer = []
                if m.group(1):
                    deps_buffer.append(m.group(1))
                continue

            if stage == "hier":
                hier_buffer.append(text)
                continue
            if stage == "deps":
                deps_buffer.append(text)
                continue

            if text == "Component relationships":
                continue

            if active is not None:
                buffer.append(text)
                continue

            # Texto suelto que cae dentro de un elemento (continuacion de su
            # redaccion, p.ej. items a) b) c) )
            if cur_component is not None and cur_component.elements:
                cur_component.elements[-1][1] += "\n" + text
            elif cur_component is not None and not relations_started:
                # Texto suelto bajo el encabezado del componente, antes de
                # "Hierarchical to:"/elementos (p.ej. avisos de deprecacion).
                note_buffer.append(text)

    flush_hier_deps()
    flush_active()
    flush_note()
    return classes, families, components


# ----------------------------------------------------------------------------
# Parser de los anexos C-M (Application notes)
# ----------------------------------------------------------------------------

def parse_annexes(tokens, classes, families, components):
    cur_annex_class = None
    cur_family = None
    cur_component = None
    buffer = []
    target = None  # ('class', code) | ('family', code) | ('component', code)

    def flush():
        nonlocal buffer, target
        if not buffer or target is None:
            buffer = []
            return
        text = normalize_ws("\n".join(buffer))
        if not text:
            buffer = []
            return
        kind, code = target
        if kind == "class" and code in classes:
            c = classes[code]
            c.annex_general_notes = (c.annex_general_notes + "\n\n" + text).strip()
        elif kind == "family" and code in families:
            f = families[code]
            f.annex_notes = (f.annex_notes + "\n\n" + text).strip()
        elif kind == "component" and code in components:
            comp = components[code]
            comp.application_notes = (comp.application_notes + "\n\n" + text).strip()
        buffer = []

    for tok in tokens:
        kind = tok[0]
        if kind == "heading":
            _, num, title, page = tok

            m_annex = ANNEX_LINE_RE.match(num) if HEADING_BARE_RE.match(num) else None
            # El token 'num' aqui es el numero de seccion (p.ej "C.2.2"); el
            # marcador de anexo en si llega como texto plano "Annex C", lo
            # manejamos abajo via el stream de texto ademas.

            if title == "(normative)":
                continue

            m_app = APPNOTES_TITLE_RE.match(title)
            if m_app:
                flush()
                cur_annex_class = m_app.group(1)
                cur_family = None
                cur_component = None
                target = ("class", cur_annex_class)
                continue

            ctype, data = classify_heading(title)
            if ctype == "family":
                code, name = data
                flush()
                cur_family = code
                target = ("family", code)
            elif ctype == "component":
                code, name = data
                flush()
                cur_component = code
                target = ("component", code)
            elif ctype == "class":
                # No deberia pasar dentro de anexos, pero por si acaso.
                continue
            else:
                # Subtitulos genericos (General, User application notes,
                # Component rationale and application notes, Operations, ...)
                # No cambian el target activo; se añade el titulo como
                # separador dentro del texto.
                if target is not None:
                    buffer.append(title)

        elif kind == "element":
            # Dentro de los anexos no deberian aparecer, pero por robustez:
            _, code, text0, page = tok
            if target is not None:
                buffer.append(f"{code} {text0}")

        else:
            _, text, _, page = tok
            m = ANNEX_LINE_RE.match(text)
            if m:
                flush()
                letter = m.group(1)
                # el nombre de clase real se fija con el titulo
                # "Class XXX: ... Application notes" que viene despues
                target = None
                continue
            if text == "Component relationships":
                continue
            if target is not None:
                buffer.append(text)
            if text.strip() == "Bibliography":
                flush()
                return

    flush()


# ----------------------------------------------------------------------------
# Separar el stream de tokens en seccion "cuerpo" y seccion "anexos"
# ----------------------------------------------------------------------------

def split_tokens(tokens):
    body_tokens = []
    annex_tokens = []
    mode = "skip"
    for tok in tokens:
        kind = tok[0]
        if kind == "heading":
            title = tok[2]
            if mode == "skip":
                m = CLASS_TITLE_RE.match(title)
                if m and m.group(1) in VALID_CLASS_CODES:
                    mode = "body"
            elif mode == "body":
                if title in ("(normative)",) or APPNOTES_TITLE_RE.match(title):
                    mode = "annex_pending"
        if kind == "text" and tok[1].strip() == "Annex A":
            if mode == "body":
                mode = "skip2"
        if kind == "text" and ANNEX_LINE_RE.match(tok[1].strip()):
            letter = tok[1].strip()[-1]
            if letter == "C":
                mode = "annex"
        if kind == "text" and tok[1].strip() == "Bibliography":
            if mode == "annex":
                annex_tokens.append(tok)
                mode = "done"
                continue

        if mode == "body":
            body_tokens.append(tok)
        elif mode == "annex":
            annex_tokens.append(tok)
        elif mode == "annex_pending":
            # headings "(normative)"/titulo de anexo se gestionan en el modo
            # annex; promovemos aqui tambien para no perder la transicion.
            annex_tokens.append(tok)
    return body_tokens, annex_tokens


# ----------------------------------------------------------------------------
# Construccion de la base de datos
# ----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE classes (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    annex_letter TEXT,
    annex_general_notes TEXT,
    page_pdf INTEGER,
    ord INTEGER
);

CREATE TABLE families (
    code TEXT PRIMARY KEY,
    class_code TEXT NOT NULL REFERENCES classes(code),
    name TEXT NOT NULL,
    behaviour TEXT,
    leveling TEXT,
    annex_notes TEXT,
    page_pdf INTEGER,
    ord INTEGER
);

CREATE TABLE components (
    code TEXT PRIMARY KEY,
    family_code TEXT NOT NULL REFERENCES families(code),
    class_code TEXT NOT NULL REFERENCES classes(code),
    name TEXT NOT NULL,
    hierarchical_to_text TEXT,
    hierarchical_to_code TEXT,
    dependencies_text TEXT,
    management_text TEXT,
    audit_text TEXT,
    application_notes TEXT,
    notes TEXT,
    page_pdf INTEGER,
    ord INTEGER
);

CREATE TABLE elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_code TEXT NOT NULL REFERENCES components(code),
    element_code TEXT NOT NULL,
    text TEXT NOT NULL,
    ord INTEGER
);

CREATE TABLE dependencies (
    component_code TEXT NOT NULL REFERENCES components(code),
    depends_on_code TEXT NOT NULL,
    PRIMARY KEY (component_code, depends_on_code)
);

CREATE INDEX idx_families_class ON families(class_code);
CREATE INDEX idx_components_family ON components(family_code);
CREATE INDEX idx_components_class ON components(class_code);
CREATE INDEX idx_elements_component ON elements(component_code);
CREATE INDEX idx_deps_component ON dependencies(component_code);
CREATE INDEX idx_deps_target ON dependencies(depends_on_code);

CREATE VIRTUAL TABLE search_index USING fts5(
    ref_type,
    ref_code,
    class_code,
    family_code,
    title,
    content,
    tokenize = "unicode61 remove_diacritics 2"
);

CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def build_database(classes, families, components, db_path):
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.executescript(SCHEMA)

    class_order = sorted(classes.values(), key=lambda c: c.page)
    for i, c in enumerate(class_order):
        cur.execute(
            "INSERT INTO classes (code, name, description, annex_letter, annex_general_notes, page_pdf, ord) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (c.code, c.name, c.description, c.annex_letter, c.annex_general_notes, c.page, i),
        )
        search_text = f"{c.code} Class {c.code} {c.name} {c.description}"
        cur.execute(
            "INSERT INTO search_index (ref_type, ref_code, class_code, family_code, title, content) "
            "VALUES ('class', ?, ?, NULL, ?, ?)",
            (c.code, c.code, f"{c.code} - {c.name}", search_text),
        )

    family_order = sorted(families.values(), key=lambda f: f.page)
    for i, f in enumerate(family_order):
        cur.execute(
            "INSERT INTO families (code, class_code, name, behaviour, leveling, annex_notes, page_pdf, ord) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f.code, f.class_code, f.name, f.behaviour, f.leveling, f.annex_notes, f.page, i),
        )
        search_text = f"{f.code} {f.name} {f.behaviour} {f.leveling} {f.annex_notes}"
        cur.execute(
            "INSERT INTO search_index (ref_type, ref_code, class_code, family_code, title, content) "
            "VALUES ('family', ?, ?, ?, ?, ?)",
            (f.code, f.class_code, f.code, f"{f.code} - {f.name}", search_text),
        )

    component_order = sorted(components.values(), key=lambda c: c.page)
    for i, comp in enumerate(component_order):
        cur.execute(
            "INSERT INTO components (code, family_code, class_code, name, hierarchical_to_text, "
            "hierarchical_to_code, dependencies_text, management_text, audit_text, application_notes, "
            "notes, page_pdf, ord) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                comp.code, comp.family_code, comp.class_code, comp.name,
                comp.hierarchical_to_text, comp.hierarchical_to_code, comp.dependencies_text,
                comp.management_text, comp.audit_text, comp.application_notes, comp.notes, comp.page, i,
            ),
        )
        for dep_code in comp.dependencies_codes:
            cur.execute(
                "INSERT OR IGNORE INTO dependencies (component_code, depends_on_code) VALUES (?, ?)",
                (comp.code, dep_code),
            )
        elem_text_all = []
        for j, (ecode, etext) in enumerate(comp.elements):
            etext_norm = normalize_ws(etext)
            cur.execute(
                "INSERT INTO elements (component_code, element_code, text, ord) VALUES (?, ?, ?, ?)",
                (comp.code, ecode, etext_norm, j),
            )
            elem_text_all.append(f"{ecode} {etext_norm}")
        search_text = (
            f"{comp.code} {comp.name} {' '.join(elem_text_all)} "
            f"{comp.management_text} {comp.audit_text} {comp.application_notes} "
            f"{comp.hierarchical_to_text} {comp.dependencies_text} {comp.notes}"
        )
        cur.execute(
            "INSERT INTO search_index (ref_type, ref_code, class_code, family_code, title, content) "
            "VALUES ('component', ?, ?, ?, ?, ?)",
            (comp.code, comp.class_code, comp.family_code, f"{comp.code} - {comp.name}", search_text),
        )

    con.commit()
    return con


# ----------------------------------------------------------------------------
# Verificacion
# ----------------------------------------------------------------------------

def verify(con):
    cur = con.cursor()
    report = []

    n_classes = cur.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    n_families = cur.execute("SELECT COUNT(*) FROM families").fetchone()[0]
    n_components = cur.execute("SELECT COUNT(*) FROM components").fetchone()[0]
    n_elements = cur.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
    n_deps = cur.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0]

    report.append("=" * 70)
    report.append("REPORTE DE VERIFICACION - CCMB build_db.py")
    report.append("=" * 70)
    report.append(f"Clases cargadas:       {n_classes} (esperado: 11)")
    report.append(f"Familias cargadas:     {n_families}")
    report.append(f"Componentes cargados:  {n_components}")
    report.append(f"Elementos cargados:    {n_elements}")
    report.append(f"Dependencias cargadas: {n_deps}")
    report.append("")

    if n_classes != 11:
        report.append("!! ADVERTENCIA: se esperaban 11 clases.")

    # Chequeos puntuales pedidos
    def get_deps(code):
        rows = cur.execute(
            "SELECT depends_on_code FROM dependencies WHERE component_code=? ORDER BY depends_on_code", (code,)
        ).fetchall()
        return sorted(r[0] for r in rows)

    arp1 = get_deps("FAU_ARP.1")
    ok_arp1 = arp1 == ["FAU_SAA.1"]
    report.append(f"FAU_ARP.1 Dependencies = {arp1}  -> {'OK' if ok_arp1 else 'FALLO (esperado [FAU_SAA.1])'}")

    gen2 = get_deps("FAU_GEN.2")
    ok_gen2 = gen2 == ["FAU_GEN.1", "FIA_UID.1"]
    report.append(f"FAU_GEN.2 Dependencies = {gen2}  -> {'OK' if ok_gen2 else 'FALLO (esperado [FAU_GEN.1, FIA_UID.1])'}")
    report.append("")

    # Componentes incompletos: sin elementos, o con 0 familia, o textos vacios
    incomplete = cur.execute(
        "SELECT code, notes FROM components WHERE code NOT IN (SELECT DISTINCT component_code FROM elements)"
    ).fetchall()
    real_incomplete = [c for c, notes in incomplete if not notes]
    if incomplete:
        report.append(f"Componentes SIN elementos ({len(incomplete)}):")
        for code, notes in incomplete:
            if notes:
                report.append(f"  - {code}  (deprecado/sin elementos en el PDF: \"{notes[:70]}...\")")
            else:
                report.append(f"  - {code}  <-- SOSPECHOSO, revisar parser")
    else:
        report.append("Todos los componentes tienen al menos un elemento. OK")

    no_appnotes = cur.execute(
        "SELECT code FROM components WHERE application_notes IS NULL OR application_notes = ''"
    ).fetchall()
    report.append("")
    report.append(f"Componentes sin 'Application notes' asociadas: {len(no_appnotes)}")
    if no_appnotes and len(no_appnotes) <= 30:
        for (code,) in no_appnotes:
            report.append(f"  - {code}")

    report.append("")
    report.append("Clases encontradas:")
    for row in cur.execute("SELECT code, name, (SELECT COUNT(*) FROM families f WHERE f.class_code=classes.code) FROM classes ORDER BY ord"):
        report.append(f"  {row[0]:4s} {row[1]:40s} familias: {row[2]}")

    report.append("=" * 70)
    return "\n".join(report), ok_arp1 and ok_gen2 and n_classes == 11 and len(real_incomplete) == 0


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "CC2022PART2R1.pdf"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "ccmb.db"

    print(f"Leyendo PDF: {pdf_path}")
    lines_with_pages = list(iter_doc_lines(pdf_path))
    print(f"Lineas de texto extraidas (limpias): {len(lines_with_pages)}")

    tokens = tokenize(lines_with_pages)
    print(f"Tokens generados: {len(tokens)}")

    body_tokens, annex_tokens = split_tokens(tokens)
    print(f"Tokens cuerpo: {len(body_tokens)}  Tokens anexos: {len(annex_tokens)}")

    classes, families, components = parse_body(body_tokens)
    parse_annexes(annex_tokens, classes, families, components)

    # asignar letra de anexo a cada clase segun el orden fijo C..M
    class_codes_in_order = [c.code for c in sorted(classes.values(), key=lambda c: c.page)]
    for letter, code in zip(ANNEX_LETTERS, class_codes_in_order):
        if code in classes:
            classes[code].annex_letter = letter

    con = build_database(classes, families, components, db_path)
    report, ok = verify(con)
    print(report)
    con.close()

    print()
    if ok:
        print(f"Base de datos generada correctamente en: {db_path}")
    else:
        print("ATENCION: hay advertencias/fallos en la verificacion (ver arriba).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
