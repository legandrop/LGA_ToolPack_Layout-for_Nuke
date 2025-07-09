"""
__________________________________________

  LGA_backdrop v0.12 | Lega Pugliese
  Backdrop personalizado con knobs modulares
__________________________________________

"""

import nuke
import nukescripts
import random
import colorsys
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QFrame
from PySide2.QtGui import QFontMetrics, QFont

# Importar modulos propios
import LGA_BD_knobs
import LGA_BD_callbacks
import LGA_BD_fit


def create_text_dialog():
    """
    Crea el dialogo para pedir el nombre del backdrop
    """
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(
        QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup
    )
    dialog.esc_exit = False  # Variable de instancia para esc_exit

    # Establecer el estilo del dialogo
    dialog.setStyleSheet("QDialog { background-color: #242527; }")

    layout = QtWidgets.QVBoxLayout(dialog)

    title = QtWidgets.QLabel("Backdrop Name")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setStyleSheet(
        "color: #AAAAAA; font-family: Verdana; font-weight: bold; font-size: 10pt;"
    )
    layout.addWidget(title)

    text_edit = QtWidgets.QTextEdit(dialog)
    text_edit.setFixedHeight(70)  # Altura para 4 renglones
    text_edit.setFrameStyle(QFrame.NoFrame)  # Sin marco
    text_edit.setStyleSheet(
        """
        background-color: #262626;
        color: #FFFFFF;
    """
    )
    layout.addWidget(text_edit)

    help_label = QtWidgets.QLabel(
        '<span style="font-size:7pt; color:#AAAAAA;">Ctrl+Enter to confirm</span>',
        dialog,
    )
    help_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(help_label)

    dialog.setLayout(layout)
    dialog.resize(200, 150)

    def event_filter(widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if (
                event.key() == QtCore.Qt.Key_Return
                and event.modifiers() == QtCore.Qt.ControlModifier
            ):
                dialog.accept()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                dialog.esc_exit = True
                dialog.reject()
                return True
        return False

    text_edit.installEventFilter(dialog)
    dialog.eventFilter = event_filter

    text_edit.setFocus()  # Poner el cursor en la caja de texto

    return dialog, text_edit


def show_text_dialog():
    """
    Muestra el dialogo y retorna el resultado
    """
    dialog, text_edit = create_text_dialog()
    cursor_pos = QtGui.QCursor.pos()
    avail_space = QtWidgets.QDesktopWidget().availableGeometry(cursor_pos)
    posx = min(max(cursor_pos.x() - 100, avail_space.left()), avail_space.right() - 200)
    posy = min(max(cursor_pos.y() - 80, avail_space.top()), avail_space.bottom() - 150)
    dialog.move(QtCore.QPoint(posx, posy))

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.esc_exit, text_edit.toPlainText()
    else:
        return dialog.esc_exit, None


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


def autoBackdrop():
    """
    Crea automaticamente un backdrop detras de los nodos seleccionados
    """
    # Obtener el texto del usuario usando el panel personalizado
    esc_exit, user_text = show_text_dialog()
    if esc_exit:
        return  # Si el usuario cancela con ESC, salir de la funcion
    if user_text is None:
        user_text = ""  # Si el usuario cancela, usar una cadena vacia

    selNodes = nuke.selectedNodes()
    forced = False

    # Si no hay nada seleccionado, crear un nodo temporal
    if not selNodes:
        forced = True
        b = nuke.createNode("NoOp")
        selNodes.append(b)

    # Calcular limites para el backdrop
    bdX = min([node.xpos() for node in selNodes])
    bdY = min([node.ypos() for node in selNodes])
    bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) - bdY

    zOrder = 0
    selectedBackdropNodes = nuke.selectedNodes("BackdropNode")

    # Si hay backdrops seleccionados, poner el nuevo inmediatamente detras del mas lejano
    if len(selectedBackdropNodes):
        zOrder = min([node["z_order"].getValue() for node in selectedBackdropNodes]) - 1
    else:
        # Si no hay backdrop en la seleccion, encontrar el backdrop mas cercano
        # si existe y poner el nuevo enfrente de el
        nonSelectedBackdropNodes = nuke.allNodes("BackdropNode")
        for nonBackdrop in selNodes:
            for backdrop in nonSelectedBackdropNodes:
                if nodeIsInside(nonBackdrop, backdrop):
                    zOrder = max(zOrder, backdrop["z_order"].getValue() + 1)

    # Usar las funciones de calculo de tamaño backdrop
    note_font_size = 42  # Default font size

    # Calcular el tamaño adicional necesario para el texto
    extra_top = LGA_BD_fit.calculate_extra_top(user_text, note_font_size)

    # Calcular el ancho minimo necesario para el texto
    min_horizontal = LGA_BD_fit.calculate_min_horizontal(user_text, note_font_size)

    # Expandir los limites para dejar un poco de borde
    margin_value = 50  # Default margin

    if margin_value < extra_top:
        top = -extra_top
    else:
        top = -margin_value

    bottom = margin_value
    left = -1 * margin_value

    # Ajustar para el ancho minimo del texto
    additional_width = max(0, min_horizontal - bdW)
    left_adjustment = additional_width / 2
    right_adjustment = additional_width / 2

    right = margin_value + right_adjustment
    left -= left_adjustment

    bdX += left
    bdY += top
    bdW += right - left
    bdH += bottom - top

    # Crear el backdrop
    n = nuke.nodes.BackdropNode(
        xpos=bdX,
        bdwidth=bdW,
        ypos=bdY,
        bdheight=bdH,
        tile_color=int((random.random() * (16 - 10))) + 10,
        note_font_size=note_font_size,
        z_order=zOrder,
        label=user_text,
    )

    # Agregar todos los knobs personalizados
    LGA_BD_knobs.add_all_knobs(n, user_text, note_font_size)

    # Configurar callbacks
    LGA_BD_callbacks.setup_callbacks(n)

    # Revertir a la seleccion previa
    n["selected"].setValue(False)
    if forced:
        nuke.delete(b)
    else:
        for node in selNodes:
            node["selected"].setValue(True)

    # Seleccionar el backdrop y mostrar sus propiedades
    n.setSelected(True)
    nuke.show(n)

    return n
