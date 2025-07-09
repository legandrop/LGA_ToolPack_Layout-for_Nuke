"""
LGA_BD_knobs.py - Manejo modular de knobs para LGA_backdrop
"""

import nuke
import os

# Variable global para activar o desactivar los prints
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


def create_divider(name=""):
    """Crea un divider (separador visual)"""
    return nuke.Text_Knob(f"divider_{name}", "")


def create_space(name="", text=" "):
    """Crea un espacio en blanco"""
    return nuke.Text_Knob(f"space_{name}", " ", text)


def create_label_knob():
    """Crea el knob de label estilo Nuke nativo (multilinea)"""
    # Renombrar para evitar conflicto con el knob 'label' nativo del BackdropNode
    label = nuke.Multiline_Eval_String_Knob("lga_label", "Label")
    label.setFlag(nuke.STARTLINE)
    # Aplicar la bandera RESIZABLE para mantener altura multilinea
    # Segun documentacion oficial: "Allows some knobs (notably curves and multi-line string)
    # to expand to fill the gaps in the interface"
    try:
        label.setFlag(0x0008)  # RESIZABLE flag value segun documentacion NDK
    except:
        # Fallback si la bandera no esta disponible en esta version
        pass
    return label


def create_font_size_knob(default_size=42):
    """Crea el knob de font size con slider"""
    # Renombrar para evitar conflicto con el knob 'note_font_size' nativo del BackdropNode
    size = nuke.Double_Knob("lga_note_font_size", "Font Size")
    size.setRange(10, 100)
    size.setValue(default_size)
    size.setFlag(nuke.NO_ANIMATION)
    return size


def create_font_bold_section(bold_value=False):
    """Crea la seccion de font bold"""
    knobs = []

    # Label para Bold
    bold_label = nuke.Text_Knob("bold_label", "", "      Bold  ")

    # Checkbox para bold
    bold_checkbox = nuke.Boolean_Knob("lga_bold", "")
    bold_checkbox.setValue(bold_value)
    bold_checkbox.setTooltip("Make text bold")

    # Configurar para que aparezcan en la misma línea
    bold_label.clearFlag(nuke.STARTLINE)
    bold_checkbox.clearFlag(nuke.STARTLINE)

    knobs.extend([bold_label, bold_checkbox])

    return knobs


def create_simple_colors_section():
    """Crea una seccion simple de colores"""
    # Boton de color aleatorio
    random_color = nuke.PyScript_Knob(
        "random_color",
        "Random Color",
        """
import random
node = nuke.thisNode()
# Generar color aleatorio en el rango que usa Nuke
random_color = int((random.random() * (16 - 10))) + 10
node['tile_color'].setValue(random_color)
""",
    )

    # Colores basicos predefinidos
    colors = [
        ("Red", 0xFF0000FF),
        ("Green", 0x00FF00FF),
        ("Blue", 0x0000FFFF),
        ("Yellow", 0xFFFF00FF),
        ("Cyan", 0x00FFFFFF),
        ("Magenta", 0xFF00FFFF),
        ("Orange", 0xFF8000FF),
        ("Purple", 0x8000FFFF),
    ]

    color_knobs = []
    color_knobs.append(random_color)
    color_knobs.append(create_space("color_space1"))

    for i, (name, color_value) in enumerate(colors):
        color_knob = nuke.PyScript_Knob(
            f"color_{name.lower()}",
            name,
            f"""
node = nuke.thisNode()
node['tile_color'].setValue({color_value})
""",
        )
        color_knobs.append(color_knob)

        # Agregar salto de linea cada 4 colores
        if (i + 1) % 4 == 0:
            color_knobs.append(create_space(f"color_newline_{i}"))

    return color_knobs


def create_resize_section(margin_value=50):
    """Crea la seccion de resize"""
    knobs = []

    # Construir la ruta absoluta al icono
    icon_path = os.path.join(os.path.dirname(__file__), "icons", "lga_bd_fit.png")

    # Label para Margin
    margin_label = nuke.Text_Knob("margin_label", "", "Margin      ")

    # Slider para margin
    margin_slider = nuke.Double_Knob("margin_slider", "")
    margin_slider.setRange(10, 200)
    margin_slider.setValue(margin_value)  # usar el valor pasado como parámetro
    margin_slider.setFlag(nuke.NO_ANIMATION)
    margin_slider.setTooltip("Margin slider for auto fit")

    # Label para Auto Fit
    autofit_label = nuke.Text_Knob("autofit_label", "", "          Auto Fit  ")

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
        "Will resize the backdrop to fit every selected nodes plus a padding number"
    )

    # Espacio después del botón de fit
    fit_space = nuke.Text_Knob("fit_space", "", "   ")

    # Configurar para que todos los elementos estén en una sola línea
    margin_label.clearFlag(nuke.STARTLINE)
    margin_slider.clearFlag(nuke.STARTLINE)
    autofit_label.clearFlag(nuke.STARTLINE)
    fit_button.clearFlag(nuke.STARTLINE)
    fit_space.clearFlag(nuke.STARTLINE)

    knobs.extend(
        [
            margin_label,
            margin_slider,
            autofit_label,
            fit_button,
            fit_space,
        ]
    )

    return knobs


