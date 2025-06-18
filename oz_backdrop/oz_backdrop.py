'''
I reused the script from Franklin VFX Co.
with mods I had from a previus tools I made.

update Lega mod v1.63   - Text input box that asks for the backdrop name at the moment of creation 
                          (most of the code of the pop-up window was taken from ku-labeler by Tianlun Jian & Erwan Leroy)
                        - Backdrop size calculation now considers the width and height of the backdrop name based on the font size, both when creating the node and when executing the encompass button.
                        - Bold text option visible in the main tab and Nuke's system settings.  
                        - Added button to toggle black & white text color in the main tab.
                        - Added buttons to copy and paste the colors, width, and height of one backdrop to another.
                        - Removed animation buttons from some knobs
                        - Updated the Z-order slider, including "back" and "front" labels in the interface for better clarity.
                        - Added a new script to replace backdrops in an external .py file, with all essential modifications included.
                        - Se puede abrir sin mostrar en el properties panel


update 1.3 - April 2023 - Added back the original colors with the 3 click shades.
                        - Now colors can be added easily with a dictionary in it's own file.

update 1.2 - April 2023 : Edited by Hossein Karamian (hkaramian.com | kmworks.call@gmail.com)
                       - Made script compatible with Nuke 12,13,14
                       - replace icons by nuke default icons. (so in a script including oz_backdrops, backdrops will perfectly shown even when oz_backdrops isn't installed)
                       - replace color icons by html/css code
                       - Add setting panel to nuke preferences, so users can set default values for new backdrops. (color,text alignment, text size, appearance, inner margin)

update 1.1 - June 2020 - Added Position knobs
                       - Split secondary code into other files
                       - Added replace old backdrops
                       - Appearance and border width from Nuke12.1
update 1.0 - 2019 -Initial Relase

oz@Garius.io
'''

import nuke, random, nukescripts, colorsys, os
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QFrame
from PySide2.QtGui import QFontMetrics, QFont




from oz_colors import colors
try:
    import oz_settings
except:
    print("Failed to find oz_settings.py, was oz_backdrop installed correctly?")

# Variable global para activar o desactivar los prints
DEBUG = False
def debug_print(*message):
    if DEBUG:
        print(*message)


# IMPORT OTHER SCRIPTS AS VARIABLES
# These are to avoid the background node from not working when loaded on a Nuke
# that doesn't have the scripts saved. Basically each created node is trying to
# be it's own little world.
file_KCS = open(os.path.join(os.path.dirname(__file__),"oz_knobChangedScript.py"), 'r')
knobChangedScript = file_KCS.read()
file_KCS.close()

file_RCS = open(os.path.join(os.path.dirname(__file__),"oz_randomColorScript.py"), 'r')
randomColorScript = file_RCS.read()
file_RCS.close()

file_ES = open(os.path.join(os.path.dirname(__file__),"oz_encompassScript.py"), 'r')
encompassScript = file_ES.read()
file_ES.close()

esc_exit = False  # Variable global para verificar si se presiono ESC


# FUNCTIONS
# These are only used on node creation.
# They don't need to travel with the nodes.
def nodeIsInside(node, backdropNode):
    '''
    Returns true if node geometry is inside backdropNode
    otherwise returns false
    '''
    topLeftNode = [node.xpos(), node.ypos()]
    topLeftBackDrop = [backdropNode.xpos(), backdropNode.ypos()]
    bottomRightNode = [node.xpos() + node.screenWidth(),
                       node.ypos() + node.screenHeight()]
    bottomRightBackdrop = [backdropNode.xpos() + backdropNode.screenWidth(),
                           backdropNode.ypos() + backdropNode.screenHeight()]

    topLeft = ((topLeftNode[0] >= topLeftBackDrop[0]) and
               (topLeftNode[1] >= topLeftBackDrop[1]))
    bottomRight = ((bottomRightNode[0] <= bottomRightBackdrop[0]) and
                   (bottomRightNode[1] <= bottomRightBackdrop[1]))

    return topLeft and bottomRight

def hsv_to_hex(hsv):
    """ converts hsv values given as a list to a hex string """
    rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    return hex_color

