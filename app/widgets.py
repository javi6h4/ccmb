"""Widgets custom para el tema de CCMB: fondo degradado suave, barra de
busqueda con foco realzado e iconos de acento por clase."""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QLineEdit, QGraphicsDropShadowEffect

from . import theme

CLASS_PALETTE = [
    "#8b7cf6", "#2dd4bf", "#fb7185", "#4ade80", "#fbbf24",
    "#60a5fa", "#f472b6", "#a3e635", "#34d399", "#c084fc", "#facc15",
]


def make_dot_icon(color, size=12):
    """Genera un icono circular solido, usado como acento por clase en el menu."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.end()
    return QIcon(pm)


class HeroBackground(QWidget):
    """Fondo tipo 'landing': una imagen ilustrada (planeta/nebulosa/montanas)
    escalada a modo 'cover', con un velo oscuro leve para asegurar contraste
    del texto que va encima."""

    def __init__(self, parent=None, image_path=None, overlay_alpha=70):
        super().__init__(parent)
        self._src = None
        self._overlay_alpha = overlay_alpha
        if image_path and os.path.exists(image_path):
            pm = QPixmap(image_path)
            if not pm.isNull():
                self._src = pm
        self._cache = None

    def resizeEvent(self, event):
        self._cache = None
        super().resizeEvent(event)

    def _rebuild(self):
        w, h = max(1, self.width()), max(1, self.height())
        pm = QPixmap(w, h)
        p = QPainter(pm)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)

        if self._src is not None:
            scaled = self._src.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width() - w) // 2
            y = (scaled.height() - h) // 2
            p.drawPixmap(-x, -y, scaled)
        else:
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0.0, QColor(theme.BG_TOP))
            grad.setColorAt(1.0, QColor(theme.BG_BOTTOM))
            p.fillRect(0, 0, w, h, grad)

        if self._overlay_alpha:
            p.fillRect(0, 0, w, h, QColor(10, 7, 18, self._overlay_alpha))

        # leve oscurecido extra en la franja inferior para que la barra de
        # estado siempre tenga buen contraste sin importar el contenido
        bottom = QLinearGradient(0, h * 0.82, 0, h)
        bottom.setColorAt(0.0, QColor(5, 3, 10, 0))
        bottom.setColorAt(1.0, QColor(5, 3, 10, 150))
        p.setPen(Qt.NoPen)
        p.setBrush(bottom)
        p.drawRect(0, int(h * 0.82), w, int(h * 0.18) + 1)

        p.end()
        self._cache = pm

    def paintEvent(self, event):
        if self._cache is None:
            self._rebuild()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cache)
        painter.end()


class GlowLineEdit(QLineEdit):
    """QLineEdit cuyo resplandor al enfocar se resuelve enteramente por QSS
    (ver :focus en theme.py). No usa QGraphicsEffect: combinado con los
    contenedores de fondo semitransparente (WA_StyledBackground) producia un
    bug real de Qt donde el campo se renderizaba desplazado de su posicion
    de layout en la plataforma xcb."""


def apply_glow(widget, color=theme.VIOLET, blur=24, alpha=60):
    effect = QGraphicsDropShadowEffect(widget)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    effect.setOffset(0, 6)
    effect.setBlurRadius(blur)
    widget.setGraphicsEffect(effect)
    return effect
