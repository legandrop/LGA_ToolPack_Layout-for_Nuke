"""
______________________________________________________________

  LGA_arrangeNodes v1.76 | 2025 | Lega   
 
  Align and distribute multiple columns based on connections  
______________________________________________________________

"""

"""

subgroups:
Se crean en la funcion subdivide_column.
Cada subgrupo representa un conjunto de nodos que estan conectados entre si dentro de la misma columna.
La funcion recorre los nodos de abajo hacia arriba, y si encuentra nodos conectados, los agrupa en un subgrupo.

subSubgroup:
Es un subconjunto de un subgrupo, que representa una parte del subgrupo que esta conectada con otras columnas.
Se crea dinamicamente dentro del bucle que procesa cada subgrupo. Si un nodo dentro de un subgrupo esta conectado 
a un nodo en otra columna, los nodos desde ese nodo hacia arriba forman un subSubgroup.
subSubgroup se procesa y distribuye verticalmente teniendo en cuenta la posicion del nodo conectado en otra columna.

subSubgroupOld:
Es una variable temporal que guarda el subSubgroup anterior.
Se utiliza para comparar la posicion del subSubgroup actual con la del anterior, permitiendo que los nodos se 
redistribuyan de manera adecuada, evitando solapamientos o desordenamientos.
Si existe un subSubgroupOld, este se redistribuye antes de procesar el nuevo subSubgroup.

"""


import nuke
from collections import defaultdict

# Variable global para activar o desactivar los prints
DEBUG = {
    'A': False,   # Desordenados
    'B': False,   # Posicion origina de los nodos y proceso de armado de columnas
    'C': False,   # Resultados del armado de columnas
    'D': False,   # Ireaciones para arreglar nodos
    'E': False,   # Distribucion
    'F': False,   # Distribucion

}

def debug_print_A(*message):
    if DEBUG['A']:
        print(' '.join(str(m) for m in message))

def debug_print_B(*message):
    if DEBUG['B']:
        print(' '.join(str(m) for m in message))

def debug_print_C(*message):
    if DEBUG['C']:
        print(' '.join(str(m) for m in message))

def debug_print_D(*message):
    if DEBUG['D']:
        print(' '.join(str(m) for m in message))
        
def debug_print_E(*message):
    if DEBUG['E']:
        print(' '.join(str(m) for m in message))        

def debug_print_F(*message):
    if DEBUG['F']:
        print(' '.join(str(m) for m in message))        

# Variable global para activar o desactivar los mensajes
DEBUG_MESSAGE = {
    'A': False,      # 
    'B': False,      # 
    'C': False,      # 
    'D': False,      # Dis

}

def debug_message_A(*message):
    if DEBUG_MESSAGE['A']:
        nuke.message(' '.join(str(m) for m in message))

def debug_message_B(*message):
    if DEBUG_MESSAGE['B']:
        nuke.message(' '.join(str(m) for m in message))

def debug_message_C(*message):
    if DEBUG_MESSAGE['C']:
        nuke.message(' '.join(str(m) for m in message))

def debug_message_D(*message):
    if DEBUG_MESSAGE['D']:
        nuke.message(' '.join(str(m) for m in message))        

toleranciaY = 0  # valor en Y de tolerancia
toleranciaX = 55  # valor en X de tolerancia para agrupar los nodos en distintas columnas

def sort_nodes_by_position(nodes, reverse=False):
    # Solo lo uso para ordenarlos en X
    return sorted(nodes, key=lambda n: (node_center(n)[0], node_center(n)[1]), reverse=reverse)

def is_connected_to_any_column(current_y_connected, node_set_potential, node_set_next, current_positions):
    """
    Busca nodos en las potential_columns que esten desde current_y_connected hacia arriba,
    y verifica si tienen alguna conexion con nodos en las next_columns.
    """
    # Extraemos los nombres de los nodos en node_set_next para facilitar la comparacion.
    next_node_names = {node.name() for node in node_set_next}

    # Filtrar nodos en potential_columns que esten desde current_y_connected hacia arriba
    filtered_nodes = [node for node in node_set_potential if current_positions[node][1] <= current_y_connected]

    # Ordenar nodos por su posicion Y de menor a mayor (mas alto a mas bajo)
    filtered_nodes.sort(key=lambda node: current_positions[node][1])

    # Imprimir nodos filtrados para ver que se esta evaluando
    #debug_print_D(f"Nodos filtrados en potential_columns: {[node.name() for node in filtered_nodes]}")

    # Iterar sobre los nodos filtrados para verificar conexiones
    for node in filtered_nodes:
        # Verificar conexiones de salida hacia nodos en next_columns
        for i in range(node.inputs()):
            input_node = node.input(i)
            if input_node and input_node.name() in next_node_names:
                next_connected_nodeY = current_positions[node][1]
                debug_print_D(f"        Conexion encontrada desde {node.name()} en {next_connected_nodeY} hacia {input_node.name()} en next_columns")
                return next_connected_nodeY

    debug_print_D("        No se encontraron")
    return None

