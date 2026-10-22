"""Capa de acceso a datos para CCMB. Lee ccmb.db (SQLite generado por build_db.py)."""
import os
import re
import sys
import sqlite3
from functools import lru_cache

DB_FILENAME = "ccmb.db"


def resource_path(filename):
    """Resuelve la ruta de un recurso tanto en desarrollo como empaquetado
    con PyInstaller (sys._MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or resource_path(DB_FILENAME)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"No se encontro la base de datos: {self.db_path}")
        self.con = sqlite3.connect(self.db_path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row

    # -- Clases -----------------------------------------------------------

    def get_classes(self):
        return self.con.execute(
            "SELECT code, name, name_es, page_pdf, annex_letter FROM classes ORDER BY ord"
        ).fetchall()

    def get_class(self, code):
        return self.con.execute("SELECT * FROM classes WHERE code=?", (code,)).fetchone()

    def get_class_detail(self, code):
        cls = self.get_class(code)
        if cls is None:
            return None
        families = self.con.execute(
            "SELECT code, name, name_es, page_pdf FROM families WHERE class_code=? ORDER BY ord", (code,)
        ).fetchall()
        return {"class": cls, "families": families}

    # -- Familias -----------------------------------------------------------

    def get_families(self, class_code):
        return self.con.execute(
            "SELECT code, name, name_es, page_pdf FROM families WHERE class_code=? ORDER BY ord", (class_code,)
        ).fetchall()

    def get_family(self, code):
        return self.con.execute("SELECT * FROM families WHERE code=?", (code,)).fetchone()

    def get_family_detail(self, code):
        fam = self.get_family(code)
        if fam is None:
            return None
        cls = self.get_class(fam["class_code"])
        components = self.con.execute(
            "SELECT code, name, name_es, page_pdf FROM components WHERE family_code=? ORDER BY ord", (code,)
        ).fetchall()
        return {"family": fam, "class": cls, "components": components}

    # -- Componentes --------------------------------------------------------

    def get_components(self, family_code):
        return self.con.execute(
            "SELECT code, name, name_es, page_pdf FROM components WHERE family_code=? ORDER BY ord", (family_code,)
        ).fetchall()

    def get_component(self, code):
        return self.con.execute("SELECT * FROM components WHERE code=?", (code,)).fetchone()

    def component_exists(self, code):
        row = self.con.execute("SELECT 1 FROM components WHERE code=?", (code,)).fetchone()
        return row is not None

    def get_component_detail(self, code):
        comp = self.get_component(code)
        if comp is None:
            return None
        family = self.get_family(comp["family_code"])
        cls = self.get_class(comp["class_code"])
        elements = self.con.execute(
            "SELECT element_code, text, text_es FROM elements WHERE component_code=? ORDER BY ord", (code,)
        ).fetchall()

        dep_codes = [r[0] for r in self.con.execute(
            "SELECT depends_on_code FROM dependencies WHERE component_code=? ORDER BY depends_on_code", (code,)
        ).fetchall()]
        dependencies = [self._resolve_ref(c) for c in dep_codes]

        reverse_codes = [r[0] for r in self.con.execute(
            "SELECT component_code FROM dependencies WHERE depends_on_code=? ORDER BY component_code", (code,)
        ).fetchall()]
        reverse_dependencies = [self._resolve_ref(c) for c in reverse_codes]

        hier_code = comp["hierarchical_to_code"]
        hierarchical_to = self._resolve_ref(hier_code) if hier_code else None

        return {
            "component": comp,
            "family": family,
            "class": cls,
            "elements": elements,
            "dependencies": dependencies,
            "reverse_dependencies": reverse_dependencies,
            "hierarchical_to": hierarchical_to,
        }

    def _resolve_ref(self, code):
        comp = self.get_component(code)
        if comp:
            return {"code": code, "name": comp["name"], "name_es": comp["name_es"], "exists": True}
        return {"code": code, "name": None, "name_es": None, "exists": False}

    # -- Busqueda -------------------------------------------------------------

    def search(self, query_text):
        """Devuelve dict con sets de codigos encontrados por tipo:
        {'class': set(), 'family': set(), 'component': set()} y una lista
        ordenada por relevancia de (ref_type, ref_code, title)."""
        tokens = re.findall(r"\w+", query_text, re.UNICODE)
        result = {"class": set(), "family": set(), "component": set(), "ranked": []}
        if not tokens:
            return result
        expr = " AND ".join(f"{_escape_token(t)}*" for t in tokens)
        try:
            rows = self.con.execute(
                "SELECT ref_type, ref_code, title FROM search_index "
                "WHERE search_index MATCH ? ORDER BY bm25(search_index)",
                (expr,),
            ).fetchall()
        except sqlite3.OperationalError:
            return result
        for row in rows:
            result[row["ref_type"]].add(row["ref_code"])
            result["ranked"].append((row["ref_type"], row["ref_code"], row["title"]))
        return result


def _escape_token(tok):
    return tok
