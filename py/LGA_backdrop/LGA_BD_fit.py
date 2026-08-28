"""
LGA_BD_fit.py - Funcionalidad de fit para LGA_backdrop

v1.02
- El aviso de autofit sin nodos sale por el helper de carteles del pack,
  con fallback a nuke.message si el helper no esta.

v1.01 | 2026-07-09
- Agrega modo silencioso para autofit automatico desde el callback runtime.
- Usa el adapter Qt para medir texto de forma compatible con Nuke 15/16.
"""

import re

import nuke
from LGA_QtAdapter_ToolPack_Layout import QtGui, horizontal_advance

# Carteles con el estilo del pack; si el helper no esta, cae al nuke.message pelado.
try:
    from LGA_UI_MessageBox_ToolPack_Layout import show_info
except ImportError:

    def show_info(parent, title, text):
        nuke.message(text)

DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def find_nodes_inside_backdrop(backdrop):
    """
    Encuentra todos los nodos que estan completamente dentro de un backdrop.
    """
    debug_print(
        f"find_nodes_inside_backdrop - Buscando nodos dentro del backdrop: {backdrop.name()}"
    )

    backdrop_left = backdrop.xpos()
    backdrop_top = backdrop.ypos()
    backdrop_right = backdrop_left + backdrop.screenWidth()
    backdrop_bottom = backdrop_top + backdrop.screenHeight()

    debug_print(
        f"Backdrop bounds: left={backdrop_left}, top={backdrop_top}, right={backdrop_right}, bottom={backdrop_bottom}"
    )

    nodes_inside = []
    all_nodes = nuke.allNodes()
    debug_print(f"Total nodos en el script: {len(all_nodes)}")

    for node in all_nodes:
        if node == backdrop or node.Class() == "Root":
            continue

        node_left = node.xpos()
        node_top = node.ypos()
        node_right = node_left + node.screenWidth()
        node_bottom = node_top + node.screenHeight()

        if (
            node_left >= backdrop_left
            and node_top >= backdrop_top
            and node_right <= backdrop_right
            and node_bottom <= backdrop_bottom
        ):
            nodes_inside.append(node)
            debug_print(f"Nodo dentro del backdrop: {node.name()} ({node.Class()})")

    debug_print(f"Total nodos encontrados dentro del backdrop: {len(nodes_inside)}")
    return nodes_inside


def get_nodes_efficiently(filter_class=None):
    """
    Obtiene nodos usando la API nativa de Nuke.
    """
    if filter_class:
        return nuke.allNodes(filter_class)
    return nuke.allNodes()


def calculate_extra_top(text, font_size):
    """
    Calcula altura adicional para el texto segun font size y cantidad de lineas.
    """
    line_count = text.count("\n") + 2
    return font_size * line_count


def strip_html_tags(text):
    """Elimina etiquetas HTML del texto."""
    return re.sub(r"<.*?>", "", text)


def calculate_min_horizontal(text, font_size):
    """
    Calcula el ancho minimo necesario para la linea mas larga del texto.
    """
    text = strip_html_tags(text)
    debug_print(f"Texto utilizado para el calculo: {text}")

    adjustment = 0.2 * font_size - 1.5
    adjusted_font_size = font_size - adjustment

    font = QtGui.QFont("Verdana")
    if hasattr(font, "setPointSizeF"):
        font.setPointSizeF(float(adjusted_font_size))
    else:
        font.setPointSize(int(round(adjusted_font_size)))
    metrics = QtGui.QFontMetrics(font)

    lines = text.split("\n")
    max_width = max(horizontal_advance(metrics, line) for line in lines)

    debug_print(f"Linea mas larga tiene {max_width} pixeles de ancho.")
    debug_print(f"Ancho minimo calculado: {max_width}")
    return max_width


