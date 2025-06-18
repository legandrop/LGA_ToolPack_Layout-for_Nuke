"""
______________________________________________________

  LGA_alignNodes_Backdrops v1.2 | 2024 | Lega   
  Aligns nodes according to input values for l r t b  
  Aligns Backdrops if more than one is selected
______________________________________________________

"""

import nuke

def alignNodes(direction='t'):
    nodes = nuke.selectedNodes()
    selected_backdrops = [n for n in nodes if n.Class() == "BackdropNode"]

    if len(selected_backdrops) >= 2:
        alignBackdrops(selected_backdrops, nodes, direction)
    else:
        alignRegularNodes(nodes, direction)

def alignRegularNodes(nodes, direction='t'):
    if direction not in ['t', 'b', 'l', 'r']:
        print("Direccion no valida")
        return

    if direction == 't':
        reference_node = min(nodes, key=lambda n: n.ypos())
        reference_pos = reference_node.ypos()
    elif direction == 'b':
        reference_node = max(nodes, key=lambda n: n.ypos() + n.screenHeight())
        reference_pos = reference_node.ypos() + reference_node.screenHeight()
    elif direction == 'l':
        reference_node = min(nodes, key=lambda n: n.xpos())
        reference_pos = reference_node.xpos()
    elif direction == 'r':
        reference_node = max(nodes, key=lambda n: n.xpos() + n.screenWidth())
        reference_pos = reference_node.xpos() + reference_node.screenWidth()

    for n in nodes:
        if n != reference_node:
            if direction in ['t', 'b']:
                offset = (reference_node.screenHeight() / 2) - (n.screenHeight() / 2)
                n.setYpos(int(reference_pos + offset) if direction == 't' else int(reference_pos - n.screenHeight() - offset))
            elif direction in ['l', 'r']:
                offset = (reference_node.screenWidth() / 2) - (n.screenWidth() / 2)
                n.setXpos(int(reference_pos + offset) if direction == 'l' else int(reference_pos - n.screenWidth() - offset))

def alignBackdrops(backdrops, all_nodes, direction='t'):
    for bd in backdrops:
        nodes_inside = [n for n in all_nodes if n['xpos'].value() >= bd['xpos'].value() and n['ypos'].value() >= bd['ypos'].value() and n['xpos'].value() + n.screenWidth() <= bd['xpos'].value() + bd['bdwidth'].value() and n['ypos'].value() + n.screenHeight() <= bd['ypos'].value() + bd['bdheight'].value() and n not in backdrops]

        if direction == 't':
            reference_bd = min(backdrops, key=lambda bd: bd.ypos())
            delta_pos = bd.ypos() - reference_bd.ypos()
            bd.setYpos(int(reference_bd.ypos()))
        elif direction == 'b':
            reference_bd = max(backdrops, key=lambda bd: bd.ypos() + bd['bdheight'].value())
            delta_pos = (bd.ypos() + bd['bdheight'].value()) - (reference_bd.ypos() + reference_bd['bdheight'].value())
            bd.setYpos(int(reference_bd.ypos() + reference_bd['bdheight'].value() - bd['bdheight'].value()))
        elif direction == 'l':
            reference_bd = min(backdrops, key=lambda bd: bd.xpos())
            delta_pos = bd.xpos() - reference_bd.xpos()
            bd.setXpos(int(reference_bd.xpos()))
        elif direction == 'r':
            reference_bd = max(backdrops, key=lambda bd: bd.xpos() + bd['bdwidth'].value())
            delta_pos = (bd.xpos() + bd['bdwidth'].value()) - (reference_bd.xpos() + reference_bd['bdwidth'].value())
            bd.setXpos(int(reference_bd.xpos() + reference_bd['bdwidth'].value() - bd['bdwidth'].value()))

        for node in nodes_inside:
            if direction in ['t', 'b']:
                node.setYpos(int(node.ypos() - delta_pos))
            elif direction in ['l', 'r']:
                node.setXpos(int(node.xpos() - delta_pos))

