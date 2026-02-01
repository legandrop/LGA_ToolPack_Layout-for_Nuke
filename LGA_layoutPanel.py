"""
__________________________________________
LGA Layout Panel v0.01 | Lega Pugliese
Numpad style panel for layout toolpack
__________________________________________
"""

from __future__ import annotations

from typing import Dict, Optional

from LGA_QtAdapter_ToolPack_Layout import (
    QtWidgets,
    QtGui,
    QtCore,
    Qt,
    primary_screen_geometry,
)

_panel_instance = None


class NumpadButton(QtWidgets.QPushButton):
    def __init__(
        self, label: str, key_id: str, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(label, parent)
        self.key_id = key_id
        self.setProperty("active", False)
        self.setFocusPolicy(Qt.NoFocus)

    def set_active(self, active: bool) -> None:
        if self.property("active") == active:
            return
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class LayoutPanel(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LGA Layout Panel")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._buttons: Dict[str, NumpadButton] = {}
        self._build_ui()
        self._build_key_map()

    def _build_ui(self) -> None:
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(0)

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
        ) -> None:
            kid = key_id or label
            btn = NumpadButton(label, kid, panel)
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

        add_btn("7", 1, 0, key_id="7")
        add_btn("8", 1, 1, key_id="8")
        add_btn("9", 1, 2, key_id="9")
        add_btn("+", 1, 3, row_span=2, key_id="+")

        add_btn("4", 2, 0, key_id="4")
        add_btn("5", 2, 1, key_id="5")
        add_btn("6", 2, 2, key_id="6")

        add_btn("1", 3, 0, key_id="1")
        add_btn("2", 3, 1, key_id="2")
        add_btn("3", 3, 2, key_id="3")
        add_btn("enter", 3, 3, row_span=2, key_id="enter")

        add_btn("0", 4, 0, col_span=2, key_id="0")
        add_btn("del", 4, 2, key_id="del")

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            #panel {
                background-color: #121417;
                border: 2px solid #2a2d31;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #1b1d20;
                color: #e6e6e6;
                border: 2px solid #8c9097;
                border-radius: 10px;
                font: 12px "Segoe UI";
                text-transform: lowercase;
            }
            QPushButton[active="true"] {
                background-color: #2a2f36;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                border: 2px solid #d7d7d7;
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

    def _on_button_click(self, key_id: str) -> None:
        if key_id == "esc":
            self.close()
            return
        self._flash_button(key_id)

    def _flash_button(self, key_id: str) -> None:
        btn = self._buttons.get(key_id)
        if not btn:
            return
        btn.set_active(True)
        QtCore.QTimer.singleShot(140, lambda: btn.set_active(False))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
            return

        key_id = self._key_map.get(event.key())
        if key_id:
            self._flash_button(key_id)
            return

        super().keyPressEvent(event)


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


__all__ = ["show_panel", "LayoutPanel"]
