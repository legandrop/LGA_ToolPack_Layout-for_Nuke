"""
______________________________________________________

  LGA_distributeNodes_Backdrops v1.2 | 2024 | Lega   
  Distribute Nodes according to input values for h v  
  Distribute Backdrops if more than two are selected
______________________________________________________

"""

import nuke

def distribute(direction='v'):
    nodes = nuke.selectedNodes()
    selected_backdrops = [n for n in nodes if n.Class() == "BackdropNode"]

    nuke.Undo().begin("Distribute Vertically" if direction == 'v' else "Distribute Horizontally")
    try:
        if len(selected_backdrops) >= 2:
            distribute_backdrops(direction, selected_backdrops, nodes)
        else:
            distribute_regular_nodes(direction, nodes)
    finally:
        nuke.Undo().end()

def distribute_regular_nodes(direction, nodes):
    if direction == 'v':
        nodes.sort(key=lambda node: node.ypos())
        positions = [node.ypos() for node in nodes]
    elif direction == 'h':
        nodes.sort(key=lambda node: node.xpos())
        positions = [node.xpos() for node in nodes]
    
    nodes_info = [(node, node.screenHeight() if direction == 'v' else node.screenWidth(), pos) for node, pos in zip(nodes, positions)]

    if len(nodes_info) < 2:
        return  # No hay suficientes nodos para distribuir

    first_node = nodes_info[0]
    last_node = nodes_info[-1]

    total_length = last_node[2] + last_node[1] - first_node[2]
    size_of_nodes = sum(node_info[1] for node_info in nodes_info)
    free_space = total_length - size_of_nodes

    if free_space < 0:
        increment = 0
    else:
        increment = free_space / (len(nodes_info) - 1)

    current_pos = first_node[2] + first_node[1]

    for i, (node, size, pos) in enumerate(nodes_info):
        if i == 0 or i == len(nodes_info) - 1:
            continue
        current_pos += increment
        if direction == 'v':
            node.setYpos(int(current_pos))
        elif direction == 'h':
            node.setXpos(int(current_pos))
        current_pos += size

def distribute_backdrops(direction, backdrops, all_nodes):
    if direction == 'v':
        backdrops.sort(key=lambda bd: bd.ypos())
        positions = [(bd.ypos(), bd.ypos() + bd.screenHeight()) for bd in backdrops]
    elif direction == 'h':
        backdrops.sort(key=lambda bd: bd.xpos())
        positions = [(bd.xpos(), bd.xpos() + bd.screenWidth()) for bd in backdrops]
    
    backdrops_info = [(bd, bd.screenHeight() if direction == 'v' else bd.screenWidth(), pos[0], pos[1]) for bd, pos in zip(backdrops, positions)]

    if len(backdrops_info) < 2:
        return

    first_bd = backdrops_info[0]
    last_bd = backdrops_info[-1]

    total_length = last_bd[3] - first_bd[2]
    size_of_backdrops = sum(bd_info[1] for bd_info in backdrops_info)
    free_space = total_length - size_of_backdrops

    if free_space < 0:
        increment = 0
    else:
        increment = free_space / (len(backdrops_info) - 1)

    current_pos = first_bd[3]

    for i, (bd, size, pos_start, pos_end) in enumerate(backdrops_info):
        if i == 0 or i == len(backdrops_info) - 1:
            continue

        current_pos += increment
        delta_pos = pos_start - current_pos

        nodes_inside = [n for n in all_nodes if n.Class() != "BackdropNode" and
                        n['xpos'].value() >= bd['xpos'].value() and
                        n['ypos'].value() >= bd['ypos'].value() and
                        n['xpos'].value() + n.screenWidth() <= bd['xpos'].value() + bd['bdwidth'].value() and
                        n['ypos'].value() + n.screenHeight() <= bd['ypos'].value() + bd['bdheight'].value()]

        for node in nodes_inside:
            if direction == 'v':
                node.setYpos(int(node.ypos() - delta_pos))
            elif direction == 'h':
                node.setXpos(int(node.xpos() - delta_pos))

        if direction == 'v':
            bd.setYpos(int(current_pos))
        elif direction == 'h':
            bd.setXpos(int(current_pos))
        current_pos += size

# Llamar a la funcion de distribucion
distribute('v')  # Para distribucion vertical
distribute('h')  # Para distribucion horizontal