def distribute_lastSubSubgroupOld(group_nodes, topTopNodeY, current_positions=None):
    """ 
    Baja el primer nodo (nodo no conectado mas alto) 35 pixeles por debajo del nodo mas alto de la columna principal 
    Despues baja el resto de 10 en 10
    Despues los distribuye
    """
    debug_print_A(f"\n+ - + - Arranca el distribute_lastSubSubgroupOld: {[node.name() for node in group_nodes]}")  # Imprime los nombres de los nodos en group_nodes

    if current_positions is None:
        current_positions = {}  # Inicializa si no se proporciona ningun diccionario
        debug_print_A("*****Sin current position")
    else:
        pass

    # Definir o actualizar las current_positions con la posicion central actual de cada nodo
    for node in group_nodes:
        if node not in current_positions:
            current_x = node.xpos() + node.screenWidth() / 2
            current_y = node.ypos() + node.screenHeight() / 2
            current_positions[node] = (current_x, current_y)
        else:
            pass

    # Ubicar al nodo mas alto 30 pixeles por debajo del topTopNodeY
    highest_node = min(group_nodes, key=lambda n: current_positions[n][1])
    new_y = topTopNodeY + 30
    #new_y = current_positions[highest_node][1] # Estoy dejando que el nodo mas alto supere la altura si quiere

    nodo_height = highest_node.screenHeight() / 2
    highest_node.setYpos(round(new_y - nodo_height))  # Para el valor de pos real hay que restar la mitad de la altura del nodo
    current_positions[highest_node] = (current_positions[highest_node][0], new_y)

    # 2 - Distribuir en caso de que haya mas de 1 nodo en el grupo / columna
    if len(group_nodes) > 1:
        debug_print_A("+ - + -hay mas de 1 nodo, vamos a distribuir de a 10 el lastSubSubgroupOld")

        # Identificar el nodo mas alto y el mas bajo usando current_positions
        highest_node = min(group_nodes, key=lambda n: current_positions[n][1])
        lowest_node = max(group_nodes, key=lambda n: current_positions[n][1])

        # Calcular el nuevo espaciado basado en los nodos extremos
        top_position = topTopNodeY + 30
        bottom_position = current_positions[lowest_node][1]
        spacing = 10

        debug_print_A(f"+ - + -top_position {top_position}")
        debug_print_A(f"+ - + -spacing {spacing}")
        debug_print_A(f"+ - + -Nodo mas alto FI POS: {highest_node.name()}")
        debug_print_A(f"+ - + -Nodo mas bajo FI POS: {lowest_node.name()}")

        current_position = topTopNodeY + 30
        debug_print_A(f"current_position fuera {current_position}")

        for node in sorted(group_nodes, key=lambda n: current_positions[n][1], reverse=False):
            if node not in (highest_node, lowest_node):
                debug_print_A(f"+ - + -current_position {current_position} del nodo {node.name()} ")
                new_y = current_position
                nodo_height = node.screenHeight() / 2
                node.setYpos(round(new_y - nodo_height))  # Para el valor de pos real hay que restar la mitad de la altura del nodo
                current_positions[node] = (current_positions[node][0], new_y)
                debug_print_A(f"+ - + -Posicion actualizada de B {node.name()}: Y = {new_y}")  # El valor de fina_pos siempre es el centro del nodo
            else:
                debug_print_A(f"+ - + -Posicion de {node.name()} no cambia (nodo mas alto o mas bajo).")
                pass
            current_position += spacing

    
    if len(group_nodes) > 2:
        distribute_vertically(group_nodes)  # Llamado a la funcion para distribuir verticalmente

        # Actualizar current_positions despues de la distribucion
        for node in group_nodes:
            current_positions[node] = (node.xpos() + node.screenWidth() / 2, node.ypos() + node.screenHeight() / 2)


    return current_positions  # Retorna el diccionario actualizado

def distribute_subSubgroupOld(group_nodes, lowest_temp_y, current_positions=None):
    debug_print_A(f"\n+ - + - Arranca distribute_subSubgroupOld para el distribute_subSubgroupOld: {[node.name() for node in group_nodes]}")  # Imprime los nombres de los nodos en group_nodes

    if current_positions is None:
        current_positions = {}  # Inicializa si no se proporciona ningun diccionario
        pass

    # Definir o actualizar las current_positions con la posicion central actual de cada nodo
    for node in group_nodes:
        if node not in current_positions:
            current_x = node.xpos() + node.screenWidth() / 2
            current_y = node.ypos() + node.screenHeight() / 2
            current_positions[node] = (current_x, current_y)
        else:
            pass

    # 2 - Distribuir en caso de que haya mas de 2 nodos en el grupo / columna
    if len(group_nodes) > 2:
        debug_print_A("+ - + -hay mas de 2 nodos, vamos a distribuir cortito el subSubgroupOld")

        # Llamado a la funcion para distribuir verticalmente
        distribute_vertically(group_nodes)

        # Actualizar current_positions despues de la distribucion
        for node in group_nodes:
            current_positions[node] = (node.xpos() + node.screenWidth() / 2, node.ypos() + node.screenHeight() / 2)

    return current_positions  # Retorna el diccionario actualizado

