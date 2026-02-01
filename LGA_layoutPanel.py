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


class NumpadButton(QtWidgets.QPushButton):
    def __init__(
        self,
        label: str,
        key_id: str,
        parent: Optional[QtWidgets.QWidget] = None,
        sub_label: Optional[str] = None,
    ) -> None:
        text = label if not sub_label else f"{label}\n{sub_label}"
        super().__init__(text, parent)
        self.key_id = key_id
        self._base_label = label
        self._base_sub_label = sub_label
        self.setProperty("active", False)
        self.setFocusPolicy(Qt.NoFocus)

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
        text = label if not sub_label else f"{label}\n{sub_label}"
        self.setText(text)


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
        self._mode_labels: Dict[
            Tuple[bool, bool, bool, bool], Dict[str, Tuple[str, Optional[str]]]
        ] = {}
        self._numpad_keys = set()
        self._build_ui()
        self._build_key_map()
        self._build_mode_labels()
        self._update_mode_labels()
        debug_print("LayoutPanel init")

    def _build_ui(self) -> None:
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(8)

        panel = QtWidgets.QFrame(self)
        panel.setObjectName("panel")
        outer_layout.addWidget(panel)

        grid = QtWidgets.QGridLayout(panel)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        base = 52
        spacing = 8

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

        add_btn("esc", 0, 0, key_id="esc")
        add_btn("/", 0, 1, key_id="/")
        add_btn("*", 0, 2, key_id="*")
        add_btn("-", 0, 3, key_id="-")

        add_btn("7", 1, 0, key_id="7", sub_label="Home")
        add_btn("8", 1, 1, key_id="8", sub_label="↑")
        add_btn("9", 1, 2, key_id="9", sub_label="PgUp")
        add_btn("+", 1, 3, row_span=2, key_id="+")

        add_btn("4", 2, 0, key_id="4", sub_label="←")
        add_btn("5", 2, 1, key_id="5", sub_label=None)
        add_btn("6", 2, 2, key_id="6", sub_label="→")

        add_btn("1", 3, 0, key_id="1", sub_label="End")
        add_btn("2", 3, 1, key_id="2", sub_label="↓")
        add_btn("3", 3, 2, key_id="3", sub_label="PgDn")
        add_btn("enter", 3, 3, row_span=2, key_id="enter")

        add_btn("0", 4, 0, col_span=2, key_id="0", sub_label="Ins")
        add_btn("del", 4, 2, key_id="del")

        mods = QtWidgets.QFrame(self)
        mods.setObjectName("mods")
        outer_layout.addWidget(mods)

        mods_layout = QtWidgets.QHBoxLayout(mods)
        mods_layout.setContentsMargins(10, 6, 10, 6)
        mods_layout.setSpacing(8)

        def add_mod(label: str, key_id: str) -> None:
            btn = NumpadButton(label, key_id, mods)
            btn.setFixedSize(base, 32)
            mods_layout.addWidget(btn)
            btn.clicked.connect(lambda _=False, k=key_id: self._on_button_click(k))
            self._buttons[key_id] = btn

        mods_layout.addStretch(1)
        add_mod("shift", "shift")
        add_mod("ctrl", "ctrl")
        add_mod(self._platform_mod_label(), "win")
        add_mod("alt", "alt")
        mods_layout.addStretch(1)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
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
            QPushButton {
                background-color: #161616;
                color: #a9a9a9;
                border: 2px solid #929292;
                border-radius: 10px;
                font: 12px "Segoe UI";
                text-transform: lowercase;
            }
            QPushButton[active="true"] {
                background-color: #4f377e;
                color: #cccccc;
                border: 2px solid #774dcb;
            }
            QPushButton[dimmed="true"] {
                color: #5a5959;
                border: 2px solid #5a5959;
            }
            QPushButton[modeChanged="true"] {
                background-color: #1d1d1d;
                color: #8455e2;
            }
            QPushButton:hover {
                color: #cccccc;
                border: 2px solid #cccccc;
            }
            """
        )

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
            "7": ("7", "Home"),
            "8": ("8", "↑"),
            "9": ("9", "PgUp"),
            "4": ("4", "←"),
            "5": ("5", None),
            "6": ("6", "→"),
            "1": ("1", "End"),
            "2": ("2", "↓"),
            "3": ("3", "PgDn"),
            "0": ("0", "Ins"),
            "del": ("del", None),
            "+": ("+", None),
            "-": ("-", None),
            "*": ("*", None),
            "/": ("/", None),
            "enter": ("enter", None),
            "esc": ("esc", None),
        }

        # (shift, ctrl, alt, win)
        self._mode_labels[(False, False, False, False)] = base

        self._mode_labels[(False, False, True, False)] = {
            **base,
            "4": ("4", "Select L"),
            "6": ("6", "Select R"),
            "8": ("8", "Select T"),
            "2": ("2", "Select B"),
        }

        self._mode_labels[(False, False, False, True)] = {
            **base,
            "4": ("4", "Conn L"),
            "6": ("6", "Conn R"),
            "8": ("8", "Conn T"),
            "2": ("2", "Conn B"),
        }

        self._mode_labels[(False, True, False, False)] = {
            **base,
            "4": ("4", "Align L"),
            "6": ("6", "Align R"),
            "8": ("8", "Align T"),
            "2": ("2", "Align B"),
            "0": ("0", "Dist H"),
            "del": ("del", "Dist V"),
            "5": ("5", "Arrange"),
            "+": ("+", "Scale"),
        }

        self._mode_labels[(False, True, True, False)] = {
            **base,
            "4": ("4", "Push L"),
            "6": ("6", "Push R"),
            "8": ("8", "Push U"),
            "2": ("2", "Push D"),
        }

        self._mode_labels[(True, True, True, False)] = {
            **base,
            "4": ("4", "Pull L"),
            "6": ("6", "Pull R"),
            "8": ("8", "Pull U"),
            "2": ("2", "Pull D"),
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
            is_changed = (label, sub) != (base_label, base_sub)
            if is_changed:
                changed_keys.add(key_id)
            btn.setProperty("modeChanged", is_changed)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

        if not mode_active:
            should_dim = True
        else:
            should_dim = len(changed_keys) > 0
        for key_id in self._numpad_keys:
            btn = self._buttons.get(key_id)
            if not btn:
                continue
            if mode_active:
                is_dimmed = should_dim and key_id not in changed_keys
            else:
                is_dimmed = True
            btn.setProperty("dimmed", is_dimmed)
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

    def _on_button_click(self, key_id: str) -> None:
        if key_id == "esc":
            self.close()
            return
        if key_id in self._mod_locked:
            self._mod_locked[key_id] = not self._mod_locked[key_id]
            self._update_mode_labels()
            return
        self._flash_button(key_id)

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
