"""CCMB - Common Criteria CC:2022 Parte 2 - Base de consulta.
Punto de entrada de la aplicacion de escritorio (PySide6)."""
import json
import os
import re
import sys

from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QSettings, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QColor, QBrush, QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QTextBrowser, QMainWindow,
    QSizePolicy, QFrame, QStackedWidget, QGraphicsOpacityEffect,
)

from . import theme, render
from .db import Database, resource_path
from .widgets import HeroBackground, GlowLineEdit, apply_glow, make_dot_icon, CLASS_PALETTE


class CCMBWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCMB - Common Criteria CC:2022 Parte 2")
        self.setMinimumSize(980, 820)
        self.resize(1400, 860)

        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db = Database()
        self.tree_items = {}
        self._family_rows = {r["code"]: r for r in self.db.con.execute(
            "SELECT code, class_code FROM families")}
        self._component_rows = {r["code"]: r for r in self.db.con.execute(
            "SELECT code, family_code, class_code FROM components")}

        self.history = []
        self.history_index = -1
        self.current_terms = []
        self.content_lang = "es"

        self.settings = QSettings("CCMB", "CCMB")
        self.recent_searches = self._load_recent_searches()

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)

        self._build_ui()
        self._build_tree()
        self._show_welcome()
        self.stack.setCurrentWidget(self.home_page)

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_page = self._build_home_page()
        self.browse_page = self._build_browse_page()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.browse_page)

        icons_dir = resource_path(os.path.join("assets", "icons"))
        self.setStyleSheet(theme.build_stylesheet(icons_dir))

        # Nota: self.search_bar / self.home_search_bar son GlowLineEdit y ya
        # gestionan su propio QGraphicsDropShadowEffect al enfocar; no se les
        # debe aplicar apply_glow() encima (pisaria y rompe ese efecto).
        apply_glow(self.detail, color="#000000", blur=40, alpha=130)
        apply_glow(self.sidebar, color="#000000", blur=30, alpha=110)
        for b in (self.btn_expand, self.btn_collapse, self.btn_back, self.btn_forward, self.btn_lang):
            apply_glow(b, color="#000000", blur=14, alpha=70)

    def _build_home_page(self):
        hero_path = resource_path(os.path.join("assets", "hero_background.jpg"))
        page = HeroBackground(image_path=hero_path, overlay_alpha=115)
        page.setObjectName("homePage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(44, 26, 44, 18)
        outer.setSpacing(0)

        # --- navbar ---
        navbar = QHBoxLayout()
        navbar.setSpacing(10)
        icon_path = resource_path(os.path.join("assets", "icon.png"))
        nav_logo = QLabel()
        if os.path.exists(icon_path):
            nav_logo.setPixmap(
                QPixmap(icon_path).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        navbar.addWidget(nav_logo)
        nav_title = QLabel("CCMB")
        nav_title.setObjectName("navTitle")
        navbar.addWidget(nav_title)
        navbar.addStretch(1)
        nav_badge = QLabel("CC:2022 · PARTE 2")
        nav_badge.setObjectName("navBadge")
        navbar.addWidget(nav_badge)
        outer.addLayout(navbar)

        outer.addStretch(1)

        # --- bloque superior: eyebrow + titulo, centrados ---
        top_col = QVBoxLayout()
        top_col.setSpacing(8)

        eyebrow = QLabel("—  BIENVENIDO A CCMB  —")
        eyebrow.setObjectName("heroEyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        top_col.addWidget(eyebrow)

        heading = QLabel(f'Common Criteria<br><span style="color:{theme.VIOLET};">CC:2022 Parte 2</span>')
        heading.setObjectName("heroHeading")
        heading.setTextFormat(Qt.RichText)
        heading.setAlignment(Qt.AlignCenter)
        top_col.addWidget(heading)

        top_row = QHBoxLayout()
        top_row.addStretch(1)
        top_row.addLayout(top_col)
        top_row.addStretch(1)
        outer.addLayout(top_row)

        outer.addSpacing(16)

        # --- tarjeta de busqueda ---
        card = QWidget()
        card.setObjectName("searchCard")
        card.setMinimumWidth(360)
        card.setMaximumWidth(440)
        card.setAttribute(Qt.WA_StyledBackground, True)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(34, 26, 34, 22)
        card_lay.setSpacing(2)
        apply_glow(card, color="#000000", blur=50, alpha=170)

        badge_row = QHBoxLayout()
        badge_row.addStretch(1)
        logo_badge = QWidget()
        logo_badge.setObjectName("logoBadge")
        logo_badge.setFixedSize(76, 76)
        apply_glow(logo_badge, color=theme.VIOLET, blur=38, alpha=220)
        badge_lay = QVBoxLayout(logo_badge)
        badge_lay.setContentsMargins(0, 0, 0, 0)
        full_icon_path = resource_path(os.path.join("assets", "logo_full.png"))
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(full_icon_path):
            logo_label.setPixmap(
                QPixmap(full_icon_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        badge_lay.addWidget(logo_label, 0, Qt.AlignCenter)
        badge_row.addWidget(logo_badge)
        badge_row.addStretch(1)
        card_lay.addLayout(badge_row)

        card_lay.addSpacing(14)

        self.home_search_bar = GlowLineEdit()
        self.home_search_bar.setObjectName("searchBarHome")
        self.home_search_bar.setPlaceholderText("Buscar en CC:2022 Parte 2...")
        self.home_search_bar.setMinimumHeight(46)
        self.home_search_bar.returnPressed.connect(self._submit_home_search)
        card_lay.addWidget(self.home_search_bar)

        card_lay.addSpacing(10)

        btn_search = QPushButton("BUSCAR   →")
        btn_search.setObjectName("homeSearchBtn")
        btn_search.setMinimumHeight(40)
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.clicked.connect(self._submit_home_search)
        card_lay.addWidget(btn_search)

        card_lay.addSpacing(6)

        btn_explore = QPushButton("Explorar todo el contenido")
        btn_explore.setObjectName("linkButton")
        btn_explore.setCursor(Qt.PointingHandCursor)
        btn_explore.clicked.connect(self._explore_all)
        card_lay.addWidget(btn_explore, 0, Qt.AlignCenter)

        card_lay.addSpacing(10)

        self.recent_label = QLabel("")
        self.recent_label.setObjectName("recentLabel")
        self.recent_label.setAlignment(Qt.AlignCenter)
        card_lay.addWidget(self.recent_label)

        card_lay.addSpacing(6)

        self.recent_chips_container = QVBoxLayout()
        self.recent_chips_container.setSpacing(6)
        card_lay.addLayout(self.recent_chips_container)

        card_row = QHBoxLayout()
        card_row.addStretch(1)
        card_row.addWidget(card)
        card_row.addStretch(1)
        outer.addLayout(card_row)

        outer.addSpacing(16)

        # --- bloque inferior: descripcion + estadisticas, centrados ---
        bottom_col = QVBoxLayout()
        bottom_col.setSpacing(14)

        desc = QLabel(
            "Base de consulta de las Security Functional Components. Busca por "
            "codigo, nombre o contenido y navega clases, familias y componentes "
            "con sus dependencias enlazadas, tal como figuran en el PDF."
        )
        desc.setObjectName("heroDesc")
        desc.setWordWrap(True)
        desc.setFixedWidth(520)
        desc.setAlignment(Qt.AlignCenter)
        bottom_col.addWidget(desc, 0, Qt.AlignHCenter)

        features_row = QHBoxLayout()
        features_row.setSpacing(34)
        for value, flabel in (
            ("11", "Clases"), ("71", "Familias"), ("156", "Componentes"), ("FTS5", "Busqueda"),
        ):
            box = QVBoxLayout()
            box.setSpacing(1)
            v = QLabel(value)
            v.setObjectName("featureValue")
            v.setAlignment(Qt.AlignCenter)
            l = QLabel(flabel)
            l.setObjectName("featureLabel")
            l.setAlignment(Qt.AlignCenter)
            box.addWidget(v)
            box.addWidget(l)
            box_widget = QWidget()
            box_widget.setLayout(box)
            features_row.addWidget(box_widget)
        bottom_col.addLayout(features_row)
        bottom_col.setAlignment(features_row, Qt.AlignHCenter)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        bottom_row.addLayout(bottom_col)
        bottom_row.addStretch(1)
        outer.addLayout(bottom_row)

        outer.addStretch(2)

        # --- barra de estado inferior ---
        status_row = QHBoxLayout()
        left_status = QLabel("CCMB · Common Criteria CC:2022 Parte 2")
        left_status.setObjectName("statusBarText")
        status_row.addWidget(left_status)
        status_row.addStretch(1)
        right_status = QLabel("Generado desde el PDF oficial · Sin conexion")
        right_status.setObjectName("statusBarText")
        status_row.addWidget(right_status)
        outer.addLayout(status_row)

        self._refresh_recent_chips()
        return page

    def _build_browse_page(self):
        page = QWidget()
        page.setObjectName("browsePage")
        page.setAttribute(Qt.WA_StyledBackground, True)
        outer = QHBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ================= Sidebar =================
        self.sidebar = QWidget()
        sidebar = self.sidebar
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(340)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(22, 24, 22, 20)
        sb.setSpacing(16)

        logo_btn = QPushButton()
        logo_btn.setObjectName("logoButton")
        logo_btn.setCursor(Qt.PointingHandCursor)
        logo_btn.setToolTip("Volver al inicio")
        logo_btn.clicked.connect(self._go_home)
        logo_row = QHBoxLayout(logo_btn)
        logo_row.setContentsMargins(0, 0, 0, 0)
        logo_row.setSpacing(10)
        icon_path = resource_path(os.path.join("assets", "icon.png"))
        logo_label = QLabel()
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(
                38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(pix)
        logo_row.addWidget(logo_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("CCMB")
        title.setObjectName("appTitle")
        title_col.addWidget(title)
        subtitle = QLabel("PANEL DE CONSULTA")
        subtitle.setObjectName("appSubtitle")
        sfont = subtitle.font()
        sfont.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        subtitle.setFont(sfont)
        title_col.addWidget(subtitle)
        logo_row.addLayout(title_col)
        logo_row.addStretch(1)
        sb.addWidget(logo_btn)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)
        self.chip_classes = QLabel("")
        self.chip_classes.setObjectName("chipClasses")
        self.chip_families = QLabel("")
        self.chip_families.setObjectName("chipFamilies")
        self.chip_components = QLabel("")
        self.chip_components.setObjectName("chipComponents")
        for chip in (self.chip_classes, self.chip_families, self.chip_components):
            chip.setAlignment(Qt.AlignCenter)
            stats_row.addWidget(chip, 1)
        sb.addLayout(stats_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setIconSize(QSize(11, 11))
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        sb.addWidget(self.tree, 1)

        outer.addWidget(sidebar)

        # ================= Area principal =================
        main_area = QWidget()
        main_area.setObjectName("mainArea")
        ma = QVBoxLayout(main_area)
        ma.setContentsMargins(28, 26, 32, 26)
        ma.setSpacing(16)

        header_bar = QWidget()
        header_bar.setObjectName("headerBar")
        hb = QHBoxLayout(header_bar)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(12)

        self.search_bar = GlowLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText(
            "Buscar por codigo, nombre o contenido...  (ej. FAU_ARP, FAU_ARP.1, security audit)"
        )
        self.search_bar.setMinimumHeight(44)
        self.search_bar.textChanged.connect(self._on_search_changed)
        hb.addWidget(self.search_bar, 1)

        self.btn_back = QPushButton("←  ATRAS")
        self.btn_forward = QPushButton("ADELANTE  →")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_forward.clicked.connect(self.go_forward)
        self.btn_back.setEnabled(False)
        self.btn_forward.setEnabled(False)

        self.btn_expand = QPushButton("⤢  EXPANDIR")
        self.btn_collapse = QPushButton("⤡  COLAPSAR")
        self.btn_expand.clicked.connect(self._expand_all)
        self.btn_collapse.clicked.connect(self._collapse_all)

        sep = QFrame()
        sep.setObjectName("toolbarSep")
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)

        sep2 = QFrame()
        sep2.setObjectName("toolbarSep")
        sep2.setFixedWidth(1)
        sep2.setFixedHeight(22)

        self.btn_lang = QPushButton("VER EN INGLES")
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.clicked.connect(self._toggle_lang)

        hb.addWidget(self.btn_back)
        hb.addWidget(self.btn_forward)
        hb.addWidget(sep)
        hb.addWidget(self.btn_expand)
        hb.addWidget(self.btn_collapse)
        hb.addWidget(sep2)
        hb.addWidget(self.btn_lang)
        ma.addWidget(header_bar)

        self.detail = QTextBrowser()
        self.detail.setObjectName("detailPanel")
        self.detail.setOpenLinks(False)
        self.detail.setOpenExternalLinks(False)
        self.detail.anchorClicked.connect(self._on_anchor_clicked)
        ma.addWidget(self.detail, 1)

        outer.addWidget(main_area, 1)
        return page

    def _tree_label(self, row):
        name = row["name"]
        if self.content_lang == "es":
            name = row["name_es"] or name
        return f'{row["code"]} - {name}'

    def _build_tree(self):
        self.tree.clear()
        self.tree_items = {}
        self._tree_rows = {}
        classes = self.db.get_classes()
        for i, cls in enumerate(classes):
            label = self._tree_label(cls)
            citem = QTreeWidgetItem([label])
            citem.setData(0, Qt.UserRole, ("class", cls["code"]))
            citem.setIcon(0, make_dot_icon(CLASS_PALETTE[i % len(CLASS_PALETTE)]))
            citem.setToolTip(0, label)
            self.tree.addTopLevelItem(citem)
            self.tree_items[("class", cls["code"])] = citem
            self._tree_rows[("class", cls["code"])] = cls

            for fam in self.db.get_families(cls["code"]):
                flabel = self._tree_label(fam)
                fitem = QTreeWidgetItem([flabel])
                fitem.setData(0, Qt.UserRole, ("family", fam["code"]))
                fitem.setToolTip(0, flabel)
                citem.addChild(fitem)
                self.tree_items[("family", fam["code"])] = fitem
                self._tree_rows[("family", fam["code"])] = fam

                for comp in self.db.get_components(fam["code"]):
                    clabel = self._tree_label(comp)
                    item = QTreeWidgetItem([clabel])
                    item.setData(0, Qt.UserRole, ("component", comp["code"]))
                    item.setToolTip(0, clabel)
                    fitem.addChild(item)
                    self.tree_items[("component", comp["code"])] = item
                    self._tree_rows[("component", comp["code"])] = comp

        n_classes = len(classes)
        n_families = len(self._family_rows)
        n_components = len(self._component_rows)
        self.chip_classes.setText(f"{n_classes}\nCLASES")
        self.chip_families.setText(f"{n_families}\nFAMILIAS")
        self.chip_components.setText(f"{n_components}\nCOMPONENTES")
        self._stats = {"classes": n_classes, "families": n_families, "components": n_components}

    def _show_welcome(self):
        self.detail.setHtml(render.render_welcome(self._stats))

    def _refresh_tree_labels(self):
        for key, item in self.tree_items.items():
            row = self._tree_rows.get(key)
            if row is None:
                continue
            label = self._tree_label(row)
            item.setText(0, label)
            item.setToolTip(0, label)

    def _toggle_lang(self):
        self.content_lang = "en" if self.content_lang == "es" else "es"
        self.btn_lang.setText("VER EN ESPANOL" if self.content_lang == "en" else "VER EN INGLES")
        self._refresh_tree_labels()
        if self.history and 0 <= self.history_index < len(self.history):
            kind, code = self.history[self.history_index]
            self.navigate_to(kind, code, push_history=False)
        else:
            self._show_welcome()

    # ------------------------------------------------------------------
    # Busqueda
    # ------------------------------------------------------------------

    def _on_search_changed(self, text):
        self._search_timer.stop()
        self._search_timer.start(180)

    def _do_search(self):
        text = self.search_bar.text().strip()
        if not text:
            self.current_terms = []
            for item in self.tree_items.values():
                item.setHidden(False)
                item.setForeground(0, QBrush(QColor(theme.TEXT_PRIMARY)))
                font = item.font(0)
                font.setBold(False)
                item.setFont(0, font)
            self._show_welcome()
            return

        self.current_terms = re.findall(r"\w+", text, re.UNICODE)
        matches = self.db.search(text)

        show_classes = set(matches["class"])
        show_families = set(matches["family"])
        show_components = set(matches["component"])

        for comp_code in list(show_components):
            row = self._component_rows.get(comp_code)
            if row:
                show_families.add(row["family_code"])
                show_classes.add(row["class_code"])

        for fam_code, row in self._family_rows.items():
            if row["class_code"] in show_classes:
                show_families.add(fam_code)

        for comp_code, row in self._component_rows.items():
            if row["family_code"] in show_families:
                show_components.add(comp_code)
                show_classes.add(row["class_code"])

        for (kind, code), item in self.tree_items.items():
            if kind == "class":
                visible = code in show_classes
                is_match = code in matches["class"]
            elif kind == "family":
                visible = code in show_families
                is_match = code in matches["family"]
            else:
                visible = code in show_components
                is_match = code in matches["component"]
            item.setHidden(not visible)
            color = QColor(theme.MAGENTA) if is_match else QColor(theme.TEXT_PRIMARY)
            item.setForeground(0, QBrush(color))
            font = item.font(0)
            font.setBold(is_match)
            item.setFont(0, font)

        self.tree.expandAll()
        self.detail.setHtml(render.render_search_results(text, matches["ranked"]))

    # ------------------------------------------------------------------
    # Inicio (pantalla tipo buscador)
    # ------------------------------------------------------------------

    def _fade_in(self, widget, duration=180):
        """Fundido breve usado al refrescar contenido (panel de detalle)."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._detail_anim = anim
        anim.start()

    def _switch_page(self, widget):
        """Cambia la pagina visible del stack con una transicion de fundido."""
        if self.stack.currentWidget() is widget:
            return
        self.stack.setCurrentWidget(widget)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._page_anim = anim  # evita que el GC lo destruya a mitad de camino
        anim.start()

    def _go_home(self):
        self.home_search_bar.clear()
        self.home_search_bar.setFocus()
        self._switch_page(self.home_page)

    def _submit_home_search(self):
        text = self.home_search_bar.text().strip()
        if not text:
            return
        self._add_recent_search(text)
        self._switch_page(self.browse_page)
        self.search_bar.setText(text)
        self._search_timer.stop()
        self._do_search()

    def _explore_all(self):
        self._switch_page(self.browse_page)
        self.search_bar.clear()
        self._search_timer.stop()
        self._do_search()
        self._show_welcome()

    def _search_from_chip(self, text):
        self.home_search_bar.setText(text)
        self._submit_home_search()

    # ------------------------------------------------------------------
    # Busquedas recientes (persistidas en disco via QSettings)
    # ------------------------------------------------------------------

    SUGGESTED_SEARCHES = ["FAU_ARP", "security audit", "FDP", "dependencies", "FMT_SMR.1"]

    def _load_recent_searches(self):
        raw = self.settings.value("recent_searches", "")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data][:8]
        except (ValueError, TypeError):
            pass
        return []

    def _save_recent_searches(self):
        self.settings.setValue("recent_searches", json.dumps(self.recent_searches))

    def _add_recent_search(self, text):
        text = text.strip()
        if not text:
            return
        self.recent_searches = [s for s in self.recent_searches if s.lower() != text.lower()]
        self.recent_searches.insert(0, text)
        self.recent_searches = self.recent_searches[:8]
        self._save_recent_searches()
        self._refresh_recent_chips()

    def _refresh_recent_chips(self):
        while self.recent_chips_container.count():
            item = self.recent_chips_container.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        if self.recent_searches:
            self.recent_label.setText("BUSQUEDAS RECIENTES")
            items = self.recent_searches[:3]
        else:
            self.recent_label.setText("PROBA CON")
            items = self.SUGGESTED_SEARCHES[:3]

        for text in items:
            chip = QPushButton(text)
            chip.setObjectName("recentChip")
            chip.setMinimumHeight(32)
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda checked=False, t=text: self._search_from_chip(t))
            self.recent_chips_container.addWidget(chip)

    # ------------------------------------------------------------------
    # Navegacion
    # ------------------------------------------------------------------

    def _on_tree_item_clicked(self, item, column):
        kind, code = item.data(0, Qt.UserRole)
        if item.childCount() > 0 and not item.isExpanded():
            item.setExpanded(True)
        self.navigate_to(kind, code, push_history=True)

    def _on_anchor_clicked(self, url):
        href = url.toString()
        if ":" not in href:
            return
        scheme, code = href.split(":", 1)
        kind_map = {"cls": "class", "fam": "family", "comp": "component"}
        kind = kind_map.get(scheme)
        if kind:
            self.navigate_to(kind, code, push_history=True)

    def navigate_to(self, kind, code, push_history=True):
        if kind == "class":
            data = self.db.get_class_detail(code)
            if data is None:
                return
            html = render.render_class(data, self.current_terms, lang=self.content_lang)
        elif kind == "family":
            data = self.db.get_family_detail(code)
            if data is None:
                return
            html = render.render_family(data, self.current_terms, lang=self.content_lang)
        else:
            data = self.db.get_component_detail(code)
            if data is None:
                return
            html = render.render_component(data, self.current_terms, lang=self.content_lang)

        self.detail.setHtml(html)
        self._fade_in(self.detail)

        item = self.tree_items.get((kind, code))
        if item is not None:
            self.tree.blockSignals(True)
            ancestor = item.parent()
            while ancestor is not None:
                ancestor.setExpanded(True)
                ancestor = ancestor.parent()
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
            self.tree.blockSignals(False)

        if push_history:
            self.history = self.history[: self.history_index + 1]
            self.history.append((kind, code))
            self.history_index += 1
        self._update_nav_buttons()

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            kind, code = self.history[self.history_index]
            self.navigate_to(kind, code, push_history=False)

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            kind, code = self.history[self.history_index]
            self.navigate_to(kind, code, push_history=False)

    def _update_nav_buttons(self):
        self.btn_back.setEnabled(self.history_index > 0)
        self.btn_forward.setEnabled(self.history_index < len(self.history) - 1)

    def _expand_all(self):
        self.tree.expandAll()

    def _collapse_all(self):
        self.tree.collapseAll()


def _load_fonts():
    fonts_dir = resource_path(os.path.join("assets", "fonts"))
    if not os.path.isdir(fonts_dir):
        return
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname))


def main():
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setApplicationName("CCMB")
    _load_fonts()
    icon_path = resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    win = CCMBWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
