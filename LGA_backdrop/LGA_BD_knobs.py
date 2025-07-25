"""
LGA_BD_knobs.py - Manejo modular de knobs para LGA_backdrop
"""

import nuke
import os

try:
    import PySide.QtCore as QtCore
    import PySide.QtGui as QtGui
    import PySide.QtGui as QtWidgets
except:
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui
    import PySide2.QtWidgets as QtWidgets

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


class ColorSwatchWidget(QtWidgets.QWidget):
    # Variables controlables para las variaciones de color
    MIN_LIGHTNESS = 0.3  # Luminancia mínima (0.0 = negro, 1.0 = blanco)
    MAX_LIGHTNESS = 0.8  # Luminancia máxima
    MIN_SATURATION = 0.4  # Saturación mínima (0.0 = gris, 1.0 = color puro)
    MAX_SATURATION = 1.0  # Saturación máxima

    # Nueva variable para la segunda fila
    SecondRow_SatuMult = 0.43  # Multiplicador de saturación para la segunda fila

    SWATCH_TOTAL = 10  # Ahora incluye gris
    SWATCH_CSS = "background-color: rgb(%03d,%03d,%03d); border: none; height: 40px;"
    SWATCH_COLOR = (58, 58, 58)

    # Variable para controlar la saturacion del gradiente en el boton random (0.0 a 1.0)
    RANDOM_GRADIENT_SATURATION = 0.7

    def __init__(self, node=None):
        super(ColorSwatchWidget, self).__init__()
        self.node = node
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

    def _get_current_color_info(self):
        """Obtiene información sobre el color actual del backdrop incluyendo la fila"""
        default_rgb = (58, 58, 58)  # Color por defecto

        if not self.node:
            debug_print(f"No node available")
            return None, default_rgb, -1, 1

        try:
            current_color_value = self.node["tile_color"].getValue()
            debug_print(f"Current tile_color value: {current_color_value}")
        except:
            debug_print(f"Error getting tile_color value")
            return None, default_rgb, -1, 1

        # Convertir el valor de color de Nuke a RGB
        if current_color_value == 0:
            current_rgb = default_rgb
        else:
            # Nuke almacena colores como enteros hex
            if isinstance(current_color_value, int):
                r = (current_color_value >> 24) & 0xFF
                g = (current_color_value >> 16) & 0xFF
                b = (current_color_value >> 8) & 0xFF
                current_rgb = (r, g, b)
                debug_print(f"Converted to RGB: {current_rgb}")
            else:
                current_rgb = default_rgb
                debug_print(f"Using default RGB (not int): {current_rgb}")

        # Buscar en qué familia de color está, en qué variación y en qué fila
        if hasattr(self, "color_variations") and self.color_variations:
            debug_print(f"Searching in color variations...")

            # Iterar a través de todas las familias de colores y ambas filas
            for color_name, _ in self.color_swatches:
                if color_name == "random":
                    continue

                # Verificar en ambas filas
                for row_num in [1, 2]:
                    row_key = f"{color_name}_row{row_num}"
                    variations = self.color_variations.get(row_key)

                    if variations:
                        debug_print(
                            f"Checking {row_key} with {len(variations)} variations"
                        )
                        for i, rgb in enumerate(variations):
                            if rgb and len(rgb) == 3:
                                debug_print(
                                    f"Comparing current {current_rgb} with {row_key}[{i}] {rgb}"
                                )
                                # Tolerancia para comparación de colores
                                if (
                                    abs(current_rgb[0] - rgb[0]) <= 5
                                    and abs(current_rgb[1] - rgb[1]) <= 5
                                    and abs(current_rgb[2] - rgb[2]) <= 5
                                ):
                                    debug_print(
                                        f"MATCH FOUND: {color_name} row{row_num} variation {i}"
                                    )
                                    return color_name, current_rgb, i, row_num
                            else:
                                debug_print(f"Invalid RGB in {row_key}[{i}]: {rgb}")
                    else:
                        debug_print(f"No variations for {row_key}")
        else:
            debug_print(f"No color_variations available")

        debug_print(f"No match found for RGB: {current_rgb}")
        return None, current_rgb, -1, 1

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
                    height: 40px;
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
                    height: 40px;
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

    def makeUI(self):
        return self

    def updateValue(self):
        pass