def distribute_columns(group_nodes, toleranciaY, offset_y=0, current_positions=None, subSubgroupOld=None, connected_node=None):
    
    debug_print_F(f"\n                Distribute_columns para el grupo: {[node.name() for node in group_nodes]}")  # Imprime los nombres de los nodos en group_nodes

    bandera_distribucion = False  # Inicializamos una bandera

    if current_positions is None:
        current_positions = {}  # Inicializa si no se proporciona ningun diccionario

    # Definir o actualizar las current_positions con la posicion central actual de cada nodo
    for node in group_nodes:
        if node not in current_positions:
            current_x = node.xpos() + node.screenWidth() / 2
            current_y = node.ypos() + node.screenHeight() / 2
            current_positions[node] = (current_x, current_y)

    debug_print_F("\n                Aplicar el offset para las columnas secundarias si es necesario:")

    # 1 - Aplicar el offset para las columnas secundarias si es necesario
    found_issue = False  # Inicializar la bandera para determinar si hay un problema

    if offset_y != 0:
        bandera_distribucion = True  # Marcamos que ya se realizo la distribucion
        # Imprimir el valor de las tres variables
        #debug_print_E(f"Valor de subSubgroupOld: {subSubgroupOld}")
        #debug_print_E(f"Valor de offset_y: {offset_y}")
        #debug_print_E(f"Valor de no_subSubgroupOld: {no_subSubgroupOld}")
        #debug_message_D("pausa")

        # Verificar si subSubgroupOld tiene informacion y si el offset es positivo (movimiento hacia abajo)
        if subSubgroupOld and offset_y > 0:
            debug_print_E(f"       ******** Se detecto un subSubgroupOld y el offset es hacia abajo:")
            for node in group_nodes:
                if node in subSubgroupOld and not found_issue:
                    # Encontrar la posicion del nodo en subSubgroupOld
                    node_index = subSubgroupOld.index(node)

                    # Verificar si hay un nodo anterior en subSubgroupOld
                    if node_index > 0:
                        #debug_message_D("1")
                        previous_node = subSubgroupOld[node_index - 1]

                        # Calcular la nueva posicion Y del nodo
                        new_y_pos = current_positions[node][1] + offset_y
                        new_y_pos = node.ypos() + node.screenHeight() / 2 + offset_y
                        previous_node_y_pos = current_positions[previous_node][1] + previous_node.screenHeight()
                        previous_node_y_pos = previous_node.ypos() + previous_node.screenHeight() / 2 
                        #previous_node_y_pos = node['ypos'].value() + node.screenHeight() / 2 



                        # Imprimir los valores de new_y_pos y previous_node_y_pos junto con los nombres de los nodos
                        debug_print_E(f"                Nodo actual: '{node.name()}' | Posicion Y actual: {current_positions[node][1]} | Nueva posicion Y con offset: {new_y_pos}")
                        debug_print_E(f"                Nodo actual: '{node.name()}' | Posicion Y centrada actual: {node.ypos() + node.screenHeight() / 2} | Nueva posicion Y con offset: {new_y_pos}")
                        debug_print_E(f"                Nodo anterior: '{previous_node.name()}' | Posicion Y + Altura: {previous_node_y_pos}")

                        # Calcular e imprimir posiciones en Y del techo y base con offset aplicado
                        node_techo_y_offset = new_y_pos - (node.screenHeight() / 2)
                        node_base_y_offset = new_y_pos + (node.screenHeight() / 2)
                        previous_node_techo_y_offset = previous_node_y_pos - (previous_node.screenHeight() / 2)
                        previous_node_base_y_offset = previous_node_y_pos + (previous_node.screenHeight() / 2)

                        debug_print_E(f"                Techo nodo actual con offset '{node.name()}': {node_techo_y_offset} | Base: {node_base_y_offset}")
                        debug_print_E(f"                Techo nodo anterior con offset '{previous_node.name()}': {previous_node_techo_y_offset} | Base: {previous_node_base_y_offset}")

                        # Comprobar si la base del nodo actual con offset no supera el techo del nodo anterior con offset
                        if node_base_y_offset <= previous_node_techo_y_offset:
                            
                            debug_print_E(f"                '{node.name()}' se puede mover sin problema.")
                            #raise Exception(f"Abortando script: Se detecto una condicion no deseada en el nodo '{node.name()}'.")
                            
                            # Continuar con el bucle de offset
                            continue


                        else:
                            debug_print_E(f"                '{node.name()}' queda superpuesto o mas abajo que '{previous_node.name()}'.")
                            debug_print_E(f"                '{node.name()}' conectado a '{connected_node.name()}'.")
                            found_issue = True  # Activar la bandera para indicar que hay un problema
                            
                            # Calcular el tamano total en Y ocupado por los nodos desde el nodo que vamos a mover hasta el primero de subSubgroupOld
                            affected_nodes = subSubgroupOld[:node_index + 1]  # Lista de nodos afectados, de abajo hacia arriba
                            
                            # Ordenar los nodos por su posicion Y
                            affected_nodes.sort(key=lambda node: node.ypos())

                            first_node = affected_nodes[0]
                            last_node = affected_nodes[-1]

                            # Calcular el espacio total disponible entre el primer y ultimo nodo
                            total_length = last_node.ypos() - first_node.ypos() + last_node.screenHeight()
                            size_of_nodes = sum(node.screenHeight() for node in affected_nodes)
                            free_space = total_length - size_of_nodes

                            # Imprimir el resultado
                            debug_print_E(f"                    Nodos en sub Sub group Old hasta el que vamos a offsetear: {[n.name() for n in affected_nodes]}")
                            debug_print_E(f"                    Total en Y ocupado por todos estos nodos (sumando alturas): {size_of_nodes}")
                            debug_print_E(f"                    Total en Y disponible desde el techo del nodo mas alto a la base del nodo mas bajo: {total_length}")
                            debug_print_E(f"                    Espacio libre disponible para distribucion: {free_space}")
                            debug_print_E(f"                    Cantidad de pixeles a offsetear hacia abajo: {offset_y}")
                            #debug_message_D("Mover sin problema WTF??")

                            
                            # Comparacion entre el espacio libre y el offset
                            if offset_y > free_space:
                                extra_pixels = offset_y - free_space
                                debug_print_E(f"                    ** El offset es mayor que el espacio libre por {extra_pixels} pixeles.")
                                
                                # Llamar a la nueva funcion para distribuir con el espacio libre disponible
                                distribute_vert_with_fixed_space(affected_nodes, 10)
                                
                                # Calcular la nueva posicion de Y del nodo conectado de esta columna
                                node_y = node.ypos() + node.screenHeight() / 2  # Actualizar la posicion de Y del nodo despues de la distribucion
                                
                                # Imprimir la nueva posicion del nodo conectado de esta columna
                                debug_print_E(f"                    ** Nueva posicion centrada en Y del nodo '{node.name()}': {node_y}")
                                
                                # Mover el 'connected_node' de acuerdo con la nueva posicion centrada en Y del nodo conectado de esta columna
                                new_connected_y = node_y - connected_node.screenHeight() / 2
                                connected_node.setYpos(int(new_connected_y))
                                current_positions[connected_node] = (
                                    current_positions[connected_node][0],  # Centro horizontal
                                    new_connected_y  # Nueva posicion en Y
                                )
                                debug_print_E(f"                    ** '{connected_node.name()}' se ha movido a centrarse en la nueva posicion Y de '{node.name()}'.")

                            else:
                                debug_print_E(f"                    ** El offset es menor o igual al espacio libre disponible.")
                                
                                # Calcular la posicion centrada actual del nodo
                                node_y = node.ypos() + node.screenHeight() / 2
                                
                                # Imprimir la posicion centrada actual del nodo
                                debug_print_E(f"                    ** Posicion centrada actual del nodo '{node.name()}': {node_y}")
                                
                                # Mover el 'connected_node' de acuerdo con la posicion centrada actual del nodo
                                new_connected_y = node_y - connected_node.screenHeight() / 2
                                connected_node.setYpos(int(new_connected_y))
                                current_positions[connected_node] = (
                                    current_positions[connected_node][0],  # Centro horizontal
                                    new_connected_y  # Nueva posicion en Y
                                )
                                debug_print_E(f"                    ** '{connected_node.name()}' se ha movido a centrarse en la posicion actual Y de '{node.name()}'.")


                    else:
                        debug_print_E(f"    {node.name()} no tiene un nodo anterior en subSubgroupOld.")
        


        # Bucle de offset normal solo si no se ha detectado un problema
        if not found_issue:
            #debug_message_D("3 pre offset")
            for node in group_nodes:
                old_new_y = round(node.ypos() + offset_y)
                # Obtener la posicion Y central actual desde current_positions
                current_currentY = current_positions[node][1]
                # Calcular la nueva posicion Y basada en el offset
                new_y_pos = round(current_currentY + offset_y)  # Este es el que se pasa a los valores current
                nodo_height = node.screenHeight() / 2
                new_y = round(current_currentY + offset_y - nodo_height)  # Este es el que se pasa para mover el nodo
                debug_print_F(f"\n                    Offset para el nodo {node.name()}")
                debug_print_F(f"                        Posicion current en Y actual {current_currentY}")
                debug_print_F(f"                        Nueva posicion current con offset: {current_currentY} + {offset_y} = {new_y_pos}")
                #debug_message_D(f"Pausa en el nodo: {node.name()}")

                node.setXYpos(round(node.xpos()), new_y)  # Actualiza la posicion Y del nodo

                # Actualizar las posiciones current despues de aplicar el offset
                current_x = current_positions[node][0] if node in current_positions else node.xpos() + node.screenWidth() / 2
                current_positions[node] = (
                    current_x,  # Centro horizontal
                    new_y_pos  # Centro vertical con el offset aplicado
                )
            #debug_message_D("3 post offset")

        if subSubgroupOld and offset_y < 0:   
            debug_print_E(f"       ******** Se detecto un subSubgroupOld y el offset es hacia arriba:")
            debug_print_E(f"       ******** Nodos que se mandan a distribuir: {[node.name() for node in subSubgroupOld]}")
            debug_print_E(f"                '{node.name()}' conectado a '{connected_node.name()}'.")
            #debug_message_D(f"Nodos que se mandan a distribuir: {[node.name() for node in subSubgroupOld]}")
            distribute_vertically(subSubgroupOld)
            bandera_distribucion = True  # Marcamos que ya se realizo la distribucion


    else:
        debug_print_F("                    No es necesario")
        #debug_message_D("no es necesario")


    # 2 - Distribuir en caso de que haya mas de 2 nodos en el grupo / columna
    if len(group_nodes) > 2 and not bandera_distribucion:

        distribute_vertically(group_nodes)  # Llamado a la funcion para distribuir verticalmente

        # Actualizar current_positions despues de la distribucion
        for node in group_nodes:
            current_positions[node] = (node.xpos() + node.screenWidth() / 2, node.ypos() + node.screenHeight() / 2)

    return current_positions  # Retorna el diccionario actualizado

