"""Tema visual de CCMB: dashboard oscuro violeta/magenta (paleta tomada de la
imagen de fondo), con cuerpo y sombra real, sidebar de navegacion."""

# Fondo (tonos tomados de la nebulosa de assets/hero_background.jpg)
BG_TOP = "#1d1640"
BG_BOTTOM = "#0c0918"
SIDEBAR_BG = "#120d1f"

# Tarjetas / paneles: color opaco con cuerpo (no transparencia tipo vidrio),
# gradiente sutil para dar volumen + sombra aplicada aparte via apply_glow.
CARD_GRAD = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #251c48, stop:1 #180f2d)"
CARD_GRAD_SOFT = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b2250, stop:1 #1f1739)"
CARD_BORDER = "rgba(255, 255, 255, 0.07)"
CARD_BORDER_TOP = "rgba(255, 255, 255, 0.16)"
CARD_BG_SOLID = "#1d1731"

# Acentos (violeta/magenta vivido, igual que los tonos dominantes de la nebulosa)
VIOLET = "#9b59f6"
VIOLET_SOFT = "rgba(155, 89, 246, 0.20)"
CYAN = "#2dd4bf"
MAGENTA = "#d6479b"
GREEN = "#4ade80"
AMBER = "#fbbf24"

# Compatibilidad con nombres previos usados en otros modulos
BG_DEEP = BG_BOTTOM
BG_PANEL = CARD_GRAD
CARD_BG = CARD_GRAD

TEXT_PRIMARY = "#f3f1fb"
TEXT_SECONDARY = "#a69fc4"
TEXT_MUTED = "#6e6690"

FONT_DISPLAY = "Rajdhani"
FONT_UI = "Rajdhani"
FONT_BODY = "Segoe UI"