# Registrar la clase globalmente para PyCustom_Knob al importar el módulo
nuke.LGA_ColorSwatchWidget = ColorSwatchWidget


class LGA_AutoFitControlWidget(QtWidgets.QWidget):
    """Widget personalizado que combina el label 'Auto Fit' y el botón de ajuste."""

    def __init__(self, node=None):
        super(LGA_AutoFitControlWidget, self).__init__()
        self.node = node
        self._create_ui()

    def _create_ui(self):
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que el widget no se estire
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Eliminar márgenes internos del layout
        main_layout.setSpacing(10)  # Eliminar espacio entre los widgets del layout
        main_layout.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )  # Alinear contenido a la DERECHA y verticalmente centrado

        # Añadir un spacer expansivo para consumir el espacio restante a la IZQUIERDA
        main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )

        # Label para el texto "Auto Fit"
        autofit_label = QtWidgets.QLabel("   Auto Fit  ")
        autofit_label.setFixedWidth(60)  # Ancho fijo para el label
        autofit_label.setMinimumWidth(60)
        autofit_label.setMaximumWidth(60)
        autofit_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar tamaño fijo
        autofit_label.setStyleSheet(
            "QLabel { padding: 0px; margin: 0px; }"
        )  # Eliminar padding y margen del label

        # Botón para el icono
        fit_button = QtWidgets.QPushButton()
        fit_button.setToolTip(
            "Resize the backdrop to fit every included nodes using a margin number"
        )
        fit_button.clicked.connect(self._on_fit_button_clicked)

        # Construir la ruta absoluta al icono
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "lga_bd_fit.png")

        # Cargar el icono y ajustar su tamaño
        icon = QtGui.QIcon(icon_path)
        fit_button.setIcon(icon)
        fit_button.setIconSize(
            QtCore.QSize(21, 21)
        )  # Reducir el tamaño del icono en 10px
        fit_button.setFixedSize(
            QtCore.QSize(25, 25)
        )  # Mantener el tamaño del botón igual
        fit_button.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar tamaño fijo del botón

        # Aplicar el estilo CSS al botón
        fit_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(50, 50, 50); /* Color de fondo similar a los otros botones */
                border: none;
                padding: 0px; /* Añadir padding por defecto del botón */
            }
            QPushButton:hover {
                background-color: rgb(80, 80, 80); /* Color al pasar el ratón */
            }
            QPushButton:pressed {
                background-color: rgb(30, 30, 30); /* Color al presionar */
            }
        """
        )

        main_layout.addWidget(autofit_label)
        main_layout.addWidget(fit_button)
        # Añadir un spacer expansivo para consumir el espacio restante a la derecha
        main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )

        # Establecer tamaño fijo para el widget completo (label + espacio + botón)
        self.setFixedSize(
            QtCore.QSize(95, 25)
        )  # Ancho fijo para el widget que contiene el label y el botón

    def _on_fit_button_clicked(self):
        """Maneja el click del botón y llama a la función de ajuste."""
        try:
            import LGA_BD_fit

            LGA_BD_fit.fit_to_selected_nodes(self.node)
            debug_print("LGA_BD_fit.fit_to_selected_nodes() called with node reference")
        except Exception as e:
            debug_print(f"Error calling fit_to_selected_nodes: {e}")

    def makeUI(self):
        return self

    def updateValue(self):
        pass

    def sizeHint(self):
        """Define el tamaño preferido del widget para el sistema de layout."""
        return QtCore.QSize(95, 25)  # Devolver el tamaño fijo deseado


nuke.LGA_AutoFitControlWidget = LGA_AutoFitControlWidget


class LGA_SaveDefaultsWidget(QtWidgets.QWidget):
    """Widget personalizado para el botón Save que guarda configuraciones por defecto."""

    def __init__(self, node=None):
        super(LGA_SaveDefaultsWidget, self).__init__()
        self.node = node
        self._icon_path = os.path.join(
            os.path.dirname(__file__), "icons", "lga_bd_save.png"
        )
        self._hover_icon_path = os.path.join(
            os.path.dirname(__file__), "icons", "lga_bd_save_hover.png"
        )
        self._create_ui()

    def _create_ui(self):
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar que el widget no se estire
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Eliminar márgenes internos del layout
        main_layout.setSpacing(0)  # Espacio pequeño entre label y botón
        main_layout.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )  # Alinear contenido a la IZQUIERDA y verticalmente centrado

        # Label para el texto "Save"
        save_label = QtWidgets.QLabel("   Save")
        save_label.setFixedWidth(50)  # Ancho fijo más amplio para el label (antes 35)
        save_label.setMinimumWidth(50)
        save_label.setMaximumWidth(50)
        save_label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar tamaño fijo
        save_label.setStyleSheet(
            "QLabel { padding: 0px; margin: 0px; text-align: left; }"
        )  # Eliminar padding y margen del label, alinear texto a la izquierda
        save_label.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )  # Alinear texto

        # Botón para el icono
        self.save_button = QtWidgets.QPushButton()  # Cambiado a self.save_button
        self.save_button.setToolTip(
            "Save current font, style and margin properties as default for new backdrops"
        )
        self.save_button.clicked.connect(self._on_save_button_clicked)

        # Cargar el icono normal
        icon = QtGui.QIcon(self._icon_path)
        self.save_button.setIcon(icon)
        self.save_button.setIconSize(
            QtCore.QSize(20, 20)
        )  # Tamaño de icono reducido en 1px
        self.save_button.setFixedSize(
            QtCore.QSize(24, 24)
        )  # Tamaño de botón reducido en 1px
        self.save_button.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Asegurar tamaño fijo del botón

        # Aplicar el estilo CSS al botón
        self.save_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(50, 50, 50); /* Color de fondo similar a los otros botones */
                border: none;
                padding: 0px; /* Añadir padding por defecto del botón */
            }
            QPushButton:hover {
                background-color: rgb(50, 50, 50); /* Color al pasar el ratón, el cambio de icono se maneja en enterEvent/leaveEvent */
            }
            QPushButton:pressed {
                background-color: rgb(70, 70, 70); /* Color al presionar */
            }
        """
        )

        main_layout.addWidget(save_label)
        main_layout.addWidget(self.save_button)  # Añadir self.save_button al layout

        # Establecer tamaño para el widget completo (label + espacio + botón)
        self.setFixedSize(
            QtCore.QSize(
                74, 24
            )  # Ancho para label (50) + espacio (0) + botón (24) = 74
        )
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )  # Tamaño fijo, no expandible

    def enterEvent(self, event):
        """Cambia el icono a la version hover cuando el raton entra."""
        if self.save_button:
            self.save_button.setIcon(QtGui.QIcon(self._hover_icon_path))
        super(LGA_SaveDefaultsWidget, self).enterEvent(event)

    def leaveEvent(self, event):
        """Cambia el icono a la version normal cuando el raton sale."""
        if self.save_button:
            self.save_button.setIcon(QtGui.QIcon(self._icon_path))
        super(LGA_SaveDefaultsWidget, self).leaveEvent(event)

    def _on_save_button_clicked(self):
        """Maneja el click del botón y guarda las configuraciones actuales como defaults."""
        try:
            import LGA_BD_config

            if not self.node:
                debug_print("No node available for saving defaults")
                return

            # Extraer configuraciones actuales del backdrop
            current_settings = LGA_BD_config.extract_current_backdrop_settings(
                self.node
            )

            # Guardar como defaults
            success = LGA_BD_config.save_backdrop_defaults(
                current_settings["font_size"],
                current_settings["font_name"],
                current_settings["bold"],
                current_settings["italic"],
                current_settings["align"],
                current_settings["margin"],
                current_settings["appearance"],
                current_settings["border_width"],
            )

            if success:
                debug_print("Backdrop defaults saved successfully")
                # Mostrar mensaje de confirmación usando nuke.message
                try:
                    import nuke

                    nuke.message("Backdrop defaults saved successfully!")
                except:
                    debug_print("Could not show nuke.message")
            else:
                debug_print("Failed to save backdrop defaults")
                try:
                    import nuke

                    nuke.message(
                        "Failed to save backdrop defaults. Check console for details."
                    )
                except:
                    debug_print("Could not show nuke.message")

        except Exception as e:
            debug_print(f"Error saving backdrop defaults: {e}")
            try:
                import nuke

                nuke.message(f"Error saving backdrop defaults: {e}")
            except:
                debug_print("Could not show nuke.message")

    def makeUI(self):
        return self

    def updateValue(self):
        pass

    def sizeHint(self):
        """Define el tamaño preferido del widget para el sistema de layout."""
        return QtCore.QSize(
            74, 24
        )  # Devolver el tamaño preferido (label + espacio + botón)


