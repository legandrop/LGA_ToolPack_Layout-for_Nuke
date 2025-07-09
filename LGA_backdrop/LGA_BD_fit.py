"""
LGA_BD_fit.py - Funcionalidad de fit para LGA_backdrop
"""

import re
import nuke
from PySide2.QtGui import QFontMetrics, QFont

# Variable global para activar o desactivar los prints
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


def find_nodes_inside_backdrop(backdrop):
    """
    Encuentra eficientemente todos los nodos (incluidos backdrops) que están dentro de un backdrop dado.
    Esta implementación optimizada evita iterar innecesariamente por todos los nodos del script.
    """
    debug_print(
        f"[DEBUG] find_nodes_inside_backdrop - Buscando nodos dentro del backdrop: {backdrop.name()}"
    )

    # Obtener límites del backdrop
    backdrop_left = backdrop.xpos()
    backdrop_top = backdrop.ypos()
    backdrop_right = backdrop_left + backdrop.screenWidth()
    backdrop_bottom = backdrop_top + backdrop.screenHeight()

    debug_print(
        f"[DEBUG] Backdrop bounds: left={backdrop_left}, top={backdrop_top}, right={backdrop_right}, bottom={backdrop_bottom}"
    )

    nodes_inside = []

    # Usar nuke.allNodes() que es la forma más eficiente en Nuke
    # Esta función está optimizada internamente y es preferible a métodos de filtrado manual
    all_nodes = nuke.allNodes()
    debug_print(f"[DEBUG] Total nodos en el script: {len(all_nodes)}")

    for node in all_nodes:
        # Excluir el backdrop mismo y nodos Root
        if node == backdrop or node.Class() == "Root":
            continue

        # Obtener límites del nodo
        node_left = node.xpos()
        node_top = node.ypos()
        node_right = node_left + node.screenWidth()
        node_bottom = node_top + node.screenHeight()

        # Verificar si el nodo está completamente dentro del backdrop
        if (
            node_left >= backdrop_left
            and node_top >= backdrop_top
            and node_right <= backdrop_right
            and node_bottom <= backdrop_bottom
        ):

            nodes_inside.append(node)
            debug_print(
                f"[DEBUG] Nodo dentro del backdrop: {node.name()} ({node.Class()})"
            )

    debug_print(
        f"[DEBUG] Total nodos encontrados dentro del backdrop: {len(nodes_inside)}"
    )
    return nodes_inside


def get_nodes_efficiently(filter_class=None):
    """
    Método optimizado para obtener nodos usando la API nativa de Nuke.
    Usa nuke.allNodes() con filtro de clase que está optimizado internamente.
    """
    if filter_class:
        return nuke.allNodes(filter_class)
    else:
        return nuke.allNodes()


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
    Redimensiona el backdrop para abarcar todos los nodos seleccionados.
    Si no hay nodos seleccionados, busca automáticamente todos los nodos dentro del backdrop.
    """
    this = nuke.thisNode()
    padding = this["margin_slider"].getValue()

    if this.isSelected:
        this.setSelected(False)

    selNodes = nuke.selectedNodes()
    debug_print(f"[DEBUG] Nodos inicialmente seleccionados: {len(selNodes)}")

    # NUEVA FUNCIONALIDAD: Si no hay nodos seleccionados, buscar nodos dentro del backdrop
    if not selNodes:
        debug_print(
            f"[DEBUG] No hay nodos seleccionados, buscando nodos dentro del backdrop"
        )
        selNodes = find_nodes_inside_backdrop(this)

        if not selNodes:
            nuke.message("No hay nodos dentro del backdrop para hacer autofit")
            return

        debug_print(
            f"[DEBUG] Encontrados {len(selNodes)} nodos dentro del backdrop para autofit"
        )

        # Mostrar qué nodos se encontraron
        node_names = [f"{node.name()} ({node.Class()})" for node in selNodes]
        debug_print(
            f"[DEBUG] Nodos que se usarán para autofit: {', '.join(node_names)}"
        )

    # Obtener el texto y tamano de fuente del backdrop actual
    user_text = this["label"].getValue()
    note_font_size = this["note_font_size"].getValue()

    # Calcular los limites para el nodo de fondo
    bdX = min([node.xpos() for node in selNodes])
    bdY = min([node.ypos() for node in selNodes])
    bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) - bdY

    debug_print(f"[DEBUG] Límites calculados: X={bdX}, Y={bdY}, W={bdW}, H={bdH}")

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

    # COMENTADO: Cálculo automático de Z-Order (causa problema de cambio no deseado)
    # zOrder = 0
    # selectedBackdropNodes = nuke.selectedNodes("BackdropNode")

    # # Si hay nodos de fondo seleccionados, colocar el nuevo inmediatamente detras del mas lejano
    # if len(selectedBackdropNodes):
    #     zOrder = min([node["z_order"].getValue() for node in selectedBackdropNodes]) - 1
    # else:
    #     # De lo contrario encontrar el fondo mas cercano si existe y colocar el nuevo frente a el
    #     nonSelectedBackdropNodes = nuke.allNodes("BackdropNode")
    #     for nonBackdrop in selNodes:
    #         for backdrop in nonSelectedBackdropNodes:
    #             if nodeIsInside(nonBackdrop, backdrop):
    #                 zOrder = max(zOrder, backdrop["z_order"].getValue() + 1)

    # Aplicar los nuevos valores al backdrop (SIN modificar Z-order)
    this["xpos"].setValue(bdX)
    this["bdwidth"].setValue(bdW)
    this["ypos"].setValue(bdY)
    this["bdheight"].setValue(bdH)
    # COMENTADO: No modificar Z-order al hacer autofit manual
    # this["z_order"].setValue(zOrder)

    # COMENTADO: No sincronizar slider zorder (causa cambio no deseado del valor)
    # # IMPORTANTE: Sincronizar el slider zorder con el valor del z_order nativo
    # if "zorder" in this.knobs():
    #     this["zorder"].setValue(zOrder)
    #     debug_print(
    #         f"[DEBUG] Sincronizado slider zorder con z_order en autofit: {zOrder}"
    #     )

    debug_print(
        f"[DEBUG] Autofit aplicado SIN modificar Z-order: X={bdX}, Y={bdY}, W={bdW}, H={bdH}"
    )
    debug_print(f"[DEBUG] Z-order preservado (no modificado por autofit)")
