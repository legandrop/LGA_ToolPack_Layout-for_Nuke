"""
_______________________________________________

  LGA_StickyNote v2.00 | 2024 | Lega
  Editor en tiempo real para StickyNotes en el Node Graph
_______________________________________________

"""

import nuke
from PySide2 import QtWidgets, QtGui, QtCore


class StickyNoteEditor(QtWidgets.QDialog):
    def __init__(self):
        super(StickyNoteEditor, self).__init__()

        self.sticky_node = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("StickyNote Editor")
        self.setFixedSize(300, 200)
        self.setStyleSheet("background-color: #242527; color: #FFFFFF;")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Layout principal
        main_layout = QtWidgets.QVBoxLayout()

        # Titulo
        title = QtWidgets.QLabel("<b>StickyNote Editor</b>")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("color: #AAAAAA; font-size: 14px; margin-bottom: 10px;")

        # Campo de texto
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #1A1A1A;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """
        )
        self.text_edit.setMaximumHeight(100)

        # Slider de font size
        font_size_layout = QtWidgets.QHBoxLayout()
        font_size_label = QtWidgets.QLabel("Font Size:")
        font_size_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")

        self.font_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.font_size_slider.setRange(8, 48)
        self.font_size_slider.setValue(20)
        self.font_size_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background: #1A1A1A;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #AAAAAA;
                border: 1px solid #555555;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """
        )

        self.font_size_value = QtWidgets.QLabel("20")
        self.font_size_value.setStyleSheet(
            "color: #AAAAAA; font-size: 11px; min-width: 25px;"
        )

        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value)

        # Ayuda
        help_label = QtWidgets.QLabel(
            '<span style="font-size:9pt; color:#666666;">ESC para cerrar</span>'
        )
        help_label.setAlignment(QtCore.Qt.AlignCenter)

        # Agregar widgets al layout
        main_layout.addWidget(title)
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(font_size_layout)
        main_layout.addWidget(help_label)

        self.setLayout(main_layout)

    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)

    def get_or_create_sticky_note(self):
        """Obtiene el sticky note seleccionado o crea uno nuevo"""
        selected_nodes = nuke.selectedNodes()

        # Buscar si hay un StickyNote seleccionado
        sticky_notes = [node for node in selected_nodes if node.Class() == "StickyNote"]

        if sticky_notes:
            # Usar el primer StickyNote encontrado
            self.sticky_node = sticky_notes[0]
            print(f"Editando StickyNote existente: {self.sticky_node.name()}")
        else:
            # Crear un nuevo StickyNote
            self.sticky_node = nuke.createNode("StickyNote")
            print(f"Creado nuevo StickyNote: {self.sticky_node.name()}")

        return self.sticky_node

    def load_sticky_note_data(self):
        """Carga los datos del sticky note en la interfaz"""
        if not self.sticky_node:
            return

        # Cargar texto
        current_text = self.sticky_node["label"].value()
        self.text_edit.blockSignals(True)  # Evitar callback recursivo
        self.text_edit.setPlainText(current_text)
        self.text_edit.blockSignals(False)

        # Cargar font size
        current_font_size = int(self.sticky_node["note_font_size"].value())
        self.font_size_slider.blockSignals(True)  # Evitar callback recursivo
        self.font_size_slider.setValue(current_font_size)
        self.font_size_value.setText(str(current_font_size))
        self.font_size_slider.blockSignals(False)

    def on_text_changed(self):
        """Callback cuando cambia el texto"""
        if self.sticky_node:
            current_text = self.text_edit.toPlainText()
            self.sticky_node["label"].setValue(current_text)

    def on_font_size_changed(self, value):
        """Callback cuando cambia el font size"""
        if self.sticky_node:
            self.sticky_node["note_font_size"].setValue(value)
            self.font_size_value.setText(str(value))

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado"""
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Se ejecuta cuando se muestra el diálogo"""
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.text_edit.setFocus()

    def run(self):
        """Ejecuta el editor"""
        # Obtener o crear el sticky note
        self.get_or_create_sticky_note()

        # Cargar datos existentes
        self.load_sticky_note_data()

        # Posicionar la ventana cerca del cursor
        cursor_pos = QtGui.QCursor.pos()
        screen = QtWidgets.QApplication.primaryScreen()
        avail_space = screen.availableGeometry()

        posx = min(
            max(cursor_pos.x() - 150, avail_space.left()), avail_space.right() - 300
        )
        posy = min(
            max(cursor_pos.y() - 100, avail_space.top()), avail_space.bottom() - 200
        )

        self.move(QtCore.QPoint(posx, posy))

        # Mostrar el diálogo
        self.show()


# Variables globales
app = None
sticky_editor = None


def main():
    """Función principal para mostrar el editor de StickyNote."""
    global app, sticky_editor
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    sticky_editor = StickyNoteEditor()
    sticky_editor.run()


# Para uso en Nuke
def run_sticky_note_editor():
    """Mostrar el editor de StickyNote dentro de Nuke"""
    global sticky_editor
    if sticky_editor is None:
        sticky_editor = StickyNoteEditor()
    sticky_editor.run()


# Ejecutar cuando se carga en Nuke
# run_sticky_note_editor()