nuke.LGA_SaveDefaultsWidget = LGA_SaveDefaultsWidget


def create_divider(name=""):
    """Crea un divider (separador visual)"""
    return nuke.Text_Knob(f"divider_{name}", "")


def create_space(name="", text=" "):
    """Crea un espacio en blanco"""
    return nuke.Text_Knob(f"space_{name}", " ", text)


def create_font_size_knob(default_size=42):
    """Crea el knob de font size con slider"""
    # Renombrar para evitar conflicto con el knob 'note_font_size' nativo del BackdropNode
    size = nuke.Double_Knob("lga_note_font_size", "Font Size")
    size.setRange(10, 100)
    size.setValue(default_size)
    size.setFlag(nuke.NO_ANIMATION)
    return size


def create_font_section():
    """Crea la seccion de font con label y dropdown en linea separada"""
    knobs = []

    # Label para Font
    font_label = nuke.Text_Knob("font_label", "", "       Font ")
    font_label.setFlag(nuke.STARTLINE)  # Nueva línea

    # Link al knob note_font nativo que incluye dropdown y controles Bold/Italic
    font_link = nuke.Link_Knob("note_font_link", "")  # Sin label
    font_link.clearFlag(nuke.STARTLINE)  # En la misma línea que el label Font

    knobs.extend([font_label, font_link])
    return knobs


