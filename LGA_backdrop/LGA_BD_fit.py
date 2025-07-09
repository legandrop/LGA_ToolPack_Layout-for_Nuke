"""
LGA_BD_fit.py - Funcionalidad de fit para LGA_backdrop
"""

import re
import nuke
from PySide2.QtGui import QFontMetrics, QFont

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def calculate_extra_top(text, font_size):
    """
    Calcula el tamano adicional necesario para el texto en funcion del tamano de la fuente y el numero de lineas.
    """
    line_count = text.count("\n") + 2  # Contar las lineas en el texto
    text_height = font_size * line_count  # Calcular la altura total del texto
    return text_height


def strip_html_tags(text):
    """Elimina las etiquetas HTML del texto."""
    clean_text = re.sub(r"<.*?>", "", text)
    return clean_text


def calculate_min_horizontal(text, font_size):
    """
    Calcula el ancho minimo necesario para el texto en funcion del tamano de la fuente y la linea mas larga,
    teniendo en cuenta el ancho real de cada caracter.
    """
    text = strip_html_tags(text)
    debug_print(f"Texto utilizado para el calculo: {text}")

    # Calcular el ajuste del tamano de la fuente
    adjustment = 0.2 * font_size - 1.5
    adjusted_font_size = font_size - adjustment

    # Crear una fuente con la familia Verdana y el tamano ajustado
    font = QFont("Verdana")
    font.setPointSize(adjusted_font_size)
    metrics = QFontMetrics(font)

    lines = text.split("\n")  # Dividir el texto en lineas
    max_width = max(
        metrics.horizontalAdvance(line) for line in lines
    )  # Encontrar la linea mas ancha
    min_horizontal = (
        max_width  # Calcular el ancho minimo basado en el ancho real del texto
    )

    debug_print(f"Linea mas larga tiene {max_width} pixeles de ancho.")
    debug_print(f"Ancho minimo calculado: {min_horizontal}")
    return min_horizontal


def nodeIsInside(node, backdropNode):
    """
    Retorna True si el nodo esta dentro del backdrop
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


def fit_to_selected_nodes():
    """
    Redimensiona el backdrop para abarcar todos los nodos seleccionados
    """
    this = nuke.thisNode()
    padding = this["margin_slider"].getValue()

    if this.isSelected:
        this.setSelected(False)
    selNodes = nuke.selectedNodes()

    if not selNodes:
        nuke.message("Some nodes should be selected")
        return

    # Obtener el texto y tamano de fuente del backdrop actual
    user_text = this["label"].getValue()
    note_font_size = this["note_font_size"].getValue()

    # Calcular los limites para el nodo de fondo
    bdX = min([node.xpos() for node in selNodes])
    bdY = min([node.ypos() for node in selNodes])
    bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) - bdY

    # Calcular el tamano adicional necesario para el texto
    extra_top = calculate_extra_top(user_text, note_font_size)
    debug_print(f"extra_top fit: {extra_top}")

    # Calcular el ancho minimo necesario para el texto
    min_horizontal = calculate_min_horizontal(user_text, note_font_size)
    debug_print(f"min_horizontal nuevo: {min_horizontal}")

    # Expandir los limites para dejar un pequeno borde
    if padding < extra_top:
        top = -extra_top
    else:
        top = -padding

    debug_print(f"top nuevo fit: {top}")
    bottom = padding
    debug_print(f"bottom nuevo fit: {bottom}")

    # Ajustar los valores de left y right para asegurar el minimo horizontal
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

    zOrder = 0
    selectedBackdropNodes = nuke.selectedNodes("BackdropNode")

    # Si hay nodos de fondo seleccionados, colocar el nuevo inmediatamente detras del mas lejano
    if len(selectedBackdropNodes):
        zOrder = min([node["z_order"].getValue() for node in selectedBackdropNodes]) - 1
    else:
        # De lo contrario encontrar el fondo mas cercano si existe y colocar el nuevo frente a el
        nonSelectedBackdropNodes = nuke.allNodes("BackdropNode")
        for nonBackdrop in selNodes:
            for backdrop in nonSelectedBackdropNodes:
                if nodeIsInside(nonBackdrop, backdrop):
                    zOrder = max(zOrder, backdrop["z_order"].getValue() + 1)

    # Aplicar los nuevos valores al backdrop
    this["xpos"].setValue(bdX)
    this["bdwidth"].setValue(bdW)
    this["ypos"].setValue(bdY)
    this["bdheight"].setValue(bdH)
    this["z_order"].setValue(zOrder)
