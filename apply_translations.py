#!/usr/bin/env python3
"""Fusiona los lotes traducidos (translation_batches/batchN_es.json) en
ccmb.db: agrega columnas _es a classes/families/components/elements y
las completa. Tambien agrega el texto en espanol al indice de busqueda
(search_index) para que la busqueda funcione sin importar el idioma
que escriba el usuario. No modifica el contenido original en ingles.
"""
import glob
import json
import sqlite3

DB = "ccmb.db"

ALTER_STATEMENTS = [
    "ALTER TABLE classes ADD COLUMN name_es TEXT",
    "ALTER TABLE classes ADD COLUMN description_es TEXT",
    "ALTER TABLE classes ADD COLUMN annex_general_notes_es TEXT",
    "ALTER TABLE families ADD COLUMN name_es TEXT",
    "ALTER TABLE families ADD COLUMN behaviour_es TEXT",
    "ALTER TABLE families ADD COLUMN leveling_es TEXT",
    "ALTER TABLE families ADD COLUMN annex_notes_es TEXT",
    "ALTER TABLE components ADD COLUMN name_es TEXT",
    "ALTER TABLE components ADD COLUMN hierarchical_to_text_es TEXT",
    "ALTER TABLE components ADD COLUMN dependencies_text_es TEXT",
    "ALTER TABLE components ADD COLUMN management_text_es TEXT",
    "ALTER TABLE components ADD COLUMN audit_text_es TEXT",
    "ALTER TABLE components ADD COLUMN application_notes_es TEXT",
    "ALTER TABLE components ADD COLUMN notes_es TEXT",
    "ALTER TABLE elements ADD COLUMN text_es TEXT",
]


def ensure_columns(con):
    cur = con.cursor()
    for stmt in ALTER_STATEMENTS:
        try:
            cur.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
    con.commit()


def apply_batch(con, data):
    cur = con.cursor()
    n_classes = n_families = n_components = n_elements = 0
    for cls in data["classes"]:
        cur.execute(
            "UPDATE classes SET name_es=?, description_es=?, annex_general_notes_es=? WHERE code=?",
            (cls.get("name_es"), cls.get("description_es"), cls.get("annex_general_notes_es"), cls["code"]),
        )
        n_classes += 1
        for fam in cls["families"]:
            cur.execute(
                "UPDATE families SET name_es=?, behaviour_es=?, leveling_es=?, annex_notes_es=? WHERE code=?",
                (
                    fam.get("name_es"), fam.get("behaviour_es"), fam.get("leveling_es"),
                    fam.get("annex_notes_es"), fam["code"],
                ),
            )
            n_families += 1
            for comp in fam["components"]:
                cur.execute(
                    """UPDATE components SET name_es=?, hierarchical_to_text_es=?,
                       dependencies_text_es=?, management_text_es=?, audit_text_es=?,
                       application_notes_es=?, notes_es=? WHERE code=?""",
                    (
                        comp.get("name_es"), comp.get("hierarchical_to_text_es"),
                        comp.get("dependencies_text_es"), comp.get("management_text_es"),
                        comp.get("audit_text_es"), comp.get("application_notes_es"),
                        comp.get("notes_es"), comp["code"],
                    ),
                )
                n_components += 1
                for el in comp["elements"]:
                    cur.execute(
                        "UPDATE elements SET text_es=? WHERE component_code=? AND element_code=?",
                        (el.get("text_es"), comp["code"], el["element_code"]),
                    )
                    n_elements += 1
    con.commit()
    return n_classes, n_families, n_components, n_elements


def rebuild_search_index_es(con):
    """Agrega el contenido en espanol al texto indexado de busqueda,
    concatenado al ingles existente, para que ambos idiomas sean buscables."""
    cur = con.cursor()

    for row in con.execute(
        "SELECT code, name_es, description_es, annex_general_notes_es FROM classes"
    ):
        extra = " ".join(filter(None, [row[1], row[2], row[3]]))
        if extra:
            cur.execute(
                "UPDATE search_index SET content = content || ' ' || ? WHERE ref_type='class' AND ref_code=?",
                (extra, row[0]),
            )

    for row in con.execute(
        "SELECT code, name_es, behaviour_es, leveling_es, annex_notes_es FROM families"
    ):
        extra = " ".join(filter(None, [row[1], row[2], row[3], row[4]]))
        if extra:
            cur.execute(
                "UPDATE search_index SET content = content || ' ' || ? WHERE ref_type='family' AND ref_code=?",
                (extra, row[0]),
            )

    for row in con.execute(
        """SELECT c.code, c.name_es, c.management_text_es, c.audit_text_es,
                  c.application_notes_es, c.notes_es,
                  (SELECT GROUP_CONCAT(text_es, ' ') FROM elements e WHERE e.component_code=c.code) elems_es
           FROM components c"""
    ):
        extra = " ".join(filter(None, [row[1], row[2], row[3], row[4], row[5], row[6]]))
        if extra:
            cur.execute(
                "UPDATE search_index SET content = content || ' ' || ? WHERE ref_type='component' AND ref_code=?",
                (extra, row[0]),
            )
    con.commit()


def main():
    con = sqlite3.connect(DB)
    ensure_columns(con)

    files = sorted(glob.glob("translation_batches/batch*_es.json"))
    if not files:
        print("No se encontraron archivos translation_batches/batch*_es.json")
        return 1

    totals = [0, 0, 0, 0]
    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        counts = apply_batch(con, data)
        totals = [a + b for a, b in zip(totals, counts)]
        print(f"{path}: clases={counts[0]} familias={counts[1]} componentes={counts[2]} elementos={counts[3]}")

    print("\nActualizando indice de busqueda con contenido en espanol...")
    rebuild_search_index_es(con)

    print(f"\nTOTAL: clases={totals[0]} familias={totals[1]} componentes={totals[2]} elementos={totals[3]}")

    # Verificacion: contar columnas _es nulas o vacias
    cur = con.cursor()
    missing = cur.execute(
        "SELECT COUNT(*) FROM components WHERE name_es IS NULL OR name_es=''"
    ).fetchone()[0]
    print(f"Componentes sin name_es: {missing} (deberia ser 0)")
    missing_el = cur.execute(
        "SELECT COUNT(*) FROM elements WHERE text_es IS NULL OR text_es=''"
    ).fetchone()[0]
    print(f"Elementos sin text_es: {missing_el} (deberia ser 0)")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
