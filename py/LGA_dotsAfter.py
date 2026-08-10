"""
__________________________________________________________

  LGA_dotsAfter v1.6 | 2024 | Lega   
  Generates a dot below the selected node and 
  another dot to the left/right of that dot as specified  
__________________________________________________________

"""

import nuke

# Variable global para activar o desactivar los prints
DEBUG = False

def debug_print(message):
    if DEBUG:
        print(message)

def dotsAfter(direction='l'):
    # Definir la distancia vertical entre los nodos Dot
    distanciaY = 70
    dot_width = int(nuke.toNode("preferences")['dot_node_scale'].value() * 12)

    # Determinar la direccion de creacion del Dot
    if direction == 'l':
        distanciaX = -140
    elif direction == 'll':
        distanciaX = -340
    elif direction == 'r':
        distanciaX = 140
    elif direction == 'rr':
        distanciaX = 340
    else:
        debug_print("Direccion no valida. Use 'l' para izquierda o 'r' para derecha.")
        return

    # Obtener el nodo seleccionado
    try:
        selected_node = nuke.selectedNode()
    except ValueError:
        nuke.message("No node selected.")
        debug_print("No node selected.")
        return

    current_node = selected_node  # Guardar en una variable para evitar multiples llamadas a nuke.selectedNode()
    debug_print(f"Nodo seleccionado: {current_node.name()}")

    pos_tolerance = 120  # Tolerancia para la posicion en X
    current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
    current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

    # Buscar el primer nodo que este debajo del nodo seleccionado con una tolerancia en X
    all_nodes = [n for n in nuke.allNodes() if n != current_node and n.Class() != 'Root' and n.Class() != 'BackdropNode']
    nodo_siguiente_en_columna = None
    distMedia_NodoSiguiente = float('inf')

    for node in all_nodes:
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        # Verifica si el nodo esta dentro de la tolerancia y en la direccion correcta (debajo del nodo actual)
        if abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y > current_node_center_y:
            distance = node_center_y - current_node_center_y
            if distance > 0 and distance < distMedia_NodoSiguiente:
                distMedia_NodoSiguiente = distance
                nodo_siguiente_en_columna = node
                debug_print(f"Nodo siguiente en la misma columna encontrado: {nodo_siguiente_en_columna.name()} a distancia {distMedia_NodoSiguiente}")

    # Ajuste de la distancia Y si es necesario
    if distMedia_NodoSiguiente != float('inf'):
        if distMedia_NodoSiguiente < distanciaY * 2:
            distanciaY = distMedia_NodoSiguiente / 2 - (dot_width / 2) - 6
        debug_print(f"Distancia Y ajustada a: {distanciaY}")

    # Calcular la posicion Y del dot
    new_y_pos = int(current_node.ypos() + current_node.screenHeight() + distanciaY)
    debug_print(f"Posicion Y del nuevo Dot: {new_y_pos}")

    if nodo_siguiente_en_columna and current_node in nodo_siguiente_en_columna.dependencies(nuke.INPUTS):
        debug_print(f"Conectando el Dot al nodo siguiente en la misma columna: {nodo_siguiente_en_columna.name()}")

        # Crear un nuevo nodo de Dot
        dot_node = nuke.nodes.Dot()

        # Calcular la posicion X para centrar el Dot horizontalmente
        dot_xpos = int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2))

        # Establecer la nueva posicion del nodo Dot
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(new_y_pos)

        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, current_node)
        debug_print(f"Nuevo Dot creado y conectado al nodo seleccionado: {current_node.name()}")

        # Conectar el nodo siguiente al nodo de Dot
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == current_node:
                nodo_siguiente_en_columna.setInput(i, dot_node)
                break

        debug_print(f"Nodo siguiente en la columna conectado al nuevo Dot: {nodo_siguiente_en_columna.name()}")

        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado
        dot_side = nuke.nodes.Dot()
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)
        debug_print(f"Nuevo Dot lateral creado y conectado al Dot principal en la direccion: {direction}")

    else:
        debug_print(f"No hay nodo siguiente en la misma columna conectado. Creando Dot debajo del nodo seleccionado: {current_node.name()}")

        # Crear un nuevo nodo de Dot debajo del nodo seleccionado
        dot_node = nuke.nodes.Dot()

        # Calcular la posicion X para centrar el Dot horizontalmente
        dot_xpos = int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2))

        # Establecer la nueva posicion del nodo Dot
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(new_y_pos)

        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, current_node)
        debug_print(f"Nuevo Dot creado y conectado al nodo seleccionado: {current_node.name()}")

        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado
        dot_side = nuke.nodes.Dot()
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)
        debug_print(f"Nuevo Dot lateral creado y conectado al Dot principal en la direccion: {direction}")