def distribute_vert_with_fixed_space(nodes, free_space):
    # Ordenar los nodos por su posicion Y de abajo hacia arriba
    nodes.sort(key=lambda node: node.ypos(), reverse=True)
    #debug_message_D("Antes de distribuir")
    # Imprimir informacion de la distribucion
    debug_print_E(f"                    Distribuyendo verticalmente con espacio fijo:")
    debug_print_E(f"                    Total de nodos a distribuir: {len(nodes)}")
    debug_print_E(f"                    Espacio libre total: {free_space}")

    # Calcular el espacio disponible entre nodos
    if len(nodes) > 1:
        space_between_nodes = free_space / (len(nodes) - 1)
    else:
        space_between_nodes = 0

    debug_print_E(f"                    Espacio calculado entre nodos: {space_between_nodes} pixeles")

    # Mover los nodos verticalmente con espacio fijo
    current_y = nodes[0].ypos()  # Posicion Y del primer nodo (mas bajo)
    for i in range(1, len(nodes)):
        previous_node = nodes[i - 1]
        current_node = nodes[i]

        # Guardar la posicion original del nodo actual
        original_y = current_node.ypos()

        # Calcular la nueva posicion Y para el nodo actual, moviendo hacia arriba (negativo en Y)
        # El techo del nodo actual debe estar en el piso del nodo anterior mas el espacio calculado
        current_y = previous_node.ypos() - current_node.screenHeight() - space_between_nodes
        current_node.setYpos(int(current_y))

        # Imprimir el resultado del movimiento con la posicion original y la nueva
        debug_print_E(f"                    Nodo '{current_node.name()}' movido de Y={int(original_y)} a Y={int(current_y)}")

def distribute_vertically(nodes):
    nodes = [n for n in nodes if n.Class() != "BackdropNode"]  # Filtra los backdrops

    if len(nodes) < 2:
        return  # No hay suficientes nodos para distribuir

    # Ordenar los nodos por su posicion Y
    nodes.sort(key=lambda node: node.ypos())

    first_node = nodes[0]
    last_node = nodes[-1]

    # Calcular el espacio total disponible entre el primer y ultimo nodo
    total_length = last_node.ypos() - first_node.ypos() + last_node.screenHeight()
    size_of_nodes = sum(node.screenHeight() for node in nodes)
    free_space = total_length - size_of_nodes

    # Almacenar las posiciones iniciales de cada nodo
    initial_positions = {node: node.ypos() for node in nodes}

    debug_print_E("\n                _______________-----______________")
    debug_print_E("\n                Distribuyendo nodos verticalmente:\n")
    debug_print_E(f"                    Total en Y ocupado por todos los nodos (sumando alturas): {size_of_nodes}")
    debug_print_E(f"                    Total en Y disponible desde el techo del nodo mas alto a la base del nodo mas bajo: {total_length}")
    debug_print_E(f"                    Espacio libre disponible para distribucion: {free_space}\n")
    
    debug_print_E(f"                {'Nodo':<20}{'Y Posicion Inicial':<20}{'Y Posicion Final':<20}")

    # Imprimir el primer nodo antes del bucle
    final_y_first = initial_positions[first_node]  # En este caso la posicion final sera igual a la inicial
    debug_print_E(f"                {first_node.name():<20}{initial_positions[first_node]:<20}{final_y_first:<20}")

    if free_space < 0:
        increment = 0
    else:
        increment = free_space / (len(nodes) - 1)

    current_y = first_node.ypos() + first_node.screenHeight()

    for i, node in enumerate(nodes):
        if i == 0 or i == len(nodes) - 1:
            continue
        current_y += increment
        node.setYpos(int(current_y))
        final_y = node.ypos()
        debug_print_E(f"                {node.name():<20}{initial_positions[node]:<20}{final_y:<20}")  # Imprimir la posicion inicial y final despues de la distribucion
        current_y += node.screenHeight()

    # Imprimir el ultimo nodo despues del bucle
    final_y_last = initial_positions[last_node]  # En este caso la posicion final sera igual a la inicial
    debug_print_E(f"                {last_node.name():<20}{initial_positions[last_node]:<20}{final_y_last:<20}")

