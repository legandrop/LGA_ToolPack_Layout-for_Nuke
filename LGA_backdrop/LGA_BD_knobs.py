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
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


class ColorSwatchWidget(QtWidgets.QWidget):
    # Variables controlables para las variaciones de color
    MIN_LIGHTNESS = 0.3  # Luminancia mínima (0.0 = negro, 1.0 = blanco)
    MAX_LIGHTNESS = 0.8  # Luminancia máxima
    MIN_SATURATION = 0.4  # Saturación mínima (0.0 = gris, 1.0 = color puro)
    MAX_SATURATION = 1.0  # Saturación máxima

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
        """Genera 5 variaciones para cada color base"""
        variations = {}

        for color_name, rgb_values in self.color_swatches:
            if color_name == "random":
                continue  # El botón random no necesita variaciones

            if color_name == "gray":
                # Para gris, solo variar el brillo (de negro a blanco)
                gray_variations = []
                for i in range(5):
                    lightness = (
                        self.MIN_LIGHTNESS
                        + (self.MAX_LIGHTNESS - self.MIN_LIGHTNESS) * i / 4
                    )
                    gray_value = int(lightness * 255)
                    gray_variations.append((gray_value, gray_value, gray_value))
                variations[color_name] = gray_variations
            else:
                # Para colores normales, variar luminancia y saturación
                h, l, s = self._rgb_to_hls(*rgb_values)
                color_variations = []

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

                    new_rgb = self._hls_to_rgb(h, new_lightness, new_saturation)
                    color_variations.append(new_rgb)

                variations[color_name] = color_variations

        return variations

    def _get_current_color_info(self):
        """Obtiene información sobre el color actual del backdrop"""
        default_rgb = (58, 58, 58)  # Color por defecto

        if not self.node:
            debug_print(f"[DEBUG] No node available")
            return None, default_rgb, -1

        try:
            current_color_value = self.node["tile_color"].getValue()
            debug_print(f"[DEBUG] Current tile_color value: {current_color_value}")
        except:
            debug_print(f"[DEBUG] Error getting tile_color value")
            return None, default_rgb, -1

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
                debug_print(f"[DEBUG] Converted to RGB: {current_rgb}")
            else:
                current_rgb = default_rgb
                debug_print(f"[DEBUG] Using default RGB (not int): {current_rgb}")

        # Buscar en qué familia de color está y en qué variación
        if hasattr(self, "color_variations") and self.color_variations:
            debug_print(f"[DEBUG] Searching in color variations...")
            for color_name, variations in self.color_variations.items():
                if variations:
                    debug_print(
                        f"[DEBUG] Checking {color_name} with {len(variations)} variations"
                    )
                    for i, rgb in enumerate(variations):
                        if rgb and len(rgb) == 3:
                            debug_print(
                                f"[DEBUG] Comparing current {current_rgb} with {color_name}[{i}] {rgb}"
                            )
                            # Tolerancia para comparación de colores
                            if (
                                abs(current_rgb[0] - rgb[0]) <= 5
                                and abs(current_rgb[1] - rgb[1]) <= 5
                                and abs(current_rgb[2] - rgb[2]) <= 5
                            ):
                                debug_print(
                                    f"[DEBUG] MATCH FOUND: {color_name} variation {i}"
                                )
                                return color_name, current_rgb, i
                        else:
                            debug_print(
                                f"[DEBUG] Invalid RGB in {color_name}[{i}]: {rgb}"
                            )
                else:
                    debug_print(f"[DEBUG] No variations for {color_name}")
        else:
            debug_print(f"[DEBUG] No color_variations available")

        debug_print(f"[DEBUG] No match found for RGB: {current_rgb}")
        return None, current_rgb, -1

    def _create_layout(self):
        color_chooser_layout = QtWidgets.QHBoxLayout()
        color_chooser_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(color_chooser_layout)

        for i, (color_name, rgb_values) in enumerate(self.color_swatches):
            color_knob = QtWidgets.QPushButton()
            color_knob.clicked.connect(self.color_knob_click)
            color_knob.setProperty("color_name", color_name)

            if color_name == "random" and rgb_values == "gradient":
                # Botón especial con gradiente multicolor
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
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        {', '.join(stop_values)});
                    border: none;
                    height: 40px;
                """
                color_knob.setStyleSheet(gradient_css)
                color_knob.setProperty("is_random", True)
            else:
                # Botón de color sólido normal
                color_knob.setToolTip(
                    f"Click to cycle through {color_name} variations!"
                )
                color_knob.setStyleSheet(
                    self.SWATCH_CSS % (rgb_values[0], rgb_values[1], rgb_values[2])
                )
                color_knob.setProperty("is_random", False)

            color_chooser_layout.addWidget(color_knob)
            self._swatch_widgets.append(color_knob)

    def color_knob_click(self):
        widget = self.sender()
        if not widget or not self.node:
            return

        color_name = widget.property("color_name")

        # Verificar si es el botón de random
        if widget.property("is_random"):
            self._apply_random_color()
            return

        # Manejar clicks en botones de color normal
        self._cycle_color_variation(color_name)

    def _cycle_color_variation(self, color_name):
        """Cicla entre las variaciones de un color específico"""
        if (
            not hasattr(self, "color_variations")
            or not self.color_variations
            or color_name not in self.color_variations
        ):
            debug_print(f"[DEBUG] No variations available for {color_name}")
            return

        # Usar tracking interno en lugar de detección de color actual
        if self._last_applied_color == color_name and self._last_applied_index >= 0:
            # Si el último color aplicado es de la misma familia, avanzar al siguiente
            next_index = (self._last_applied_index + 1) % 5  # Loop de 0 a 4
            debug_print(
                f"[DEBUG] Current {color_name} variation: {self._last_applied_index}, next: {next_index}"
            )
        else:
            # Si no es de la misma familia o es la primera vez, empezar desde 0
            next_index = 0
            debug_print(f"[DEBUG] Starting {color_name} variations from index 0")

        # Aplicar la nueva variación
        variations = self.color_variations.get(color_name)
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

                    debug_print(
                        f"[DEBUG] Applied {color_name} variation {next_index}: RGB({r}, {g}, {b}) = {hex_color}"
                    )
                else:
                    debug_print(
                        f"[DEBUG] Error: Invalid node or missing tile_color knob"
                    )
            else:
                debug_print(
                    f"[DEBUG] Error: Invalid RGB values for {color_name} variation {next_index}"
                )
        else:
            debug_print(f"[DEBUG] Error: No valid variations found for {color_name}")

    def _apply_random_color(self):
        """Aplica un color completamente aleatorio"""
        import random

        # Generar valores RGB aleatorios
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)

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

            debug_print(
                f"[DEBUG] Applied random color: RGB({r}, {g}, {b}) = {hex_color}"
            )
        else:
            debug_print(f"[DEBUG] Error: Invalid node or missing tile_color knob")

    def makeUI(self):
        return self

    def updateValue(self):
        pass


# Registrar la clase globalmente para PyCustom_Knob al importar el módulo
nuke.LGA_ColorSwatchWidget = ColorSwatchWidget


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

    # Label para Auto Fit
    autofit_label = nuke.Text_Knob("autofit_label", "", "     Auto Fit  ")

    # Boton Auto Fit
    fit_button = nuke.PyScript_Knob(
        "fit_to_selected_nodes",
        f' <img src="{icon_path}" width="20" height="20">',
        """
