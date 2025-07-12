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

# Margen vertical para la interfaz de usuario
UI_MARGIN_Y = 20

# Variables configurables para el drop shadow
SHADOW_BLUR_RADIUS = 25  # Radio de blur (más alto = más blureado)
SHADOW_OPACITY = 60  # Opacidad (0-255, más alto = más opaco)
SHADOW_OFFSET_X = 3  # Desplazamiento horizontal
SHADOW_OFFSET_Y = 3  # Desplazamiento vertical
SHADOW_MARGIN = 25  # Margen adicional para la sombra proyectada


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
        self.drag_position = None  # Para el arrastre de la ventana
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Configurar ventana contenedora transparente
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")

        # Layout principal con margenes para la sombra
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(
            SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN
        )  # Margen para la sombra
        main_layout.setSpacing(0)

        # Frame principal que contendra todo el contenido
        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1f1f1f;
                border: 1px solid #555555;
                border-radius: 10px;
                color: #CCCCCC;
            }
        """
        )

        # Aplicar sombra al frame principal
        self.shadow = QtWidgets.QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(SHADOW_BLUR_RADIUS)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, SHADOW_OPACITY))
        self.shadow.setOffset(SHADOW_OFFSET_X, SHADOW_OFFSET_Y)
        self.main_frame.setGraphicsEffect(self.shadow)

        # Layout del frame principal
        frame_layout = QtWidgets.QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Barra de título personalizada
        self.title_bar = QtWidgets.QLabel("StickyNote Editor")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(
            """
            QLabel {
                background-color: #1f1f1f; 
                color: #cccccc; 
                padding-left: 10px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border: none;
                font-weight: bold;
            }
        """
        )
        self.title_bar.setAlignment(QtCore.Qt.AlignCenter)

        # Conectar eventos para arrastrar
        self.title_bar.mousePressEvent = self.start_move
        self.title_bar.mouseMoveEvent = self.move_window
        self.title_bar.mouseReleaseEvent = self.stop_move

        frame_layout.addWidget(self.title_bar)

        # Contenedor para el contenido con padding
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1f1f1f;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

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
        font_size_label.setStyleSheet("color: #AAAAAA; font-size: 12px; border: none;")
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
        self.font_size_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; border: none;"
        )
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
        margin_x_label.setStyleSheet("color: #AAAAAA; font-size: 12px; border: none;")
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
        self.margin_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; border: none;"
        )
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
        margin_y_label.setStyleSheet("color: #AAAAAA; font-size: 12px; border: none;")
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
        self.margin_y_value.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; border: none;"
        )
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
        arrows_label.setStyleSheet("color: #AAAAAA; font-size: 12px; border: none;")
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

        # Agregar widgets al layout de contenido
        content_layout.addWidget(self.text_edit)
        content_layout.addLayout(font_size_layout)
        content_layout.addLayout(margin_x_layout)
        content_layout.addLayout(margin_y_layout)
        content_layout.addLayout(arrows_layout)

        # Agregar el contenedor al layout del frame
        frame_layout.addWidget(content_widget)

        # Agregar el frame principal al layout principal
        main_layout.addWidget(self.main_frame)

        self.setLayout(main_layout)
        self.adjustSize()  # Ajustar tamaño después de configurar todo

    def start_move(self, event):
        """Inicia el movimiento de la ventana"""
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def move_window(self, event):
        """Mueve la ventana durante el arrastre"""
        if self.drag_position and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def stop_move(self, event):
        """Detiene el movimiento de la ventana"""
        self.drag_position = None

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

        lines = current_text.split("\n")

        # Valores por defecto
        margin_x_detected = 0
        margin_y_detected = 0
        final_clean_text = ""

        if current_text.strip():
            # --- Detección de Margin X: buscar primera línea con contenido ---
            for line in lines:
                if line.strip():
                    leading = len(line) - len(line.lstrip(" "))
                    trailing = len(line) - len(line.rstrip(" "))
                    margin_x_detected = min(leading, trailing)
                    debug_print(
                        f"Margen X detectado en línea con contenido: {margin_x_detected}"
                    )
                    break

            # --- Detección de Margin Y: líneas vacías al inicio y al final ---
            start_empty = 0
            for line in lines:
                if line.strip() == "":
                    start_empty += 1
                else:
                    break

            end_empty = 0
            for line in reversed(lines):
                if line.strip() == "":
                    end_empty += 1
                else:
                    break

            margin_y_detected = min(start_empty, end_empty)
            debug_print(
                f"Lineas vacías inicio: {start_empty}, fin: {end_empty}, margin Y: {margin_y_detected}"
            )

            # --- Extraer solo las líneas de contenido sin margin Y ---
            if margin_y_detected * 2 < len(lines):
                content_lines = lines[
                    margin_y_detected : len(lines) - margin_y_detected
                ]
            else:
                content_lines = []

            # --- Limpiar espacios laterales según margin X detectado ---
            clean_lines = []
            for line in content_lines:
                if margin_x_detected > 0 and len(line) >= 2 * margin_x_detected:
                    clean_line = line[margin_x_detected : len(line) - margin_x_detected]
                else:
                    # Si no hay margin X o la línea es muy corta, solo strip
                    clean_line = line.strip()
                clean_lines.append(clean_line)

            final_clean_text = "\n".join(clean_lines)

        # Actualizar QTextEdit sin disparar señales
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
        self.margin_slider.setValue(margin_x_detected)
        self.margin_value.setText(str(margin_x_detected))
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

        # Posicionar la ventana respecto al sticky note
        self.position_window_relative_to_sticky()

        # Mostrar el diálogo
        self.show()

    def position_window_relative_to_sticky(self):
        """Posiciona la ventana respecto al StickyNote con tamaño dinámico."""
        # Asegurarnos de que la ventana tenga el tamaño correcto
        self.adjustSize()
        window_width = self.width()
        window_height = self.height()

        if not self.sticky_node:
            # Fallback al cursor si no hay sticky note
            cursor_pos = QtGui.QCursor.pos()
            self.move(
                QtCore.QPoint(
                    cursor_pos.x() - window_width // 2,
                    cursor_pos.y() - window_height // 2,
                )
            )
            return

        try:
            # Posición del nodo en el DAG (centro)
            node_x = self.sticky_node.xpos() + self.sticky_node.screenWidth() // 2
            node_y = self.sticky_node.ypos() + self.sticky_node.screenHeight() // 2

            # Zoom y centro de la vista
            zoom = nuke.zoom()
            center_x, center_y = nuke.center()

            # Delta desde el centro, ajustado por zoom
            delta_x = (node_x - center_x) * zoom
            delta_y = (node_y - center_y) * zoom

            # Encontrar widget DAG
            dag_widget = None
            for widget in QtWidgets.QApplication.allWidgets():
                if "DAG" in widget.objectName():
                    dag_widget = widget
                    break

            if not dag_widget:
                # Si no encontramos el DAG, fallback al cursor
                cursor_pos = QtGui.QCursor.pos()
                self.move(
                    QtCore.QPoint(
                        cursor_pos.x() - window_width // 2,
                        cursor_pos.y() - window_height // 2,
                    )
                )
                return

            # Esquina superior izquierda del DAG
            dag_top_left = dag_widget.mapToGlobal(QtCore.QPoint(0, 0))

            # Coordenadas reales en pantalla
            screen_x = dag_top_left.x() + dag_widget.width() // 2 + delta_x
            screen_y = dag_top_left.y() + dag_widget.height() // 2 + delta_y

            avail = QtWidgets.QApplication.primaryScreen().availableGeometry()

            # Centro horizontal
            window_x = int(screen_x - window_width // 2)

            # Intentar arriba
            sticky_top = self.sticky_node.ypos()
            delta_top = (sticky_top - center_y) * zoom
            sticky_top_screen = dag_top_left.y() + dag_widget.height() // 2 + delta_top
            y_above = int(sticky_top_screen - UI_MARGIN_Y - window_height)

            if y_above >= avail.top():
                window_y = y_above - 50
                debug_print(f"Arriba: ({window_x}, {window_y})")
            else:
                # Si no cabe, debajo
                sticky_bot = self.sticky_node.ypos() + self.sticky_node.screenHeight()
                delta_bot = (sticky_bot - center_y) * zoom
                sticky_bot_screen = (
                    dag_top_left.y() + dag_widget.height() // 2 + delta_bot
                )
                window_y = int(sticky_bot_screen + UI_MARGIN_Y)
                debug_print(f"Debajo: ({window_x}, {window_y})")

            # Ajustar para que no salga de pantalla
            window_x = min(max(window_x, avail.left()), avail.right() - window_width)
            window_y = min(max(window_y, avail.top()), avail.bottom() - window_height)

            self.move(QtCore.QPoint(window_x, window_y))

        except Exception as e:
            debug_print(f"Error al posicionar ventana: {e}")
            # Fallback al cursor
            cursor_pos = QtGui.QCursor.pos()
            self.move(
                QtCore.QPoint(
                    cursor_pos.x() - window_width // 2,
                    cursor_pos.y() - window_height // 2,
                )
            )


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