def create_font_bold_section(bold_value=False, italic_value=False):
    """Crea la seccion de font bold e italic usando controles nativos de Nuke"""
    knobs = []

    # Link al knob note_font nativo que incluye botones Bold/Italic nativos
    font_link = nuke.Link_Knob("note_font_link", "")  # Sin label
    font_link.clearFlag(nuke.STARTLINE)  # En la misma línea que font size
    knobs.append(font_link)

    return knobs


def create_margin_alignment_section(alignment_value="left"):
    """Crea la seccion de margin alignment"""
    knobs = []

    # Label para Margin
    margin_align_label = nuke.Text_Knob("margin_align_label", "", "    Margin ")

    # Dropdown para alignment
    margin_dropdown = nuke.Enumeration_Knob(
        "lga_margin", "", ["left", "center", "right"]
    )
    margin_dropdown.setValue(alignment_value)
    margin_dropdown.setTooltip("Text alignment")

    # Configurar para que margin_align_label y dropdown estén en la misma línea que el botón Bold
    margin_align_label.clearFlag(nuke.STARTLINE)  # En la misma línea que Bold
    margin_dropdown.clearFlag(nuke.STARTLINE)  # Al lado del label

    knobs.extend([margin_align_label, margin_dropdown])

    return knobs


def create_lga_color_swatch_buttons():
    """Crea seccion de colores"""
    color_knobs = []

    # Widget de colores personalizados usando clase registrada globalmente
    lga_color_palette_widget = nuke.PyCustom_Knob(
        "lga_color_palette", "", "nuke.LGA_ColorSwatchWidget(nuke.thisNode())"
    )

    color_knobs.append(lga_color_palette_widget)

    return color_knobs


