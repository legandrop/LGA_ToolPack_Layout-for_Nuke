"""
__________________________________________
LGA_layoutPanel v0.01 | Lega Pugliese
Numpad style panel for layout toolpack
__________________________________________
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import logging
import os
import queue
import time
import platform
from logging.handlers import QueueHandler, QueueListener

from LGA_QtAdapter_ToolPack_Layout import (
    QtWidgets,
    QtGui,
    QtCore,
    Qt,
    primary_screen_geometry,
)

try:
    from PySide6 import QtSvg
except Exception:
    try:
        from PySide2 import QtSvg
    except Exception:
        QtSvg = None

# -----------------------------------------------------------------------------
# Logging (ver Docu_Logging_System.md)
# -----------------------------------------------------------------------------
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
script_start_time = None
debug_log_listener = None


class RelativeTimeFormatter(logging.Formatter):
    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="LGA_layoutPanel"):
    global debug_log_listener

    log_filename = f"debugPy_{script_name}.log"
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", log_filename)

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Warning: No se pudo limpiar el log: {e}")

    logger_name = f"{script_name.lower()}_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = RelativeTimeFormatter("[%(relative_time)s] %(message)s")
    file_handler.setFormatter(formatter)

    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass

    debug_log_listener = QueueListener(
        log_queue, file_handler, respect_handler_level=True
    )
    debug_log_listener.daemon = True
    debug_log_listener.start()

    return logger


debug_logger = setup_debug_logging(script_name="LGA_layoutPanel")


def debug_print(*message, level="info"):
    global script_start_time

    msg = " ".join(str(arg) for arg in message)

    if DEBUG and DEBUG_LOG:
        if script_start_time is None:
            script_start_time = time.time()

        if level == "debug":
            debug_logger.debug(msg)
        elif level == "warning":
            debug_logger.warning(msg)
        elif level == "error":
            debug_logger.error(msg)
        else:
            debug_logger.info(msg)

    if DEBUG and DEBUG_CONSOLE:
        if script_start_time is None:
            script_start_time = time.time()

        relative_time = time.time() - script_start_time
        timestamped_msg = f"[{relative_time:.3f}s] {msg}"
        print(timestamped_msg)


_panel_instance = None
LAYOUT_SCALE = 1.2
FONT_SCALE = 1 + (LAYOUT_SCALE - 1) * 0.5
FONT_SIZE = max(12, int(round(12 * FONT_SCALE)))
FONT_WEIGHT = 600 if LAYOUT_SCALE >= 1.1 else 500
FUNC_FONT_WEIGHT = 500
ARROW_STROKE = 10
COLOR_BASE = "#a9a9a9"
COLOR_ACTIVE = "#adadad"
COLOR_DIMMED = "#5a5959"
COLOR_MODE = "#8455e2"
COLOR_HOVER = "#b48cff"
ARROW_ACTIVE_SCALE = 0.8
CLOSE_SIZE_PX = 10
CLOSE_WIDE_SCALE = 1.6

_ARROW_SVG_CACHE: Dict[str, Optional[str]] = {}
_CLOSE_SVG_CACHE: Dict[str, Optional[str]] = {}


def _load_arrow_svg(variant: str) -> Optional[str]:
    global _ARROW_SVG_CACHE
    if variant in _ARROW_SVG_CACHE:
        return _ARROW_SVG_CACHE[variant]
    icons_root = os.path.join(os.path.dirname(__file__), "icons_layoutpanel")
    path = os.path.join(icons_root, f"arrow_down_{variant}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _ARROW_SVG_CACHE[variant] = f.read()
    except Exception:
        _ARROW_SVG_CACHE[variant] = None
    return _ARROW_SVG_CACHE[variant]


def _load_close_svg(variant: str) -> Optional[str]:
    global _CLOSE_SVG_CACHE
    if variant in _CLOSE_SVG_CACHE:
        return _CLOSE_SVG_CACHE[variant]
    icons_root = os.path.join(os.path.dirname(__file__), "icons_layoutpanel")
    path = os.path.join(icons_root, f"close_{variant}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _CLOSE_SVG_CACHE[variant] = f.read()
    except Exception:
        _CLOSE_SVG_CACHE[variant] = None
    return _CLOSE_SVG_CACHE[variant]


def _arrow_rotation(direction: str) -> int:
    if direction == "up":
        return 180
    if direction == "left":
        return 90
    if direction == "right":
        return -90
    return 0


def _render_arrow_pixmap(
    variant: str, size: int, direction: str
) -> Optional[QtGui.QPixmap]:
    if QtSvg is None:
        return None
    svg_data = _load_arrow_svg(variant)
    if not svg_data:
        return None
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_data.encode("utf-8")))
    if not renderer.isValid():
        return None
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    pixmap = QtGui.QPixmap.fromImage(image)
    rotation = _arrow_rotation(direction)
    if rotation != 0:
        pixmap = pixmap.transformed(
            QtGui.QTransform().rotate(rotation), QtCore.Qt.SmoothTransformation
        )
    return pixmap


def _render_close_pixmap(variant: str, size: int) -> Optional[QtGui.QPixmap]:
    if QtSvg is None:
        return None
    svg_data = _load_close_svg(variant)
    if not svg_data:
        return None
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_data.encode("utf-8")))
    if not renderer.isValid():
        return None
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    return QtGui.QPixmap.fromImage(image)


class NumpadButton(QtWidgets.QToolButton):
    def __init__(
        self,
        label: str,
        key_id: str,
        parent: Optional[QtWidgets.QWidget] = None,
        sub_label: Optional[str] = None,
    ) -> None:
        text = label if not sub_label else f"{label}\n{sub_label}"
        super().__init__(parent)
        self.setText(text)
        self.key_id = key_id
        self._base_label = label
        self._base_sub_label = sub_label
        self.setProperty("active", False)
        self.setProperty("dimmed", False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._has_icon = False
        self._icon_only = False
        self._arrow_dir = None
        self._arrow_size = 0
        self._hovered = False
        self._logged_paint = False
        self._close_size = 0

    def set_active(self, active: bool) -> None:
        if self.property("active") == active:
            return
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_labels(self, label: str, sub_label: Optional[str] = None) -> None:
        self._base_label = label
        self._base_sub_label = sub_label
        if sub_label and label:
            text = f"{label}\n{sub_label}"
        elif sub_label and not label:
            text = sub_label
        else:
            text = label
        self.setText(text)

    def set_icon(self, icon: QtGui.QIcon, size: QtCore.QSize) -> None:
        self.setIcon(icon)
        self.setIconSize(size)
        self._has_icon = True

    def set_icon_only(self, icon_only: bool) -> None:
        self._icon_only = icon_only
        if self._has_icon and icon_only:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

    def set_arrow(self, direction: str, size: int) -> None:
        self._arrow_dir = direction
        self._arrow_size = size
        self.update_arrow_icon()

    def set_close(self, size: int) -> None:
        self._close_size = size
        self.update_close_icon()

    def update_close_icon(self) -> None:
        if self._close_size <= 0:
            return
        variant = "hover" if self._hovered else "base"
        pixmap = _render_close_pixmap(variant, self._close_size)
        if pixmap is None:
            return
        self.setIcon(QtGui.QIcon(pixmap))
        self.setIconSize(QtCore.QSize(self._close_size, self._close_size))
        self._has_icon = True

    def update_arrow_icon(self) -> None:
        if not self._arrow_dir or self._arrow_size <= 0:
            return
        size = int(round(self._arrow_size * ARROW_ACTIVE_SCALE))
        variant = self._resolve_arrow_variant()
        pixmap = _render_arrow_pixmap(variant, size, self._arrow_dir)
        if pixmap is None:
            return
        self.setIcon(QtGui.QIcon(pixmap))
        self.setIconSize(QtCore.QSize(size, size))
        self._has_icon = True

    def _resolve_arrow_variant(self) -> str:
        if self.property("dimmed"):
            return "dimmed"
        if self._hovered and self.property("modeChanged"):
            return "hover"
        if self.property("modeChanged"):
            return "mode"
        if self.property("active"):
            return "active"
        return "base"

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self._hovered = True
        self.update_arrow_icon()
        if self.property("closeButton"):
            self.update_close_icon()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self._hovered = False
        self.update_arrow_icon()
        if self.property("closeButton"):
            self.update_close_icon()
        super().leaveEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        opt = QtWidgets.QStyleOptionToolButton()
        self.initStyleOption(opt)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_PanelButtonTool, opt, painter, self)

        se_contents = (
            QtWidgets.QStyle.SE_ToolButtonContents
            if hasattr(QtWidgets.QStyle, "SE_ToolButtonContents")
            else QtWidgets.QStyle.SE_PushButtonContents
        )
        content = style.subElementRect(se_contents, opt, self)
        if content.width() <= 0 or content.height() <= 0:
            pad = int(round(6 * LAYOUT_SCALE))
            content = self.rect().adjusted(pad, pad, -pad, -pad)
        if self.property("closeButton"):
            content = self.rect()
            if not self._has_icon or self.icon().isNull():
                self.update_close_icon()
            icon_size = self.iconSize()
            icon_rect = QtCore.QRect(
                content.center().x() - int(icon_size.width() / 2),
                content.center().y() - int(icon_size.height() / 2),
                icon_size.width(),
                icon_size.height(),
            )
            self.icon().paint(painter, icon_rect, Qt.AlignCenter)
            return
        text = self.text() or ""
        has_icon = self._has_icon and not self.icon().isNull()
        icon_size = self.iconSize()
        gap = int(round(2 * LAYOUT_SCALE))
        if not self._logged_paint:
            debug_print(
                "paint",
                self.key_id,
                "icon_only",
                self._icon_only,
                "gap",
                gap,
                "content",
                content.width(),
                content.height(),
            )
            self._logged_paint = True
        painter.setPen(opt.palette.buttonText().color())

        if has_icon and self._icon_only:
            icon_rect = QtCore.QRect(
                content.center().x() - int(icon_size.width() / 2),
                content.center().y() - int(icon_size.height() / 2),
                icon_size.width(),
                icon_size.height(),
            )
            self.icon().paint(painter, icon_rect, Qt.AlignCenter)
            return

        if has_icon and text:
            lines = text.split("\n")
            fm = painter.fontMetrics()
            line_h = fm.height()
            text_h = line_h * len(lines)
            total_h = icon_size.height() + gap + text_h
            start_y = int(content.center().y() - total_h / 2)
            icon_rect = QtCore.QRect(
                content.center().x() - int(icon_size.width() / 2),
                start_y,
                icon_size.width(),
                icon_size.height(),
            )
            text_rect = QtCore.QRect(
                content.left(),
                start_y + icon_size.height() + gap,
                content.width(),
                text_h,
            )
            if self._arrow_dir in ("left", "right"):
                text_rect.moveTop(text_rect.top() - int(round(2 * LAYOUT_SCALE)))
            self.icon().paint(painter, icon_rect, Qt.AlignCenter)
            if self.property("hasFuncText"):
                # line 0 (label) stays violet, line 1 (function) in cccc
                base_color = QtGui.QColor(COLOR_MODE)
                func_color = QtGui.QColor(COLOR_ACTIVE)
                if len(lines) == 1:
                    painter.setPen(func_color)
                    painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, lines[0])
                else:
                    painter.setPen(base_color)
                    line0_rect = QtCore.QRect(
                        text_rect.left(),
                        text_rect.top(),
                        text_rect.width(),
                        line_h,
                    )
                    painter.drawText(
                        line0_rect, Qt.AlignHCenter | Qt.AlignTop, lines[0]
                    )
                    painter.setPen(func_color)
                    line1_rect = QtCore.QRect(
                        text_rect.left(),
                        text_rect.top() + line_h,
                        text_rect.width(),
                        line_h,
                    )
                    painter.drawText(
                        line1_rect, Qt.AlignHCenter | Qt.AlignTop, lines[1]
                    )
            else:
                painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, text)
            return

        if self.property("hasFuncText"):
            lines = text.split("\n")
            fm = painter.fontMetrics()
            line_h = fm.height()
            text_h = line_h * len(lines)
            start_y = int(content.center().y() - text_h / 2)
            base_color = QtGui.QColor(COLOR_MODE)
            func_color = QtGui.QColor(COLOR_ACTIVE)
            if len(lines) == 1:
                painter.setPen(func_color)
                painter.drawText(
                    QtCore.QRect(content.left(), start_y, content.width(), line_h),
                    Qt.AlignHCenter | Qt.AlignTop,
                    lines[0],
                )
            else:
                painter.setPen(base_color)
                painter.drawText(
                    QtCore.QRect(content.left(), start_y, content.width(), line_h),
                    Qt.AlignHCenter | Qt.AlignTop,
                    lines[0],
                )
                painter.setPen(func_color)
                painter.drawText(
                    QtCore.QRect(
                        content.left(), start_y + line_h, content.width(), line_h
                    ),
                    Qt.AlignHCenter | Qt.AlignTop,
                    lines[1],
                )
            return

        painter.drawText(content, Qt.AlignCenter, text)


class LayoutPanel(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LGA Layout Panel")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._buttons: Dict[str, NumpadButton] = {}
        self._drag_active = False
        self._drag_offset = QtCore.QPoint(0, 0)
        self._mod_pressed = {"shift": False, "ctrl": False, "alt": False, "win": False}
        self._mod_locked = {"shift": False, "ctrl": False, "alt": False, "win": False}
        self._func_active = None
        self._mode_labels: Dict[
            Tuple[bool, bool, bool, bool], Dict[str, Tuple[str, Optional[str]]]
        ] = {}
        self._numpad_keys = set()
        self._always_active_keys = set()
        self._build_ui()
        self._build_key_map()
        self._build_mode_labels()
        self._update_mode_labels()
        debug_print("LayoutPanel init")

    def _build_ui(self) -> None:
        scale = LAYOUT_SCALE
        m6 = int(round(6 * scale))
        m10 = int(round(10 * scale))
        spacing = int(round(8 * scale))

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(m6, m6, m6, m6)
        outer_layout.setSpacing(spacing)

        panel = QtWidgets.QFrame(self)
        panel.setObjectName("panel")
        outer_layout.addWidget(panel)

        grid = QtWidgets.QGridLayout(panel)
        grid.setContentsMargins(m10, m10, m10, m10)
        grid.setHorizontalSpacing(spacing)
        grid.setVerticalSpacing(spacing)

        base = int(round(52 * scale))
        arrow_size = int(round(base * 0.42))

        def add_btn(
            label: str,
            row: int,
            col: int,
            row_span: int = 1,
            col_span: int = 1,
            key_id: Optional[str] = None,
            sub_label: Optional[str] = None,
        ) -> None:
            kid = key_id or label
            btn = NumpadButton(label, kid, panel, sub_label=sub_label)
            width = base * col_span + spacing * (col_span - 1)
            height = base * row_span + spacing * (row_span - 1)
            btn.setFixedSize(width, height)
            grid.addWidget(btn, row, col, row_span, col_span)
            btn.clicked.connect(lambda _=False, k=kid: self._on_button_click(k))
            self._buttons[kid] = btn

        top_bar = QtWidgets.QFrame(panel)
        top_bar.setObjectName("topbar")
        top_bar_layout = QtWidgets.QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        top_bar.setFixedHeight(int(round(CLOSE_SIZE_PX * LAYOUT_SCALE)))
        top_bar_layout.addStretch(1)

        close_btn = NumpadButton("", "close", top_bar)
        close_size = int(round(CLOSE_SIZE_PX * LAYOUT_SCALE))
        close_btn.setFixedSize(int(round(close_size * CLOSE_WIDE_SCALE)), close_size)
        close_btn.setProperty("closeButton", True)
        close_btn.setMinimumSize(0, 0)
        close_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        close_btn.setContentsMargins(0, 0, 0, 0)
        close_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        close_btn.setAttribute(Qt.WA_Hover, True)
        close_btn.setMouseTracking(True)
        close_btn.set_close(close_size)
        close_btn.clicked.connect(self.close)
        top_bar_layout.addWidget(close_btn)
        self._buttons["close"] = close_btn

        grid.addWidget(top_bar, 0, 0, 1, 4)
        debug_print(
            "topbar",
            "height",
            top_bar.height(),
            "close_size",
            close_size,
            "topbar_sizeHint",
            top_bar.sizeHint().width(),
            top_bar.sizeHint().height(),
        )

        add_btn("Home", 1, 0, key_id="7")
        add_btn("", 1, 1, key_id="8")
        self._buttons["8"].set_arrow("up", arrow_size)
        self._buttons["8"].set_icon_only(True)
        add_btn("PgUp", 1, 2, key_id="9")
        add_btn("+", 1, 3, row_span=2, key_id="+")

        add_btn("", 2, 0, key_id="4")
        self._buttons["4"].set_arrow("left", arrow_size)
        self._buttons["4"].set_icon_only(True)
        add_btn("5", 2, 1, key_id="5", sub_label=None)
        add_btn("", 2, 2, key_id="6")
        self._buttons["6"].set_arrow("right", arrow_size)
        self._buttons["6"].set_icon_only(True)

        add_btn("End", 3, 0, key_id="1")
        add_btn("", 3, 1, key_id="2")
        self._buttons["2"].set_arrow("down", arrow_size)
        self._buttons["2"].set_icon_only(True)
        add_btn("PgDn", 3, 2, key_id="3")
        add_btn("enter", 3, 3, row_span=2, key_id="enter")

        add_btn("Ins", 4, 0, col_span=2, key_id="0")
        add_btn("del", 4, 2, key_id="del")

        mods = QtWidgets.QFrame(self)
        mods.setObjectName("mods")
        outer_layout.addWidget(mods)

        mods_layout = QtWidgets.QHBoxLayout(mods)
        mods_layout.setContentsMargins(m10, m6, m10, m6)
        mods_layout.setSpacing(spacing)

        def add_mod(label: str, key_id: str) -> None:
            btn = NumpadButton(label, key_id, mods)
            btn.setFixedSize(base, int(round(32 * scale)))
            mods_layout.addWidget(btn)
            btn.clicked.connect(lambda _=False, k=key_id: self._on_button_click(k))
            self._buttons[key_id] = btn

        mods_layout.addStretch(1)
        add_mod("shift", "shift")
        add_mod("ctrl", "ctrl")
        add_mod(self._platform_mod_label(), "win")
        add_mod("alt", "alt")
        mods_layout.addStretch(1)

        func = QtWidgets.QFrame(self)
        func.setObjectName("func")
        outer_layout.addWidget(func)

        func_layout = QtWidgets.QVBoxLayout(func)
        func_layout.setContentsMargins(m10, m6, m10, m6)
        func_layout.setSpacing(spacing)

        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(spacing)
        func_layout.addLayout(row1)

        def add_func(layout: QtWidgets.QHBoxLayout, label: str, key_id: str) -> None:
            btn = NumpadButton(label, key_id, func)
            btn.setFixedSize(base, int(round(32 * scale)))
            btn.setProperty("funcButton", True)
            layout.addWidget(btn)
            btn.clicked.connect(lambda _=False, k=key_id: self._on_button_click(k))
            self._buttons[key_id] = btn

        row1.addStretch(1)
        add_func(row1, "Push", "func_push")
        add_func(row1, "Pull", "func_pull")
        add_func(row1, "Select", "func_select")
        add_func(row1, "Sel Con", "func_selcon")
        row1.addStretch(1)

        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(spacing)
        func_layout.addLayout(row2)
        row2.addStretch(1)
        add_func(row2, "Align", "func_align")
        add_func(row2, "Distrib", "func_distrib")
        add_func(row2, "Arrange", "func_arrange")
        add_func(row2, "Scale", "func_scale")
        row2.addStretch(1)

        self._apply_style()

    def _apply_style(self) -> None:
        style = """
            #panel {
                background-color: #161616;
                border: 0px solid #a9a9a9;
                border-radius: 12px;
            }
            #mods {
                background-color: #161616;
                border: 0px solid #a9a9a9;
                border-radius: 12px;
            }
            #func {
                background-color: #161616;
                border: 0px solid #a9a9a9;
                border-radius: 12px;
            }
            #topbar {
                background-color: #161616;
                border: 0px solid #a9a9a9;
                border-radius: 10px;
            }
            QToolButton {
                background-color: #161616;
                color: #a9a9a9;
                border: 2px solid #929292;
                border-radius: 10px;
                font: __FONT_WEIGHT__ __FONT_SIZE__px "Segoe UI";
                text-transform: lowercase;
            }
            QToolButton[funcButton="true"] {
                font: __FUNC_FONT_WEIGHT__ __FONT_SIZE__px "Segoe UI";
                text-transform: none;
            }
            QToolButton[active="true"] {
                background-color: #4f377e;
                color: #cccccc;
                border: 2px solid #774dcb;
            }
            QToolButton[dimmed="true"] {
                color: #5a5959;
                border: 2px solid #5a5959;
            }
            QToolButton[modeChanged="true"] {
                background-color: #1d1d1d;
                color: #8455e2;
                border: 2px solid #8455e2;
            }
            QToolButton[modeChanged="true"]:hover {
                color: #b48cff;
                border: 2px solid #b48cff;
            }
            QToolButton[closeButton="true"] {
                background-color: transparent;
                border: 0px solid transparent;
                color: #a9a9a9;
                text-transform: none;
            }
            QToolButton[closeButton="true"]:hover {
                color: #b48cff;
            }
            """
        style = (
            style.replace("__FONT_SIZE__", str(FONT_SIZE))
            .replace("__FONT_WEIGHT__", str(FONT_WEIGHT))
            .replace("__FUNC_FONT_WEIGHT__", str(FUNC_FONT_WEIGHT))
        )
        self.setStyleSheet(style)

    def _build_key_map(self) -> None:
        self._key_map = {
            Qt.Key_0: "0",
            Qt.Key_1: "1",
            Qt.Key_2: "2",
            Qt.Key_3: "3",
            Qt.Key_4: "4",
            Qt.Key_5: "5",
            Qt.Key_6: "6",
            Qt.Key_7: "7",
            Qt.Key_8: "8",
            Qt.Key_9: "9",
            Qt.Key_Plus: "+",
            Qt.Key_Minus: "-",
            Qt.Key_Asterisk: "*",
            Qt.Key_Slash: "/",
            Qt.Key_Enter: "enter",
            Qt.Key_Return: "enter",
            Qt.Key_Delete: "del",
        }
        self._modifier_map = {
            Qt.Key_Shift: "shift",
            Qt.Key_Control: "ctrl",
            Qt.Key_Alt: "alt",
            Qt.Key_Meta: "win",
        }

    def _platform_mod_label(self) -> str:
        system = platform.system().lower()
        if "darwin" in system or "mac" in system:
            return "⌘"
        return "win"

    def _build_mode_labels(self) -> None:
        base = {
            "7": ("Home", None),
            "8": ("", None),
            "9": ("PgUp", None),
            "4": ("", None),
            "5": ("5", None),
            "6": ("", None),
            "1": ("End", None),
            "2": ("", None),
            "3": ("PgDn", None),
            "0": ("Ins", None),
            "del": ("del", None),
            "+": ("+", None),
            "enter": ("enter", None),
        }

        # (shift, ctrl, alt, win)
        self._mode_labels[(False, False, False, False)] = base

        self._mode_labels[(False, False, True, False)] = {
            **base,
            "4": ("", "Select"),
            "6": ("", "Select"),
            "8": ("", "Select"),
            "2": ("", "Select"),
        }

        self._mode_labels[(False, False, False, True)] = {
            **base,
            "4": ("", "Sel Con"),
            "6": ("", "Sel Con"),
            "8": ("", "Sel Con"),
            "2": ("", "Sel Con"),
        }

        self._mode_labels[(False, True, False, False)] = {
            **base,
            "4": ("", "Align"),
            "6": ("", "Align"),
            "8": ("", "Align"),
            "2": ("", "Align"),
            "0": ("Ins", "Dist H"),
            "del": ("del", "Dist V"),
            "5": ("5", "Arrange"),
            "+": ("+", "Scale"),
        }

        self._mode_labels[(False, True, True, False)] = {
            **base,
            "4": ("", "Push"),
            "6": ("", "Push"),
            "8": ("", "Push"),
            "2": ("", "Push"),
        }

        self._mode_labels[(True, True, True, False)] = {
            **base,
            "4": ("", "Pull"),
            "6": ("", "Pull"),
            "8": ("", "Pull"),
            "2": ("", "Pull"),
        }
        self._numpad_keys = set(base.keys())

    def _effective_mod_state(self) -> Tuple[bool, bool, bool, bool]:
        shift = self._mod_pressed["shift"] or self._mod_locked["shift"]
        ctrl = self._mod_pressed["ctrl"] or self._mod_locked["ctrl"]
        alt = self._mod_pressed["alt"] or self._mod_locked["alt"]
        win = self._mod_pressed["win"] or self._mod_locked["win"]
        return shift, ctrl, alt, win

    def _update_mode_labels(self) -> None:
        mode = self._effective_mod_state()
        mapping = (
            self._mode_labels.get(mode)
            or self._mode_labels[(False, False, False, False)]
        )
        mode_active = mode != (False, False, False, False)
        changed_keys = set()
        for key_id, labels in mapping.items():
            btn = self._buttons.get(key_id)
            if not btn:
                continue
            label, sub = labels
            btn.set_labels(label, sub)
            base_label, base_sub = self._mode_labels[(False, False, False, False)].get(
                key_id, (label, sub)
            )
            if key_id in self._always_active_keys:
                is_changed = True
            else:
                is_changed = (label, sub) != (base_label, base_sub)
            if is_changed:
                changed_keys.add(key_id)
            btn.setProperty("modeChanged", is_changed)
            btn.setProperty("hasFuncText", bool(sub))
            if key_id in ("2", "4", "6", "8"):
                btn.set_icon_only(not is_changed)
                btn.update_arrow_icon()
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

        for key_id in self._numpad_keys:
            btn = self._buttons.get(key_id)
            if not btn:
                continue
            if key_id in self._always_active_keys:
                is_dimmed = False
            elif mode_active and len(changed_keys) > 0:
                is_dimmed = key_id not in changed_keys
            else:
                is_dimmed = True
            btn.setProperty("dimmed", is_dimmed)
            if key_id in ("2", "4", "6", "8"):
                btn.update_arrow_icon()
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

        for mod_key in ("shift", "ctrl", "alt", "win"):
            self._set_modifier_state(
                mod_key,
                self._effective_mod_state()[
                    ("shift", "ctrl", "alt", "win").index(mod_key)
                ],
            )
        self._sync_func_buttons()

    def _on_button_click(self, key_id: str) -> None:
        if key_id == "close":
            self.close()
            return
        if key_id.startswith("func_"):
            self._toggle_func_button(key_id)
            return
        if key_id in self._mod_locked:
            # Click overrides current key state: if pressed, force off; else toggle lock
            if self._mod_pressed.get(key_id):
                self._mod_pressed[key_id] = False
                self._mod_locked[key_id] = False
            else:
                self._mod_locked[key_id] = not self._mod_locked[key_id]
            self._func_active = None
            self._update_mode_labels()
            return
        self._flash_button(key_id)

    def _toggle_func_button(self, key_id: str) -> None:
        if (
            key_id in ("func_align", "func_distrib", "func_arrange", "func_scale")
            and self._mod_locked["ctrl"]
            and not self._mod_locked["alt"]
            and not self._mod_locked["shift"]
            and not self._mod_locked["win"]
        ):
            self._func_active = None
            self._mod_locked = {
                "shift": False,
                "ctrl": False,
                "alt": False,
                "win": False,
            }
            self._update_mode_labels()
            return
        if self._func_active == key_id:
            self._func_active = None
            self._mod_locked = {
                "shift": False,
                "ctrl": False,
                "alt": False,
                "win": False,
            }
        else:
            self._func_active = key_id
            if key_id == "func_push":
                self._mod_locked = {
                    "shift": False,
                    "ctrl": True,
                    "alt": True,
                    "win": False,
                }
            elif key_id == "func_pull":
                self._mod_locked = {
                    "shift": True,
                    "ctrl": True,
                    "alt": True,
                    "win": False,
                }
            elif key_id == "func_select":
                self._mod_locked = {
                    "shift": False,
                    "ctrl": False,
                    "alt": True,
                    "win": False,
                }
            elif key_id == "func_selcon":
                self._mod_locked = {
                    "shift": False,
                    "ctrl": False,
                    "alt": False,
                    "win": True,
                }
            elif key_id in ("func_align", "func_distrib", "func_arrange", "func_scale"):
                self._mod_locked = {
                    "shift": False,
                    "ctrl": True,
                    "alt": False,
                    "win": False,
                }
        for fid in (
            "func_push",
            "func_pull",
            "func_select",
            "func_selcon",
            "func_align",
            "func_distrib",
            "func_arrange",
            "func_scale",
        ):
            btn = self._buttons.get(fid)
            if btn:
                btn.set_active(fid == self._func_active)
        self._update_mode_labels()
        self._sync_func_buttons()

    def _sync_func_buttons(self) -> None:
        ctrl = self._mod_locked["ctrl"]
        alt = self._mod_locked["alt"]
        shift = self._mod_locked["shift"]
        win = self._mod_locked["win"]

        active_set = set()
        if ctrl and alt and shift:
            active_set = {"func_pull"}
        elif ctrl and alt:
            active_set = {"func_push"}
        elif alt and not ctrl and not win:
            active_set = {"func_select"}
        elif win and not alt and not ctrl:
            active_set = {"func_selcon"}
        elif ctrl and not alt and not win:
            active_set = {"func_align", "func_distrib", "func_arrange", "func_scale"}

        self._func_active = None if len(active_set) != 1 else next(iter(active_set))
        for fid in (
            "func_push",
            "func_pull",
            "func_select",
            "func_selcon",
            "func_align",
            "func_distrib",
            "func_arrange",
            "func_scale",
        ):
            btn = self._buttons.get(fid)
            if btn:
                btn.set_active(fid in active_set)

    def _flash_button(self, key_id: str) -> None:
        btn = self._buttons.get(key_id)
        if not btn:
            return
        btn.set_active(True)
        QtCore.QTimer.singleShot(140, lambda: btn.set_active(False))

    def _set_modifier_state(self, key_id: str, is_down: bool) -> None:
        btn = self._buttons.get(key_id)
        if not btn:
            return
        btn.set_active(is_down)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
            return

        mod_key = self._modifier_map.get(event.key())
        if mod_key:
            self._mod_pressed[mod_key] = True
            # Keyboard press overrides any click-lock for this modifier
            self._mod_locked[mod_key] = False
            self._update_mode_labels()
            return

        key_id = self._key_map.get(event.key())
        if key_id:
            self._flash_button(key_id)
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        mod_key = self._modifier_map.get(event.key())
        if mod_key:
            self._mod_pressed[mod_key] = False
            self._update_mode_labels()
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child is None or isinstance(child, QtWidgets.QFrame):
                self._drag_active = True
                self._drag_offset = (
                    self._global_pos(event) - self.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_active:
            self.move(self._global_pos(event) - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._drag_active:
            self._drag_active = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @staticmethod
    def _global_pos(event: QtGui.QMouseEvent) -> QtCore.QPoint:
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()


def _place_near_cursor(widget: QtWidgets.QWidget) -> None:
    pos = QtGui.QCursor.pos()
    geo = primary_screen_geometry(pos)
    size = widget.sizeHint()

    x = pos.x() - int(size.width() / 2)
    y = pos.y() - int(size.height() / 2)

    x = max(geo.left(), min(x, geo.right() - size.width()))
    y = max(geo.top(), min(y, geo.bottom() - size.height()))

    widget.move(x, y)


def show_panel() -> None:
    global _panel_instance

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    if _panel_instance is None or not _panel_instance.isVisible():
        _panel_instance = LayoutPanel()
    _place_near_cursor(_panel_instance)
    _panel_instance.show()
    _panel_instance.raise_()
    _panel_instance.activateWindow()
    _panel_instance.setFocus()
    debug_print("Panel shown")


__all__ = ["show_panel", "LayoutPanel"]
