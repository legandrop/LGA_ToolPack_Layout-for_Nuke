"""
LGA_BD_knobs.py - Manejo modular de knobs para LGA_backdrop
"""

import nuke


def create_divider(name=""):
    """Crea un divider (separador visual)"""
    return nuke.Text_Knob(f"divider_{name}", "")


def create_space(name="", text=" "):
    """Crea un espacio en blanco"""
    return nuke.Text_Knob(f"space_{name}", " ", text)


def create_label_knob():
    """Crea el knob de label estilo Nuke nativo (multilinea)"""
    label = nuke.Multiline_Eval_String_Knob("label", "label")
    label.setFlag(nuke.STARTLINE)
    return label


def create_font_size_knob(default_size=42):
    """Crea el knob de font size con slider"""
    size = nuke.Double_Knob("note_font_size", "Font Size")
    size.setRange(10, 100)
    size.setValue(default_size)
    size.setFlag(nuke.NO_ANIMATION)
    return size


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


def create_resize_section():
    """Crea la seccion de resize"""
    knobs = []

    # Botones grow y shrink
    grow = nuke.PyScript_Knob(
        "grow",
        ' <img src="MergeMin.png">',
        """
n = nuke.thisNode()

def grow(node=None, step=50):
    try:
        if not node:
            n = nuke.selectedNode()
        else:
            n = node
            n['xpos'].setValue(n['xpos'].getValue() - step)
            n['ypos'].setValue(n['ypos'].getValue() - step)
            n['bdwidth'].setValue(n['bdwidth'].getValue() + step * 2)
            n['bdheight'].setValue(n['bdheight'].getValue() + step * 2)
    except Exception as e:
        print('Error:: %s' % e)

grow(n, 50)
""",
    )
    grow.setTooltip("Grows the size of the Backdrop by 50pt in every direction")

    shrink = nuke.PyScript_Knob(
        "shrink",
        ' <img src="MergeMax.png">',
        """
n = nuke.thisNode()

def shrink(node=None, step=50):
    try:
        if not node:
            n = nuke.selectedNode()
        else:
            n = node
            n['xpos'].setValue(n['xpos'].getValue() + step)
            n['ypos'].setValue(n['ypos'].getValue() + step)
            n['bdwidth'].setValue(n['bdwidth'].getValue() - step * 2)
            n['bdheight'].setValue(n['bdheight'].getValue() - step * 2)
    except Exception as e:
        print('Error:: %s' % e)

shrink(n, 50)
""",
    )
    shrink.setTooltip("Shrinks the size of the Backdrop by 50pt in every direction")

    # Boton fit
    fit_button = nuke.PyScript_Knob(
        "fit_selected_nodes",
        ' <img src="ContactSheet.png">',
        """
import LGA_BD_fit
LGA_BD_fit.fit_selected_nodes()
""",
    )
    fit_button.setTooltip(
        "Will resize the backdrop to fit every selected nodes plus a padding number"
    )

    # Padding para fit
    fit_padding = nuke.Int_Knob("sides", "")
    fit_padding.setValue(50)  # default value
    fit_padding.clearFlag(nuke.STARTLINE)
    fit_padding.setTooltip(
        "When fitting nodes this number of pt will be added to the Backdrop size in every direction"
    )

    # Configurar para que todos los elementos estén en una sola línea
    shrink.clearFlag(nuke.STARTLINE)
    fit_button.clearFlag(nuke.STARTLINE)
    fit_padding.clearFlag(nuke.STARTLINE)

    knobs.extend(
        [
            grow,
            shrink,
            fit_button,
            fit_padding,
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

    # Configurar flags para que aparezcan en la misma linea
    zorder_label.clearFlag(nuke.STARTLINE)
    zorder_back_label.clearFlag(nuke.STARTLINE)
    zorder.clearFlag(nuke.STARTLINE)
    zorder_front_label.clearFlag(nuke.STARTLINE)
    zorder.setFlag(nuke.NO_ANIMATION)

    knobs.extend([zorder_label, zorder_back_label, zorder, zorder_front_label])

    return knobs


def add_all_knobs(node, user_text=""):
    """Agrega todos los knobs al nodo"""
    # Tab principal
    tab = nuke.Tab_Knob("backdrop")  # Cambiar de 'Settings' a 'backdrop'
    node.addKnob(tab)

    # Label (estilo Nuke nativo)
    label = create_label_knob()
    label.setValue(user_text)
    node.addKnob(label)

    # Font Size
    font_size = create_font_size_knob()
    node.addKnob(font_size)

    # Divider 1
    node.addKnob(create_divider("1"))

    # Seccion de colores
    color_knobs = create_simple_colors_section()
    for knob in color_knobs:
        node.addKnob(knob)

    # Divider 2
    node.addKnob(create_divider("2"))

    # Seccion de resize
    resize_knobs = create_resize_section()
    for knob in resize_knobs:
        node.addKnob(knob)

    # Divider 3 (saltamos la seccion de posiciones)
    node.addKnob(create_divider("3"))

    # Seccion de Z-order
    zorder_knobs = create_zorder_section()
    for knob in zorder_knobs:
        node.addKnob(knob)
