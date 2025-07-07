"""
________________________________________________________________________________

  LGA_scriptChecker v0.86 | Lega
  Script para verificar si los inputs de los nodos estan correctamente posicionados
  segun las reglas de posicion definidas.
________________________________________________________________________________

"""

import nuke
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QStyledItemDelegate,
)
from PySide2.QtGui import QColor, QBrush, QCursor, QFontMetrics
from PySide2.QtCore import Qt, QRect, QMargins

import time

# Variable global para activar o desactivar los prints
DEBUG = False

# Variable para mostrar solo nodos con errores
ShowOnlyWrong = True

# Variables de configuracion de posicion
# Para nodos especiales (Merge2, Keymix)
inputA_special = "left"
inputB_special = "top"
inputMask = "right"

# Para nodos regulares
inputA = "top"

# Para nodos Merge en modo mask/stencil
inputA_mergeMaskStencil = "right"

# Lista de nodos que tienen inputs B, A y Mask
NODES_WITH_SPECIAL_INPUTS = ["Merge2", "Keymix", "Dissolve", "Copy"]

# Lista de nodos que no se chequean
NODES_TO_SKIP = [
    "Dot",
    "AppendClip",
    "CopyCat",
    "PostageStamp",
    "Viewer",
    "Switch",
    "OFXuk.co.thefoundry.keylight.keylight_v201",
    "Write",
    "IBKGizmoV3",
    "PointsTo3D",
    "MergeGeo",
    "Project3D2",
    "ScanlineRender",
    "Scene",
    "RayRender",
]

# Lista de nodos con inputs invertidos (A=top, B=left)
NODES_INVERTED_INPUTS = ["VectorDistort"]


def debug_print(*message):
    if DEBUG:
        print(*message)


def convert_color(value):
    """Convierte el valor de color de Nuke a RGB"""
    r = int((value & 0xFF000000) >> 24)
    g = int((value & 0x00FF0000) >> 16)
    b = int((value & 0x0000FF00) >> 8)
    return r, g, b


def get_node_color(node):
    """Obtiene el color del nodo"""
    if "tile_color" in node.knobs():
        color_value = node["tile_color"].value()
        if color_value == 0:
            node_class = node.Class()
            default_color_value = nuke.defaultNodeColor(node_class)
            return convert_color(default_color_value)
        else:
            return convert_color(color_value)
    else:
        return 255, 255, 255


def is_color_light(r, g, b):
    """Determina si el color es claro"""
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    return brightness > 126


def get_relative_position(node1, node2):
    """Determina la posicion relativa de node2 respecto a node1 usando los puntos centrales."""
    # Obtener las coordenadas del centro de node1
    x1_center = node1.xpos() + node1.screenWidth() / 2
    y1_center = node1.ypos() + node1.screenHeight() / 2

    # Obtener las coordenadas del centro de node2
    x2_center = node2.xpos() + node2.screenWidth() / 2
    y2_center = node2.ypos() + node2.screenHeight() / 2

    dx = x2_center - x1_center
    dy = y2_center - y1_center

    # Determinar la direccion principal
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    else:
        return "bottom" if dy > 0 else "top"