def create_text_dialog():
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
    dialog.esc_exit = False  # Anadir una variable de instancia para esc_exit

    # Establecer el estilo del dialogo directamente
    dialog.setStyleSheet("QDialog { background-color: #242527; }")  # Color de fondo de la ventana

    layout = QtWidgets.QVBoxLayout(dialog)

    title = QtWidgets.QLabel("Backdrop Name")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setStyleSheet("color: #AAAAAA; font-family: Verdana; font-weight: bold; font-size: 10pt;")  # Ajustar el tamano de la fuente
    layout.addWidget(title)

    text_edit = QtWidgets.QTextEdit(dialog)
    text_edit.setFixedHeight(70)  # Ajusta la altura para 4 renglones
    text_edit.setFrameStyle(QFrame.NoFrame)  # Quitar el marco del QTextEdit
    text_edit.setStyleSheet("""
        background-color: #262626;  # Fondo de la caja de texto gris
        color: #FFFFFF;  # Texto blanco
    """)
    layout.addWidget(text_edit)

    help_label = QtWidgets.QLabel('<span style="font-size:7pt; color:#AAAAAA;">Ctrl+Enter to confirm</span>', dialog)
    help_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(help_label)

    dialog.setLayout(layout)
    dialog.resize(200, 150)

    def event_filter(widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() == QtCore.Qt.ControlModifier:
                dialog.accept()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                dialog.esc_exit = True  # Establecer esc_exit en True cuando se presiona ESC
                dialog.reject()
                return True
        return False

    text_edit.installEventFilter(dialog)
    dialog.eventFilter = event_filter

    text_edit.setFocus()  # Poner el cursor dentro de la caja de texto

    return dialog, text_edit

def show_text_dialog():
    dialog, text_edit = create_text_dialog()
    cursor_pos = QtGui.QCursor.pos()
    avail_space = QtWidgets.QDesktopWidget().availableGeometry(cursor_pos)
    posx = min(max(cursor_pos.x()-100, avail_space.left()), avail_space.right()-200)
    posy = min(max(cursor_pos.y()-80, avail_space.top()), avail_space.bottom()-150)
    dialog.move(QtCore.QPoint(posx, posy))

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.esc_exit, text_edit.toPlainText()
    else:
        return dialog.esc_exit, None

def calculate_extra_top(text, font_size):
    """
    Calcula el tamano adicional necesario para el texto en funcion del tamano de la fuente y el numero de lineas.
    """
    line_count = text.count('\n') + 2  # Contar las lineas en el texto
    text_height = font_size * line_count  # Calcular la altura total del texto
    return text_height

def calculate_min_horizontal(text, font_size):
    """
    Calcula el ancho minimo necesario para el texto en funcion del tamano de la fuente y la linea mas larga,
    teniendo en cuenta el ancho real de cada caracter.
    """
    # Calcular el ajuste del tamano de la fuente
    adjustment = 0.2 * font_size - 1.5
    adjusted_font_size = font_size - adjustment

    # Crear una fuente con la familia Verdana y el tamano ajustado
    font = QFont("Verdana")
    font.setPointSize(adjusted_font_size)
    metrics = QFontMetrics(font)
    
    lines = text.split('\n')  # Dividir el texto en lineas
    max_width = max(metrics.horizontalAdvance(line) for line in lines)  # Encontrar la linea mas ancha
    min_horizontal = max_width  # Calcular el ancho minimo basado en el ancho real del texto
    
    debug_print(f"Linea mas larga tiene {max_width} pixeles de ancho.")
    debug_print(f"Ancho minimo calculado: {min_horizontal}")
    return min_horizontal



def order_overlapping_backdrops(new_backdrop):
    debug_print("\n--- Iniciando order_overlapping_backdrops ---")
    
    def get_backdrops():
        return [n for n in nuke.allNodes() if n.Class() == "BackdropNode"]

    def is_overlapping(a, b):
        ax, ay = a['xpos'].value(), a['ypos'].value()
        aw, ah = a['bdwidth'].value(), a['bdheight'].value()
        bx, by = b['xpos'].value(), b['ypos'].value()
        bw, bh = b['bdwidth'].value(), b['bdheight'].value()
        return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)

    def is_inside(inner, outer):
        ix, iy = inner['xpos'].value(), inner['ypos'].value()
        iw, ih = inner['bdwidth'].value(), inner['bdheight'].value()
        ox, oy = outer['xpos'].value(), outer['ypos'].value()
        ow, oh = outer['bdwidth'].value(), outer['bdheight'].value()
        return (ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih)

    def get_area(backdrop):
        return backdrop['bdwidth'].value() * backdrop['bdheight'].value()

    # Obtener todos los backdrops
    all_backdrops = get_backdrops()
    debug_print(f"Total de backdrops: {len(all_backdrops)}")
    
    # Encontrar backdrops superpuestos con el nuevo
    overlapping_group = [new_backdrop]
    for backdrop in all_backdrops:
        if backdrop != new_backdrop and is_overlapping(new_backdrop, backdrop):
            overlapping_group.append(backdrop)
    
    debug_print(f"Backdrops superpuestos: {len(overlapping_group)}")
    
    # Si no hay superposiciones, no es necesario hacer nada
    if len(overlapping_group) == 1:
        debug_print("No hay superposiciones, saliendo.")
        return

    # Ordenar el grupo
    overlapping_group.sort(key=get_area)
    ordered = []
    while overlapping_group:
        current = overlapping_group.pop(0)
        insert_index = len(ordered)
        for i, ordered_backdrop in enumerate(ordered):
            if is_inside(current, ordered_backdrop):
                insert_index = i + 1
            elif is_inside(ordered_backdrop, current):
                insert_index = i
                break
            elif get_area(current) > get_area(ordered_backdrop):
                insert_index = i
                break
        ordered.insert(insert_index, current)
    
    debug_print("Orden final de backdrops (de atras hacia adelante):")
    for i, backdrop in enumerate(ordered):
        debug_print(f"  {i+1}. {backdrop.name()} - Area: {get_area(backdrop)}")

    # Asignar nuevos valores Z
    debug_print("\nAsignando nuevos valores Z:")
    for i, backdrop in enumerate(ordered):
        old_z = backdrop['z_order'].value()
        new_z = i * 1  # Puedes ajustar este valor si necesitas mas espacio entre los valores Z
        backdrop['z_order'].setValue(new_z)
        debug_print(f"  {backdrop.name()}: Z anterior = {old_z}, Nuevo Z = {new_z}")

    debug_print("--- Finalizando order_overlapping_backdrops ---\n")


