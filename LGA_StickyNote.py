"""
_______________________________________________

  LGA_StickyNote v2.00 | 2024 | Lega
  Editor en tiempo real para StickyNotes en el Node Graph
_______________________________________________

"""

import nuke
import os
from PySide2 import QtWidgets, QtGui, QtCore


# Variable global para activar o desactivar los prints
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


# Colores para el gradiente
BLUE_COLOR = "#9370DB"
VIOLET_COLOR = "#4169E1"
HANDLE_SIZE = 12  # Tamaño del handle del slider
LINE_HEIGHT = 25  # Altura de cada linea de control


class StickyNoteEditor(QtWidgets.QDialog):
    def __init__(self):
        super(StickyNoteEditor, self).__init__()

        self.sticky_node = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet("background-color: #1f1f1f; color: #CCCCCC;")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.adjustSize()

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
        font_size_layout.insertSpacing(0, 5)  # Añadir espacio a la izquierda del label
        font_size_label = QtWidgets.QLabel("Font Size")
        font_size_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        font_size_label.setFixedHeight(LINE_HEIGHT)  # Asegurar altura de la etiqueta
        font_size_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        self.font_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.font_size_slider.setRange(10, 100)
        self.font_size_slider.setValue(20)
        self.font_size_slider.setFixedHeight(LINE_HEIGHT)  # Asegurar altura del slider
        self.font_size_slider.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )  # El slider puede expandirse horizontalmente, pero la altura es fija
        self.font_size_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                border: 0px solid #555555;
                height: 2px;
                background: #545454;
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE_COLOR}, stop:1 {VIOLET_COLOR});
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #AAAAAA;
                border: 1px solid #555555;
                width: {HANDLE_SIZE}px;
                height: {HANDLE_SIZE}px;
                margin: -6px 0; /* Centrar el handle verticalmente */
                border-radius: 7px;
            }}
        """
        )

        self.font_size_value = QtWidgets.QLabel("20")
        self.font_size_value.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.font_size_value.setFixedHeight(
            LINE_HEIGHT
        )  # Asegurar altura de la etiqueta de valor
        self.font_size_value.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value)
        font_size_layout.addSpacing(5)  # Añadir espacio a la derecha del valor

        # Slider de margin X
        margin_x_layout = QtWidgets.QHBoxLayout()
        margin_x_layout.insertSpacing(0, 5)  # Añadir espacio a la izquierda del label
        margin_x_label = QtWidgets.QLabel("Margin X")
        margin_x_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        margin_x_label.setFixedHeight(LINE_HEIGHT)  # Asegurar altura de la etiqueta
        margin_x_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        self.margin_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.margin_slider.setRange(0, 10)
        self.margin_slider.setValue(0)
        self.margin_slider.setFixedHeight(LINE_HEIGHT)  # Asegurar altura del slider
        self.margin_slider.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )  # El slider puede expandirse horizontalmente, pero la altura es fija
        self.margin_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                border: 0px solid #555555;
                height: 2px;
                background: #545454;
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE_COLOR}, stop:1 {VIOLET_COLOR});
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #AAAAAA;
                border: 1px solid #555555;
                width: {HANDLE_SIZE}px;
                height: {HANDLE_SIZE}px;
                margin: -6px 0;
                border-radius: 7px;
            }}
        """
        )

        self.margin_value = QtWidgets.QLabel("0")
        self.margin_value.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.margin_value.setFixedHeight(
            LINE_HEIGHT
        )  # Asegurar altura de la etiqueta de valor
        self.margin_value.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        margin_x_layout.addWidget(margin_x_label)
        margin_x_layout.addWidget(self.margin_slider)
        margin_x_layout.addWidget(self.margin_value)
        margin_x_layout.addSpacing(5)  # Añadir espacio a la derecha del valor

        # Slider de margin Y
        margin_y_layout = QtWidgets.QHBoxLayout()
        margin_y_layout.insertSpacing(0, 5)  # Añadir espacio a la izquierda del label
        margin_y_label = QtWidgets.QLabel("Margin Y")
        margin_y_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        margin_y_label.setFixedHeight(LINE_HEIGHT)  # Asegurar altura de la etiqueta
        margin_y_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        self.margin_y_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.margin_y_slider.setRange(0, 4)
        self.margin_y_slider.setValue(0)
        self.margin_y_slider.setFixedHeight(LINE_HEIGHT)  # Asegurar altura del slider
        self.margin_y_slider.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )  # El slider puede expandirse horizontalmente, pero la altura es fija
        self.margin_y_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                border: 0px solid #555555;
                height: 2px;
                background: #545454;
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE_COLOR}, stop:1 {VIOLET_COLOR});
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #AAAAAA;
                border: 1px solid #555555;
                width: {HANDLE_SIZE}px;
                height: {HANDLE_SIZE}px;
                margin: -6px 0;
                border-radius: 7px;
            }}
        """
        )

        self.margin_y_value = QtWidgets.QLabel("0")
        self.margin_y_value.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.margin_y_value.setFixedHeight(
            LINE_HEIGHT
        )  # Asegurar altura de la etiqueta de valor
        self.margin_y_value.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        margin_y_layout.addWidget(margin_y_label)
        margin_y_layout.addWidget(self.margin_y_slider)
        margin_y_layout.addWidget(self.margin_y_value)
        margin_y_layout.addSpacing(5)  # Añadir espacio a la derecha del valor

        # Botones de flechas
        arrows_layout = QtWidgets.QHBoxLayout()
        arrows_layout.insertSpacing(0, 5)  # Añadir espacio a la izquierda del label
        arrows_label = QtWidgets.QLabel("Arrows:")
        arrows_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        arrows_label.setFixedHeight(LINE_HEIGHT)  # Asegurar altura de la etiqueta
        arrows_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que la altura sea fija

        # Botón de flecha derecha
        self.right_arrow_button = QtWidgets.QPushButton()
        self.right_arrow_button.setToolTip("Add right arrow")
        self.right_arrow_button.setFixedSize(
            QtCore.QSize(LINE_HEIGHT, LINE_HEIGHT)
        )  # Ajustar tamaño del botón

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
                background-color: #1f1f1f;
                border: none;
                padding: 0px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1f1f1f;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
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

        # Agregar widgets al layout
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(font_size_layout)
        main_layout.addLayout(margin_x_layout)
        main_layout.addLayout(margin_y_layout)
        main_layout.addLayout(arrows_layout)

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

        # Cargar texto
        current_text = self.sticky_node["label"].value()
        debug_print(f"Texto actual del StickyNote: '{current_text}'")

        # Si el sticky note esta vacio o solo contiene espacios, inicializar los margenes a 0
        if not current_text.strip():
            margin_y_detected = 0
            total_margin_x_detected = 0
            margin_x_for_slider = 0
            final_clean_text = ""
            lines_processed_for_y_margin = []
        else:
            lines = current_text.split("\n")

            # --- Deteccion de Margin X ---
            total_margin_x_detected = 0
            if lines and lines[0]:
                left_spaces = len(lines[0]) - len(lines[0].lstrip(" "))
                right_spaces = len(lines[0]) - len(lines[0].rstrip(" "))
                total_margin_x_detected = min(left_spaces, right_spaces)
                debug_print(f"Primera linea: '{lines[0]}'")
                debug_print(
                    f"Espacios a la izquierda detectados (total): {left_spaces}"
                )
                debug_print(f"Espacios a la derecha detectados (total): {right_spaces}")
                debug_print(
                    f"Total Margin X detectado en el texto: {total_margin_x_detected}"
                )

            # El valor del slider es la mitad del total de espacios detectados
            margin_x_for_slider = total_margin_x_detected // 2
            debug_print(f"Margen X para el slider (por lado): {margin_x_for_slider}")

            # --- Deteccion de Margin Y ---
            margin_y_detected = 0
            lines_processed_for_y_margin = list(
                lines
            )  # Copia de las lineas para trabajar

            if lines:
                start_empty = 0
                for i, line in enumerate(lines):
                    # Una linea vacia de Margin Y, despues de aplicar Margin X, deberia tener ' ' * total_margin_x_detected
                    if line.strip() == "" or (
                        total_margin_x_detected > 0
                        and line == " " * total_margin_x_detected
                    ):
                        start_empty += 1
                    else:
                        break

                end_empty = 0
                for i in reversed(range(len(lines))):
                    line = lines[i]
                    if line.strip() == "" or (
                        total_margin_x_detected > 0
                        and line == " " * total_margin_x_detected
                    ):
                        end_empty += 1
                    else:
                        break

                # Usar el menor como margin Y. Asegurarse que no se remuevan todas las lineas.
                margin_y_detected = min(start_empty, end_empty)
                debug_print(f"Lineas vacias al inicio detectadas: {start_empty}")
                debug_print(f"Lineas vacias al final detectadas: {end_empty}")
                debug_print(f"Margen Y detectado: {margin_y_detected}")

                # Remover las lineas vacias del margin Y
                if margin_y_detected * 2 < len(lines):
                    lines_processed_for_y_margin = lines[
                        margin_y_detected : len(lines) - margin_y_detected
                    ]
                else:
                    lines_processed_for_y_margin = (
                        lines  # Si el margin Y es muy grande, no remover nada
                    )

            # --- Limpiar texto aplicando los margenes detectados ---
            clean_text_lines = []
            for line in lines_processed_for_y_margin:
                clean_line = line
                # Remover espacios de Margin X
                if len(clean_line) >= total_margin_x_detected:
                    clean_line = clean_line[margin_x_for_slider:]
                    if clean_line.endswith(" " * margin_x_for_slider):
                        clean_line = clean_line[:-margin_x_for_slider]
                clean_text_lines.append(clean_line)

            final_clean_text = "\n".join(clean_text_lines)
            debug_print(f"Texto limpio para el editor: '{final_clean_text}'")

        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(final_clean_text)
        self.text_edit.blockSignals(False)

        # Cargar font size
        current_font_size = int(self.sticky_node["note_font_size"].value())
        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(current_font_size)
        self.font_size_value.setText(str(current_font_size))
        self.font_size_slider.blockSignals(False)

        # Cargar margin X
        self.margin_slider.blockSignals(True)
        self.margin_slider.setValue(margin_x_for_slider)
        self.margin_value.setText(str(margin_x_for_slider))
        self.margin_slider.blockSignals(False)

        # Cargar margin Y
        self.margin_y_slider.blockSignals(True)
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