def build_stylesheet(icons_dir):
    """Arma el QSS completo. icons_dir: carpeta absoluta con los chevron_*.png
    usados como indicadores de expandir/colapsar en el arbol."""
    def icon_url(name):
        path = f"{icons_dir}/{name}".replace("\\", "/")
        return f'url("{path}")'

    return f"""
* {{
    outline: none;
}}

QMainWindow, QWidget#rootBackground {{
    background: transparent;
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "{FONT_BODY}", "Cantarell", sans-serif;
    font-size: 13px;
}}

/* ---------- Pantalla de inicio (landing) ---------- */
QWidget#homePage {{
    background: transparent;
}}

QLabel#navTitle {{
    color: {TEXT_PRIMARY};
    font-family: "{FONT_DISPLAY}", sans-serif;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#navBadge {{
    color: {TEXT_SECONDARY};
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
    padding: 5px 14px;
    font-family: "{FONT_UI}", sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#heroEyebrow {{
    color: {VIOLET};
    font-family: "{FONT_UI}", sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
}}

QLabel#heroHeading {{
    color: {TEXT_PRIMARY};
    font-family: "{FONT_DISPLAY}", sans-serif;
    font-size: 36px;
    font-weight: 700;
    margin-top: 4px;
    margin-bottom: 2px;
}}

QLabel#heroDesc {{
    color: {TEXT_SECONDARY};
    font-size: 14.5px;
    line-height: 1.6;
    margin-top: 6px;
}}

QLabel#featureValue {{
    color: {VIOLET};
    font-family: "{FONT_DISPLAY}", sans-serif;
    font-size: 22px;
    font-weight: 700;
}}

QLabel#featureLabel {{
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QWidget#searchCard {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(44, 32, 78, 0.62), stop:1 rgba(20, 14, 34, 0.68));
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-top: 1px solid rgba(255, 255, 255, 0.30);
    border-radius: 22px;
}}

QWidget#logoBadge {{
    background: qradialgradient(cx:0.5, cy:0.42, radius:0.85, fx:0.5, fy:0.35,
        stop:0 #4a3580, stop:0.55 #2c1f52, stop:1 #170f28);
    border: 1px solid rgba(155, 89, 246, 0.45);
    border-radius: 38px;
}}

QLabel#statusBarText {{
    color: rgba(255, 255, 255, 0.45);
    font-family: "{FONT_UI}", sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

QLineEdit#searchBarHome {{
    background: {CARD_GRAD};
    border: 1px solid {CARD_BORDER};
    border-top: 1px solid {CARD_BORDER_TOP};
    border-radius: 27px;
    padding: 13px 26px;
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 17px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    selection-background-color: {VIOLET};
}}

QLineEdit#searchBarHome:focus {{
    border: 1px solid {VIOLET};
}}

QPushButton#homeSearchBtn {{
    background: {VIOLET};
    border: none;
    border-radius: 9px;
    padding: 10px 22px;
    color: #15101f;
    font-family: "{FONT_UI}", sans-serif;
    font-size: 12.5px;
    font-weight: 800;
}}

QPushButton#homeSearchBtn:hover {{
    background: #a090ff;
}}

QPushButton#homeSearchBtn:pressed {{
    background: #7363e0;
}}

QPushButton#linkButton {{
    background: transparent;
    border: none;
    padding: 10px 10px;
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", sans-serif;
    font-size: 12px;
    font-weight: 700;
}}

QPushButton#linkButton:hover {{
    color: {VIOLET};
}}

QLabel#recentLabel {{
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 1.8px;
}}

QPushButton#recentChip {{
    background: {CARD_GRAD_SOFT};
    border: 1px solid {CARD_BORDER};
    border-top: 1px solid {CARD_BORDER_TOP};
    border-radius: 9px;
    padding: 8px 14px;
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#recentChip:hover {{
    border: 1px solid {VIOLET};
    color: {TEXT_PRIMARY};
    background: {VIOLET_SOFT};
}}

/* ---------- Pagina de exploracion ---------- */
QWidget#browsePage {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {BG_TOP}, stop:1 {BG_BOTTOM});
}}

QWidget#sidebar {{
    background: {SIDEBAR_BG};
    border-right: 1px solid {CARD_BORDER};
}}

QPushButton#logoButton {{
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 4px;
}}

QPushButton#logoButton:hover {{
    background: rgba(255, 255, 255, 0.045);
}}

QLabel#appTitle {{
    color: {TEXT_PRIMARY};
    font-family: "{FONT_DISPLAY}", sans-serif;
    font-size: 19px;
    font-weight: 700;
}}

QLabel#appSubtitle {{
    color: {TEXT_MUTED};
    font-family: "{FONT_UI}", sans-serif;
    font-size: 10px;
    font-weight: 600;
}}

QLabel#chipClasses, QLabel#chipFamilies, QLabel#chipComponents {{
    font-family: "{FONT_UI}", sans-serif;
    font-size: 11px;
    font-weight: 700;
    border-radius: 9px;
    padding: 7px 10px;
}}

QLabel#chipClasses {{
    color: {VIOLET};
    background: rgba(155, 89, 246, 0.14);
    border: 1px solid rgba(155, 89, 246, 0.30);
}}

QLabel#chipFamilies {{
    color: {CYAN};
    background: rgba(45, 212, 191, 0.12);
    border: 1px solid rgba(45, 212, 191, 0.28);
}}

QLabel#chipComponents {{
    color: {AMBER};
    background: rgba(251, 191, 36, 0.12);
    border: 1px solid rgba(251, 191, 36, 0.28);
}}

/* ---------- Busqueda ---------- */
QLineEdit#searchBar {{
    background: {CARD_GRAD};
    border: 1px solid {CARD_BORDER};
    border-top: 1px solid {CARD_BORDER_TOP};
    border-radius: 14px;
    padding: 11px 18px;
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    selection-background-color: {VIOLET};
}}

QLineEdit#searchBar:focus {{
    border: 1px solid {VIOLET};
    background: {CARD_GRAD};
}}

/* ---------- Botones ---------- */
QPushButton {{
    background: {CARD_GRAD_SOFT};
    border: 1px solid {CARD_BORDER};
    border-top: 1px solid {CARD_BORDER_TOP};
    border-radius: 9px;
    padding: 8px 14px;
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 11.5px;
    font-weight: 700;
}}

QPushButton:hover {{
    border: 1px solid {VIOLET};
    color: {TEXT_PRIMARY};
    background: {VIOLET_SOFT};
}}

QPushButton:pressed {{
    background: rgba(155, 89, 246, 0.38);
    border-top: 1px solid {CARD_BORDER};
}}

QPushButton:disabled {{
    color: {TEXT_MUTED};
    border: 1px solid rgba(255, 255, 255, 0.04);
    background: rgba(255, 255, 255, 0.015);
}}

QFrame#toolbarSep {{
    background: {CARD_BORDER};
}}

QSplitter::handle {{
    background: transparent;
}}

/* ---------- Arbol (menu del sidebar) ---------- */
QTreeWidget {{
    background: transparent;
    border: none;
    padding: 2px 4px;
    show-decoration-selected: 1;
}}

QTreeWidget::item {{
    padding: 7px 8px;
    margin: 1px 0px;
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 13.5px;
    font-weight: 600;
}}

QTreeWidget::item:hover {{
    background: rgba(255, 255, 255, 0.055);
    color: {TEXT_PRIMARY};
}}

QTreeWidget::item:selected {{
    background: {VIOLET};
    color: #ffffff;
}}

QTreeView::branch {{
    background: transparent;
}}

QTreeView::branch:selected {{
    background: {VIOLET};
}}

QTreeView::branch:has-children:closed {{
    image: {icon_url("chevron_right.png")};
}}

QTreeView::branch:has-children:open {{
    image: {icon_url("chevron_down.png")};
}}

/* ---------- Panel de detalle ---------- */
QTextBrowser#detailPanel {{
    background: {CARD_GRAD};
    border: 1px solid {CARD_BORDER};
    border-top: 1px solid {CARD_BORDER_TOP};
    border-radius: 18px;
    padding: 30px 38px;
    selection-background-color: {VIOLET};
}}

QWidget#toolbar, QWidget#mainArea, QWidget#headerBar {{
    background: transparent;
}}

QLabel#crumbs {{
    color: {TEXT_MUTED};
    font-family: "{FONT_UI}", "{FONT_BODY}", sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 3px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.16);
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {VIOLET};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 9px;
    margin: 3px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(255, 255, 255, 0.16);
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {VIOLET};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QToolTip {{
    background: {CARD_BG_SOLID};
    color: {TEXT_PRIMARY};
    border: 1px solid {CARD_BORDER};
    padding: 4px;
}}

QStatusBar {{
    background: transparent;
    color: {TEXT_MUTED};
}}
"""


