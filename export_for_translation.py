#!/usr/bin/env python3
"""Exporta el contenido traducible de ccmb.db a lotes JSON para traducir.
No modifica la base. Genera translation_batches/batchN.json
"""
import json
import os
import sqlite3

DB = "ccmb.db"
OUT_DIR = "translation_batches"

# Agrupamos clases en lotes balanceados por cantidad de componentes.
BATCHES = [
    ["FDP"],
    ["FPT"],
    ["FAU", "FIA", "FCO"],
    ["FMT", "FCS", "FTP"],
    ["FPR", "FTA", "FRU"],
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    for i, class_codes in enumerate(BATCHES, start=1):
        batch = {"classes": []}
        for ccode in class_codes:
            cls = con.execute("SELECT * FROM classes WHERE code=?", (ccode,)).fetchone()
            class_obj = {
                "code": cls["code"],
                "name": cls["name"],
                "name_es": None,
                "description": cls["description"],
                "description_es": None,
                "annex_general_notes": cls["annex_general_notes"],
                "annex_general_notes_es": None,
                "families": [],
            }
            for fam in con.execute(
                "SELECT * FROM families WHERE class_code=? ORDER BY ord", (ccode,)
            ):
                fam_obj = {
                    "code": fam["code"],
                    "name": fam["name"],
                    "name_es": None,
                    "behaviour": fam["behaviour"],
                    "behaviour_es": None,
                    "leveling": fam["leveling"],
                    "leveling_es": None,
                    "annex_notes": fam["annex_notes"],
                    "annex_notes_es": None,
                    "components": [],
                }
                for comp in con.execute(
                    "SELECT * FROM components WHERE family_code=? ORDER BY ord", (fam["code"],)
                ):
                    comp_obj = {
                        "code": comp["code"],
                        "name": comp["name"],
                        "name_es": None,
                        "hierarchical_to_text": comp["hierarchical_to_text"],
                        "hierarchical_to_text_es": None,
                        "dependencies_text": comp["dependencies_text"],
                        "dependencies_text_es": None,
                        "management_text": comp["management_text"],
                        "management_text_es": None,
                        "audit_text": comp["audit_text"],
                        "audit_text_es": None,
                        "application_notes": comp["application_notes"],
                        "application_notes_es": None,
                        "notes": comp["notes"],
                        "notes_es": None,
                        "elements": [],
                    }
                    for el in con.execute(
                        "SELECT * FROM elements WHERE component_code=? ORDER BY ord",
                        (comp["code"],),
                    ):
                        comp_obj["elements"].append(
                            {"element_code": el["element_code"], "text": el["text"], "text_es": None}
                        )
                    fam_obj["components"].append(comp_obj)
                class_obj["families"].append(fam_obj)
            batch["classes"].append(class_obj)

        path = os.path.join(OUT_DIR, f"batch{i}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=1)
        words = sum(
            len((c["description"] or "").split())
            + sum(
                len((fm["behaviour"] or "").split()) + len((fm["leveling"] or "").split())
                + len((fm["annex_notes"] or "").split())
                + sum(
                    len((cp["management_text"] or "").split())
                    + len((cp["audit_text"] or "").split())
                    + len((cp["application_notes"] or "").split())
                    + sum(len((e["text"] or "").split()) for e in cp["elements"])
                    for cp in fm["components"]
                )
                for fm in c["families"]
            )
            for c in batch["classes"]
        )
        n_comp = sum(len(fm["components"]) for c in batch["classes"] for fm in c["families"])
        print(f"batch{i}.json: clases={class_codes} componentes={n_comp} ~palabras={words}")

    con.close()


if __name__ == "__main__":
    main()