def subdivide_column(group_nodes):
    # Divide a cada columna en subgrupos. Cada subgrupo se compone de nodos que estan conectados entre si.
    # Ordenar los nodos de abajo hacia arriba
    sorted_nodes = sorted(group_nodes, key=lambda n: n.ypos(), reverse=True)
    subgroups = []
    current_subgroup = []
    subgroup_number = 1

    for node in sorted_nodes:
        connected_nodes = [node.input(i) for i in range(node.inputs()) if node.input(i)]

        if not connected_nodes:
            if current_subgroup:
                current_subgroup.append(node)  # agrega el nodo actual al subgrupo actual
                subgroups.append(current_subgroup.copy())  # agrega una copia del subgrupo actual a subgroups
                subgroup_number += 1
                current_subgroup = []  # Empieza un nuevo subgrupo vacio
            else:
                subgroups.append([node])
        else:
            for connected_node in connected_nodes:
                if not current_subgroup or any(connected_node in subgroup for subgroup in subgroups):
                    current_subgroup.append(node)
                    break
            else:
                current_subgroup.append(node)

    if current_subgroup:
        subgroups.append(current_subgroup)

    return subgroups

def is_connected_to_any_node(check_node, nodes_set):
    # Verifica y detalla si alguna de las entradas de los nodos en nodes_set coincide con check_node.
    # y despues verifica si alguna de las entradas del check_node coincide con alguno de los nombres en nodes_set
    # De esta forma verifica conexiones de entrada y de salida del check_node con alguno del nodes_set

    for node in nodes_set:
        has_input = False

        for i in range(node.inputs()):
            input_node = node.input(i)
            if input_node:
                has_input = True
                if input_node.name() == check_node.name():
                    return True

        if not has_input:
            pass

    node_set_names = {node.name() for node in nodes_set}

    for i in range(check_node.inputs()):
        input_node = check_node.input(i)
        if input_node and input_node.name() in node_set_names:
            return True

    return False

def subdivide_column_and_get_heights(group_nodes):
    # Funcion para buscar la altura de todos los subgrupos de cada columna, 
    # y en base a eso luego se determina cual es la columna principal
    sorted_nodes = sorted(group_nodes, key=lambda n: n.ypos(), reverse=True)
    subgroups = []
    heights = []
    current_subgroup = []

    for node in sorted_nodes:
        connected_nodes = [node.input(i) for i in range(node.inputs()) if node.input(i)]
        if not connected_nodes:
            if current_subgroup:
                current_subgroup.append(node)
                subgroups.append(current_subgroup.copy())
                heights.append(max(current_subgroup, key=lambda n: n.ypos()).ypos() - min(current_subgroup, key=lambda n: n.ypos()).ypos())
                current_subgroup = []
        else:
            for connected_node in connected_nodes:
                if not current_subgroup or any(connected_node in subgroup for subgroup in subgroups):
                    current_subgroup.append(node)
                    break
            else:
                current_subgroup.append(node)

    if current_subgroup:
        subgroups.append(current_subgroup)
        heights.append(max(current_subgroup, key=lambda n: n.ypos()).ypos() - min(current_subgroup, key=lambda n: n.ypos()).ypos())

    return subgroups, heights

def align_nodes_in_column(nodes):
    # Calcular el centro X promedio de todos los nodos
    center_x_positions = [(node.xpos() + node.screenWidth() / 2) for node in nodes]
    average_center_x = sum(center_x_positions) / len(center_x_positions)

    # Alinear todos los nodos centrados en el promedio del centro X
    for n in nodes:
        new_x = int(average_center_x - (n.screenWidth() / 2))
        n.setXpos(new_x)

def node_center(node):
    return (node.xpos() + node.screenWidth() / 2, node.ypos() + node.screenHeight() / 2)

def store_original_positions(nodes, debug=True):
    # Almacenar posiciones originales
    original_positions = {
        node: (
            node.xpos() + node.screenWidth() / 2,  # Centro horizontal
            node.ypos() + node.screenHeight() / 2  # Centro vertical
        ) for node in nodes
    }

    # Si debug esta activado, imprimir posiciones originales
    if debug:
        debug_print_B("___________________________")
        debug_print_B("Posicion original de los nodos:")
        for node, pos in original_positions.items():
            debug_print_B(f"    {node.name():<20} | Posicion X: {pos[0]:<10} | Posicion Y: {pos[1]}")

    return original_positions

def organize_columns_and_find_principal(regular_nodes, original_positions, toleranciaX):
    # Crear columnGroups basados en la proximidad en X
    debug_print_B("___________________________")
    debug_print_B("\n++ Analizando que nodos pertenecen a cada columna:")
    columnGroups = defaultdict(list)


    for node in sort_nodes_by_position(regular_nodes):
        pos = original_positions[node][0]  # Usar la posicion X almacenada en original_positions
        found_group = False
        debug_print_B(f"    Procesando nodo {node.name():<20} | Posicion X: {pos:<10}")
        for group_pos in columnGroups.keys():
            distance = abs(pos - group_pos)
            debug_print_B(f"        Comparando con grupo en {group_pos:<10} | Distancia: {distance}")
            if distance <= toleranciaX:
                columnGroups[group_pos].append(node)
                found_group = True
                debug_print_B(f"        -> Agrupando {node.name()} en grupo {group_pos}")
                break
        if not found_group:
            columnGroups[pos].append(node)
            debug_print_B(f"        -> Creando nuevo grupo para {node.name()} en posicion {pos}")

    # Determinar la altura de cada grupo y encontrar la columna (grupo) principal
    columnGroupHeights = {}
    for group_pos, nodes in columnGroups.items():
        highest_node = max(nodes, key=lambda n: n.ypos())
        lowest_node = min(nodes, key=lambda n: n.ypos())
        columnGroupHeights[group_pos] = highest_node.ypos() - lowest_node.ypos()

    max_height = 0
    principalGroup = None

    for group_pos, group_nodes in columnGroups.items():
        subgroups, subgroup_heights = subdivide_column_and_get_heights(group_nodes)
        local_max_height = max(subgroup_heights, default=0)
        
        if local_max_height > max_height:
            max_height = local_max_height
            principalGroup = group_pos

    # Verifica si la principalGroup es None
    if principalGroup is None:
        debug_print_C("No se encontro una columna principal.")
        return None, None, None, None, None  # Retornar 5 valores None

    # Numerar columnas secundarias segun su distancia a la principal
    column_order = sorted(columnGroups.keys())
    principal_index = column_order.index(principalGroup)
    
    # Guardando lista con nombre de la columna segun su posicion en X y su numero de indice en cercania a la principal
    column_numbers = {pos: idx - principal_index for idx, pos in enumerate(column_order)} 

    # Imprimir la numeracion y los nodos de cada columna
    debug_print_C("___________________________")
    debug_print_C("\nColumnas con sus Nodos Contenidos:")
    for pos, index in column_numbers.items():
        nodes_in_column = [node.name() for node in columnGroups[pos]]
        debug_print_C(f"    Columna {pos:<10} (Num: {index:<3}) | Nodos: {nodes_in_column}")

    # Ordenar las posiciones de las columnas en base a su distancia relativa
    sorted_column_positions = sorted(columnGroups.keys(), key=lambda x: (abs(column_numbers[x]), column_numbers[x]))

    return columnGroups, columnGroupHeights, principalGroup, sorted_column_positions, column_numbers

