"""
_______________________________________________

  LGA_StickyNote v1.91 | Lega
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

# Namespace único para evitar conflictos con otros scripts
LGA_STICKY_NOTE_NAMESPACE = "LGA_StickyNote_v190"

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

# Variables para el sistema de debouncing
DEBOUNCE_DELAY = 150  # Milisegundos de delay para evitar escritura excesiva


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
        self.undo_started = False  # Flag para controlar si se inicio el undo

        # DESHABILITAR COMPLETAMENTE EL SISTEMA DE DEBOUNCING
        # Comentando todo el sistema de timer para evitar loops
        # self.update_timer = QtCore.QTimer()
        # self.update_timer.setSingleShot(True)
        # self.update_timer.timeout.connect(self._delayed_text_update)
        # self._pending_update = False

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Configurar ventana contenedora transparente y siempre on top
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Window
            | QtCore.Qt.WindowStaysOnTopHint
        )
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

        # Botón de flecha izquierda
        self.left_arrow_button = QtWidgets.QPushButton()
        self.left_arrow_button.setFixedSize(
            QtCore.QSize(LINE_HEIGHT, LINE_HEIGHT)
        )  # Ajustar tamaño del botón

        # Rutas de los iconos para flecha izquierda (mismo icono rotado 180°)
        icons_path = os.path.join(os.path.dirname(__file__), "icons")
        self.left_arrow_icon_path = os.path.join(icons_path, "lga_right_arrow.png")
        self.left_arrow_hover_icon_path = os.path.join(
            icons_path, "lga_right_arrow_hover.png"
        )

        # Cargar el icono normal rotado 180°
        if os.path.exists(self.left_arrow_icon_path):
            # Cargar el pixmap original
            pixmap = QtGui.QPixmap(self.left_arrow_icon_path)
            # Crear una transformación de rotación de 180°
            transform = QtGui.QTransform().rotate(180)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.left_arrow_button.setIcon(icon)
            self.left_arrow_button.setIconSize(QtCore.QSize(20, 20))

        # Aplicar estilo CSS al botón
        self.left_arrow_button.setStyleSheet(
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
        self.left_arrow_button.clicked.connect(self.on_left_arrow_clicked)
        self.left_arrow_button.enterEvent = self.on_left_arrow_enter
        self.left_arrow_button.leaveEvent = self.on_left_arrow_leave

        # Instalar filtro de eventos para manejar Ctrl+Enter
        self.left_arrow_button.installEventFilter(self)

        # Botón de flecha derecha
        self.right_arrow_button = QtWidgets.QPushButton()
        self.right_arrow_button.setFixedSize(
            QtCore.QSize(LINE_HEIGHT, LINE_HEIGHT)
        )  # Ajustar tamaño del botón

        # Rutas de los iconos
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

        # Instalar filtro de eventos para manejar Ctrl+Enter
        self.right_arrow_button.installEventFilter(self)

        # Botón de flecha arriba
        self.up_arrow_button = QtWidgets.QPushButton()
        self.up_arrow_button.setFixedSize(
            QtCore.QSize(LINE_HEIGHT, LINE_HEIGHT)
        )  # Ajustar tamaño del botón

        # Rutas de los iconos para flecha arriba (mismo icono rotado -90°)
        self.up_arrow_icon_path = os.path.join(icons_path, "lga_right_arrow.png")
        self.up_arrow_hover_icon_path = os.path.join(
            icons_path, "lga_right_arrow_hover.png"
        )

        # Cargar el icono normal rotado -90°
        if os.path.exists(self.up_arrow_icon_path):
            # Cargar el pixmap original
            pixmap = QtGui.QPixmap(self.up_arrow_icon_path)
            # Crear una transformación de rotación de -90°
            transform = QtGui.QTransform().rotate(-90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.up_arrow_button.setIcon(icon)
            self.up_arrow_button.setIconSize(QtCore.QSize(20, 20))

        # Aplicar estilo CSS al botón
        self.up_arrow_button.setStyleSheet(
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
        self.up_arrow_button.clicked.connect(self.on_up_arrow_clicked)
        self.up_arrow_button.enterEvent = self.on_up_arrow_enter
        self.up_arrow_button.leaveEvent = self.on_up_arrow_leave

        # Instalar filtro de eventos para manejar Ctrl+Enter
        self.up_arrow_button.installEventFilter(self)

        # Botón de flecha abajo
        self.down_arrow_button = QtWidgets.QPushButton()
        self.down_arrow_button.setFixedSize(
            QtCore.QSize(LINE_HEIGHT, LINE_HEIGHT)
        )  # Ajustar tamaño del botón

        # Rutas de los iconos para flecha abajo (mismo icono rotado 90°)
        self.down_arrow_icon_path = os.path.join(icons_path, "lga_right_arrow.png")
        self.down_arrow_hover_icon_path = os.path.join(
            icons_path, "lga_right_arrow_hover.png"
        )

        # Cargar el icono normal rotado 90°
        if os.path.exists(self.down_arrow_icon_path):
            # Cargar el pixmap original
            pixmap = QtGui.QPixmap(self.down_arrow_icon_path)
            # Crear una transformación de rotación de 90°
            transform = QtGui.QTransform().rotate(90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.down_arrow_button.setIcon(icon)
            self.down_arrow_button.setIconSize(QtCore.QSize(20, 20))

        # Aplicar estilo CSS al botón
        self.down_arrow_button.setStyleSheet(
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
        self.down_arrow_button.clicked.connect(self.on_down_arrow_clicked)
        self.down_arrow_button.enterEvent = self.on_down_arrow_enter
        self.down_arrow_button.leaveEvent = self.on_down_arrow_leave

        # Instalar filtro de eventos para manejar Ctrl+Enter
        self.down_arrow_button.installEventFilter(self)

        arrows_layout.addWidget(arrows_label)
        arrows_layout.addWidget(self.left_arrow_button)
        arrows_layout.addWidget(self.right_arrow_button)
        arrows_layout.addWidget(self.up_arrow_button)
        arrows_layout.addWidget(self.down_arrow_button)
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
        # Desconectar conexiones previas para evitar acumulación
        self._disconnect_all_signals()

        self.text_edit.textChanged.connect(self.on_text_changed)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        self.margin_slider.valueChanged.connect(self.on_margin_changed)
        self.margin_y_slider.valueChanged.connect(self.on_margin_y_changed)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_ok_clicked)

    def _disconnect_all_signals(self):
        """Desconecta todas las señales para evitar acumulación de forma segura"""
        signals_to_disconnect = [
            (self.text_edit, "textChanged"),
            (self.font_size_slider, "valueChanged"),
            (self.margin_slider, "valueChanged"),
            (self.margin_y_slider, "valueChanged"),
            (self.cancel_button, "clicked"),
            (self.ok_button, "clicked"),
        ]

        for widget, signal_name in signals_to_disconnect:
            try:
                if hasattr(widget, signal_name):
                    signal = getattr(widget, signal_name)
                    if signal.receivers() > 0:
                        signal.disconnect()
            except (RuntimeError, TypeError, AttributeError):
                # La señal ya fue desconectada, el objeto fue destruido, o no existe
                pass

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

        # Cargar margin X - Si es un nodo nuevo, usar margin X = 2 por defecto
        if self.state_manager.is_new_node:
            margin_x_to_use = 2
        else:
            margin_x_to_use = margin_x_detected

        self.margin_slider.blockSignals(True)
        self.margin_slider.setValue(margin_x_to_use)
        self.margin_value.setText(str(margin_x_to_use))
        self.margin_slider.blockSignals(False)

        # Cargar margin Y
        self.margin_y_slider.blockSignals(True)
        self.margin_y_slider.setValue(margin_y_detected)
        self.margin_y_value.setText(str(margin_y_detected))
        self.margin_y_slider.blockSignals(False)

        # Establecer el nodo en el widget de colores
        self.color_swatch_widget.set_node(self.sticky_node)

        # Si es un nodo nuevo, aplicar el margin X por defecto
        if self.state_manager.is_new_node:
            self.on_text_changed()  # Esto aplicará el margin X = 2 al texto

    def on_text_changed(self):
        """Callback cuando cambia el texto - ESCRITURA INMEDIATA SIN DEBOUNCING"""
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
        """Callback cuando cambia el margin X - ESCRITURA INMEDIATA"""
        if self.sticky_node:
            self.margin_value.setText(str(value))
            # Escribir inmediatamente sin debouncing
            self.on_text_changed()

    def on_margin_y_changed(self, value):
        """Callback cuando cambia el margin Y - ESCRITURA INMEDIATA"""
        if self.sticky_node:
            self.margin_y_value.setText(str(value))
            # Escribir inmediatamente sin debouncing
            self.on_text_changed()

    def on_left_arrow_clicked(self):
        """Callback cuando se hace click en el botón de flecha izquierda"""
        if not self.sticky_node:
            return

        current_text = self.text_edit.toPlainText()
        lines = current_text.split("\n")

        if not lines:
            return

        # Filtrar líneas que no son flechas arriba/abajo para calcular la línea central
        text_lines = []
        start_index = 0
        end_index = len(lines)

        # Verificar si hay flecha arriba (primera línea es "↑")
        if len(lines) >= 1 and lines[0] == "↑":
            start_index = 1

        # Verificar si hay flecha abajo (última línea es "↓")
        if len(lines) >= 1 and lines[-1] == "↓":
            end_index = len(lines) - 1

        # Obtener solo las líneas de texto (sin flechas arriba/abajo)
        text_lines = lines[start_index:end_index]

        if not text_lines:
            return

        # Encontrar la línea central del texto real
        center_line_index_in_text = len(text_lines) // 2
        center_line_index_in_full = start_index + center_line_index_in_text
        center_line = lines[center_line_index_in_full]

        # Verificar si ya existe "←" en la línea central
        if "←" in center_line:
            # Remover la flecha
            new_center_line = center_line.replace("←", "").strip()
        else:
            # Agregar la flecha
            if center_line.strip():
                new_center_line = "← " + center_line
            else:
                new_center_line = "←"

        # Actualizar la línea en el array
        lines[center_line_index_in_full] = new_center_line

        # Reconstruir el texto
        new_text = "\n".join(lines)

        # Actualizar el editor
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(new_text)
        self.text_edit.blockSignals(False)

        # Actualizar el sticky note
        self.on_text_changed()

        print(
            f"Flecha izquierda {'removida' if '←' not in new_center_line else 'agregada'} en línea central del texto"
        )

    def on_right_arrow_clicked(self):
        """Callback cuando se hace click en el botón de flecha derecha"""
        if not self.sticky_node:
            return

        current_text = self.text_edit.toPlainText()
        lines = current_text.split("\n")

        if not lines:
            return

        # Filtrar líneas que no son flechas arriba/abajo para calcular la línea central
        text_lines = []
        start_index = 0
        end_index = len(lines)

        # Verificar si hay flecha arriba (primera línea es "↑")
        if len(lines) >= 1 and lines[0] == "↑":
            start_index = 1

        # Verificar si hay flecha abajo (última línea es "↓")
        if len(lines) >= 1 and lines[-1] == "↓":
            end_index = len(lines) - 1

        # Obtener solo las líneas de texto (sin flechas arriba/abajo)
        text_lines = lines[start_index:end_index]

        if not text_lines:
            return

        # Encontrar la línea central del texto real
        center_line_index_in_text = len(text_lines) // 2
        center_line_index_in_full = start_index + center_line_index_in_text
        center_line = lines[center_line_index_in_full]

        # Verificar si ya existe "→" en la línea central
        if "→" in center_line:
            # Remover la flecha
            new_center_line = center_line.replace("→", "").strip()
        else:
            # Agregar la flecha
            if center_line.strip():
                new_center_line = center_line + " →"
            else:
                new_center_line = "→"

        # Actualizar la línea en el array
        lines[center_line_index_in_full] = new_center_line

        # Reconstruir el texto
        new_text = "\n".join(lines)

        # Actualizar el editor
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(new_text)
        self.text_edit.blockSignals(False)

        # Actualizar el sticky note
        self.on_text_changed()

        print(
            f"Flecha derecha {'removida' if '→' not in new_center_line else 'agregada'} en línea central del texto"
        )

    def on_up_arrow_clicked(self):
        """Callback cuando se hace click en el botón de flecha arriba"""
        if not self.sticky_node:
            return

        current_text = self.text_edit.toPlainText()
        lines = current_text.split("\n")

        # Verificar si ya existe la flecha arriba (primera línea es "↑")
        if len(lines) >= 1 and lines[0] == "↑":
            # Remover la flecha arriba (eliminar la primera línea)
            lines = lines[1:]
            print("Flecha arriba removida del comienzo del texto")
        else:
            # Agregar la flecha arriba al comienzo
            lines.insert(0, "↑")
            print("Flecha arriba agregada al comienzo del texto")

        # Reconstruir el texto
        new_text = "\n".join(lines)

        # Actualizar el editor
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(new_text)
        self.text_edit.blockSignals(False)

        # Actualizar el sticky note
        self.on_text_changed()

    def on_down_arrow_clicked(self):
        """Callback cuando se hace click en el botón de flecha abajo"""
        if not self.sticky_node:
            return

        current_text = self.text_edit.toPlainText()
        lines = current_text.split("\n")

        # Verificar si ya existe la flecha abajo (última línea es "↓")
        if len(lines) >= 1 and lines[-1] == "↓":
            # Remover la flecha abajo (eliminar la última línea)
            lines = lines[:-1]
            print("Flecha abajo removida del final del texto")
        else:
            # Agregar la flecha abajo al final
            lines.append("↓")
            print("Flecha abajo agregada al final del texto")

        # Reconstruir el texto
        new_text = "\n".join(lines)

        # Actualizar el editor
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(new_text)
        self.text_edit.blockSignals(False)

        # Actualizar el sticky note
        self.on_text_changed()

    def on_left_arrow_enter(self, event):
        """Cambia el icono a la version hover cuando el ratón entra"""
        if hasattr(self, "left_arrow_button") and os.path.exists(
            self.left_arrow_hover_icon_path
        ):
            # Cargar el pixmap hover original
            pixmap = QtGui.QPixmap(self.left_arrow_hover_icon_path)
            # Crear una transformación de rotación de 180°
            transform = QtGui.QTransform().rotate(180)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.left_arrow_button.setIcon(icon)

    def on_left_arrow_leave(self, event):
        """Cambia el icono a la version normal cuando el ratón sale"""
        if hasattr(self, "left_arrow_button") and os.path.exists(
            self.left_arrow_icon_path
        ):
            # Cargar el pixmap normal original
            pixmap = QtGui.QPixmap(self.left_arrow_icon_path)
            # Crear una transformación de rotación de 180°
            transform = QtGui.QTransform().rotate(180)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.left_arrow_button.setIcon(icon)

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

    def on_up_arrow_enter(self, event):
        """Cambia el icono a la version hover cuando el ratón entra"""
        if hasattr(self, "up_arrow_button") and os.path.exists(
            self.up_arrow_hover_icon_path
        ):
            # Cargar el pixmap hover original
            pixmap = QtGui.QPixmap(self.up_arrow_hover_icon_path)
            # Crear una transformación de rotación de -90°
            transform = QtGui.QTransform().rotate(-90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.up_arrow_button.setIcon(icon)

    def on_up_arrow_leave(self, event):
        """Cambia el icono a la version normal cuando el ratón sale"""
        if hasattr(self, "up_arrow_button") and os.path.exists(self.up_arrow_icon_path):
            # Cargar el pixmap normal original
            pixmap = QtGui.QPixmap(self.up_arrow_icon_path)
            # Crear una transformación de rotación de -90°
            transform = QtGui.QTransform().rotate(-90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.up_arrow_button.setIcon(icon)

    def on_down_arrow_enter(self, event):
        """Cambia el icono a la version hover cuando el ratón entra"""
        if hasattr(self, "down_arrow_button") and os.path.exists(
            self.down_arrow_hover_icon_path
        ):
            # Cargar el pixmap hover original
            pixmap = QtGui.QPixmap(self.down_arrow_hover_icon_path)
            # Crear una transformación de rotación de 90°
            transform = QtGui.QTransform().rotate(90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.down_arrow_button.setIcon(icon)

    def on_down_arrow_leave(self, event):
        """Cambia el icono a la version normal cuando el ratón sale"""
        if hasattr(self, "down_arrow_button") and os.path.exists(
            self.down_arrow_icon_path
        ):
            # Cargar el pixmap normal original
            pixmap = QtGui.QPixmap(self.down_arrow_icon_path)
            # Crear una transformación de rotación de 90°
            transform = QtGui.QTransform().rotate(90)
            # Aplicar la transformación al pixmap
            rotated_pixmap = pixmap.transformed(
                transform, QtCore.Qt.SmoothTransformation
            )
            # Crear el icono con el pixmap rotado
            icon = QtGui.QIcon(rotated_pixmap)
            self.down_arrow_button.setIcon(icon)

    def on_cancel_clicked(self):
        """Callback cuando se hace click en Cancel"""
        try:
            # Cancelar el undo (no crear punto de undo)
            self._cancel_undo_group()
            print(
                "Acción de cancelación completada exitosamente - No se creó punto de undo"
            )
        except Exception as e:
            print(f"Error durante la cancelación: {e}")
        finally:
            # Limpieza completa antes de cerrar
            self._cleanup_resources()
            self.close()

    def on_ok_clicked(self):
        """Callback cuando se hace click en OK"""
        try:
            # YA NO HAY TIMER QUE DETENER
            # self.update_timer.stop()
            # self._pending_update = False

            # Finalizar el grupo de undo (crear punto de undo)
            self._end_undo_group()
            print("Cambios confirmados exitosamente - Punto de undo creado")
        except Exception as e:
            print(f"Error durante la confirmación: {e}")
        finally:
            # Limpieza completa antes de cerrar
            self._cleanup_resources()
            self.close()

    def _start_undo_group(self):
        """Inicia un grupo de undo para todas las operaciones del StickyNote"""
        try:
            if not self.undo_started:
                nuke.Undo().begin("Edit StickyNote")
                self.undo_started = True
                debug_print("Grupo de undo iniciado")
        except Exception as e:
            print(f"Error al iniciar grupo de undo: {e}")

    def _end_undo_group(self):
        """Finaliza el grupo de undo creando un punto de undo"""
        try:
            if self.undo_started:
                nuke.Undo().end()
                self.undo_started = False
                debug_print("Grupo de undo finalizado - Punto de undo creado")
        except Exception as e:
            print(f"Error al finalizar grupo de undo: {e}")

    def _cancel_undo_group(self):
        """Cancela el grupo de undo sin crear punto de undo"""
        try:
            if self.undo_started:
                # Cancelar el undo deshaciendo todos los cambios
                nuke.Undo().cancel()
                self.undo_started = False
                debug_print("Grupo de undo cancelado - Cambios revertidos")
        except Exception as e:
            print(f"Error al cancelar grupo de undo: {e}")

    def _cleanup_resources(self):
        """Limpieza completa de recursos para evitar memory leaks"""
        try:
            # Asegurarse de que el undo esté cerrado si aún está abierto
            if self.undo_started:
                try:
                    nuke.Undo().cancel()
                    self.undo_started = False
                    debug_print("Grupo de undo cancelado durante limpieza")
                except:
                    pass

            # Desconectar todas las señales de forma segura
            self._disconnect_all_signals()

            # Limpiar referencias
            self.sticky_node = None
            # self._pending_update = False  # Ya no existe

            # Limpiar tooltip personalizado
            if hasattr(self, "tooltip_label") and self.tooltip_label:
                try:
                    self.tooltip_label.close()
                    self.tooltip_label = None
                except:
                    pass

        except Exception as e:
            print(f"Error durante la limpieza: {e}")

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

    def focusOutEvent(self, event):
        """Se ejecuta cuando la ventana pierde el foco - mantener siempre activa"""
        # Ignorar la pérdida de foco para mantener la ventana siempre visible
        super().focusOutEvent(event)
        # Reactivar la ventana después de un breve delay
        QtCore.QTimer.singleShot(50, self.reactivate_window)

    def reactivate_window(self):
        """Reactiva la ventana para mantenerla siempre on top"""
        if self.isVisible():
            self.activateWindow()
            self.raise_()

    def closeEvent(self, event):
        """Se ejecuta cuando se cierra el diálogo - limpieza automática"""
        # Si el diálogo se cierra sin OK ni Cancel, cancelar el undo
        if self.undo_started:
            self._cancel_undo_group()
            debug_print("Diálogo cerrado sin OK/Cancel - Undo cancelado")
        self._cleanup_resources()
        super().closeEvent(event)

    def show_sticky_note_editor(self):
        """Ejecuta el editor de sticky note con nombre único"""
        # Iniciar el grupo de undo ANTES de crear o modificar cualquier nodo
        self._start_undo_group()

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


# Variables globales con nombres únicos para evitar conflictos
app = None
lga_sticky_note_editor_instance = None  # Cambio de nombre para evitar conflictos


def main():
    """Función principal para mostrar el editor de StickyNote."""
    global app, lga_sticky_note_editor_instance
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    lga_sticky_note_editor_instance = StickyNoteEditor()
    lga_sticky_note_editor_instance.show_sticky_note_editor()


# Para uso en Nuke - INSTANCIACIÓN TARDÍA
def run_sticky_note_editor():
    """Mostrar el editor de StickyNote dentro de Nuke usando instanciación tardía"""
    global lga_sticky_note_editor_instance

    # INSTANCIACIÓN TARDÍA: Solo crear cuando se necesite
    # Verificar que no haya instancias de otros scripts conflictivos
    app_instance = QtWidgets.QApplication.instance()
    if app_instance:
        # Buscar widgets existentes que puedan causar conflictos
        conflicting_widgets = []
        for widget in app_instance.allWidgets():
            widget_name = widget.__class__.__name__
            if widget_name in ["ScaleWidget", "NodeLabelEditor"] and widget.isVisible():
                conflicting_widgets.append(widget_name)

        if conflicting_widgets:
            print(
                f"Advertencia: Se detectaron widgets que pueden causar conflictos: {conflicting_widgets}"
            )
            print("Cerrando widgets conflictivos...")
            for widget in app_instance.allWidgets():
                if (
                    widget.__class__.__name__ in conflicting_widgets
                    and widget.isVisible()
                ):
                    try:
                        widget.close()
                    except:
                        pass

    # Si ya existe una instancia del editor, cerrarla y eliminarla completamente
    if lga_sticky_note_editor_instance is not None:
        try:
            if isinstance(lga_sticky_note_editor_instance, QtWidgets.QDialog):
                # Limpieza completa de la instancia anterior
                if hasattr(lga_sticky_note_editor_instance, "_cleanup_resources"):
                    lga_sticky_note_editor_instance._cleanup_resources()
                lga_sticky_note_editor_instance.close()
                lga_sticky_note_editor_instance.deleteLater()
            # Forzar procesamiento de eventos para asegurar limpieza
            if QtWidgets.QApplication.instance():
                QtWidgets.QApplication.processEvents()
        except Exception as e:
            print(f"Error limpiando instancia anterior: {e}")
        finally:
            lga_sticky_note_editor_instance = None  # Resetear la variable global

    # INSTANCIACIÓN TARDÍA: Crear solo cuando se ejecuta la función
    try:
        print("Creando instancia de StickyNoteEditor con instanciación tardía...")
        lga_sticky_note_editor_instance = StickyNoteEditor()
        lga_sticky_note_editor_instance.show_sticky_note_editor()
        print(
            f"LGA_StickyNote iniciado correctamente - Namespace: {LGA_STICKY_NOTE_NAMESPACE}"
        )
    except Exception as e:
        print(f"Error al iniciar LGA_StickyNote: {e}")
        lga_sticky_note_editor_instance = None


# Ejecutar cuando se carga en Nuke
# run_sticky_note_editor()
