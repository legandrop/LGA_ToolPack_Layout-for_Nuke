"""
_______________________________________________

  LGA_NodeLabel v0.81 | Lega
  Editor de labels para nodos en el Node Graph
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


class NodeLabelEditor(QtWidgets.QDialog):
    def __init__(self):
        super(NodeLabelEditor, self).__init__()

        self.selected_node = None
        self.original_label = ""
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
        self.title_bar = QtWidgets.QLabel("Node Label")
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
                selection-background-color: #555555;
                selection-color: #FFFFFF;
            }
        """
        )
        self.text_edit.setMaximumHeight(100)

        # Botones Cancel y OK
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)  # Espacio entre botones

        # Estilo común para ambos botones (grises)
        button_style = """
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #CCCCCC;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setFixedHeight(30)
        self.cancel_button.setStyleSheet(button_style)

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setFixedHeight(30)
        self.ok_button.setStyleSheet(button_style)

        # Crear tooltips personalizados
        self.tooltip_label = None
        self.cancel_button.enterEvent = lambda event: self.show_custom_tooltip(
            "Esc", self.cancel_button
        )
        self.cancel_button.leaveEvent = lambda event: self.hide_custom_tooltip()
        self.ok_button.enterEvent = lambda event: self.show_custom_tooltip(
            "Ctrl+Enter", self.ok_button
        )
        self.ok_button.leaveEvent = lambda event: self.hide_custom_tooltip()

        # Agregar botones con igual ancho (mitad cada uno)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)

        # Agregar widgets al layout de contenido
        content_layout.addWidget(self.text_edit)
        content_layout.addSpacing(10)  # Espacio antes de los botones
        content_layout.addLayout(buttons_layout)

        # Agregar el contenedor al layout del frame
        frame_layout.addWidget(content_widget)

        # Agregar el frame principal al layout principal
        main_layout.addWidget(self.main_frame)

        self.setLayout(main_layout)
        self.adjustSize()  # Ajustar tamaño después de configurar todo

        # Hacer la ventana 40px más chica de ancho
        current_size = self.size()
        self.setFixedSize(current_size.width() - 40, current_size.height())

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

    def show_custom_tooltip(self, text, widget):
        """Muestra un tooltip personalizado"""
        if self.tooltip_label:
            self.tooltip_label.close()

        self.tooltip_label = QtWidgets.QLabel(text)
        self.tooltip_label.setWindowFlags(QtCore.Qt.ToolTip)
        self.tooltip_label.setStyleSheet(
            """
            QLabel {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """
        )

        # Posicionar el tooltip centrado encima del botón
        if widget:
            # Obtener la posición global del botón
            global_pos = widget.mapToGlobal(QtCore.QPoint(0, 0))
            # Centrar el tooltip horizontalmente respecto al botón
            button_width = widget.width()
            tooltip_width = self.tooltip_label.sizeHint().width()
            x_offset = (button_width - tooltip_width) // 2
            # Posicionar encima del botón
            self.tooltip_label.move(global_pos.x() + x_offset, global_pos.y() - 35)

        self.tooltip_label.show()

    def hide_custom_tooltip(self):
        """Oculta el tooltip personalizado"""
        if self.tooltip_label:
            self.tooltip_label.close()
            self.tooltip_label = None

    def setup_connections(self):
        """Configura las conexiones de señales"""
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_ok_clicked)

    def get_selected_node(self):
        """Obtiene el nodo seleccionado"""
        selected_nodes = nuke.selectedNodes()

        if not selected_nodes:
            debug_print("No hay nodos seleccionados")
            return None

        # Usar el primer nodo seleccionado
        self.selected_node = selected_nodes[0]
        # Guardar el label original
        self.original_label = self.selected_node["label"].value()
        debug_print(f"Nodo seleccionado: {self.selected_node.name()}")
        debug_print(f"Label original: '{self.original_label}'")

        return self.selected_node

    def load_node_label(self):
        """Carga el label del nodo en la interfaz"""
        if not self.selected_node:
            return

        # Cargar el label actual
        current_label = self.selected_node["label"].value()

        # Actualizar QTextEdit
        self.text_edit.setPlainText(current_label)

        # Actualizar el título para mostrar el nombre del nodo
        self.title_bar.setText(f"Node Label - {self.selected_node.name()}")

    def on_cancel_clicked(self):
        """Callback cuando se hace click en Cancel"""
        debug_print("Cancelando edición de label")
        self.close()

    def on_ok_clicked(self):
        """Callback cuando se hace click en OK"""
        if not self.selected_node:
            debug_print("No hay nodo seleccionado para aplicar el label")
            self.close()
            return

        # Obtener el nuevo label del text edit
        new_label = self.text_edit.toPlainText()

        # Aplicar el nuevo label al nodo
        self.selected_node["label"].setValue(new_label)

        debug_print(
            f"Label aplicado al nodo {self.selected_node.name()}: '{new_label}'"
        )
        self.close()

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado"""
        if event.key() == QtCore.Qt.Key_Escape:
            # ESC funciona como Cancel
            self.on_cancel_clicked()
        elif event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # Ctrl+Enter funciona como OK
            if event.modifiers() & QtCore.Qt.ControlModifier:
                self.on_ok_clicked()
            else:
                # Enter normal solo inserta nueva línea
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Se ejecuta cuando se muestra el diálogo"""
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.text_edit.setFocus()
        self.text_edit.selectAll()

    def run(self):
        """Ejecuta el editor"""
        # Obtener el nodo seleccionado
        if not self.get_selected_node():
            nuke.message("Por favor selecciona un nodo para editar su label.")
            return

        # Cargar datos existentes
        self.load_node_label()

        # Posicionar la ventana respecto al nodo
        self.position_window_relative_to_node()

        # Mostrar el diálogo
        self.show()

    def position_window_relative_to_node(self):
        """Posiciona la ventana respecto al nodo seleccionado con tamaño dinámico."""
        # Asegurarnos de que la ventana tenga el tamaño correcto
        self.adjustSize()
        window_width = self.width()
        window_height = self.height()

        if not self.selected_node:
            # Fallback al cursor si no hay nodo seleccionado
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
            node_x = self.selected_node.xpos() + self.selected_node.screenWidth() // 2
            node_y = self.selected_node.ypos() + self.selected_node.screenHeight() // 2

            # Zoom y centro de la vista
            zoom = nuke.zoom()  # type: ignore
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
            node_top = self.selected_node.ypos()
            delta_top = (node_top - center_y) * zoom
            node_top_screen = dag_top_left.y() + dag_widget.height() // 2 + delta_top
            y_above = int(node_top_screen - UI_MARGIN_Y - window_height)

            if y_above >= avail.top():
                window_y = y_above + 20
                debug_print(f"Posicionando arriba: ({window_x}, {window_y})")
            else:
                # Si no cabe, debajo
                node_bot = self.selected_node.ypos() + self.selected_node.screenHeight()
                delta_bot = (node_bot - center_y) * zoom
                node_bot_screen = (
                    dag_top_left.y() + dag_widget.height() // 2 + delta_bot
                )
                window_y = int(node_bot_screen + UI_MARGIN_Y)
                debug_print(f"Posicionando debajo: ({window_x}, {window_y})")

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
node_label_editor = None


def main():
    """Función principal para mostrar el editor de Node Label."""
    global app, node_label_editor
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    node_label_editor = NodeLabelEditor()
    node_label_editor.run()


# Para uso en Nuke
def run_node_label_editor():
    """Mostrar el editor de Node Label dentro de Nuke"""
    global node_label_editor
    if node_label_editor is None:
        node_label_editor = NodeLabelEditor()
    node_label_editor.run()


# Ejecutar cuando se carga en Nuke
# run_node_label_editor()
