"""
_______________________________________________

  LGA_StickyNote v2.00 | 2024 | Lega
  Editor en tiempo real para StickyNotes en el Node Graph
_______________________________________________

"""

import nuke
import os
from PySide2 import QtWidgets, QtGui, QtCore


class StickyNoteEditor(QtWidgets.QDialog):
    def __init__(self):
        super(StickyNoteEditor, self).__init__()

        self.sticky_node = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setFixedSize(300, 320)
        self.setStyleSheet("background-color: #1f1f1f; color: #CCCCCC;")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Layout principal
        main_layout = QtWidgets.QVBoxLayout()

        # Campo de texto
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3D3D3D;
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
        font_size_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        self.font_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.font_size_slider.setRange(10, 100)
        self.font_size_slider.setValue(20)
        self.font_size_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 0px solid #555555;
                height: 2px;
                background: #6C6C6C;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #AAAAAA;
                border: 1px solid #555555;
                width: 4px;
                margin: -6px 0;
                border-radius: 10px;
            }
        """
        )

        self.font_size_value = QtWidgets.QLabel("20")
        self.font_size_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; min-width: 25px;"
        )

        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value)

        # Slider de margin X
        margin_x_layout = QtWidgets.QHBoxLayout()
        margin_x_label = QtWidgets.QLabel("Margin X:")
        margin_x_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        self.margin_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.margin_slider.setRange(0, 10)
        self.margin_slider.setValue(0)
        self.margin_slider.setStyleSheet(
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

        self.margin_value = QtWidgets.QLabel("0")
        self.margin_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; min-width: 25px;"
        )

        margin_x_layout.addWidget(margin_x_label)
        margin_x_layout.addWidget(self.margin_slider)
        margin_x_layout.addWidget(self.margin_value)

        # Slider de margin Y
        margin_y_layout = QtWidgets.QHBoxLayout()
        margin_y_label = QtWidgets.QLabel("Margin Y:")
        margin_y_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        self.margin_y_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.margin_y_slider.setRange(0, 4)
        self.margin_y_slider.setValue(0)
        self.margin_y_slider.setStyleSheet(
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

        self.margin_y_value = QtWidgets.QLabel("0")
        self.margin_y_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; min-width: 25px;"
        )

        margin_y_layout.addWidget(margin_y_label)
        margin_y_layout.addWidget(self.margin_y_slider)
        margin_y_layout.addWidget(self.margin_y_value)

        # Botones de flechas
        arrows_layout = QtWidgets.QHBoxLayout()
        arrows_label = QtWidgets.QLabel("Arrows:")
        arrows_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        # Botón de flecha derecha
        self.right_arrow_button = QtWidgets.QPushButton()
        self.right_arrow_button.setToolTip("Add right arrow")
        self.right_arrow_button.setFixedSize(QtCore.QSize(28, 28))
        self.right_arrow_button.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        # Rutas de los iconos
        icons_path = os.path.join(os.path.dirname(__file__), "icons")
        self.right_arrow_icon_path = os.path.join(icons_path, "lga_right_arrow.png")
        self.right_arrow_hover_icon_path = os.path.join(
            icons_path, "lga_right_arrow_hover.png"
        )

        # Cargar el icono normal
        if os.path.exists(self.right_arrow_icon_path):
            icon = QtGui.QIcon(self.right_arrow_icon_path)
            self.right_arrow_button.setIcon(icon)
            self.right_arrow_button.setIconSize(QtCore.QSize(20, 20))

        # Aplicar estilo CSS al botón
        self.right_arrow_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(50, 50, 50);
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgb(50, 50, 50);
            }
            QPushButton:pressed {
                background-color: rgb(70, 70, 70);
            }
        """
        )

        # Conectar eventos del botón
        self.right_arrow_button.clicked.connect(self.on_right_arrow_clicked)
        self.right_arrow_button.enterEvent = self.on_right_arrow_enter
        self.right_arrow_button.leaveEvent = self.on_right_arrow_leave

        arrows_layout.addWidget(arrows_label)
        arrows_layout.addWidget(self.right_arrow_button)
        arrows_layout.addStretch()  # Spacer para empujar todo a la izquierda

        # Ayuda
        help_label = QtWidgets.QLabel(
            '<span style="font-size:9pt; color:#666666;">ESC para cerrar</span>'
        )
        help_label.setAlignment(QtCore.Qt.AlignCenter)

        # Agregar widgets al layout
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(font_size_layout)
        main_layout.addLayout(margin_x_layout)
        main_layout.addLayout(margin_y_layout)
        main_layout.addLayout(arrows_layout)
        main_layout.addWidget(help_label)

        self.setLayout(main_layout)

    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        self.margin_slider.valueChanged.connect(self.on_margin_changed)
        self.margin_y_slider.valueChanged.connect(self.on_margin_y_changed)

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

        # Cargar texto (removiendo espacios del margin para mostrarlo limpio en el editor)
        current_text = self.sticky_node["label"].value()

        # Intentar detectar el margin actual basado en los espacios al inicio y final
        lines = current_text.split("\n")
        margin_detected = 0
        if lines and lines[0]:
            # Contar espacios al inicio de la primera línea
            left_spaces = len(lines[0]) - len(lines[0].lstrip(" "))
            # Contar espacios al final de la primera línea
            right_spaces = len(lines[0]) - len(lines[0].rstrip(" "))
            # Usar el menor de los dos como margin (asumiendo que son iguales)
            margin_detected = min(left_spaces, right_spaces)

        # Remover los espacios del margin para mostrar texto limpio
        clean_text = ""
        for line in lines:
            # Remover espacios del inicio y final según el margin detectado
            if len(line) >= margin_detected * 2:
                # Remover espacios del inicio y final
                clean_line = line[margin_detected:] if margin_detected > 0 else line
                if margin_detected > 0 and clean_line.endswith(" " * margin_detected):
                    clean_line = clean_line[:-margin_detected]
                clean_text += clean_line + "\n"
            else:
                clean_text += line + "\n"
        clean_text = clean_text.rstrip("\n")  # Remover último salto de línea

        self.text_edit.blockSignals(True)  # Evitar callback recursivo
        self.text_edit.setPlainText(clean_text)
        self.text_edit.blockSignals(False)

        # Cargar font size
        current_font_size = int(self.sticky_node["note_font_size"].value())
        self.font_size_slider.blockSignals(True)  # Evitar callback recursivo
        self.font_size_slider.setValue(current_font_size)
        self.font_size_value.setText(str(current_font_size))
        self.font_size_slider.blockSignals(False)

        # Detectar margin Y (líneas vacías al inicio y final)
        margin_y_detected = 0
        if lines:
            # Contar líneas vacías al inicio (que contengan solo espacios del margin X)
            start_empty = 0
            for line in lines:
                # Una línea vacía del margin Y contendría solo espacios del margin X
                if line.strip() == "" or (
                    margin_detected > 0 and line == " " * (margin_detected * 2)
                ):
                    start_empty += 1
                else:
                    break

            # Contar líneas vacías al final
            end_empty = 0
            for line in reversed(lines):
                if line.strip() == "" or (
                    margin_detected > 0 and line == " " * (margin_detected * 2)
                ):
                    end_empty += 1
                else:
                    break

            # Usar el menor como margin Y
            margin_y_detected = min(start_empty, end_empty)

            # Remover las líneas vacías del margin Y para el texto limpio
            if margin_y_detected > 0:
                # Asegurar que no removemos todas las líneas
                if margin_y_detected * 2 < len(lines):
                    lines = lines[margin_y_detected:-margin_y_detected]
                else:
                    lines = lines  # Mantener las líneas originales si el margin Y es muy grande

                # Recalcular clean_text sin las líneas del margin Y
                clean_text = ""
                for line in lines:
                    # Remover espacios del inicio y final según el margin detectado
                    if len(line) >= margin_detected * 2:
                        # Remover espacios del inicio y final
                        clean_line = (
                            line[margin_detected:] if margin_detected > 0 else line
                        )
                        if margin_detected > 0 and clean_line.endswith(
                            " " * margin_detected
                        ):
                            clean_line = clean_line[:-margin_detected]
                        clean_text += clean_line + "\n"
                    else:
                        clean_text += line + "\n"
                clean_text = clean_text.rstrip("\n")  # Remover último salto de línea

                # Actualizar el texto en el editor
                self.text_edit.blockSignals(True)
                self.text_edit.setPlainText(clean_text)
                self.text_edit.blockSignals(False)

        # Cargar margin X
        self.margin_slider.blockSignals(True)  # Evitar callback recursivo
        self.margin_slider.setValue(margin_detected)
        self.margin_value.setText(str(margin_detected))
        self.margin_slider.blockSignals(False)

        # Cargar margin Y
        self.margin_y_slider.blockSignals(True)  # Evitar callback recursivo
        self.margin_y_slider.setValue(margin_y_detected)
        self.margin_y_value.setText(str(margin_y_detected))
        self.margin_y_slider.blockSignals(False)

    def on_text_changed(self):
        """Callback cuando cambia el texto"""
        if self.sticky_node:
            current_text = self.text_edit.toPlainText()
            margin_x_spaces = " " * self.margin_slider.value()
            margin_y_lines = self.margin_y_slider.value()

            # Agregar espacios a ambos lados de cada línea (Margin X)
            lines = current_text.split("\n")
            final_lines = []
            for line in lines:
                final_lines.append(margin_x_spaces + line + margin_x_spaces)

            # Agregar líneas vacías arriba y abajo (Margin Y)
            empty_line = margin_x_spaces + margin_x_spaces  # Línea vacía con margin X
            for _ in range(margin_y_lines):
                final_lines.insert(0, empty_line)  # Agregar arriba
                final_lines.append(empty_line)  # Agregar abajo

            final_text = "\n".join(final_lines)
            self.sticky_node["label"].setValue(final_text)

    def on_font_size_changed(self, value):
        """Callback cuando cambia el font size"""
        if self.sticky_node:
            self.sticky_node["note_font_size"].setValue(value)
            self.font_size_value.setText(str(value))

    def on_margin_changed(self, value):
        """Callback cuando cambia el margin X"""
        if self.sticky_node:
            self.margin_value.setText(str(value))
            # Actualizar el texto con el nuevo margin
            self.on_text_changed()

    def on_margin_y_changed(self, value):
        """Callback cuando cambia el margin Y"""
        if self.sticky_node:
            self.margin_y_value.setText(str(value))
            # Actualizar el texto con el nuevo margin
            self.on_text_changed()

    def on_right_arrow_clicked(self):
        """Callback cuando se hace click en el botón de flecha derecha"""
        if not self.sticky_node:
            return

        current_text = self.text_edit.toPlainText()
        lines = current_text.split("\n")

        if not lines:
            return

        # Encontrar la línea central
        center_line_index = len(lines) // 2
        center_line = lines[center_line_index]

        # Verificar si ya existe "-->" en la línea central
        if "-->" in center_line:
            # Remover la flecha
            new_center_line = center_line.replace("-->", "").strip()
        else:
            # Agregar la flecha
            if center_line.strip():
                new_center_line = center_line + " -->"
            else:
                new_center_line = "-->"

        # Actualizar la línea en el array
        lines[center_line_index] = new_center_line

        # Reconstruir el texto
        new_text = "\n".join(lines)

        # Actualizar el editor
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(new_text)
        self.text_edit.blockSignals(False)

        # Actualizar el sticky note
        self.on_text_changed()

        print(
            f"Flecha derecha {'removida' if '-->' not in new_center_line else 'agregada'} en línea central"
        )

    def on_right_arrow_enter(self, event):
        """Cambia el icono a la version hover cuando el ratón entra"""
        if hasattr(self, "right_arrow_button") and os.path.exists(
            self.right_arrow_hover_icon_path
        ):
            self.right_arrow_button.setIcon(
                QtGui.QIcon(self.right_arrow_hover_icon_path)
            )

    def on_right_arrow_leave(self, event):
        """Cambia el icono a la version normal cuando el ratón sale"""
        if hasattr(self, "right_arrow_button") and os.path.exists(
            self.right_arrow_icon_path
        ):
            self.right_arrow_button.setIcon(QtGui.QIcon(self.right_arrow_icon_path))

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
