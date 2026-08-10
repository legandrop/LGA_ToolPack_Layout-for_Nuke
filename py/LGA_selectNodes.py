"""
__________________________________________________________________________________________________

  LGA_selectNodes v1.3 | 2024 | Lega
  Select connected or unconnected nodes in any direction with a tolerance of 30px, ignoring flow
  Or select all nodee in one direction
__________________________________________________________________________________________________

"""

import nuke

def selectNodes(direction):
    pos_tolerance = 30  # Tolerancia para la posicion en X y Y

    # Comenzar con el nodo seleccionado actualmente
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        nuke.message('Please select at least one node to proceed.')
        return

    # Obtener el nodo seleccionado actualmente
    current_node = selected_nodes[0]

    # Asegurarse de que el nodo actual no sea el nodo raiz ni un BackdropNode
    if current_node.Class() == 'Root' or current_node.Class() == 'BackdropNode':
        nuke.message('The operation cannot be performed on the root node or a backdrop node. Please select a different node.')
        return

    # Calcular el centro del nodo actual
    current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
    current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

    # Obtener todos los nodos que no sean el nodo raiz, el nodo seleccionado actualmente, ni BackdropNode
    all_nodes = [n for n in nuke.allNodes() if n != current_node and n.Class() != 'Root' and n.Class() != 'BackdropNode']

    for node in all_nodes:
        # Calcular el centro del nodo
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        # Verificar la posicion del nodo en relacion al nodo seleccionado y la tolerancia
        if direction == 'l' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x < current_node_center_x:
            node['selected'].setValue(True)
        elif direction == 'r' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x > current_node_center_x:
            node['selected'].setValue(True)
        elif direction == 't' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y < current_node_center_y:
            node['selected'].setValue(True)
        elif direction == 'b' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y > current_node_center_y:
            node['selected'].setValue(True)



def selectConnectedNodes(direction):
    pos_tolerance = 30  # Tolerancia para la posicion en X y Y

    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        return

    current_node = selected_nodes[0]
    if current_node.Class() == 'Root' or current_node.Class() == 'BackdropNode':
        return

    while current_node:
        # Calcula el centro del nodo actual
        current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
        current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

        current_node['selected'].setValue(True)

        # Lista para mantener los nodos conectados tanto aguas arriba como aguas abajo
        search_nodes = [current_node.input(i) for i in range(current_node.inputs()) if current_node.input(i) and current_node.input(i).Class() != 'BackdropNode']
        search_nodes += [n for n in current_node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS) if n.Class() != 'BackdropNode']
        search_nodes = list(set(search_nodes))  # Elimina duplicados y None

        connected_node = None
        for node in search_nodes:
            if node.Class() == 'Root' or node.Class() == 'BackdropNode':
                continue

            # Calcula el centro del nodo conectado
            node_center_x = node.xpos() + (node.screenWidth() / 2)
            node_center_y = node.ypos() + (node.screenHeight() / 2)

            # Verifica la direccion y si el nodo conectado esta dentro de la tolerancia y en la direccion correcta
            if direction == 'l' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x < current_node_center_x:
                connected_node = node
            elif direction == 'r' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x > current_node_center_x:
                connected_node = node
            elif direction == 't' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y < current_node_center_y:
                connected_node = node
            elif direction == 'b' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y > current_node_center_y:
                connected_node = node

        if connected_node:
            connected_node['selected'].setValue(True)
            current_node = connected_node
        else:
            break

def selectAllNodes(direction):
    # Crear un nodo NoOp en la posicion del puntero del mouse y obtener su posicion
    pivot_node = nuke.createNode("NoOp")
    mouse_x = pivot_node.xpos() + (pivot_node.screenWidth() / 2)
    mouse_y = pivot_node.ypos() + (pivot_node.screenHeight() / 2)

    # Eliminar el nodo NoOp creado
    nuke.delete(pivot_node)

    # Obtener todos los nodos que no sean el nodo raiz
    all_nodes = [n for n in nuke.allNodes() if n.Class() != 'Root']

    for node in all_nodes:
        # Calcular el centro del nodo
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        # Verificar la posicion del nodo en relacion a la posicion del puntero del mouse
        if direction == 'l' and node_center_x < mouse_x:
            node['selected'].setValue(True)
        elif direction == 'r' and node_center_x > mouse_x:
            node['selected'].setValue(True)
        elif direction == 't' and node_center_y < mouse_y:
            node['selected'].setValue(True)
        elif direction == 'b' and node_center_y > mouse_y:
            node['selected'].setValue(True)