DETAIL_HTML_CSS = f"""
body {{ color: {TEXT_PRIMARY}; font-family: "{FONT_BODY}", sans-serif; font-size: 14px; line-height: 1.65; }}
h1 {{ color: {TEXT_PRIMARY}; font-family: "{FONT_DISPLAY}", sans-serif; font-size: 25px; font-weight: 700; margin-bottom: 4px; }}
h2 {{ color: {TEXT_SECONDARY}; font-family: "{FONT_UI}", sans-serif; font-size: 12.5px; font-weight: 700; letter-spacing: 1.4px;
      text-transform: uppercase; margin-top: 26px; padding-bottom: 6px; border-bottom: 1px solid {CARD_BORDER}; }}
.subtitle {{ color: {TEXT_SECONDARY}; font-family: "{FONT_UI}", sans-serif; font-weight: 600; font-size: 16px; margin-bottom: 10px; }}
.meta {{ color: {TEXT_SECONDARY}; margin-bottom: 4px; }}
.badge {{ color: #1d1731; background: {VIOLET}; padding: 2px 10px; border-radius: 10px; font-family: "{FONT_UI}", sans-serif;
          font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px; }}
.badge-violet {{ color: {TEXT_PRIMARY}; background: rgba(155,89,246,0.22); border: 1px solid rgba(155,89,246,0.4);
                  padding: 2px 10px; border-radius: 10px; font-family: "{FONT_UI}", sans-serif;
                  font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px; }}
.note {{ background: rgba(251, 113, 133, 0.10); border-left: 3px solid {MAGENTA}; padding: 10px 14px; margin: 10px 0; color: #ffb4c0; border-radius: 0 8px 8px 0; }}
a {{ color: {CYAN}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.elem-code {{ color: {VIOLET}; font-family: "{FONT_UI}", sans-serif; font-weight: 700; font-size: 15px; }}
.dep-missing {{ color: {TEXT_MUTED}; font-style: italic; }}
.hl {{ background: rgba(251, 113, 133, 0.38); color: #fff; border-radius: 2px; }}
ul {{ margin-top: 6px; }}
li {{ margin-bottom: 6px; }}
.page-tag {{ color: {TEXT_MUTED}; font-size: 12px; margin-bottom: 16px; }}
"""