def create_resize_section(margin_value=50):
    """Crea la seccion de resize"""
    knobs = []

    # Construir la ruta absoluta al icono
    icon_path = os.path.join(os.path.dirname(__file__), "icons", "lga_bd_fit.png")

    # Label principal para Resize (siguiendo el patrón de Z Order)
    resize_label = nuke.Text_Knob("resize_label", "", "    Resize  ")

    # Label para Margin
    margin_label = nuke.Text_Knob("margin_label", "", "Margin ")

    # Slider para margin
    margin_slider = nuke.Double_Knob("margin_slider", "")
    margin_slider.setRange(10, 200)
    margin_slider.setValue(margin_value)  # usar el valor pasado como parámetro
    margin_slider.setFlag(nuke.NO_ANIMATION)
    margin_slider.setTooltip("Margin slider for auto fit")

    # Nuevo widget de PySide2 que contiene tanto el label como el botón de Auto Fit
    autofit_control_widget = nuke.PyCustom_Knob(
        "lga_autofit_control", "", "nuke.LGA_AutoFitControlWidget(nuke.thisNode())"
    )
    autofit_control_widget.clearFlag(nuke.STARTLINE)  # Al lado del slider

    # Configurar para que todos los elementos estén en una sola línea
    resize_label.clearFlag(nuke.STARTLINE)
    margin_label.clearFlag(nuke.STARTLINE)
    margin_slider.clearFlag(nuke.STARTLINE)
    autofit_control_widget.clearFlag(nuke.STARTLINE)

    knobs.extend(
        [
            resize_label,
            margin_label,
            margin_slider,
            autofit_control_widget,
        ]
    )

    return knobs


def create_appearance_section():
    """Crea la sección de Style con dropdown y width slider"""
    knobs = []

    # Label principal para Style (en nueva línea)
    appearance_label = nuke.Text_Knob("appearance_label", "", "      Style ")
    appearance_label.setFlag(nuke.STARTLINE)  # Nueva línea

    # Link al dropdown nativo de appearance
    appearance_link = nuke.Link_Knob("appearance_link", "")
    appearance_link.clearFlag(nuke.STARTLINE)  # En la misma línea que el label

    # Link al slider nativo de border_width
    border_width_link = nuke.Link_Knob("border_width_link", "")
    border_width_link.clearFlag(nuke.STARTLINE)  # En la misma línea

    # Widget de save defaults al final de la línea de style
    save_defaults_widget = nuke.PyCustom_Knob(
        "lga_save_defaults", "", "nuke.LGA_SaveDefaultsWidget(nuke.thisNode())"
    )
    save_defaults_widget.clearFlag(nuke.STARTLINE)  # En la misma línea

    knobs.extend(
        [appearance_label, appearance_link, border_width_link, save_defaults_widget]
    )

    return knobs


def create_zorder_section(z_value=0):
    """Crea la seccion de Z-order"""
    knobs = []

    # Labels y slider de Z-order
    zorder_label = nuke.Text_Knob("z_order_label", "", "   Z Order  ")
    zorder_back_label = nuke.Text_Knob("zorder_back", "", "Back ")
    zorder = nuke.Double_Knob("zorder", "")
    zorder.setRange(-10.0, +10.0)
    zorder.setValue(int(z_value))  # Establecer el valor existente como entero
    zorder_front_label = nuke.Text_Knob("zorder_front", "", " Front")

    # Espacio después del label Front
    zorder_space = nuke.Text_Knob("zorder_space", "", " ")

    # Configurar flags para que aparezcan en la misma linea
    zorder_label.clearFlag(nuke.STARTLINE)
    zorder_back_label.clearFlag(nuke.STARTLINE)
    zorder.clearFlag(nuke.STARTLINE)
    zorder_front_label.clearFlag(nuke.STARTLINE)
    zorder_space.clearFlag(nuke.STARTLINE)
    zorder.setFlag(nuke.NO_ANIMATION)

    knobs.extend(
        [zorder_label, zorder_back_label, zorder, zorder_front_label, zorder_space]
    )

    return knobs


