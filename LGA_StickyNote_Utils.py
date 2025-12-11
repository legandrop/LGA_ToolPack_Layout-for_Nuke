"""
_______________________________________________

  LGA_StickyNote_Utils v1.01 | Lega
  Utilidades para el editor de StickyNotes
_______________________________________________

"""

import nuke
from qt_compat import QtWidgets, QtGui, QtCore


class StickyNoteStateManager:
    """Clase para manejar el estado original y las operaciones de los StickyNotes"""

    def __init__(self):
        self.original_state = None
        self.is_new_node = False
        self.sticky_node = None

    def save_original_state(self, sticky_node):
        """Guarda el estado original del sticky note"""
        self.sticky_node = sticky_node

        if sticky_node:
            self.original_state = {
                "label": sticky_node["label"].value(),
                "note_font_size": sticky_node["note_font_size"].value(),
                "note_font_color": sticky_node["note_font_color"].value(),
                "tile_color": sticky_node["tile_color"].value(),
            }
            print(f"Estado original guardado para: {sticky_node.name()}")
        else:
            self.original_state = None

    def set_as_new_node(self, sticky_node):
        """Marca el nodo como nuevo (recién creado)"""
        self.is_new_node = True
        self.sticky_node = sticky_node
        self.original_state = None
        print(f"Nodo marcado como nuevo: {sticky_node.name()}")

    def restore_original_state(self):
        """Restaura el estado original del sticky note"""
        if not self.sticky_node or not self.original_state:
            print("No hay estado original para restaurar")
            return False

        try:
            # Restaurar todos los valores originales
            self.sticky_node["label"].setValue(self.original_state["label"])
            self.sticky_node["note_font_size"].setValue(
                self.original_state["note_font_size"]
            )
            self.sticky_node["note_font_color"].setValue(
                self.original_state["note_font_color"]
            )
            self.sticky_node["tile_color"].setValue(self.original_state["tile_color"])

            print(f"Estado original restaurado para: {self.sticky_node.name()}")
            return True
        except Exception as e:
            print(f"Error al restaurar estado original: {e}")
            return False

    def delete_new_node(self):
        """Elimina el nodo si es nuevo"""
        if self.is_new_node and self.sticky_node:
            try:
                node_name = self.sticky_node.name()
                nuke.delete(self.sticky_node)
                print(f"Nodo nuevo eliminado: {node_name}")
                return True
            except Exception as e:
                print(f"Error al eliminar nodo nuevo: {e}")
                return False
        return False

    def handle_cancel_action(self):
        """Maneja la acción de cancelar"""
        if self.is_new_node:
            # Si es un nodo nuevo, eliminarlo
            return self.delete_new_node()
        else:
            # Si es un nodo existente, restaurar estado original
            return self.restore_original_state()

    def handle_ok_action(self):
        """Maneja la acción de confirmar (mantener cambios)"""
        # No hacer nada especial, solo confirmar que los cambios se mantienen
        if self.sticky_node:
            print(f"Cambios confirmados para: {self.sticky_node.name()}")
            return True
        return False

    def reset(self):
        """Resetea el estado del manager"""
        self.original_state = None
        self.is_new_node = False
        self.sticky_node = None


