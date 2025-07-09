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
    SWATCH_TOTAL = 8
    SWATCH_CSS = "background-color: rgb(%03d,%03d,%03d); border: none; height: 40px;"
    SWATCH_COLOR = (58, 58, 58)

    def __init__(self, node=None):
        super(ColorSwatchWidget, self).__init__()
        self.node = node
        self._swatch_widgets = []

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
        ]

        self._create_layout()

    def _create_layout(self):
        color_chooser_layout = QtWidgets.QHBoxLayout()
        color_chooser_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(color_chooser_layout)

        for i, (color_name, rgb_values) in enumerate(self.color_swatches):
            color_knob = QtWidgets.QPushButton()
            color_knob.clicked.connect(self.color_knob_click)

            if color_name == "random" and rgb_values == "gradient":
                # Botón especial con gradiente multicolor
                color_knob.setToolTip("Click to Apply Random Color!")
                gradient_css = """
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 rgb(255, 0, 0),
                        stop: 0.16 rgb(255, 127, 0),
                        stop: 0.33 rgb(255, 255, 0),
                        stop: 0.5 rgb(0, 255, 0),
                        stop: 0.66 rgb(0, 0, 255),
                        stop: 0.83 rgb(139, 0, 255),
                        stop: 1 rgb(255, 0, 255));
                    border: none;
                    height: 40px;
                """
                color_knob.setStyleSheet(gradient_css)
                color_knob.setProperty("is_random", True)
            else:
                # Botón de color sólido normal
                color_knob.setToolTip("Click to Select This Color!")
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

        # Verificar si es el botón de random
        if widget.property("is_random"):
            import random

            random_color = int((random.random() * (16 - 10))) + 10
            self.node["tile_color"].setValue(random_color)
            return

        # Botón de color normal
        color_stylesheet = widget.styleSheet()

        import re

        matches = re.findall("[(](?:\d{1,3}[,\)]){3}", color_stylesheet)
        if matches:
            color_value = matches[0][1:-1].split(",")
            color_value.append("255")

            rgb_color = tuple(map(int, color_value))
            hex_color = int("%02x%02x%02x%02x" % rgb_color, 16)

            self.node["tile_color"].setValue(hex_color)

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
