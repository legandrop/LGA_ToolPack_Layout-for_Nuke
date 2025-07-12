"""
_______________________________________________

  LGA_StickyNote v2.00 | Lega
  Editor en tiempo real para StickyNotes en el Node Graph
_______________________________________________

"""

import nuke
import os
from PySide2 import QtWidgets, QtGui, QtCore
from LGA_StickyNote_Utils import (
    StickyNoteStateManager,
    extract_clean_text_and_margins,
    format_text_with_margins,
)


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

# Variables configurables para los botones de color
COLOR_BUTTON_HEIGHT = 16  # Altura de los botones de color (en pixels)
COLOR_BUTTON_BORDER_RADIUS = (
    2  # Radio de los bordes redondeados de los botones (en pixels)
)


def debug_print(*message):
    if DEBUG:
        print(*message)


# Colores para el gradiente
BLUE_COLOR = "#9370DB"
VIOLET_COLOR = "#4169E1"
HANDLE_SIZE = 12  # Tamaño del handle del slider
LINE_HEIGHT = 25  # Altura de cada linea de control


class StickyNoteColorSwatchWidget(QtWidgets.QWidget):
    """Widget de colores para StickyNote, idéntico al backdrop pero con botones de la mitad del tamaño"""

    # Variables controlables para las variaciones de color
    MIN_LIGHTNESS = 0.3  # Luminancia mínima (0.0 = negro, 1.0 = blanco)
    MAX_LIGHTNESS = 0.8  # Luminancia máxima
    MIN_SATURATION = 0.4  # Saturación mínima (0.0 = gris, 1.0 = color puro)
    MAX_SATURATION = 1.0  # Saturación máxima

    # Nueva variable para la segunda fila
    SecondRow_SatuMult = 0.43  # Multiplicador de saturación para la segunda fila

    SWATCH_TOTAL = 10  # Ahora incluye gris
    SWATCH_CSS = f"background-color: rgb(%03d,%03d,%03d); border: none; height: {COLOR_BUTTON_HEIGHT}px; border-radius: {COLOR_BUTTON_BORDER_RADIUS}px;"
    SWATCH_COLOR = (58, 58, 58)

    # Variable para controlar la saturacion del gradiente en el boton random (0.0 a 1.0)
    RANDOM_GRADIENT_SATURATION = 0.7

    def __init__(self, node=None, parent_dialog=None):
        super(StickyNoteColorSwatchWidget, self).__init__()
        self.node = node
        self.parent_dialog = parent_dialog  # Referencia al diálogo padre
        self._swatch_widgets = []

        # Sistema de tracking interno para colores
        self._last_applied_color = None  # Nombre del último color aplicado
        self._last_applied_index = -1  # Índice del último color aplicado
        self._last_applied_row = 1  # Fila del último color aplicado (1 o 2)

        # Definir colores base y sus variaciones
        self.color_swatches = [
            ("random", "gradient"),  # Botón especial con gradiente multicolor
            ("red", (204, 85, 85)),
            ("green", (85, 204, 85)),
            ("blue", (85, 85, 204)),
            ("yellow", (204, 204, 85)),
            ("cyan", (85, 204, 204)),
            ("magenta", (204, 85, 204)),
            ("orange", (204, 136, 85)),
            ("purple", (136, 85, 204)),
            ("gray", (128, 128, 128)),  # Nuevo botón gris
        ]

        # Generar todas las variaciones de colores al inicializar
        self.color_variations = self._generate_color_variations()

        self._create_layout()

    def _rgb_to_hls(self, r, g, b):
        """Convierte RGB (0-255) a HLS (0-1)"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)

        # Lightness
        l = (max_val + min_val) / 2.0

        if max_val == min_val:
            h = s = 0.0  # achromatic
        else:
            d = max_val - min_val
            s = d / (2.0 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)

            if max_val == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_val == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6.0

        return h, l, s

    def _hls_to_rgb(self, h, l, s):
        """Convierte HLS (0-1) a RGB (0-255)"""

        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        if s == 0:
            r = g = b = l  # achromatic
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)

        return int(r * 255), int(g * 255), int(b * 255)

    def _saturate_rgb(self, r, g, b, saturation_factor):
        """Ajusta la saturacion de un color RGB (0-255) por un factor (0.0 a 1.0)"""
        h, l, s = self._rgb_to_hls(r, g, b)
        new_s = s * saturation_factor
        return self._hls_to_rgb(h, l, new_s)

    def _generate_color_variations(self):
        """Genera 5 variaciones para cada color base en ambas filas"""
        variations = {}

        for color_name, rgb_values in self.color_swatches:
            if color_name == "random":
                continue  # El botón random no necesita variaciones

            # Generar variaciones para la primera fila (saturación normal)
            row1_key = f"{color_name}_row1"
            # Generar variaciones para la segunda fila (saturación reducida)
            row2_key = f"{color_name}_row2"

            if color_name == "gray":
                # Para gris, solo variar el brillo (de negro a blanco) en ambas filas
                gray_variations_row1 = []
                gray_variations_row2 = []
                for i in range(5):
                    lightness = (
                        self.MIN_LIGHTNESS
                        + (self.MAX_LIGHTNESS - self.MIN_LIGHTNESS) * i / 4
                    )
                    gray_value = int(lightness * 255)
                    gray_variations_row1.append((gray_value, gray_value, gray_value))

                    # Para la segunda fila del gris, aplicar el multiplicador a la luminancia
                    gray_value_row2 = int(lightness * 255 * self.SecondRow_SatuMult)
                    gray_variations_row2.append(
                        (gray_value_row2, gray_value_row2, gray_value_row2)
                    )

                variations[row1_key] = gray_variations_row1
                variations[row2_key] = gray_variations_row2
            else:
                # Para colores normales, variar luminancia y saturación
                h, l, s = self._rgb_to_hls(*rgb_values)
                color_variations_row1 = []
                color_variations_row2 = []

                for i in range(5):
                    # Interpolar entre valores mínimos y máximos
                    progress = i / 4.0
                    new_lightness = (
                        self.MIN_LIGHTNESS
                        + (self.MAX_LIGHTNESS - self.MIN_LIGHTNESS) * progress
                    )
                    new_saturation = (
                        self.MIN_SATURATION
                        + (self.MAX_SATURATION - self.MIN_SATURATION) * progress
                    )

                    # Primera fila: saturación normal
                    new_rgb_row1 = self._hls_to_rgb(h, new_lightness, new_saturation)
                    color_variations_row1.append(new_rgb_row1)

                    # Segunda fila: saturación multiplicada por SecondRow_SatuMult
                    new_saturation_row2 = new_saturation * self.SecondRow_SatuMult
                    new_rgb_row2 = self._hls_to_rgb(
                        h, new_lightness, new_saturation_row2
                    )
                    color_variations_row2.append(new_rgb_row2)

                variations[row1_key] = color_variations_row1
                variations[row2_key] = color_variations_row2

        return variations

    def _create_layout(self):
        # Layout principal vertical para contener las dos filas
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(5)  # Espacio entre filas
        self.setLayout(main_layout)

        # Primera fila de botones (saturación normal)
        row1_layout = QtWidgets.QHBoxLayout()
        row1_layout.setAlignment(QtCore.Qt.AlignTop)

        for i, (color_name, rgb_values) in enumerate(self.color_swatches):
            color_knob = QtWidgets.QPushButton()
            color_knob.clicked.connect(self.color_knob_click)
            color_knob.setProperty("color_name", color_name)
            color_knob.setProperty("row_number", 1)  # Primera fila

            if color_name == "random" and rgb_values == "gradient":
                # Botón especial con gradiente multicolor (primera fila)
                color_knob.setToolTip("Click to Apply Random Color!")

                # Generar colores para el gradiente con saturacion controlada
                gradient_colors_rgb = [
                    (255, 0, 0),
                    (255, 127, 0),
                    (255, 255, 0),
                    (0, 255, 0),
                    (0, 0, 255),
                    (139, 0, 255),
                    (255, 0, 255),
                ]

                # Aplicar el factor de saturacion a cada color
                saturated_colors = []
                for r, g, b in gradient_colors_rgb:
                    saturated_colors.append(
                        self._saturate_rgb(r, g, b, self.RANDOM_GRADIENT_SATURATION)
                    )

                # Construir el string CSS para el gradiente
                stop_values = [
                    "stop: 0 rgb(%d, %d, %d)" % saturated_colors[0],
                    "stop: 0.16 rgb(%d, %d, %d)" % saturated_colors[1],
                    "stop: 0.33 rgb(%d, %d, %d)" % saturated_colors[2],
                    "stop: 0.5 rgb(%d, %d, %d)" % saturated_colors[3],
                    "stop: 0.66 rgb(%d, %d, %d)" % saturated_colors[4],
                    "stop: 0.83 rgb(%d, %d, %d)" % saturated_colors[5],
                    "stop: 1 rgb(%d, %d, %d)" % saturated_colors[6],
                ]

                gradient_css = f"""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        {', '.join(stop_values)});
                    border: none;
                    height: {COLOR_BUTTON_HEIGHT}px;
                    border-radius: {COLOR_BUTTON_BORDER_RADIUS}px;
                """
                color_knob.setStyleSheet(gradient_css)
                color_knob.setProperty("is_random", True)
            else:
                # Botón de color sólido normal (primera fila)
                color_knob.setToolTip(
                    f"Click to cycle through {color_name} variations! (Full Saturation)"
                )
                color_knob.setStyleSheet(
                    self.SWATCH_CSS % (rgb_values[0], rgb_values[1], rgb_values[2])
                )
                color_knob.setProperty("is_random", False)

            row1_layout.addWidget(color_knob)
            self._swatch_widgets.append(color_knob)

            # Instalar filtro de eventos si hay referencia al diálogo padre
            if self.parent_dialog:
                color_knob.installEventFilter(self.parent_dialog)

        # Segunda fila de botones (saturación reducida)
        row2_layout = QtWidgets.QHBoxLayout()
        row2_layout.setAlignment(QtCore.Qt.AlignTop)

        for i, (color_name, rgb_values) in enumerate(self.color_swatches):
            color_knob = QtWidgets.QPushButton()
            color_knob.clicked.connect(self.color_knob_click)
            color_knob.setProperty("color_name", color_name)
            color_knob.setProperty("row_number", 2)  # Segunda fila

            if color_name == "random" and rgb_values == "gradient":
                # Botón especial con gradiente multicolor (segunda fila, saturación reducida)
                color_knob.setToolTip(
                    "Click to Apply Random Color! (Reduced Saturation)"
                )

                # Generar colores para el gradiente con saturacion reducida
                gradient_colors_rgb = [
                    (255, 0, 0),
                    (255, 127, 0),
                    (255, 255, 0),
                    (0, 255, 0),
                    (0, 0, 255),
                    (139, 0, 255),
                    (255, 0, 255),
                ]

                # Aplicar el factor de saturacion reducido a cada color
                saturated_colors = []
                for r, g, b in gradient_colors_rgb:
                    reduced_saturation = (
                        self.RANDOM_GRADIENT_SATURATION * self.SecondRow_SatuMult
                    )
                    saturated_colors.append(
                        self._saturate_rgb(r, g, b, reduced_saturation)
                    )

                # Construir el string CSS para el gradiente
                stop_values = [
                    "stop: 0 rgb(%d, %d, %d)" % saturated_colors[0],
                    "stop: 0.16 rgb(%d, %d, %d)" % saturated_colors[1],
                    "stop: 0.33 rgb(%d, %d, %d)" % saturated_colors[2],
                    "stop: 0.5 rgb(%d, %d, %d)" % saturated_colors[3],
                    "stop: 0.66 rgb(%d, %d, %d)" % saturated_colors[4],
                    "stop: 0.83 rgb(%d, %d, %d)" % saturated_colors[5],
                    "stop: 1 rgb(%d, %d, %d)" % saturated_colors[6],
                ]

                gradient_css = f"""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        {', '.join(stop_values)});
                    border: none;
                    height: {COLOR_BUTTON_HEIGHT}px;
                    border-radius: {COLOR_BUTTON_BORDER_RADIUS}px;
                """
                color_knob.setStyleSheet(gradient_css)
                color_knob.setProperty("is_random", True)
            else:
                # Botón de color sólido normal (segunda fila, saturación reducida)
                if color_name == "gray":
                    # Para gris, aplicar el multiplicador a la luminancia
                    reduced_gray = int(rgb_values[0] * self.SecondRow_SatuMult)
                    reduced_rgb = (reduced_gray, reduced_gray, reduced_gray)
                else:
                    # Para colores normales, reducir la saturación
                    h, l, s = self._rgb_to_hls(*rgb_values)
                    reduced_saturation = s * self.SecondRow_SatuMult
                    reduced_rgb = self._hls_to_rgb(h, l, reduced_saturation)

                color_knob.setToolTip(
                    f"Click to cycle through {color_name} variations! (Reduced Saturation)"
                )
                color_knob.setStyleSheet(
                    self.SWATCH_CSS % (reduced_rgb[0], reduced_rgb[1], reduced_rgb[2])
                )
                color_knob.setProperty("is_random", False)

            row2_layout.addWidget(color_knob)
            self._swatch_widgets.append(color_knob)

            # Instalar filtro de eventos si hay referencia al diálogo padre
            if self.parent_dialog:
                color_knob.installEventFilter(self.parent_dialog)

        # Agregar las dos filas al layout principal
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)

    def color_knob_click(self):
        widget = self.sender()
        if not widget or not self.node:
            return

        color_name = widget.property("color_name")
        row_number = widget.property("row_number")

        # Verificar si es el botón de random
        if widget.property("is_random"):
            self._apply_random_color(row_number)
            return

        # Manejar clicks en botones de color normal
        self._cycle_color_variation(color_name, row_number)

    def _cycle_color_variation(self, color_name, row_number):
        """Cicla entre las variaciones de un color específico en la fila especificada"""
        row_key = f"{color_name}_row{row_number}"

        if (
            not hasattr(self, "color_variations")
            or not self.color_variations
            or row_key not in self.color_variations
        ):
            debug_print(f"No variations available for {row_key}")
            return

        # Usar tracking interno en lugar de detección de color actual
        if (
            self._last_applied_color == color_name
            and self._last_applied_row == row_number
            and self._last_applied_index >= 0
        ):
            # Si el último color aplicado es de la misma familia y fila, avanzar al siguiente
            next_index = (self._last_applied_index + 1) % 5  # Loop de 0 a 4
            debug_print(
                f"Current {color_name} row{row_number} variation: {self._last_applied_index}, next: {next_index}"
            )
        else:
            # Si no es de la misma familia/fila o es la primera vez, empezar desde 0
            next_index = 0
            debug_print(
                f"Starting {color_name} row{row_number} variations from index 0"
            )

        # Aplicar la nueva variación
        variations = self.color_variations.get(row_key)
        if variations and next_index < len(variations):
            new_rgb = variations[next_index]
            if new_rgb and len(new_rgb) == 3:
                r, g, b = new_rgb

                # Convertir a formato hex para Nuke
                hex_color = (r << 24) | (g << 16) | (b << 8) | 255
                if (
                    self.node
                    and hasattr(self.node, "__getitem__")
                    and "tile_color" in self.node.knobs()
                ):
                    self.node["tile_color"].setValue(hex_color)

                    # Actualizar tracking interno
                    self._last_applied_color = color_name
                    self._last_applied_index = next_index
                    self._last_applied_row = row_number

                    debug_print(
                        f"Applied {color_name} row{row_number} variation {next_index}: RGB({r}, {g}, {b}) = {hex_color}"
                    )
                else:
                    debug_print(f"Error: Invalid node or missing tile_color knob")
            else:
                debug_print(
                    f"Error: Invalid RGB values for {color_name} row{row_number} variation {next_index}"
                )
        else:
            debug_print(f"Error: No valid variations found for {row_key}")

    def _apply_random_color(self, row_number=1):
        """Aplica un color completamente aleatorio según la fila especificada"""
        import random

        # Generar valores RGB aleatorios
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)

        # Si es la segunda fila, aplicar el multiplicador de saturación
        if row_number == 2:
            h, l, s = self._rgb_to_hls(r, g, b)
            reduced_saturation = s * self.SecondRow_SatuMult
            r, g, b = self._hls_to_rgb(h, l, reduced_saturation)

        # Convertir a formato hex para Nuke
        hex_color = (r << 24) | (g << 16) | (b << 8) | 255
        if (
            self.node
            and hasattr(self.node, "__getitem__")
            and "tile_color" in self.node.knobs()
        ):
            self.node["tile_color"].setValue(hex_color)

            # Reset tracking para colores random
            self._last_applied_color = None
            self._last_applied_index = -1
            self._last_applied_row = row_number

            debug_print(
                f"Applied random color row{row_number}: RGB({r}, {g}, {b}) = {hex_color}"
            )
        else:
            debug_print(f"Error: Invalid node or missing tile_color knob")

    def set_node(self, node):
        """Establece el nodo StickyNote para aplicar colores"""
        self.node = node


class StickyNoteEditor(QtWidgets.QDialog):
    def __init__(self):
        super(StickyNoteEditor, self).__init__()

        self.sticky_node = None
        self.drag_position = None  # Para el arrastre de la ventana
        self.state_manager = StickyNoteStateManager()  # Gestor de estado
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

        # Widget de colores
        self.color_swatch_widget = StickyNoteColorSwatchWidget(parent_dialog=self)
        self.color_swatch_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # Instalar filtro de eventos para manejar Ctrl+Enter en botones de color
        self.color_swatch_widget.installEventFilter(self)

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
        content_layout.addLayout(font_size_layout)
        content_layout.addLayout(margin_x_layout)
        content_layout.addLayout(margin_y_layout)
        content_layout.addLayout(arrows_layout)
        content_layout.addWidget(self.color_swatch_widget)
        content_layout.addSpacing(10)  # Espacio antes de los botones
        content_layout.addLayout(buttons_layout)

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
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_ok_clicked)

    def get_or_create_sticky_note(self):
        """Obtiene el sticky note seleccionado o crea uno nuevo"""
        selected_nodes = nuke.selectedNodes()

        # Buscar si hay un StickyNote seleccionado
        sticky_notes = [node for node in selected_nodes if node.Class() == "StickyNote"]

        if sticky_notes:
            # Usar el primer StickyNote encontrado
            self.sticky_node = sticky_notes[0]
            # Guardar estado original para poder restaurarlo
            self.state_manager.save_original_state(self.sticky_node)
            print(f"Editando StickyNote existente: {self.sticky_node.name()}")
        else:
            # Crear un nuevo StickyNote
            self.sticky_node = nuke.createNode("StickyNote")
            # Marcar como nuevo para poder eliminarlo si se cancela
            self.state_manager.set_as_new_node(self.sticky_node)
            print(f"Creado nuevo StickyNote: {self.sticky_node.name()}")

        # Deseleccionar todos los nodos después de obtener o crear el StickyNote
        for node in nuke.selectedNodes():
            node.setSelected(False)

        return self.sticky_node

    def load_sticky_note_data(self):
        """Carga los datos del sticky note en la interfaz"""
        if not self.sticky_node:
            return

        # Cargar texto usando las funciones utilitarias
        current_text = self.sticky_node["label"].value()
        debug_print(f"Texto actual del StickyNote: '{current_text}'")

        # Extraer texto limpio y márgenes
        final_clean_text, margin_x_detected, margin_y_detected = (
            extract_clean_text_and_margins(current_text)
        )

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

        # Establecer el nodo en el widget de colores
        self.color_swatch_widget.set_node(self.sticky_node)

    def on_text_changed(self):
        """Callback cuando cambia el texto"""
        if self.sticky_node:
            current_text = self.text_edit.toPlainText()
            margin_x = self.margin_slider.value()
            margin_y = self.margin_y_slider.value()

            # Formatear texto usando las funciones utilitarias
            final_text = format_text_with_margins(current_text, margin_x, margin_y)
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

    def on_cancel_clicked(self):
        """Callback cuando se hace click en Cancel"""
        try:
            # Usar el gestor de estado para manejar la cancelación
            success = self.state_manager.handle_cancel_action()
            if success:
                print("Acción de cancelación completada exitosamente")
            else:
                print("No se pudo completar la acción de cancelación")
        except Exception as e:
            print(f"Error durante la cancelación: {e}")
        finally:
            # Cerrar el diálogo
            self.close()

    def on_ok_clicked(self):
        """Callback cuando se hace click en OK"""
        try:
            # Usar el gestor de estado para confirmar los cambios
            success = self.state_manager.handle_ok_action()
            if success:
                print("Cambios confirmados exitosamente")
            else:
                print("No se pudieron confirmar los cambios")
        except Exception as e:
            print(f"Error durante la confirmación: {e}")
        finally:
            # Cerrar el diálogo
            self.close()

    def eventFilter(self, obj, event):
        """Filtro de eventos para interceptar Ctrl+Enter en botones de color"""
        if event.type() == QtCore.QEvent.KeyPress:
            if (
                event.key() == QtCore.Qt.Key_Return
                or event.key() == QtCore.Qt.Key_Enter
            ):
                if event.modifiers() & QtCore.Qt.ControlModifier:
                    # Interceptar Ctrl+Enter y ejecutar OK
                    self.on_ok_clicked()
                    return True  # Evento manejado
            elif event.key() == QtCore.Qt.Key_Escape:
                # Interceptar ESC y ejecutar Cancel
                self.on_cancel_clicked()
                return True  # Evento manejado

        # Permitir que el evento continue normalmente
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado"""
        if event.key() == QtCore.Qt.Key_Escape:
            # ESC funciona como Cancel
            self.on_cancel_clicked()
        elif event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # Ctrl+Enter funciona como OK, sin importar qué widget tenga el foco
            if event.modifiers() & QtCore.Qt.ControlModifier:
                self.on_ok_clicked()
                event.accept()  # Marcar el evento como manejado
                return
            else:
                super().keyPressEvent(event)
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

        # Ajustar el ancho de la ventana después de que se haya ajustado el tamaño inicial
        current_width = self.width()
        self.setFixedWidth(current_width - 140)

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
            sticky_top = self.sticky_node.ypos()
            delta_top = (sticky_top - center_y) * zoom
            sticky_top_screen = dag_top_left.y() + dag_widget.height() // 2 + delta_top
            y_above = int(sticky_top_screen - UI_MARGIN_Y - window_height)

            if y_above >= avail.top():
                window_y = y_above + 20
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

    # Si ya existe una instancia del editor, cerrarla y eliminarla
    if sticky_editor is not None and isinstance(sticky_editor, QtWidgets.QDialog):
        sticky_editor.close()
        sticky_editor.deleteLater()  # Borrar el objeto de la memoria de forma segura
        sticky_editor = None  # Resetear la variable global

    sticky_editor = StickyNoteEditor()
    sticky_editor.run()


# Ejecutar cuando se carga en Nuke
# run_sticky_note_editor()