def update_backdrop_properties(node):
    # Cerrar el panel de propiedades
    node.hideControlPanel()
    
    # Volver a abrir el panel de propiedades
    #node.showControlPanel()


def autoBackdrop(show_input=True, is_replacement=False, original_node=None):
    '''
    Automatically puts a backdrop behind the selected nodes.

    The backdrop will be just big enough to fit all the select nodes in,
    with room at the top for some text in a large font.
    '''
    if show_input:
        # Obtener el texto del usuario usando el panel personalizado
        esc_exit, user_text = show_text_dialog()
        if esc_exit:
            return  # Si el usuario cancela con ESC, salir de la funcion
        if user_text is None:
            user_text = ""  # Si el usuario cancela, usar una cadena vacia
    else:
        user_text = ""
    
    sel = nuke.selectedNodes()
    forced = False

    # if nothing is selected
    if not sel:
        forced = True
        b = nuke.createNode('NoOp')
        sel.append(b)

    # Calculate bounds for the backdrop node.
    bdX = min([node.xpos() for node in sel])
    bdY = min([node.ypos() for node in sel])
    bdW = max([node.xpos() + node.screenWidth() for node in sel]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in sel]) - bdY

    zOrder = 0
    selectedBackdropNodes = nuke.selectedNodes("BackdropNode")

    # if there are backdropNodes selected
    # put the new one immediately behind the farthest one
    if len(selectedBackdropNodes):
        zOrder = min([node.knob("z_order").value()
                      for node in selectedBackdropNodes]) - 1
    else:
        # otherwise (no backdrop in selection) find the nearest backdrop
        # if exists and set the new one in front of it
        nonSelectedBackdropNodes = nuke.allNodes("BackdropNode")
        for nonBackdrop in sel:
            for backdrop in nonSelectedBackdropNodes:
                if nodeIsInside(nonBackdrop, backdrop):
                    zOrder = max(zOrder, backdrop.knob("z_order").value() + 1)

    # Valores predeterminados desde los settings
    try:
        appearance_value = nuke.toNode('preferences')['Oz_Backdrop_Appearance'].value()
        default_color = nuke.toNode('preferences')['Oz_Backdrop_color'].value()
        alignment_value = nuke.toNode('preferences')['Oz_Backdrop_text_alignment'].value()
        note_font_size = int((nuke.toNode('preferences')['Oz_Backdrop_font_size'].value()))
        margin_value = int(nuke.toNode('preferences')['Oz_Backdrop_margin'].value())
        bold_value = nuke.toNode('preferences')['Oz_Backdrop_bold'].value()
        debug_print(f"Valores desde settings: bold_value={bold_value}")
    except:
        appearance_value = "Fill"
        default_color = "Random"
        alignment_value = "left"
        note_font_size = 50
        margin_value = 50
        bold_value = False
        debug_print("Usando valores predeterminados por defecto.")

    # Si estamos reemplazando un backdrop existente
    if is_replacement and original_node:
        if 'note_font' in original_node.knobs():
            current_font = original_node['note_font'].value()
            font_family = current_font.replace(" bold", "").replace(" regular", "")
            debug_print(f"Fuente capturada desde el nodo original: {current_font}")
            bold_value = "Bold" in current_font
            debug_print(f"Estado inicial de bold_value basado en la fuente existente: {bold_value}")
    else:
        debug_print("Creando un nuevo backdrop, usando bold_value desde las preferencias.")

    # Aqui continuarias con el resto del codigo para crear o reemplazar el backdrop...
    debug_print(f"Valor final de bold_value: {bold_value}")

    # Apply bold to text if necessary
    default_text = user_text if user_text else ""
    if bold_value:
        display_text = f"{default_text}"
        text_label = default_text  # Sin las etiquetas <b>
    else:
        display_text = default_text
        text_label = default_text

    # Aplicar la fuente y el estado de bold
    def apply_font(node, bold_value):
        if bold_value:
            new_font = f"{font_family} Bold"
        else:
            new_font = font_family
        node['note_font'].setValue(new_font)
        debug_print(f"Fuente establecida en el nodo: {new_font}")        

    # Obtener el valor de padding desde las preferencias
    try:
        padding = int(nuke.toNode('preferences')['Oz_Backdrop_margin'].value())
        debug_print(f"padding calculado: {padding}")
    except:
        padding = 50  # Valor predeterminado en caso de error    
        debug_print(f"padding fijo: {padding}")

    # Calcular el tamano adicional necesario para el texto
    extra_top = calculate_extra_top(user_text, note_font_size)
    debug_print(f"extra_top nuevo: {extra_top}")

    # Calcular el ancho minimo necesario para el texto
    min_horizontal = calculate_min_horizontal(user_text, note_font_size)
    debug_print(f"min_horizontal nuevo: {min_horizontal}")

    # Expandir los limites del backdrop
    if padding < extra_top:
        top = -extra_top
    else:
        top = -padding
    debug_print(f"top nuevo: {top}")
    bottom = margin_value
    debug_print(f"bottom nuevo: {bottom}")

    left = -1 * margin_value
    debug_print(f"left nuevo: {left}")
    additional_width = max(0, min_horizontal - bdW)
    left_adjustment = additional_width / 2
    right_adjustment = additional_width / 2

    right = margin_value + right_adjustment
    debug_print(f"right nuevo: {right}")
    left -= left_adjustment
    debug_print(f"left ajustado: {left}")

    debug_print(f"Valores iniciales: bdX={bdX}, bdY={bdY}, bdW={bdW}, bdH={bdH}")

    bdX += left
    bdY += top
    bdW += (right - left)
    bdH += (bottom - top)

    debug_print(f"Valores ajustados: bdX={bdX}, bdY={bdY}, bdW={bdW}, bdH={bdH}")

    rgbRandom = random.random(), .1 + random.random() * .15, .15 + random.random() * .15

    def switch_color(case):
        return colors.get(case, rgbRandom)

    R, G, B = colorsys.hsv_to_rgb(switch_color(default_color)[0], switch_color(default_color)[1], switch_color(default_color)[2])

    tile_color = int('%02x%02x%02x%02x' % (int(R*255), int(G*255), int(B*255), 255), 16)

    # En caso de que solo haya un Backdrop seleccionado y estemos reemplazando, usa su fuente
    if is_replacement and len(selectedBackdropNodes) == 1:
        current_font = selectedBackdropNodes[0]['note_font'].value()
        font_family = current_font.replace(" bold", "").replace(" regular", "")
    else:
        font_family = "Verdana"

    debug_print(f"Fuente seleccionada o por defecto: {font_family}")

    # Crear el nuevo BackdropNode:
    n = nuke.nodes.BackdropNode(xpos=bdX, bdwidth=bdW, ypos=bdY,
                                bdheight=bdH,
                                tile_color=tile_color,
                                note_font_size=note_font_size,
                                note_font=f"{font_family} bold" if bold_value else font_family,  # Mantener la familia de fuentes y ajustar el peso
                                z_order=zOrder,
                                label=display_text,
                                appearance=appearance_value
                                )


    # Reordenar los backdrops superpuestos con el nuevo backdrop
    #order_all_backdrops(n)

    # Aplicar el font al nodo creado
    apply_font(n, bold_value)
    

    if show_input:
        n.showControlPanel()


    # Buid all knobs for Backdrop
    tab = nuke.Tab_Knob('Settings')
    text = nuke.Multiline_Eval_String_Knob('text', 'Text')
    text.setFlag(nuke.STARTLINE)
    text.setValue(text_label)  # Para poner un texto por defecto (o de un input box)
    size = nuke.Double_Knob('font_size', 'Font Size') 
    size.setRange(10,100)
    size.setValue(note_font_size) # default value : 50
    size.setFlag(nuke.NO_ANIMATION)

    # Agregar knob para indicar si la negrita esta activada
    bold_knob = nuke.Boolean_Knob('Oz_Backdrop_bold', 'Bold', bold_value)
    #bold_text = nuke.Text_Knob('bold_text', '', 'Bold')
    #bold_knob = nuke.Boolean_Knob('Oz_Backdrop_bold', '')    

    alignment = nuke.Enumeration_Knob('alignment', '', ['left', 'center', 'right'])
    alignment.clearFlag(nuke.STARTLINE)
    alignment.setValue(alignment_value)



    
    # Nuevo knob para el color de la fuente
    font_color = nuke.PyScript_Knob('font_color_toggle', 'B/W', '''
node = nuke.thisNode()

# Obtiene el color actual desde note_font_color
current_font_color = node['note_font_color'].value()

# Definir los valores
white_color = 4294967295  # Blanco que funciona
black_color = 0x000000  # Negro que funciona

# Alterna entre blanco y negro
if current_font_color == white_color:
    new_font_color = black_color
else:
    new_font_color = white_color

# Establece el nuevo color en note_font_color
node['note_font_color'].setValue(new_font_color)

print(f"Boton B/W: Cambiado color a {'Blanco' if new_font_color == white_color else 'Negro'}")
''')

    


    appearance = nuke.Enumeration_Knob('oz_appearance', ' Appearance      ', ['Fill', 'Border'])
    appearance.clearFlag(nuke.STARTLINE)
    appearance.setValue(appearance_value)
    border = nuke.Double_Knob('oz_border_width', 'Border')
    border.clearFlag(nuke.STARTLINE)
    border.setRange(0,30)
    border.setValue(2)
    border.setFlag(nuke.NO_ANIMATION)
    border.setTooltip("Border width for Border appearence")  # Adjust the number of spaces to fit your nee
    space1 = nuke.Text_Knob('S01', ' ', ' ')
    space2 = nuke.Text_Knob('S02', ' ', ' ')
    space3 = nuke.Text_Knob('S03', ' ', '     ')
    space3.clearFlag(nuke.STARTLINE)
    space4 = nuke.Text_Knob('S04', ' ', ' ')
    space4.clearFlag(nuke.STARTLINE)
    space5 = nuke.Text_Knob('S05', ' ', ' ')
    space5.clearFlag(nuke.STARTLINE)
    space6 = nuke.Text_Knob('S06', ' ', ' ')
    space7 = nuke.Text_Knob('S07', ' ', ' ')
    #space7.clearFlag(nuke.STARTLINE)
    space8 = nuke.Text_Knob('S08', ' ', ' ')
    space82 = nuke.Text_Knob('S08', ' ', '       ')
    space82.clearFlag(nuke.STARTLINE)
    space9 = nuke.Text_Knob('S09', ' ', ' ')
    divider1 = nuke.Text_Knob('divider1','')
    divider2 = nuke.Text_Knob('divider2','')
    divider3 = nuke.Text_Knob('divider3','')
    divider4 = nuke.Text_Knob('divider4', '')
    divider5 = nuke.Text_Knob('divider5', '')
    
    grow = nuke.PyScript_Knob('grow', ' <img src="MergeMin.png">', "n=nuke.thisNode()\n\ndef grow(node=None,step=50):\n    try:\n        if not node:\n            n=nuke.selectedNode()\n        else:\n            n=node\n            n['xpos'].setValue(n['xpos'].getValue()-step)\n            n['ypos'].setValue(n['ypos'].getValue()-step)\n            n['bdwidth'].setValue(n['bdwidth'].getValue()+step*2)\n            n['bdheight'].setValue(n['bdheight'].getValue()+step*2)\n    except e:\n        print('Error:: %s' % e)\n\ngrow(n,50)")
    shrink = nuke.PyScript_Knob('shrink', ' <img src="MergeMax.png">', "n=nuke.thisNode()\n\ndef shrink(node=None,step=50):\n    try:\n        if not node:\n            n=nuke.selectedNode()\n        else:\n            n=node\n            n['xpos'].setValue(n['xpos'].getValue()+step)\n            n['ypos'].setValue(n['ypos'].getValue()+step)\n            n['bdwidth'].setValue(n['bdwidth'].getValue()-step*2)\n            n['bdheight'].setValue(n['bdheight'].getValue()-step*2)\n    except e:\n        print('Error:: %s' % e)\n\nshrink(n,50)")

    
    # Add Z Order label and number input
    zorder_label = nuke.Text_Knob('z_order_label', '', 'Z Order     ')
    zorder_back_label = nuke.Text_Knob('', '', 'Back ')
    zorder = nuke.Double_Knob("zorder", "")
    zorder.setRange(-5, +5)
    zorder_front_label = nuke.Text_Knob('', '', ' Front')
    
    # Set flags to align on the same line
    zorder_label.clearFlag(nuke.STARTLINE)
    zorder_back_label.clearFlag(nuke.STARTLINE)
    zorder.clearFlag(nuke.STARTLINE)
    zorder_front_label.clearFlag(nuke.STARTLINE) 
    zorder.setFlag(nuke.NO_ANIMATION)
    
    
    encompassButton = nuke.PyScript_Knob('encompassSelectedNodes', ' <img src="ContactSheet.png">', '''
import oz_encompassScript
oz_encompassScript.encompass_selected_nodes()
''')
    encompassPadding = nuke.Int_Knob('sides',"")
    encompassPadding.setValue(margin_value) # default value : 50
    encompassPadding.clearFlag(nuke.STARTLINE)
    position_text = nuke.Text_Knob('pos_text', 'Position', ' ')
    position_text.clearFlag(nuke.STARTLINE)
    position_x = nuke.Int_Knob("node_position_x", "x")
    position_x.clearFlag(nuke.STARTLINE)
    position_y = nuke.Int_Knob("node_position_y", "y")
    position_y.clearFlag(nuke.STARTLINE)
    sizeWH = nuke.WH_Knob("sizeNode", "Size       ")
    sizeWH.setSingleValue(False)
    sizeWH.clearFlag(nuke.STARTLINE)
    sizeWH.setFlag(nuke.NO_ANIMATION)
    


    # Boton Copy W
    copy_w_button = nuke.PyScript_Knob('copy_width', 'Copy W', '''
import subprocess
import platform

node = nuke.thisNode()

# Funcion updateKnobs para actualizar todos los valores para hacer un refresh antes del copy
def updateKnobs(node):
    nodeWidth = node['bdwidth'].getValue()
    nodeHeight = node['bdheight'].getValue()
    node['sizeNode'].setValue([int(nodeWidth), int(nodeHeight)])
    node['zorder'].setValue(int(node['z_order'].getValue()))
    node['font_size'].setValue(int(node['note_font_size'].getValue()))
    node['oz_appearance'].setValue(node['appearance'].value())
    node['oz_border_width'].setValue(node['border_width'].value())

updateKnobs(node)

size_w = node['sizeNode'].getValue()[0]

# Copiar al portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'echo ' + str(size_w).strip() + '| clip'
    subprocess.run(cmd, shell=True)
elif platform.system() == 'Darwin':
    cmd = 'echo ' + str(size_w).strip() + ' | pbcopy'
    subprocess.run(cmd, shell=True)
else:
    print("Sistema operativo no soportado para copiar al portapapeles")

#print("Size W copiado al portapapeles:", size_w)
''')
    copy_w_button.setTooltip("Copy the width of this backdrop to use in another backdrop")



    
    # Boton Paste W con funcionalidad para pegar el valor desde el portapapeles
    paste_w_button = nuke.PyScript_Knob('paste_width', 'Paste W', '''
import subprocess
import platform

node = nuke.thisNode()

# Obtener el valor del portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'powershell Get-Clipboard'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size_w = result.stdout.strip()
elif platform.system() == 'Darwin':
    cmd = 'pbpaste'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size_w = result.stdout.strip()
else:
    print("Sistema operativo no soportado para pegar desde el portapapeles")
    size_w = None

if size_w:
    try:
        size_w = float(size_w)
        node['bdwidth'].setValue(size_w)
        node['sizeNode'].setValue([size_w, node['sizeNode'].getValue()[1]])
        #print("Size W pegado desde el portapapeles:", size_w)
    except ValueError:
        print("El valor en el portapapeles no es un numero valido")
''')
    paste_w_button.setTooltip("Set this backdrop's width using the value copied from another backdrop")



   
    # Boton Copy H con actualizacion de valores
    copy_h_button = nuke.PyScript_Knob('copy_height', 'Copy H', '''
import subprocess
import platform

node = nuke.thisNode()


# Funcion updateKnobs para actualizar todos los valores para hacer un refresh antes del copy
def updateKnobs(node):
    nodeWidth = node['bdwidth'].getValue()
    nodeHeight = node['bdheight'].getValue()
    node['sizeNode'].setValue([int(nodeWidth), int(nodeHeight)])
    node['zorder'].setValue(int(node['z_order'].getValue()))
    node['font_size'].setValue(int(node['note_font_size'].getValue()))
    node['oz_appearance'].setValue(node['appearance'].value())
    node['oz_border_width'].setValue(node['border_width'].value())

updateKnobs(node)

size_h = node['sizeNode'].getValue()[1]

# Copiar al portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'echo ' + str(size_h).strip() + '| clip'
    subprocess.run(cmd, shell=True)
elif platform.system() == 'Darwin':
    cmd = 'echo ' + str(size_h).strip() + ' | pbcopy'
    subprocess.run(cmd, shell=True)
else:
    print("Sistema operativo no soportado para copiar al portapapeles")

print("Size H copiado al portapapeles:", size_h)
''')
    copy_h_button.setTooltip("Copy the height of this backdrop to use in another backdrop")




    # Boton Paste H con funcionalidad para pegar el valor desde el portapapeles
    paste_h_button = nuke.PyScript_Knob('paste_height', 'Paste H', '''
import subprocess
import platform

node = nuke.thisNode()

# Obtener el valor del portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'powershell Get-Clipboard'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size_h = result.stdout.strip()
elif platform.system() == 'Darwin':
    cmd = 'pbpaste'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size_h = result.stdout.strip()
else:
    print("Sistema operativo no soportado para pegar desde el portapapeles")
    size_h = None

if size_h:
    try:
        size_h = float(size_h)
        node['bdheight'].setValue(size_h)
        node['sizeNode'].setValue([node['sizeNode'].getValue()[0], size_h])
        #print("Size H pegado desde el portapapeles:", size_h)
    except ValueError:
        print("El valor en el portapapeles no es un numero valido")
''')
    paste_h_button.setTooltip("Set this backdrop's height using the value copied from another backdrop")




    
    # Boton Copy Color con funcionalidad para copiar el valor de tile_color
    copy_color_button = nuke.PyScript_Knob('copy_color', '   Copy Color   ', '''
import subprocess
import platform

node = nuke.thisNode()

tile_color = node['tile_color'].value()
tile_color_hex = '{:08x}'.format(tile_color)  # Convertir a cadena hexadecimal de 8 digitos

# Copiar al portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'echo ' + tile_color_hex + '| clip'
    subprocess.run(cmd, shell=True)
elif platform.system() == 'Darwin':
    cmd = 'echo ' + tile_color_hex + ' | pbcopy'
    subprocess.run(cmd, shell=True)
else:
    print("Sistema operativo no soportado para copiar al portapapeles")

#print("Color copiado al portapapeles:", tile_color_hex)
''')




    # Boton Paste Color con funcionalidad para pegar el valor de tile_color desde el portapapeles
    paste_color_button = nuke.PyScript_Knob('paste_color', '   Paste Color   ', '''
import subprocess
import platform

node = nuke.thisNode()

# Obtener el valor del portapapeles segun el sistema operativo
if platform.system() == 'Windows':
    cmd = 'powershell Get-Clipboard'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tile_color_hex = result.stdout.strip()
elif platform.system() == 'Darwin':
    cmd = 'pbpaste'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tile_color_hex = result.stdout.strip()
else:
    print("Sistema operativo no soportado para pegar desde el portapapeles")
    tile_color_hex = None

if tile_color_hex:
    try:
        tile_color = int(tile_color_hex, 16)
        node['tile_color'].setValue(tile_color)
        #print("Color pegado desde el portapapeles:", tile_color_hex)
    except ValueError:
        print("El valor en el portapapeles no es un color valido")
''')


    
    buttonRandomColor = nuke.PyScript_Knob('Random Color', ' <img src="ColorBars.png">', randomColorScript)
    
    # Generating buttons for colors.
    color_buttons = []
    
    for key, value in colors.items():
        name = "<div>{}</div>".format(key.capitalize()) if value["title"] else ""
        script_code = (
            "import colorsys\n"
            "n=nuke.thisNode()\n"
            "def clamp(x):\n"
            "    return int(max(0, min(x, 255)))\n"
            "tile_color=n['tile_color'].value()\n"
            "colors={}\n"
            "#converting colors\n"
            "colors_hex=[colorsys.hsv_to_rgb(color[0],color[1],color[2]) for color in colors]\n"
            "colors_int=[int('%02x%02x%02x%02x' % (clamp(color[0]*255),clamp(color[1]*255),clamp(color[2]*255),255), 16) for color in colors_hex]\n"
            "#selecting color logic\n"
            "if tile_color in colors_int:\n"
            "    current_index=colors_int.index(tile_color)\n"
            "    if current_index >= (len(colors_int)-1):\n"
            "        new_color = colors_int[0]\n"
            "    else:\n"
            "        new_color = colors_int[current_index+1]\n"
            "else:\n"
            "    new_color = colors_int[0]\n"
            "#apply color\n"
            "n['tile_color'].setValue(new_color)"
        ).format(value["hsv"])
        
        globals()[key] = nuke.PyScript_Knob(
            key.capitalize(),
            '<div style="background-color: {0}; color: {0}; font-size: 7px;">______</div>'
            '<div style="background-color: {1}; color: {1}; font-size: 7px;">______</div>'
            '<div style="background-color: {2}; color: {2}; font-size: 7px;">______</div>{title}'.format(
                hsv_to_hex(value["hsv"][0]), hsv_to_hex(value["hsv"][1]), hsv_to_hex(value["hsv"][2]), title=name
            ),
            script_code
        )
        globals()[key].setTooltip(value["tooltip"])
        if value["newline"]:
            space = nuke.Text_Knob('space', ' ', ' ')
            color_buttons.append(space)
        color_buttons.append(globals()[key])


        
        

    # Tooltips

    grow.setTooltip("Grows the size of the Backdrop by 50pt in every direction")
    shrink.setTooltip("Shrinks the size of the Backdrop by 50pt in every direction")
    encompassButton.setTooltip("Will resize the backdrop to encompass every selected nodes plus a padding number (the number next to the button)")
    encompassPadding.setTooltip("When encompassing nodes this number of pt will be added to the Backdrop size in every direction")

    buttonRandomColor.setTooltip("Generates a random color for the Backdrop (dark shades)")

    # Add the knobs
    n.addKnob(tab)
    n.addKnob(text)
    n.addKnob(size)
    #n.addKnob(bold_text)
    n.addKnob(bold_knob)
    n.addKnob(alignment)
    n.addKnob(font_color)
    n.addKnob(divider1)
    n.addKnob(space1)
    n.addKnob(buttonRandomColor)
    for button in color_buttons:
        n.addKnob(button)
    
    n.addKnob(space8)
    n.addKnob(copy_color_button)
    n.addKnob(paste_color_button)
    n.addKnob(space7)
    n.addKnob(appearance)
    n.addKnob(space82)
    n.addKnob(border)
    
   
    
    n.addKnob(divider2)
    n.addKnob(space2)
    n.addKnob(grow)
    n.addKnob(shrink)
    n.addKnob(space3)
    n.addKnob(encompassButton)
    n.addKnob(space4)
    n.addKnob(encompassPadding)
    n.addKnob(divider3)
    n.addKnob(space5)
    n.addKnob(position_text)
    n.addKnob(position_x)
    n.addKnob(position_y)
    n.addKnob(space6)
    n.addKnob(sizeWH)


    # Anadir los knobs al nodo
    n.addKnob(space9)
    n.addKnob(copy_w_button)
    n.addKnob(paste_w_button)
    n.addKnob(copy_h_button)
    n.addKnob(paste_h_button)  

    n.addKnob(divider4)
    #n.addKnob(zorder)    
 
    # Add the knobs in the correct order
    n.addKnob(zorder_label)
    n.addKnob(zorder_back_label)
    n.addKnob(zorder)
    n.addKnob(zorder_front_label) 
 
    





    # Add Logic & initial setup
    n['knobChanged'].setValue(knobChangedScript)

    # revert to previous selection
    n['selected'].setValue(True)
    if forced:
        nuke.delete(b)
    else:
        for node in sel:
            node['selected'].setValue(True)

    if show_input:
        # Analizar y cambiar Z en caso de ser necesario
        order_overlapping_backdrops(n)
        update_backdrop_properties(n) 

    #return the new backdrop node        
    return n