import LGA_BD_fit
LGA_BD_fit.fit_to_selected_nodes()
""",
    )
    fit_button.setTooltip(
        "Resize the backdrop to fit every included nodes using a margin number"
    )

    # Espacio después del botón de fit
    fit_space = nuke.Text_Knob("fit_space", "", " ")

    # Configurar para que todos los elementos estén en una sola línea
    resize_label.clearFlag(nuke.STARTLINE)
    margin_label.clearFlag(nuke.STARTLINE)
    margin_slider.clearFlag(nuke.STARTLINE)
    autofit_label.clearFlag(nuke.STARTLINE)
    fit_button.clearFlag(nuke.STARTLINE)
    fit_space.clearFlag(nuke.STARTLINE)

    knobs.extend(
        [
            resize_label,
            margin_label,
            margin_slider,
            autofit_label,
            fit_button,
            fit_space,
        ]
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
    zorder_space = nuke.Text_Knob("zorder_space", "", "  ")

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


def add_all_knobs(node, text_label="", existing_margin_alignment="left"):
    """Agrega todos los knobs personalizados al BackdropNode pero solo si no existen"""
    debug_print(f"[DEBUG] Adding knobs to node: {node.name()}")

    # Verificar si ya tiene el tab Backdrop y los knobs principales
    if "backdrop" in node.knobs() and "label_link" in node.knobs():
        debug_print(f"[DEBUG] Knobs already exist, skipping recreation")
        return

    # Crear tab backdrop solo si no existe
    if "backdrop" not in node.knobs():
        backdrop_tab = nuke.Tab_Knob("backdrop")
        node.addKnob(backdrop_tab)
        debug_print(f"[DEBUG] Created backdrop tab")

    # Crear link al label nativo solo si no existe (como en el ejemplo)
    if "label_link" not in node.knobs():
        label_link = nuke.Link_Knob("label_link", "Label")
        label_link.makeLink(node.name(), "label")
        node.addKnob(label_link)
        debug_print(f"[DEBUG] Created label_link to native label")

        # Si tenemos texto para asignar, hacerlo al label nativo
        if text_label:
            node["label"].setValue(text_label)

    # Crear font size slider solo si no existe (USAR LA FUNCIÓN ORIGINAL)
    if "lga_note_font_size" not in node.knobs():
        lga_font_size_knob = create_font_size_knob(42)  # usar la función original
        lga_font_size_knob.setFlag(nuke.STARTLINE | nuke.NO_ANIMATION)
        node.addKnob(lga_font_size_knob)
        debug_print(f"[DEBUG] Created font size slider")

    # Crear link de font bold/italic solo si no existe (SIN LABEL)
    if "note_font_link" not in node.knobs():
        font_link = nuke.Link_Knob("note_font_link", "")  # Sin label
        font_link.clearFlag(nuke.STARTLINE)  # En la misma línea que font size
        node.addKnob(font_link)
        font_link.makeLink(node.name(), "note_font")
        debug_print(f"[DEBUG] Created and configured note_font_link")

    # Crear margin dropdown solo si no existe (SIN LABEL)
    if "lga_margin" not in node.knobs():
        margin_dropdown = nuke.Enumeration_Knob(
            "lga_margin", "", ["left", "center", "right"]
        )
        margin_dropdown.setValue(existing_margin_alignment)
        margin_dropdown.clearFlag(nuke.STARTLINE)  # En la misma línea
        node.addKnob(margin_dropdown)
        debug_print(f"[DEBUG] Created margin dropdown")

    # Agregar el resto de los knobs usando las funciones existentes si no existen
    add_remaining_knobs_if_missing(node, existing_margin_alignment)

    debug_print(f"[DEBUG] Finished adding all knobs")


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


def add_knobs_to_existing_backdrops():
    """
    Busca BackdropNodes existentes en el script actual y les agrega/actualiza knobs personalizados.
    Se ejecuta cuando se carga un script.
    """
    debug_print(f"[DEBUG] add_knobs_to_existing_backdrops called - onScriptLoad")

    # Buscar todos los BackdropNodes en el script actual
    backdrop_nodes = [
        node for node in nuke.allNodes() if node.Class() == "BackdropNode"
    ]

    if not backdrop_nodes:
        debug_print(f"[DEBUG] Found 0 BackdropNode(s)")
        debug_print(f"[DEBUG] add_knobs_to_existing_backdrops completed")
        return

    debug_print(f"[DEBUG] Found {len(backdrop_nodes)} BackdropNode(s)")

    for node in backdrop_nodes:
        debug_print(f"[DEBUG] Processing node: {node.name()}")

        # Obtener el valor del label nativo para preservarlo
        existing_label_value = node["label"].getValue()
        debug_print(f"[DEBUG] Using label value: '{existing_label_value}'")

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

        debug_print(f"[DEBUG] Clean text: '{clean_text}'")

        # Llamar a add_all_knobs con el texto limpio
        add_all_knobs(node, clean_text, existing_margin_alignment)

        debug_print(f"[DEBUG] Finished processing node: {node.name()}")

    debug_print(f"[DEBUG] add_knobs_to_existing_backdrops completed")
