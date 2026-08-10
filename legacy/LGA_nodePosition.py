"""
____________________________________________

  LGA_nodePosition v1.0 | 2024 | Lega   
  Prints the position of the selected node  
____________________________________________

"""

import nuke

def nodePosition():
    node = nuke.selectedNode()  # Obtener el nodo seleccionado actualmente
    if node:
        pos_y = node['ypos'].value() + node.screenHeight() / 2  # Obtener la posicion en Y del nodo
        print(f"Posicion Y del nodo {node.name()}: {pos_y}")
    else:
        print("No hay ningun nodo seleccionado.")

# Llamar a la funcion para imprimir la posicion Y del nodo seleccionado
#nodePosition()