def create_save_defaults_section():
    """Crea la sección del botón Save Defaults"""
    knobs = []

    # Widget de save defaults usando clase registrada globalmente
    save_defaults_widget = nuke.PyCustom_Knob(
        "lga_save_defaults", "", "nuke.LGA_SaveDefaultsWidget(nuke.thisNode())"
    )

    knobs.append(save_defaults_widget)

    return knobs


def add_all_knobs(node, text_label="", existing_margin_alignment="left"):
    """Agrega todos los knobs personalizados al BackdropNode pero solo si no existen"""
    debug_print(f"Adding knobs to node: {node.name()}")

    # Verificar si ya tiene el tab Backdrop y los knobs principales
    if "backdrop" in node.knobs() and "label_link" in node.knobs():
        debug_print(f"Knobs already exist, skipping recreation")
        return

    # Crear tab backdrop solo si no existe
    if "backdrop" not in node.knobs():
        backdrop_tab = nuke.Tab_Knob("backdrop")
        node.addKnob(backdrop_tab)
        debug_print(f"Created backdrop tab")

    # Crear link al label nativo solo si no existe (como en el ejemplo)
    if "label_link" not in node.knobs():
        label_link = nuke.Link_Knob("label_link", "Label")
        label_link.makeLink(node.name(), "label")
        node.addKnob(label_link)
        debug_print(f"Created label_link to native label")

        # Si tenemos texto para asignar, hacerlo al label nativo
        if text_label:
            node["label"].setValue(text_label)

    # Crear font size slider solo si no existe (USAR LA FUNCIÓN ORIGINAL)
    if "lga_note_font_size" not in node.knobs():
        lga_font_size_knob = create_font_size_knob(42)  # usar la función original
        lga_font_size_knob.setFlag(nuke.STARTLINE | nuke.NO_ANIMATION)
        node.addKnob(lga_font_size_knob)
        debug_print(f"Created font size slider")

    # Crear margin dropdown solo si no existe (EN LA MISMA LÍNEA que font size)
    if "lga_margin" not in node.knobs():
        margin_dropdown = nuke.Enumeration_Knob(
            "lga_margin", "", ["left", "center", "right"]
        )
        margin_dropdown.setValue(existing_margin_alignment)
        margin_dropdown.clearFlag(nuke.STARTLINE)  # En la misma línea que font size
        node.addKnob(margin_dropdown)
        debug_print(f"Created margin dropdown")

    # Crear font section (label + dropdown) solo si no existe
    if "font_label" not in node.knobs():
        font_section_knobs = create_font_section()
        for knob in font_section_knobs:
            if knob.name() not in node.knobs():
                node.addKnob(knob)
                if knob.name() == "note_font_link":
                    knob.makeLink(node.name(), "note_font")
        debug_print(f"Created font section (label + dropdown)")

    # Agregar el resto de los knobs usando las funciones existentes si no existen
    add_remaining_knobs_if_missing(node, existing_margin_alignment)

    debug_print(f"Finished adding all knobs")