def extract_clean_text_and_margins(text):
    """
    Extrae el texto limpio y detecta los márgenes X e Y de un texto con formato.

    Args:
        text (str): Texto con formato de StickyNote

    Returns:
        tuple: (texto_limpio, margin_x, margin_y)
    """
    if not text.strip():
        return "", 0, 0

    lines = text.split("\n")

    # Valores por defecto
    margin_x_detected = 0
    margin_y_detected = 0

    # --- Detectar flechas verticales para márgenes, pero NO eliminarlas del texto ---
    has_up_arrow = False
    has_down_arrow = False
    
    # Detectar flecha arriba (primera línea es "↑")
    if len(lines) >= 1 and lines[0].strip() == "↑":
        has_up_arrow = True

    # Detectar flecha abajo (última línea es "↓")
    if len(lines) >= 1 and lines[-1].strip() == "↓":
        has_down_arrow = True

    # Para detectar márgenes, trabajar con las líneas sin flechas verticales
    lines_for_margin_detection = lines[:]
    if has_up_arrow:
        lines_for_margin_detection = lines_for_margin_detection[1:]
    if has_down_arrow:
        lines_for_margin_detection = lines_for_margin_detection[:-1]

    # --- Detección de Margin X: buscar primera línea con contenido ---
    for line in lines_for_margin_detection:
        if line.strip():
            leading = len(line) - len(line.lstrip(" "))
            trailing = len(line) - len(line.rstrip(" "))
            margin_x_detected = min(leading, trailing)
            break

    # --- Detección de Margin Y: líneas vacías al inicio y al final ---
    start_empty = 0
    for line in lines_for_margin_detection:
        if line.strip() == "":
            start_empty += 1
        else:
            break

    end_empty = 0
    for line in reversed(lines_for_margin_detection):
        if line.strip() == "":
            end_empty += 1
        else:
            break

    margin_y_detected = min(start_empty, end_empty)

    # --- Extraer solo las líneas de contenido sin margin Y ---
    if margin_y_detected * 2 < len(lines_for_margin_detection):
        content_lines = lines_for_margin_detection[margin_y_detected : len(lines_for_margin_detection) - margin_y_detected]
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

    # --- Reconstruir el texto final con flechas verticales preservadas ---
    final_clean_text = "\n".join(clean_lines)
    
    # Agregar flechas verticales de vuelta al texto limpio
    if has_up_arrow:
        final_clean_text = "↑\n" + final_clean_text
    if has_down_arrow:
        final_clean_text = final_clean_text + "\n↓"

    return final_clean_text, margin_x_detected, margin_y_detected


def format_text_with_margins(text, margin_x, margin_y):
    """
    Formatea el texto aplicando los márgenes especificados.

    Args:
        text (str): Texto limpio
        margin_x (int): Margen horizontal (espacios a cada lado)
        margin_y (int): Margen vertical (líneas vacías arriba y abajo)

    Returns:
        str: Texto formateado con márgenes
    """
    if not text:
        return ""

    margin_x_spaces = " " * margin_x

    # Agregar espacios a ambos lados de cada línea (Margin X)
    lines = text.split("\n")
    final_lines = []
    for line in lines:
        final_lines.append(margin_x_spaces + line + margin_x_spaces)

    # Agregar líneas vacías arriba y abajo (Margin Y)
    empty_line = margin_x_spaces + margin_x_spaces  # Línea vacía con margin X
    for _ in range(margin_y):
        final_lines.insert(0, empty_line)  # Agregar arriba
        final_lines.append(empty_line)  # Agregar abajo

    return "\n".join(final_lines)


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


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
    SWATCH_CSS = "background-color: rgb(%03d,%03d,%03d); border: none; height: 20px;"  # Mitad del tamaño (40px -> 20px)
    SWATCH_COLOR = (58, 58, 58)

    # Variable para controlar la saturacion del gradiente en el boton random (0.0 a 1.0)
    RANDOM_GRADIENT_SATURATION = 0.7

    def __init__(self, node=None):
        super(StickyNoteColorSwatchWidget, self).__init__()
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
        """Obtiene información sobre el color actual del StickyNote incluyendo la fila"""
        default_rgb = (58, 58, 58)  # Color por defecto

        if not self.node:
            debug_print(f"No node available")
            return None, default_rgb, -1, 1

        try:
            # Para StickyNote usamos tile_color en lugar de tile_color del backdrop
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
                    height: 20px;
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
                    height: 20px;
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

    def set_node(self, node):
        """Establece el nodo StickyNote para aplicar colores"""
        self.node = node

    def makeUI(self):
        return self

    def updateValue(self):
        pass