def check_node_inputs(node):
    """Verifica los inputs de un nodo y retorna la informacion"""
    result = {
        "node": node,
        "inputA": None,
        "inputB": None,
        "inputMask": None,
        "inputA_position": None,
        "inputB_position": None,
        "inputMask_position": None,
        "inputA_error": None,
        "inputB_error": None,
        "inputMask_error": None,
        "status": "OK",
    }

    node_class = node.Class()

    if node_class in NODES_WITH_SPECIAL_INPUTS:
        # Nodos con inputs B(0), A(1), Mask(2)
        if node.input(0):  # Input B
            result["inputB"] = node.input(0)
            result["inputB_position"] = get_relative_position(node, node.input(0))

        if node.input(1):  # Input A
            result["inputA"] = node.input(1)
            result["inputA_position"] = get_relative_position(node, node.input(1))

        if node.input(2):  # Input Mask
            result["inputMask"] = node.input(2)
            result["inputMask_position"] = get_relative_position(node, node.input(2))
    elif node_class in NODES_INVERTED_INPUTS:
        # Nodos con inputs invertidos A(0), B(1)
        if node.input(0):  # Input A
            result["inputA"] = node.input(0)
            result["inputA_position"] = get_relative_position(node, node.input(0))

        if node.input(1):  # Input B
            result["inputB"] = node.input(1)
            result["inputB_position"] = get_relative_position(node, node.input(1))
    else:
        # Nodos regulares con Input A(0) y Mask(1)
        if node.input(0):  # Input A
            result["inputA"] = node.input(0)
            result["inputA_position"] = get_relative_position(node, node.input(0))

        if node.input(1):  # Input Mask
            result["inputMask"] = node.input(1)
            result["inputMask_position"] = get_relative_position(node, node.input(1))

    # Verificar si las posiciones son correctas
    errors = []

    # Determinar que variable usar para Input A
    expected_inputA = inputA  # Por defecto para nodos regulares

    if node_class in NODES_WITH_SPECIAL_INPUTS:
        # Verificar si es un Merge en modo mask/stencil
        if node_class == "Merge2" and "operation" in node.knobs():
            operation = node["operation"].value()
            if operation in ["mask", "stencil"]:
                expected_inputA = inputA_mergeMaskStencil
                debug_print(
                    f"Node {node.name()} is Merge2 in {operation} mode, using inputA_mergeMaskStencil"
                )
            else:
                expected_inputA = inputA_special
        else:
            expected_inputA = inputA_special
    elif node_class in NODES_INVERTED_INPUTS:
        expected_inputA = "left"  # Para nodos invertidos, Input A debe ser left

    # Verificar Input A
    if result["inputA"] and result["inputA_position"] != expected_inputA:
        error_msg = (
            f"Input A should be {expected_inputA}, but is {result['inputA_position']}"
        )
        errors.append(error_msg)
        result["inputA_error"] = (
            f"({result['inputA_position']} / should be {expected_inputA})"
        )

    # Verificar Input B
    expected_inputB = inputB_special  # Por defecto para nodos especiales
    if node_class in NODES_INVERTED_INPUTS:
        expected_inputB = "top"  # Para nodos invertidos, Input B debe ser top

    if result["inputB"] and result["inputB_position"] != expected_inputB:
        error_msg = (
            f"Input B should be {expected_inputB}, but is {result['inputB_position']}"
        )
        errors.append(error_msg)
        result["inputB_error"] = (
            f"({result['inputB_position']} / should be {expected_inputB})"
        )

    # Verificar Input Mask
    if result["inputMask"] and result["inputMask_position"] != inputMask:
        error_msg = (
            f"Input Mask should be {inputMask}, but is {result['inputMask_position']}"
        )
        errors.append(error_msg)
        result["inputMask_error"] = (
            f"({result['inputMask_position']} / should be {inputMask})"
        )

    if errors:
        result["status"] = "Wrong"
        result["errors"] = errors

    debug_print(f"Node {node.name()}: {result['status']}")

    return result


class CustomItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Obtener el QTableWidgetItem directamente del QTableWidget (option.widget)
        table_widget = option.widget
        item = table_widget.item(index.row(), index.column())

        if not item:
            super(CustomItemDelegate, self).paint(painter, option, index)
            return

        # Rellenar todo el rectangulo con el color de fondo
        if item.background() and item.background().color().isValid():
            painter.fillRect(option.rect, item.background())

        # Determinar el color del texto base (negro o blanco) basado en el color de fondo
        bg_color = item.background().color()
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
        if is_color_light(r, g, b):
            base_text_color = QColor(0, 0, 0)  # Negro
            error_text_color = QColor(150, 0, 0)  # Rojo oscuro
        else:
            base_text_color = QColor(255, 255, 255)  # Blanco
            error_text_color = QColor(255, 150, 150)  # Rojo claro

        # Manejo especial para la columna de Status (columna 4)
        if index.column() == 4:
            painter.setPen(base_text_color)
            status_text = item.text()
            metrics = QFontMetrics(painter.font())

            # Calcular la posicion para centrar el texto manualmente
            text_width = metrics.horizontalAdvance(status_text)
            x_centered = option.rect.x() + (option.rect.width() - text_width) / 2

            # Ajustar para centrado vertical
            text_y = (
                option.rect.top()
                + (option.rect.height() - metrics.height()) / 2
                + metrics.ascent()
            )

            debug_print(
                f"Columna 4 - Item: {status_text}, Rect: {option.rect}, Calc X: {x_centered:.2f}, Calc Y: {text_y:.2f}"
            )
            painter.drawText(x_centered, text_y, status_text)
            return  # Salir del metodo paint para esta columna

        metrics = QFontMetrics(painter.font())

        # Ajustar el rectangulo para crear padding izquierdo
        padded_rect = QRect(option.rect)
        padding_left = 5
        padding_right = 5  # Anadir padding derecho
        padded_rect.adjust(
            padding_left, 0, -padding_right, 0
        )  # Ajustar el rectangulo con ambos paddings

        # Calcular la posicion vertical para centrar el texto
        text_y = (
            padded_rect.top()
            + (padded_rect.height() - metrics.height()) / 2
            + metrics.ascent()
        )
        current_x = padded_rect.left()

        error_pattern = " / should be "
        if error_pattern in item.text():
            index_error_start = item.text().find(error_pattern)

            # Parte 1: Texto antes del patron de error (ej., "Blur14 (right")
            main_part = item.text()[:index_error_start]
            painter.setPen(base_text_color)
            painter.drawText(current_x, text_y, main_part)
            current_x += metrics.horizontalAdvance(main_part)

            # Parte 2 y 3: El texto de error y el parentesis final (si existe y esta al final)
            last_paren_index_in_full_text = item.text().rfind(")")

            if (
                last_paren_index_in_full_text != -1
                and last_paren_index_in_full_text == len(item.text()) - 1
                and index_error_start < last_paren_index_in_full_text
            ):
                # El parentesis final pertenece a la parte no-error
                actual_error_text = item.text()[
                    index_error_start:last_paren_index_in_full_text
                ]
                closing_paren_text = item.text()[last_paren_index_in_full_text:]
            else:
                # No hay parentesis final a separar, o no esta al final
                actual_error_text = item.text()[index_error_start:]
                closing_paren_text = ""  # No hay parentesis de cierre separado para dibujar en color base

            painter.setPen(error_text_color)
            painter.drawText(current_x, text_y, actual_error_text)
            current_x += metrics.horizontalAdvance(actual_error_text)

            # Parte 3: El parentesis de cierre (si se separo)
            if closing_paren_text:
                painter.setPen(base_text_color)
                painter.drawText(current_x, text_y, closing_paren_text)
        else:
            # Si no hay patron de error, dibujar todo el texto con el color base
            painter.setPen(base_text_color)
            painter.drawText(padded_rect, option.displayAlignment, item.text())

    def sizeHint(self, option, index):
        """Ajusta el tamano de la sugerencia para incluir el padding"""
        original_size = super(CustomItemDelegate, self).sizeHint(option, index)
        padding_left = 5
        padding_right = 5  # Usar el mismo padding derecho que en paint
        return original_size.grownBy(
            QMargins(
                padding_left, 0, padding_right, 0
            )  # Anadir padding izquierdo y derecho
        )