def add_remaining_knobs_if_missing(node, existing_margin_alignment):
    """Agrega los knobs restantes solo si no existen"""

    # Divider 2 (antes de la sección de resize)
    if "divider_2" not in node.knobs():
        divider2 = nuke.Text_Knob("divider_2", "", "")
        divider2.setFlag(nuke.STARTLINE)
        node.addKnob(divider2)

    # Resize section (includes margin slider)
    resize_knobs = create_resize_section(50)  # default margin value
    for knob in resize_knobs:
        if knob.name() not in node.knobs():
            # Asegurar que los sliders tengan NO_ANIMATION
            if hasattr(knob, "setFlag") and knob.name() == "margin_slider":
                knob.setFlag(nuke.NO_ANIMATION)
            node.addKnob(knob)

    # Divider antes de la sección de Style
    if "divider_style" not in node.knobs():
        divider_style = nuke.Text_Knob("divider_style", "", "")
        divider_style.setFlag(nuke.STARTLINE)
        node.addKnob(divider_style)

    # Style section (antes Appearance)
    appearance_knobs = create_appearance_section()
    for knob in appearance_knobs:
        if knob.name() not in node.knobs():
            node.addKnob(knob)
            # Hacer el link con los knobs nativos
            if knob.name() == "appearance_link":
                knob.makeLink(node.name(), "appearance")
            elif knob.name() == "border_width_link":
                knob.makeLink(node.name(), "border_width")
                # INMEDIATAMENTE aplicar NO_ANIMATION al knob nativo border_width
                if "border_width" in node.knobs():
                    border_width_knob = node["border_width"]
                    if hasattr(border_width_knob, "setFlag"):
                        border_width_knob.setFlag(nuke.NO_ANIMATION)
                        debug_print(
                            f"Applied NO_ANIMATION to native border_width IMMEDIATELY after link"
                        )

    # Divider 3 (antes de la sección de z-order)
    if "divider_3" not in node.knobs():
        divider3 = nuke.Text_Knob("divider_3", "", "")
        divider3.setFlag(nuke.STARTLINE)
        node.addKnob(divider3)

    # Z-order section
    zorder_knobs = create_zorder_section(0)  # default z value
    for knob in zorder_knobs:
        if knob.name() not in node.knobs():
            # Asegurar que el slider zorder tenga NO_ANIMATION
            if hasattr(knob, "setFlag") and knob.name() == "zorder":
                knob.setFlag(nuke.NO_ANIMATION)
            node.addKnob(knob)

    # Divider 4 (antes de la sección de colores)
    if "divider_4" not in node.knobs():
        divider4 = nuke.Text_Knob("divider_4", "", "")
        divider4.setFlag(nuke.STARTLINE)
        node.addKnob(divider4)

    # Colors section (movida al final)
    color_knobs = create_lga_color_swatch_buttons()
    for knob in color_knobs:
        if knob.name() not in node.knobs():
            node.addKnob(knob)

    # Nota: Save Defaults section ahora está integrada en la font section
    # por lo que no necesitamos crear una sección separada


def add_knobs_to_existing_backdrops():
    """
    Busca BackdropNodes existentes en el script actual y les agrega/actualiza knobs personalizados.
    Se ejecuta cuando se carga un script.
    """
    debug_print(f"add_knobs_to_existing_backdrops called - onScriptLoad")

    # Buscar todos los BackdropNodes en el script actual
    backdrop_nodes = [
        node for node in nuke.allNodes() if node.Class() == "BackdropNode"
    ]

    if not backdrop_nodes:
        debug_print(f"Found 0 BackdropNode(s)")
        debug_print(f"add_knobs_to_existing_backdrops completed")
        return

    debug_print(f"Found {len(backdrop_nodes)} BackdropNode(s)")

    for node in backdrop_nodes:
        debug_print(f"Processing node: {node.name()}")

        # Obtener el valor del label nativo para preservarlo
        existing_label_value = node["label"].getValue()
        debug_print(f"Using label value: '{existing_label_value}'")

        # Limpiar el texto para detectar alignment
        clean_text = existing_label_value
        if clean_text.startswith('<div align="center">') and clean_text.endswith(
            "</div>"
        ):
            existing_margin_alignment = "center"
            clean_text = clean_text.replace('<div align="center">', "").replace(
                "</div>", ""
            )
        elif clean_text.startswith('<div align="right">') and clean_text.endswith(
            "</div>"
        ):
            existing_margin_alignment = "right"
            clean_text = clean_text.replace('<div align="right">', "").replace(
                "</div>", ""
            )
        else:
            existing_margin_alignment = "left"

        debug_print(f"Clean text: '{clean_text}'")

        # Llamar a add_all_knobs con el texto limpio
        add_all_knobs(node, clean_text, existing_margin_alignment)

        debug_print(f"Finished processing node: {node.name()}")

    debug_print(f"add_knobs_to_existing_backdrops completed")