def main():
    # Obtener nodos seleccionados
    selected_nodes = nuke.selectedNodes()
    
    # Verificar si hay menos de 2 nodos seleccionados
    if len(selected_nodes) < 2:
        nuke.message("Select at least 2 nodes to arrange")
        return

    # Iniciar el undo
    undo = nuke.Undo()
    undo.begin("Arrange Nodes")

    # Crear una lista con todos los nodos seleccionados que no sean backdrops ni viewers
    regular_nodes = [node for node in selected_nodes if node.Class() not in ["BackdropNode", "Viewer"]]


    # Paso A: Almacenar posiciones originales
    original_positions = store_original_positions(regular_nodes)

    # Paso B: Agrupar nodos en columnas segun su proximidad en X, identificar la columna principal y ordenar las columnas secundarias
    columnGroups, columnGroupHeights, principalGroup, sorted_column_positions, column_numbers = organize_columns_and_find_principal(regular_nodes, original_positions, toleranciaX)

    # Verificar si no hay columna principal antes de continuar
    if principalGroup is None:
        undo.end()
        return

    # Numeracion de grupos y columnas
    numerated_groups = {pos: idx for idx, pos in enumerate(sorted_column_positions)}
    sorted_numerated_groups = sorted(numerated_groups.items(), key=lambda x: x[1])    

    # Paso C: Alinea y distribuir la columna principal y almacenar las posiciones current.
    current_positions = original_positions
    for group_pos in sorted_column_positions:
        if group_pos == principalGroup:
            debug_print_C("\n___________________________")
            debug_print_C("\nColumna Principal:")

            distribute_columns(columnGroups[group_pos], toleranciaY, 0, current_positions, None, None)
            align_nodes_in_column(columnGroups[group_pos])  # Alinear los nodos a la derecha   

            # Filtrar para obtener solo los nodos en la columna principal de original_positions
            principal_nodes_positions = {node: pos for node, pos in original_positions.items() if node in columnGroups[group_pos]}
            # Identificar el nodo con la posicion en Y mas baja (mas alto en la pantalla) entre los nodos de la columna principal
            topTopNode = min(principal_nodes_positions, key=lambda node: principal_nodes_positions[node][1])
            topTopNodeY = principal_nodes_positions[topTopNode][1]
            debug_print_C(f"    Nodo mas alto en la columna principal: {topTopNode.name()} | Posicion Y: {principal_nodes_positions[topTopNode][1]}")


    # Paso D: Ajustar y distribuir columnas secundarias.
    """
    Las columnas secundarias vamos a dividirlas en:
        Subgrupos: Partes de esta columna compuestas por nodos conectados entre si.
        SubSubGrupos: Son partes del Subgrupo. Son temporales. Se buscan de abajo hacia arriba los nodos conectados con otra columna.
                     Cuando se encuentra alguno, se genera un subsubgrupo desde este nodo hacia el mas alto del subgrupo.
        SubSubGruposOld: Es una variable temporal que guarda al subsubgrupo anterior. Se crea para generar una nueva distribucion
                         de este luego de haber offseteado el nodo inferior del subsubgrupo.
        Potential_columns: incluye a la columna principal y todas las columnas entre la columna actual y la principal.
                             
        Antes de aplicar el offset y distribucion del subsubgrupo nuevo, tenemos que ver si existe un SubSubGruposOld.
        Si existe, tenemos que evaluar cual sera el valor para el lowest_node con offset de align. 
        Este valor lo tomaremos viendo el current_position del nodo + el offset_y. 
        Lo almacenaremos en una variable llamada lowest_temp_y.
        Esto nos dara el valor en Y al que quedara este lowest_node luego de su distribucion con offset.

        Luego, tendremos que analizar cuales son los nodos del SubSubGruposOld. Y de arriba hacia abajo hacer lo siguiente:
        Al mas alto, no lo moveremos (porque es el mismo nodo que el lowest_node del subsubgroup).
        Al que le siga, lo moveremos 10 pixeles hacia abajo del valor lowest_temp_y (es decir lowest_temp_y + 10).
        Al que le siga, lo moveremos 10 pixeles * 2 hacia abajo del valor lowest_temp_y (es decir lowest_temp_y + 10*2).
        Y asi hasta llegar al mas bajo del Old, al que no moveremos.
    """
    for group_pos, group_nodes in columnGroups.items():
        if group_pos == principalGroup:
            continue  # Omitir la columna principal

        # Obtener el indice desde column_numbers
        group_index = column_numbers[group_pos]

        # Subdividir la columna secundaria en subgrupos basados en las conexiones
        debug_print_D("\n___________________________")
        debug_print_D(f"\nColumna Secundaria {group_index} (index) en X {group_pos} con Nodos: {[node.name() for node in columnGroups[group_pos]]}")
        debug_print_D("\nVamos a dividirla en subgrupos:")
        subgroups = subdivide_column(group_nodes)  # Uso la funcion subdivide_column para dividir a la columna en subgrupos
        subSubgroupOld = None  # Inicializar la variable para guardar el subSubgrupo anterior

        for subgroup in subgroups:
            # Ordenar los nodos de este subgrupo de abajo hacia arriba y luego invertir para comenzar desde el mas bajo
            sorted_subgroup = sorted(subgroup, key=lambda n: n.ypos(), reverse=True)
            any_connected_node = False  # Variable para rastrear si se encontro alguna conexion en el subgrupo

            for node in sorted_subgroup:
                connected_node = None
                debug_print_D("\n   ----------------")
                debug_message_A("Click en OK nueva iteracion del bluce principal")
                # Crear una lista de columnas con potenciales nodos conectados al nodo actual
                # Incluye a la columna principal y todas las columnas entre la columna actual y la principal
                potential_columns = [columnGroups[principalGroup]]  # Siempre incluir la columna principal
                if column_numbers[group_pos] > 0:  # Si la columna actual esta a la derecha de la principal
                    potential_columns += [columnGroups[col] for col in sorted_column_positions if 0 <= column_numbers[col] < column_numbers[group_pos]]
                elif column_numbers[group_pos] < 0:  # Si la columna actual esta a la izquierda de la principal
                    potential_columns += [columnGroups[col] for col in sorted_column_positions if column_numbers[group_pos] < column_numbers[col] <= 0]

                # Verificar si este nodo esta conectado a algun nodo de las columnas potenciales
                for column in potential_columns:
                    for target_node in column:
                        # Usar la funcion is_connected_to_any_node para detectar si el node esta conectado al grupo de nodos target_node
                        if is_connected_to_any_node(node, [target_node]): 
                            connected_node = target_node
                            break
                    if connected_node:
                        break

                # Determinar las columnas que estan mas lejos de la principal que la columna actual
                next_columns = []
                if column_numbers[group_pos] > 0:  # Si la columna actual esta a la derecha de la principal
                    next_columns = [columnGroups[col] for col in sorted_column_positions if column_numbers[col] > column_numbers[group_pos]]
                elif column_numbers[group_pos] < 0:  # Si la columna actual esta a la izquierda de la principal
                    next_columns = [columnGroups[col] for col in sorted_column_positions if column_numbers[col] < column_numbers[group_pos]]

                # Imprimir la columna actual y las columnas que estan mas lejos de la principal
                debug_print_D("\n    Buscando conexion desde algun nodo de esta columna a alguno de una columna mas alejada de la principal:")

                if not next_columns:
                    debug_print_D("        No se encontraron.")
                else:
                    for col in next_columns:
                        debug_print_D(f"        Se encontro conexion a columna {col[0].name():<20} con los nodos {[node.name() for node in col]}")


                if connected_node:
                    any_connected_node = True

                    # Buscar la posicion en Y del connected_node
                    current_y_connected = current_positions[connected_node][1]

                    # Crear una lista plana de todos los nodos en potential_columns
                    node_set_potential = [node for column in potential_columns for node in column]
                    # Crear una lista plana de todos los nodos en next_columns
                    node_set_next = [node for column in next_columns for node in column]

                    # Llamar a la funcion que detecta si algun nodo de las potential column esta conectado a alguno de las next_columns
                    debug_print_D("\n    Buscando conexiones entre la columna principal y alguna columnas mas alejada que la actual: ")
                    next_connected_nodeY = is_connected_to_any_column(current_y_connected, node_set_potential, node_set_next, current_positions)
                    #debug_print_D(f"     Conexion a nodo en Y: {next_connected_nodeY}")

                    # Buscar el nodo conectado directamente en este subgroup comparando nombres
                    node_position = None
                    for i, sub_node in enumerate(subgroup):
                        if sub_node.name() == node.name():
                            node_position = i
                            break

                    debug_print_D(f"\n    Nodos en el subgrupo: {[node.name() for node in subgroup]}")

                    debug_print_D("\n    Buscando nodos conectados en este subgrupo:")

                    if node_position is not None:
                        debug_print_D(f"        -> Match encontrado. Nodo '{node.name()}' | Posicion vertical en la columna: {node_position}")
                        # Crear subSubgroup desde el nodo encontrado hacia arriba (hasta el final de la lista)
                        subSubgroup = subgroup[node_position:]
                        debug_print_D(f"        -> Nodos en el Sub Sub Grupo (aka desde este nodo hacia arriba): {[n.name() for n in subSubgroup]}")

                    else:
                        subSubgroup = subgroup
                        subSubgroupOld = None
                        debug_print_D(f"        == No se encontro un match para {node.name()} en el subgrupo.")

                    original_y_connected = original_positions[connected_node][1]
                    current_y = current_positions[node][1]
                    current_y_connected = current_positions[connected_node][1]
                    offset_y = current_y_connected - original_y_connected

                    # Aplicar offset a todo el subgrupo basado en la conexion encontrada
                    debug_print_D(f"\n    Offseteando el Sub Sub Grupo:")
                    debug_print_D(f"        Nodo '{node.name()}' | Conectado a: '{connected_node.name()}'")
                    debug_print_D(f"        Posicion Y original de '{connected_node.name()}' | Y: {original_y_connected}")
                    debug_print_D(f"        Posicion Y actual de '{connected_node.name()}' | Y: {current_y_connected}")
                    debug_print_D(f"        Offset Y sin align: {offset_y}")

                    debug_print_D(f"        Calculando el offset extra para alinear usando actual Y: {current_y}")
                    offset_align = original_y_connected - current_y
                    debug_print_D(f"        Offset necesario para align: {offset_align}")
                    offset_y += offset_align
                    debug_print_D(f"        Offset Y total incluyendo align: {offset_y}")

                    # Si ya existia un subSubgroupOld, entonces tenemos que fijarnos que los nodos de este queden
                    # todos por debajo del lowest_node del subsubgroup. Sino nos pueden quedar desordenados.
                    # Los mandamos a distribuir cerca uno de otro y despues los distribuimos bien
                    if subSubgroupOld:
                        debug_print_D(f"\n        Es sub Sub group Old")
                        lowest_temp_y = current_y_connected
                        connected_node_position = next((i for i, n in enumerate(subSubgroupOld) if n.name() == node.name()), None)
                        debug_print_D(f"        Posicion nodo conectado: {connected_node_position}")
                        debug_print_D(f"        Nombre nodo: '{node.name()}'")
                        if connected_node_position is not None:
                            # Crear subSubgroupOldTrim hasta el nodo conectado actual
                            subSubgroupOldTrim = subSubgroupOld[:connected_node_position + 1]
                            debug_print_D(f"            -> Nodos en sub Sub group Old Trim: {[n.name() for n in subSubgroupOldTrim]}")
                        else:
                            subSubgroupOldTrim = subSubgroupOld  # En caso de no encontrarlo, usamos el grupo completo

                        debug_print_D(f"            -> Distribuyendo sub Sub group Old Trim: {[n.name() for n in subSubgroupOldTrim]} | Debajo de {connected_node.name()} en {lowest_temp_y}")
                        distribute_subSubgroupOld(subSubgroupOldTrim, lowest_temp_y, current_positions)

                        debug_print_F("\n                ________________===========______________")

                        debug_print_D(f"            -> Distribuyendo sub Sub group CON OLD: {[n.name() for n in subSubgroupOldTrim]}")
                        #debug_message_D("> Distribuyendo sub Sub group CON OLD")
                        distribute_columns(subSubgroup, toleranciaY, offset_y, current_positions, subSubgroupOldTrim, connected_node)

                    else:
                        # Encontrar la posicion del connected_node en el subgroup
                        connected_node_position = next((i for i, n in enumerate(subgroup) if n.name() == node.name()), None)
                        debug_print_D(f"        Posicion nodo conectado en subgroup: {connected_node_position}")
                        debug_print_D(f"        Nombre nodo conectado: '{connected_node.name()}'")
                        
                        if connected_node_position is not None:
                            # Crear subgroupTrim hasta el nodo conectado actual
                            subgroupTrim = subgroup[:connected_node_position + 1]
                            debug_print_D(f"            -> Nodos en subgroup Trim: {[n.name() for n in subgroupTrim]}")
                        else:
                            subgroupTrim = subgroup  # En caso de no encontrarlo, usamos el grupo completo

                        debug_print_F("\n                ________________===========______________")
                        debug_print_D(f"            -> Distribuyendo sub Sub group SIN OLD usando subgroupTrim: {[n.name() for n in subgroupTrim]}")
                        #debug_message_D("Distribuyendo sub Sub group SIN OLD usando subgroupTrim")
                        distribute_columns(subSubgroup, toleranciaY, offset_y, current_positions, subgroupTrim, connected_node)




                    """
                    if subSubgroupOld:
                        # Buscar la posicion del nodo actualmente conectado en subSubgroupOld
                        connected_node_position = next((i for i, n in enumerate(subSubgroupOld) if n.name() == node.name()), None)
                        debug_print_D(f"        Posicion nodo conectado: {connected_node_position}")
                        debug_print_D(f"        Nombre nodo: '{node.name()}'")
                        if connected_node_position is not None:
                            # Crear subSubgroupOldTrim hasta el nodo conectado actual
                            subSubgroupOldTrim = subSubgroupOld[:connected_node_position + 1]
                            debug_print_D(f"        -> Nodos en subSubgroupOldTrim: {[n.name() for n in subSubgroupOldTrim]}")
                        else:
                            subSubgroupOldTrim = subSubgroupOld  # En caso de no encontrarlo, usamos el grupo completo

                        debug_print_D(f"        -> Distribuyendo sin offset subSubgroupOldTrim: {[n.name() for n in subSubgroupOldTrim]}")
                        distribute_columns(subSubgroupOldTrim, toleranciaY, 0, current_positions)
                    """

                    subSubgroupOld = subSubgroup  # Guardar el subSubgrupo actual para la proxima iteracion
                    debug_print_D(f"\n            -> Se guardo sub Sub group Old: {[n.name() for n in subSubgroupOld]}")

                else:  # Si no hay mas nodos conectados
                    """
                    Si no encontramos mas nodos conectados, tenemos que hacer un chequeo de los nodos de abajo hacia arriba (esto pasa automaticamente)
                    y ver si el ultimo nodo no conectado supera en altura (o sea su valor de Y es menor) al nodo mas alto de la columna principal.
                    En ese caso vamos a mandar a distribuir con distribute_lastSubSubgroupOld.
                    """
                    if subSubgroupOld is not None and len(subSubgroupOld) > 0:
                        if node == subSubgroupOld[-1]:  # Verificamos si es el ultimo nodo del subSubgroupOld
                            debug_print_D("\n   ==============================")
                            debug_print_D("\n   Chequeos finales en la columna")
                            debug_print_D("\n     Chequeando si el nodo mas alto esta mas arriba que el mas alto de la columna principal:")
                            debug_print_D(f"        Nodo '{node.name()}' | Es el ultimo del subSubgroupOld (y no esta conectado).")
                            
                            # Verificamos si este nodo no este mas alto que el topTopNode
                            if current_positions[node][1] < topTopNodeY:
                                debug_print_D(f"        Nodo '{node.name()}' | Y: {current_positions[node][1]:<10} | Esta mas alto que el topTopNodeY: {topTopNodeY}")
                                # Los tenemos que mandar a distribuir cerca uno de otro y despues los distribuimos bien
                                
                                debug_message_B("Click en OK 1")
                                #distribute_lastSubSubgroupOld(subSubgroupOld, topTopNodeY, current_positions)
                            else:
                                debug_print_D(f"        Nodo '{node.name()}' | Y: {current_positions[node][1]:<10} | NO esta mas alto que el topTopNodeY: {topTopNodeY}")
                            """
                            Si es el ultimo nodo, tambien tenemos que chequear que su altura no sea mayor al nodo siguiente en altura.
                            """
                            debug_print_D("\n     Chequeando que la altura no sea mayor al nodo siguiente en altura:")
                            debug_print_D(f"        Next_connected_nodeY: {next_connected_nodeY}")
                            debug_print_D(f"        Current_positions[node][1]: {current_positions[node][1]}")
                            current_node_y_margin = current_positions[node][1] - 30
                            if next_connected_nodeY is not None and current_node_y_margin < next_connected_nodeY:
                                debug_print_D(f"        Nodo '{node.name()}' | Y: {current_node_y_margin:<10} (incluye margen de 30) | Esta mas alto que next_connected_nodeY: '{next_connected_nodeY}'")
                                # Los tenemos que mandar a distribuir cerca uno de otro y despues los distribuimos bien
                                
                                debug_message_B("Click en OK 2")
                                distribute_lastSubSubgroupOld(subSubgroupOld, next_connected_nodeY, current_positions)
                        else:
                            debug_print_D(f"        Nodo '{node.name()}' sin conexion.")
                        debug_print_D(f"        Nodos en subSubgroupOld: {[n.name() for n in subSubgroupOld]}")

            if not any_connected_node:
                debug_print_D("        No conectados.")
                distribute_columns(subgroup, toleranciaY, 0, current_positions, None, None)  # Distribuir si no se encontraron conexiones

            debug_print_D("\n    Alineando en X centrado")
            align_nodes_in_column(subgroup)  # Alinear los nodos en X centrado despues de la distribucion

    undo.end()



# Llamar a la funcion principal
#main()