def create_zorder_section():
    """Crea la seccion de Z-order"""
    knobs = []

    # Labels y slider de Z-order
    zorder_label = nuke.Text_Knob("z_order_label", "", "Z Order     ")
    zorder_back_label = nuke.Text_Knob("zorder_back", "", "Back ")
    zorder = nuke.Double_Knob("zorder", "")
    zorder.setRange(-5, +5)
    zorder_front_label = nuke.Text_Knob("zorder_front", "", " Front")

    # Espacio después del label Front
    zorder_space = nuke.Text_Knob("zorder_space", "", "   ")

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


def add_all_knobs(node, user_text="", note_font_size=None):
    """Agrega todos los knobs al nodo"""
    # Obtener el valor actual del font size si no se proporciona
    if note_font_size is None:
        note_font_size = node["note_font_size"].getValue()

    # Obtener valores existentes para preservarlos
    existing_margin_value = 50  # default
    if "margin_slider" in node.knobs():
        existing_margin_value = node["margin_slider"].getValue()

    existing_bold_value = False  # default
    if "lga_bold" in node.knobs():
        existing_bold_value = node["lga_bold"].getValue()
    else:
        # Si no existe el knob, detectar bold del texto original
        original_text = node["label"].getValue()
        existing_bold_value = original_text.startswith(
            "<b>"
        ) and original_text.endswith("</b>")

    # Verificar si ya existen knobs personalizados
    has_custom_knobs = "backdrop" in node.knobs()

    if has_custom_knobs:
        # Verificar si el lga_label existente ya tiene la bandera RESIZABLE
        if "lga_label" in node.knobs():
            lga_label_knob = node["lga_label"]
            # Verificar si ya tiene la bandera RESIZABLE (0x0008)
            has_resizable_flag = lga_label_knob.getFlag(0x0008)
            debug_print(
                f"[DEBUG] lga_label exists, has RESIZABLE flag: {has_resizable_flag}"
            )

            if has_resizable_flag:
                debug_print(
                    f"[DEBUG] lga_label already has RESIZABLE flag, no recreation needed"
                )
                return  # No necesitamos recrear nada

        debug_print(
            f"[DEBUG] Custom knobs exist, recreating knobs content (keeping existing tab)"
        )
        # Si ya existen knobs personalizados, eliminar solo los knobs DENTRO del tab
        # MANTENER el tab backdrop existente

        # Lista de knobs personalizados que necesitamos eliminar (SIN el tab backdrop)
        custom_knob_names = [
            "lga_label",
            "lga_note_font_size",
            "bold_label",
            "lga_bold",
            "divider_1",
            "random_color",
            "space_color_space1",
            "color_red",
            "color_green",
            "color_blue",
            "color_yellow",
            "space_color_newline_3",
            "color_cyan",
            "color_magenta",
            "color_orange",
            "color_purple",
            "space_color_newline_7",
            "divider_2",
            "margin_label",
            "margin_slider",
            "autofit_label",
            "fit_to_selected_nodes",
            "fit_space",
            "divider_3",
            "z_order_label",
            "zorder_back",
            "zorder",
            "zorder_front",
            "zorder_space",
        ]

        # Eliminar todos los knobs personalizados existentes (EXCEPTO el tab)
        for knob_name in custom_knob_names:
            if knob_name in node.knobs():
                try:
                    node.removeKnob(node[knob_name])
                    debug_print(f"[DEBUG] Removed knob: {knob_name}")
                except:
                    debug_print(f"[DEBUG] Could not remove knob: {knob_name}")

        debug_print(f"[DEBUG] Creating knobs content inside existing backdrop tab")
    else:
        # Crear todos los knobs desde cero - primera vez
        debug_print(f"[DEBUG] Creating all knobs from scratch for node: {node.name()}")

        # Tab principal - solo si no existe
        tab = nuke.Tab_Knob("backdrop")
        node.addKnob(tab)

    # Crear el contenido del tab (sea primera vez o recreando)
    # Label (estilo Nuke nativo) - PRIMERO DE TODO
    lga_label_knob = create_label_knob()
    lga_label_knob.setValue(user_text)
    node.addKnob(lga_label_knob)
    debug_print(f"[DEBUG] Added lga_label knob with RESIZABLE flag")

    # Font Size
    lga_font_size_knob = create_font_size_knob(default_size=note_font_size)
    node.addKnob(lga_font_size_knob)

    # Seccion de Bold
    bold_knobs = create_font_bold_section(existing_bold_value)
    for knob in bold_knobs:
        node.addKnob(knob)

    # Divider 1
    node.addKnob(create_divider("1"))

    # Seccion de colores
    color_knobs = create_simple_colors_section()
    for knob in color_knobs:
        node.addKnob(knob)

    # Divider 2
    node.addKnob(create_divider("2"))

    # Seccion de resize
    resize_knobs = create_resize_section(existing_margin_value)
    for knob in resize_knobs:
        node.addKnob(knob)

    # Divider 3
    node.addKnob(create_divider("3"))

    # Seccion de Z-order
    zorder_knobs = create_zorder_section()
    for knob in zorder_knobs:
        node.addKnob(knob)

    debug_print(f"[DEBUG] Finished creating all knobs in correct order")
    debug_print(f"[DEBUG] Bold checkbox value set to: {existing_bold_value}")