def nodeIsInside(node, backdropNode):
    """
    Retorna True si el nodo esta dentro del backdrop.
    """
    topLeftNode = [node.xpos(), node.ypos()]
    topLeftBackDrop = [backdropNode.xpos(), backdropNode.ypos()]
    bottomRightNode = [
        node.xpos() + node.screenWidth(),
        node.ypos() + node.screenHeight(),
    ]
    bottomRightBackdrop = [
        backdropNode.xpos() + backdropNode.screenWidth(),
        backdropNode.ypos() + backdropNode.screenHeight(),
    ]

    topLeft = (topLeftNode[0] >= topLeftBackDrop[0]) and (
        topLeftNode[1] >= topLeftBackDrop[1]
    )
    bottomRight = (bottomRightNode[0] <= bottomRightBackdrop[0]) and (
        bottomRightNode[1] <= bottomRightBackdrop[1]
    )

    return topLeft and bottomRight


def _is_node_selected(node):
    try:
        return bool(node["selected"].value())
    except Exception:
        try:
            return bool(node.isSelected())
        except Exception:
            return False


def fit_to_selected_nodes(backdrop_node=None, show_message=True):
    """
    Redimensiona el backdrop para abarcar nodos seleccionados.
    Si no hay seleccion, busca todos los nodos dentro del backdrop.

    Args:
        backdrop_node: Node opcional. Si no se proporciona, usa nuke.thisNode().
        show_message: Si es False, no muestra popup cuando no hay nodos para ajustar.
    """
    this = backdrop_node if backdrop_node else nuke.thisNode()
    padding = this["margin_slider"].getValue()

    if _is_node_selected(this):
        this.setSelected(False)

    selNodes = nuke.selectedNodes()
    debug_print(f"Nodos inicialmente seleccionados: {len(selNodes)}")

    if not selNodes:
        debug_print("No hay nodos seleccionados, buscando nodos dentro del backdrop")
        selNodes = find_nodes_inside_backdrop(this)

        if not selNodes:
            if show_message:
                show_info(
                    None,
                    "LGA Backdrop",
                    "No hay nodos dentro del backdrop para hacer autofit",
                )
            return

        debug_print(
            f"Encontrados {len(selNodes)} nodos dentro del backdrop para autofit"
        )
        node_names = [f"{node.name()} ({node.Class()})" for node in selNodes]
        debug_print(f"Nodos que se usaran para autofit: {', '.join(node_names)}")

    user_text = this["label"].getValue()
    note_font_size = this["note_font_size"].getValue()

    bdX = min([node.xpos() for node in selNodes])
    bdY = min([node.ypos() for node in selNodes])
    bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) - bdY

    debug_print(f"Limites calculados: X={bdX}, Y={bdY}, W={bdW}, H={bdH}")

    extra_top = calculate_extra_top(user_text, note_font_size)
    debug_print(f"extra_top fit: {extra_top}")

    min_horizontal = calculate_min_horizontal(user_text, note_font_size)
    debug_print(f"min_horizontal nuevo: {min_horizontal}")

    if padding < extra_top:
        top = -extra_top
    else:
        top = -padding

    debug_print(f"top nuevo fit: {top}")
    bottom = padding
    debug_print(f"bottom nuevo fit: {bottom}")

    left = -1 * padding
    debug_print(f"left nuevo: {left}")
    additional_width = max(0, min_horizontal - bdW)
    left_adjustment = additional_width / 2
    right_adjustment = additional_width / 2

    right = padding + right_adjustment
    debug_print(f"right nuevo: {right}")
    left -= left_adjustment
    debug_print(f"left ajustado: {left}")

    bdX += left
    bdY += top
    bdW += right - left
    bdH += bottom - top

    # Aplicar nuevos valores sin modificar Z-order.
    this["xpos"].setValue(bdX)
    this["bdwidth"].setValue(bdW)
    this["ypos"].setValue(bdY)
    this["bdheight"].setValue(bdH)

    debug_print(
        f"Autofit aplicado SIN modificar Z-order: X={bdX}, Y={bdY}, W={bdW}, H={bdH}"
    )
    debug_print("Z-order preservado (no modificado por autofit)")