class ScriptCheckerWindow(QWidget):
    def __init__(self, initial_results, parent=None):
        super(ScriptCheckerWindow, self).__init__(parent)
        self.results = initial_results
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Script Checker Results")
        # Asegura que la ventana permanezca en primer plano
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)

        # Crear la tabla con 5 columnas
        self.table = QTableWidget(len(self.results), 5, self)
        self.table.setHorizontalHeaderLabels(
            ["Node", "Input A", "Input B", "Input Mask", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        # Conectar la senal de clic de la celda al metodo go_to_node
        self.table.cellClicked.connect(self.go_to_node)
        debug_print("Senal cellClicked conectada a go_to_node.")

        # Aplicar el delegado personalizado para el padding
        self.table.setItemDelegate(CustomItemDelegate(self.table))

        # Cargar datos en la tabla
        self.load_data()

        layout.addWidget(self.table)

        # Crear boton de cerrar
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        # Anadir boton de Refresh
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Ajustar tamano de ventana
        self.adjust_window_size()

    def load_data(self):
        self.table.setRowCount(
            len(self.results)
        )  # Asegurarse de que la tabla tenga el numero correcto de filas
        for row, result in enumerate(self.results):
            node = result["node"]
            r, g, b = get_node_color(node)
            node_qcolor = QColor(r, g, b)

            # Determinar color del texto
            if is_color_light(r, g, b):
                text_color = QColor(0, 0, 0)
            else:
                text_color = QColor(255, 255, 255)

            # Columna 0: Node
            node_item = QTableWidgetItem(node.name())
            node_item.setBackground(node_qcolor)
            node_item.setForeground(QBrush(text_color))
            self.table.setItem(row, 0, node_item)

            # Columna 1: Input A
            if result["inputA"]:
                if result["inputA_error"]:
                    input_text = f"{result['inputA'].name()} {result['inputA_error']}"
                else:
                    input_text = (
                        f"{result['inputA'].name()} ({result['inputA_position']})"
                    )
            else:
                input_text = "-"
            input_a_item = QTableWidgetItem(input_text)
            input_a_item.setBackground(node_qcolor)
            input_a_item.setForeground(
                QBrush(text_color)
            )  # Mantener para fallback si el delegado falla
            self.table.setItem(row, 1, input_a_item)

            # Columna 2: Input B
            if result["inputB"]:
                if result["inputB_error"]:
                    input_text = f"{result['inputB'].name()} {result['inputB_error']}"
                else:
                    input_text = (
                        f"{result['inputB'].name()} ({result['inputB_position']})"
                    )
            else:
                input_text = "-"
            input_b_item = QTableWidgetItem(input_text)
            input_b_item.setBackground(node_qcolor)
            input_b_item.setForeground(QBrush(text_color))  # Mantener para fallback
            self.table.setItem(row, 2, input_b_item)

            # Columna 3: Input Mask
            if result["inputMask"]:
                if result["inputMask_error"]:
                    input_text = (
                        f"{result['inputMask'].name()} {result['inputMask_error']}"
                    )
                else:
                    input_text = (
                        f"{result['inputMask'].name()} ({result['inputMask_position']})"
                    )
            else:
                input_text = "-"
            input_mask_item = QTableWidgetItem(input_text)
            input_mask_item.setBackground(node_qcolor)
            input_mask_item.setForeground(QBrush(text_color))  # Mantener para fallback
            self.table.setItem(row, 3, input_mask_item)

            # Columna 4: Status
            status_item = QTableWidgetItem(result["status"])
            status_item.setTextAlignment(Qt.AlignCenter)  # Centrar el texto
            if result["status"] == "OK":
                status_item.setBackground(QColor(0, 255, 0))  # Verde
                status_item.setForeground(QBrush(QColor(0, 0, 0)))  # Texto negro
            else:
                status_item.setBackground(QColor(125, 0, 0))  # Rojo
                status_item.setForeground(QBrush(QColor(255, 255, 255)))  # Texto blanco
            self.table.setItem(row, 4, status_item)

        self.table.resizeColumnsToContents()

    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana
        width = self.table.verticalHeader().width()
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 10

        # Calcular la altura de la tabla y anadir el espacio para el boton
        table_height = self.table.horizontalHeader().height() + 4
        for i in range(self.table.rowCount()):
            table_height += self.table.rowHeight(i)

        # Anadir un padding para que no este todo tan justo
        height = table_height + 50

        # Limitar la altura maxima al 90% de la altura de la pantalla
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        max_height = int(screen_geometry.height() * 0.80)

        if height > max_height:
            height = max_height

        # Reactivar el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamano de la ventana
        self.resize(width, height)

        # Centrar la ventana en la pantalla

        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2 - 20
        self.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super(ScriptCheckerWindow, self).keyPressEvent(event)

    def go_to_node(self, row, column):
        """Selecciona y centra el nodo en el Node Graph de Nuke al hacer clic en la tabla."""
        start_time = time.time()
        node_name_item = self.table.item(
            row, 0
        )  # La primera columna es el nombre del nodo
        if node_name_item:
            node_name = node_name_item.text()
            debug_print(
                f"[{time.time() - start_time:.4f}s] Intentando ir al nodo: {node_name}"
            )

            node_get_time_start = time.time()
            node = nuke.toNode(node_name)
            debug_print(
                f"[{time.time() - node_get_time_start:.4f}s] nuke.toNode('{node_name}') completado."
            )

            if node:
                # Deseleccionar todos los nodos existentes para asegurar que solo el nodo de interes este seleccionado.
                # Esto es mas eficiente que nuke.selectAll() y nuke.invertSelection().
                for n in nuke.selectedNodes():
                    n.setSelected(False)

                node_select_time_start = time.time()
                node.setSelected(True)
                debug_print(
                    f"[{time.time() - node_select_time_start:.4f}s] node.setSelected(True) completado."
                )

                zoom_time_start = time.time()
                nuke.zoomToFitSelected()
                debug_print(
                    f"[{time.time() - zoom_time_start:.4f}s] nuke.zoomToFitSelected() completado."
                )

                panel_time_start = time.time()
                node.showControlPanel()
                debug_print(
                    f"[{time.time() - panel_time_start:.4f}s] node.showControlPanel() completado."
                )

                # Obtener la informacion completa del nodo para debug
                # Asegurarse de que el objeto 'result' este disponible en 'go_to_node'
                # Para esto, necesitamos pasar el 'result' completo o el indice de la fila
                # al conectar la senal. Actualmente, cellClicked solo pasa (row, column).
                # La forma mas sencilla es obtener la informacion del nodo nuevamente o acceder a ella desde self.results

                # Encontrar el 'result' correspondiente en la lista self.results
                current_result = None
                for res in self.results:
                    if res["node"].name() == node_name:
                        current_result = res
                        break

                if current_result:
                    # Calcular coordenadas del centro para el nodo enfocado
                    node_x_center = node.xpos() + node.screenWidth() / 2
                    node_y_center = node.ypos() + node.screenHeight() / 2

                    debug_msg = f"Nodo enfocado: {node.name()} (X: {node.xpos()}, Y: {node.ypos()}) Centro (X: {node_x_center:.2f}, Y: {node_y_center:.2f})\n"

                    if current_result["inputA"]:
                        input_a_node = current_result["inputA"]
                        input_a_x_center = (
                            input_a_node.xpos() + input_a_node.screenWidth() / 2
                        )
                        input_a_y_center = (
                            input_a_node.ypos() + input_a_node.screenHeight() / 2
                        )
                        debug_msg += f"  Input A: {input_a_node.name()} (X: {input_a_node.xpos()}, Y: {input_a_node.ypos()}) Centro (X: {input_a_x_center:.2f}, Y: {input_a_y_center:.2f})\n"
                    if current_result["inputB"]:
                        input_b_node = current_result["inputB"]
                        input_b_x_center = (
                            input_b_node.xpos() + input_b_node.screenWidth() / 2
                        )
                        input_b_y_center = (
                            input_b_node.ypos() + input_b_node.screenHeight() / 2
                        )
                        debug_msg += f"  Input B: {input_b_node.name()} (X: {input_b_node.xpos()}, Y: {input_b_node.ypos()}) Centro (X: {input_b_x_center:.2f}, Y: {input_b_y_center:.2f})\n"
                    if current_result["inputMask"]:
                        input_mask_node = current_result["inputMask"]
                        input_mask_x_center = (
                            input_mask_node.xpos() + input_mask_node.screenWidth() / 2
                        )
                        input_mask_y_center = (
                            input_mask_node.ypos() + input_mask_node.screenHeight() / 2
                        )
                        debug_msg += f"  Input Mask: {input_mask_node.name()} (X: {input_mask_node.xpos()}, Y: {input_mask_node.ypos()}) Centro (X: {input_mask_x_center:.2f}, Y: {input_mask_y_center:.2f})\n"

                    debug_print(debug_msg)

                debug_print(
                    f"[{time.time() - start_time:.4f}s] Nodo {node_name} seleccionado y en foco. Total time."
                )

                # Traer la ventana de vuelta al frente
                self.activateWindow()
                self.raise_()

            else:
                debug_print(
                    f"[{time.time() - start_time:.4f}s] El nodo {node_name} no existe en Nuke."
                )
                nuke.message(f"El nodo '{node_name}' no se encontró en Nuke.")

    def refresh_data(self):
        debug_print("Refreshing data...")
        # Limpiar la tabla actual
        self.table.clearContents()
        self.table.setRowCount(0)

        # Obtener los nuevos resultados
        self.results = self._get_checked_nodes()

        if not self.results:
            nuke.message(
                "No se encontraron nodos con inputs para verificar despues del refresco."
            )
            self.close()  # Cerrar la ventana si no hay resultados para mostrar
            return

        # Cargar los nuevos datos en la tabla
        self.load_data()
        # Ajustar el tamano de la ventana y centrarla de nuevo
        self.adjust_window_size()
        debug_print("Data refreshed and window adjusted.")

    def _get_checked_nodes(self):
        """Obtiene y verifica los nodos segun la seleccion actual o todos los nodos."""
        # Siempre verificar todos los nodos, ignorando la seleccion.
        nodes_to_check = nuke.allNodes()
        debug_print("Verificando todos los nodos del script.")

        checked_results = []
        for node in nodes_to_check:
            if node.inputs() > 0 and node.Class() not in NODES_TO_SKIP:
                result = check_node_inputs(node)
                checked_results.append(result)

        if ShowOnlyWrong:
            checked_results = [
                result for result in checked_results if result["status"] == "Wrong"
            ]

        return checked_results


app = None
window = None


def main():
    global app, window
    # Crear una instancia de la ventana, que internamente llamara a _get_checked_nodes
    # para obtener los datos iniciales.
    # Obtener los resultados iniciales para pasarselos al constructor
    initial_results = []
    # Crear un objeto temporal para llamar a _get_checked_nodes antes de crear la ventana completa
    temp_checker = ScriptCheckerWindow(
        initial_results
    )  # initial_results es una lista vacia temporalmente
    initial_results = temp_checker._get_checked_nodes()

    if not initial_results:
        nuke.message(
            "No se encontraron nodos con inputs para verificar o todos estan correctos."
        )
        return

    # Check if there's already an instance of QApplication
    app = QApplication.instance() or QApplication([])
    window = ScriptCheckerWindow(initial_results)
    window.show()

    debug_print(f"Ventana mostrada con {len(initial_results)} resultados")


if __name__ == "__main__":
    main()
