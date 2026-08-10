"""
______________________________________________________________

  LGA_arrangeNodes v1.13 | 2024 | Lega
 
  Align and distribute multiple columns based on connections 

______________________________________________________________

"""

import nuke
from collections import defaultdict

# Variable global para la tolerancia en X
TOLERANCIA_X = 50

# Variable global para activar o desactivar los prints
DEBUG = {
    'B': False,   # find_main_column
    'A': False,   # Armando GR1 con columna principal
    'C': False,   # Armando GR2 y GR1 nuevos
    'D': False,   # Sort numerated groups
    'E': False,   # Arrange nodes
    'E1': False,  # align_connected_and_master
    'F': False,   # align_parent_to_first_or_last
    'F1': False,  # align_parent_to_first_or_last en la parte de find_parent_connected_nodes_vertically
    'G': False,   # distribute_nodes_in_column
    'H': False,   # extract_group_name_parts    
    'I': False,   # rename_group_names_by_proximity        
    'J': False,   # sort_columns_overlapping_nodes        
    'R': False    # Resultados de nuevos Grupos y nodos en columna principal
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

def debug_print_E1(*message):
    if DEBUG['E1']:
        print(' '.join(str(m) for m in message))        

def debug_print_F(*message):
    if DEBUG['F']:
        print(' '.join(str(m) for m in message))        

def debug_print_F1(*message):
    if DEBUG['F1']:
        print(' '.join(str(m) for m in message))     

def debug_print_G(*message):
    if DEBUG['G']:
        print(' '.join(str(m) for m in message))        

def debug_print_H(*message):
    if DEBUG['H']:
        print(' '.join(str(m) for m in message))        

def debug_print_I(*message):
    if DEBUG['I']:
        print(' '.join(str(m) for m in message))        

def debug_print_J(*message):
    if DEBUG['J']:
        print(' '.join(str(m) for m in message))        

def debug_print_R(*message):
    if DEBUG['R']:
        print(' '.join(str(m) for m in message))        


# Variable global para activar o desactivar los mensajes
DEBUG_MESSAGE = {
    'A': False,      # sort_parent_overlapping_nodes
    'B': False,      # Arranging grupo
    'C': False,      # arrange, align_connected y distribute_Groups
    'D': False,      # Compensar en el distribute groups
    'E': False,       # align_parent_to_first_or_last
    'F': False       # sort_columns_overlapping_nodes    
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

def debug_message_E(*message):
    if DEBUG_MESSAGE['E']:
        nuke.message(' '.join(str(m) for m in message))

def debug_message_F(*message):
    if DEBUG_MESSAGE['F']:
        nuke.message(' '.join(str(m) for m in message))

## Funciones para encontrar la columna principal

def distribute_Groups(sorted_numerated_groups, numerated_groups, selected_nodes):
    debug_print_G("\n\n_________________________________________________________________________________")
    debug_print_G("++Distribute GRs:\n")

    # Procesar cada grupo numerado en el orden proporcionado
    for group_name in sorted_numerated_groups:
        nodes = numerated_groups[group_name]
        debug_print_G(f"\n  Distribuyendo grupo: {group_name}")
        
        # Llamar a distribute_nodes_in_column para cada grupo
        distribute_nodes_in_column(selected_nodes, nodes, called_from_distribute_Groups=True, numerated_groups=numerated_groups, sorted_numerated_groups=sorted_numerated_groups)

    debug_print_G("Distribucion de todos los GRs completada.\n")

def subdivide_column_and_get_heights(group_nodes):
    # Funcion para buscar la altura de todos los subgrupos de cada columna, 
    # y en base a eso luego se determinar cual es la columna principal
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

def find_main_column(nodes):
    original_positions = {
        node: (
            node.xpos() + node.screenWidth() / 2,  # Centro horizontal
            node.ypos() + node.screenHeight() / 2  # Centro vertical
        ) for node in nodes
    }

    debug_print_B("\n\n\n_________________________________________________________________________________\n")
    debug_print_B("Posicion original de todos los nodos seleccionados:\n")
    for node, pos in original_positions.items():
        debug_print_B(f"{node.name()}: Posicion X = {pos[0]}, Posicion Y = {pos[1]}")

    # Crear columnGroups basados en la proximidad en X
    debug_print_B("\n\n_________________________________________________________________________________\n")
    debug_print_B("Analizando que nodos pertenecen a cada columna:\n")
    columnGroups = defaultdict(list)

    sorted_nodes = sorted(nodes, key=lambda n: (n.xpos() + n.screenWidth() / 2, n.ypos()))
    for node in sorted_nodes:
        pos = original_positions[node][0]  # Usar la posicion X centrada
        found_group = False
        for group_pos in columnGroups.keys():
            distance = abs(pos - group_pos)
            if distance <= TOLERANCIA_X:
                columnGroups[group_pos].append(node)
                found_group = True
                debug_print_B(f"Agrupando {node.name()} en el grupo llamado: {group_pos}")
                break
        if not found_group:
            columnGroups[pos].append(node)
            debug_print_B(f"\nCreando nuevo grupo para columna de {node.name()} con nombre {pos}")

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
        debug_print_B("No se encontro una columna principal.")
        return None, None, None, None

    return columnGroups, columnGroups[principalGroup], principalGroup, original_positions


def extract_group_name_parts(group_name):
    if len(group_name) < 7:  # Asegurarse de que el nombre del grupo tenga al menos el prefijo y un nombre de nodo
        debug_print_H(f"Error en extract_group_name_parts: Nombre del grupo demasiado corto: {group_name}")
        return None, None, None, None, None, None  # En caso de que el formato no sea el esperado, devolver None

    if '_' not in group_name:
        debug_print_H(f"Error en extract_group_name_parts: Falta guion bajo en el nombre del grupo: {group_name}")
        return None, None, None, None, None, None  # En caso de que el formato no sea el esperado, devolver None

    split_index = group_name.find('_')
    prefix = group_name[:split_index]
    remaining_name = group_name[split_index + 1:]

    debug_print_H(f"         Prefijo: {prefix}, Nombre restante: {remaining_name}")

    if '-' not in remaining_name:
        debug_print_H(f"Error en extract_group_name_parts: Falta guion medio en el nombre restante: {remaining_name}")
        return prefix, remaining_name, None, None, None, None  # En caso de que el formato no sea el esperado, devolver None

    connected_master = remaining_name.split('-')

    debug_print_H(f"         Partes despues de dividir por guion medio: {connected_master}")

    if len(connected_master) != 2:
        debug_print_H(f"Error en extract_group_name_parts: Formato del nombre del nodo MASTER no es el esperado: {remaining_name}")
        return prefix, remaining_name, None, None, None, None  # En caso de que el formato no sea el esperado, devolver None

    connected_name = connected_master[0]
    master_name = connected_master[1]

    debug_print_H(f"         Nombre del nodo CONNECTED: {connected_name}, Nombre del nodo MASTER: {master_name}")

    return prefix, remaining_name, connected_name, master_name, connected_name, master_name



## Encontrando grupos

def find_GR1(principal_nodes, selected_nodes):
    groups = defaultdict(list)
    visited_nodes = set()  # Registro de nodos visitados

    def explore_connections(node, group_name, current_x_pos, is_master, selected_nodes):
        if node in visited_nodes:
            return
        visited_nodes.add(node)  # Marcar el nodo como visitado

        # Analizar conexiones de entrada
        for input_index in range(node.inputs()):
            connected_node = node.input(input_index)
            if connected_node:
                debug_print_A(f"      Analizando conexion de entrada: {node.name()} -> {connected_node.name()}")

                if connected_node in principal_nodes:
                    debug_print_A(f"        {connected_node.name()} descartado: pertenece a la columna principal")
                    continue

                if connected_node not in selected_nodes:
                    debug_print_A(f"        {connected_node.name()} descartado: no esta en los nodos seleccionados")
                    continue

                if abs((connected_node.xpos() + connected_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) <= TOLERANCIA_X:
                    debug_print_A(f"        {connected_node.name()} esta en la misma columna")
                    if connected_node not in groups[group_name]:
                        if is_master:
                            debug_print_A(f"          MASTER encontrado: {connected_node.name()}")
                        debug_print_A(f"          {connected_node.name()} agregado al grupo {group_name}")
                        groups[group_name].append(connected_node)
                        # Actualizar current_x_pos al centro del nodo conectado
                        current_x_pos = connected_node.xpos()
                        explore_connections(connected_node, group_name, current_x_pos, False, selected_nodes)
                else:
                    connected_center_x = connected_node.xpos() + connected_node.screenWidth() / 2
                    current_center_x = current_x_pos + node.screenWidth() / 2
                    difference = abs(connected_center_x - current_center_x)
                    debug_print_A(f"        {connected_node.name()} no esta en la misma columna. X de {connected_node.name()}: {connected_node.xpos()} (Centro: {connected_center_x}), comparado con {node.name()} en X: {node.xpos()} (Centro: {current_center_x}). Diferencia: {difference}")
                if is_master and abs((connected_node.xpos() + connected_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) > TOLERANCIA_X:
                    new_group_name = f"GR1-{node.name()}-{connected_node.name()}"
                    new_base_x_pos = connected_node.xpos()
                    if connected_node not in groups[new_group_name]:
                        debug_print_A(f"          {connected_node.name()} inicia nuevo grupo {new_group_name} con X = {new_base_x_pos}")
                        groups[new_group_name].append(connected_node)
                        explore_connections(connected_node, new_group_name, new_base_x_pos, True, selected_nodes)

                # Comprobar si hay otras conexiones dentro de los nodos seleccionados
                for input_index in range(node.inputs()):
                    next_connected_node = node.input(input_index)
                    if next_connected_node and next_connected_node in selected_nodes and next_connected_node != connected_node:
                        debug_print_A(f"        {next_connected_node.name()} es otro nodo seleccionado conectado a {node.name()}")
                        break
                else:
                    debug_print_A(f"        No hay mas conexiones seleccionadas para {node.name()}, deteniendo la busqueda.")
                    break


    def explore_output_connections_recursively(node, current_x_pos, group_name, selected_nodes):
        debug_print_A(f"      Explorando conexiones de salida recursivamente para {node.name()} en grupo {group_name}:")

        for output_node in node.dependent():
            if output_node:
                debug_print_A(f"        Analizando conexion de salida recursiva: {node.name()} -> {output_node.name()}")

                if output_node in principal_nodes:
                    debug_print_A(f"          {output_node.name()} descartado: pertenece a la columna principal")
                    continue

                if output_node not in selected_nodes:
                    debug_print_A(f"          {output_node.name()} descartado: no esta en los nodos seleccionados")
                    continue

                if abs((output_node.xpos() + output_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) <= TOLERANCIA_X:
                    debug_print_A(f"            {output_node.name()} esta en la misma columna")
                    if output_node not in groups[group_name]:
                        debug_print_A(f"          {output_node.name()} agregado al grupo {group_name}")
                        groups[group_name].append(output_node)
                        explore_connections(output_node, group_name, current_x_pos, False, selected_nodes)
                        explore_output_connections_recursively(output_node, current_x_pos, group_name, selected_nodes)
                    else:
                        debug_print_A(f"          {output_node.name()} ya esta en el grupo {group_name}")
                else:
                    debug_print_A(f"          {output_node.name()} no esta en la misma columna")

    def explore_output_connections(node, current_x_pos, selected_nodes):
        debug_print_A(f"  Explorando conexiones de salida para {node.name()}:")

        for output_node in node.dependent():
            if output_node:
                debug_print_A(f"    Analizando conexion de salida: {node.name()} -> {output_node.name()}")

                if output_node in principal_nodes:
                    debug_print_A(f"      {output_node.name()} descartado: pertenece a la columna principal")
                    continue

                if output_node not in selected_nodes:
                    debug_print_A(f"      {output_node.name()} descartado: no esta en los nodos seleccionados")
                    continue

                new_group_name = f"GR1-{node.name()}-{output_node.name()}"
                new_current_x_pos = output_node.xpos()
                debug_print_A(f"      Creando nuevo grupo basado en salida: {new_group_name} con base en {output_node.name()} (X = {new_current_x_pos})")

                # Verificar si el nodo MASTER ya pertenece a algun grupo
                master_exists = None
                for grp_name, grp_nodes in groups.items():
                    if output_node in grp_nodes:
                        master_exists = grp_name
                        break

                if output_node not in groups[new_group_name]:
                    debug_print_A(f"      {output_node.name()} agregado al grupo {new_group_name}")
                    groups[new_group_name].append(output_node)
                    explore_connections(output_node, new_group_name, new_current_x_pos, True, selected_nodes)
                    explore_output_connections_recursively(output_node, new_current_x_pos, new_group_name, selected_nodes)
                else:
                    debug_print_A(f"      {output_node.name()} ya esta en el grupo {new_group_name}")


    # Primero, buscar y crear todos los grupos basados en conexiones de entrada
    debug_print_A("\n_________________________________________________________________________________\n\n")
    debug_print_A("Buscando grupos basados en la columna principal (find_GR1):")
    for node in principal_nodes:
        group_name = f"GR1-{node.name()}"
        current_x_pos = node.xpos()  # Valor X del nodo principal
        debug_print_A(f"\n  Iniciando grupo {group_name} con base en {node.name()} (X = {current_x_pos})")
        debug_print_A(f"   CONNECTED: {node.name()}")
        explore_connections(node, group_name, current_x_pos, True, selected_nodes)

    for node in principal_nodes:
        debug_print_A(f"\nExplorando conexiones de salida para {node.name()}")
        explore_output_connections(node, node.xpos(), selected_nodes)

    return groups

def find_remaining_GR2(principal_nodes, selected_nodes, all_groups):
    # Combinar todos los nodos de los grupos existentes en una lista
    used_nodes = set(principal_nodes)
    for nodes in all_groups.values():
        used_nodes.update(nodes)
    
    # Imprimir los nodos usados
    debug_print_C("Nodos usados:")
    for node in used_nodes:
        debug_print_C(f"  {node.name()}")

    # Filtrar los nodos restantes
    #remaining_nodes = [node for node in selected_nodes if node not in used_nodes]

    #Solo descartamos a los de la columna principal y analizamos a todo el resto
    remaining_nodes = [node for node in selected_nodes if node not in principal_nodes]

    
    # Imprimir los nodos restantes
    debug_print_C("\nNodos restantes:")
    for node in remaining_nodes:
        debug_print_C(f"  {node.name()}")

    new_groups = defaultdict(list)
    visited_nodes = set()  # Registro de nodos visitados

    debug_print_C("\nGrupos en all_groups uno:")
    for grp_name in all_groups:
        debug_print_C(f"    {grp_name}")


    def explore_connections(node, group_name, current_x_pos):
        if node in visited_nodes:
            return
        visited_nodes.add(node)  # Marcar el nodo como
        
        debug_print_C(f"  Accediendo a explore_connections con {group_name}")
        # Imprimir los valores de new_groups y all_groups dentro de la funcion auxiliar
        debug_print_C("  (Dentro de explore_connections) Grupos en new_groups:")
        for grp_name in new_groups:
            debug_print_C(f"    {grp_name}")
        debug_print_C("  (Dentro de explore_connections) Grupos en all_groups:")
        for grp_name in all_groups:
            debug_print_C(f"    {grp_name}")
        
        # Analizar conexiones de entrada
        for input_index in range(node.inputs()):
            connected_node = node.input(input_index)
            if connected_node and connected_node in selected_nodes:
                debug_print_C(f"    Analizando conexion de ENTRADA de: {node.name()} desde-> {connected_node.name()}")
                if abs((connected_node.xpos() + connected_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) <= TOLERANCIA_X:
                    debug_print_C(f"        {connected_node.name()} esta en la misma columna")
                    if connected_node not in new_groups[group_name]:
                        # Verificar si el nodo ya pertenece a otro grupo
                        if any(connected_node in grp for grp in all_groups.values()):
                            debug_print_C(f"      {connected_node.name()} ya pertenece a otro grupo, deteniendo expansion")
                            return
                        debug_print_C(f"      {connected_node.name()} agregado al grupo {group_name}")
                        new_groups[group_name].append(connected_node)
                        # Actualizar current_x_pos al centro del nodo conectado
                        current_x_pos = connected_node.xpos()
                        explore_connections(connected_node, group_name, current_x_pos)
                    else:
                        # Convertir los nodos en new_groups[group_name] a sus nombres para imprimir
                        group_node_names = [n.name() for n in new_groups[group_name]]
                        debug_print_C(f"      Descartado porque el nodo {connected_node.name()} ya esta en un grupo con: {group_node_names}")
                else:
                    connected_center_x = connected_node.xpos() + connected_node.screenWidth() / 2
                    current_center_x = current_x_pos + node.screenWidth() / 2
                    difference = abs(connected_center_x - current_center_x)
                    debug_print_C(f"      {connected_node.name()} no esta en la misma columna. X de {connected_node.name()}: {connected_node.xpos()} (Centro: {connected_center_x}), comparado con {node.name()} en X: {node.xpos()} (Centro: {current_center_x}). Diferencia: {difference}")

        # Analizar conexiones de salida
        for output_node in node.dependent():
            if output_node and output_node in selected_nodes:
                debug_print_C(f"    Analizando conexion de SALIDA de: {node.name()} hacia-> {output_node.name()}")
                if abs(output_node.xpos() - current_x_pos) <= TOLERANCIA_X:
                    if output_node not in new_groups[group_name]:
                        # Verificar si el nodo ya pertenece a otro grupo
                        if any(output_node in grp for grp in all_groups.values()):
                            debug_print_C(f"      {output_node.name()} ya pertenece a otro grupo, deteniendo expansion")
                            return
                        debug_print_C(f"      {output_node.name()} agregado al grupo {group_name}")
                        new_groups[group_name].append(output_node)
                        # Actualizar current_x_pos al centro del nodo conectado
                        current_x_pos = output_node.xpos()
                        explore_connections(output_node, group_name, current_x_pos)

    for node in remaining_nodes:
        # Verificar si el nodo tiene una conexion directa en su input a un nodo que ya forme parte de un GR o de la columna principal
        for input_index in range(node.inputs()):
            connected_node = node.input(input_index)
            if connected_node and connected_node in used_nodes:
                # Verificar si ambos nodos ya pertenecen al mismo grupo
                already_in_same_group = any(node in grp and connected_node in grp for grp in all_groups.values())
                if already_in_same_group:
                    debug_print_C(f"  {node.name()} y {connected_node.name()} ya pertenecen al mismo grupo, descartando.")
                    continue            

                # Crear un nuevo grupo GR2
                group_name = f"GR2-{connected_node.name()}-{node.name()}"
                group_name_without_prefix = group_name[4:]

                # Verificar si el nombre del grupo ya existe
                debug_print_C(f"Verificando existencia del grupo {group_name}")

                # Imprimir los valores de new_groups y all_groups
                debug_print_C("  Grupos en new_groups:")
                for grp_name in new_groups:
                    debug_print_C(f"    {grp_name}")
                debug_print_C("  Grupos en all_groups:")
                for grp_name in all_groups:
                    debug_print_C(f"    {grp_name}")

                new_groups_without_prefix = [grp_name[4:] for grp_name in new_groups]
                all_groups_without_prefix = [grp_name[4:] for grp_name in all_groups]

                if group_name_without_prefix in new_groups_without_prefix:
                    debug_print_C(f"  El grupo {group_name} ya existe en new_groups, descartando.")
                    continue
                if group_name_without_prefix in all_groups_without_prefix:
                    debug_print_C(f"  El grupo {group_name} ya existe en all_groups, descartando.")
                    continue

                current_x_pos = node.xpos()  # Valor X del nodo
                debug_print_C(f"  Iniciando grupo {group_name} con base en {node.name()} (X = {current_x_pos})")
                new_groups[group_name].append(node)

                # Verificar si el nodo MASTER ya pertenece a algun grupo
                master_exists = any(node in grp for grp in all_groups.values())
                if master_exists:
                    debug_print_C(f"      {node.name()} ya pertenece a otro grupo, no se expandira mas")
                else:
                    explore_connections(node, group_name, current_x_pos)
                
                break  # Solo necesitamos encontrar una conexion valida para crear el grupo

    # Imprimir los nuevos grupos formados
    debug_print_C("Nuevos grupos GR2 formados:")
    for group_name, nodes in new_groups.items():
        debug_print_C(f"  {group_name}: {[node.name() for node in nodes]}")

    return new_groups

def find_remaining_GR1(principal_nodes, selected_nodes, all_groups):
    debug_print_C("\n_________________________________________________________________________________\n")
    debug_print_C("Buscando nuevos GR1")
    new_groups = defaultdict(list)

    # Obtener todos los nodos de MAIN, GR1 y GR2
    used_nodes = set(principal_nodes)
    for nodes in all_groups.values():
        used_nodes.update(nodes)
    debug_print_C("\n Estos son todos los grupos existentes hasta ahora:")
    for group_name, nodes in all_groups.items():
        debug_print_C(f"   {group_name} compuesto por estos nodos:")
        for node in nodes:
            debug_print_C(f"     {node.name()}: Posicion X = {node.xpos()}, Posicion Y = {node.ypos()}")
    debug_print_C("")

    # Filtrar los nodos que no pertenecen a MAIN, GR1 ni GR2
    nodes_without_GR = [node for node in selected_nodes if node not in used_nodes]

    debug_print_C(f"  Nodos sin GR (no en MAIN, GR1 ni GR2): {[node.name() for node in nodes_without_GR]}")

    temp_updated_all_groups = all_groups.copy()

    def explore_connections(node, group_name, current_x_pos):
        # Analizar conexiones de entrada
        for input_index in range(node.inputs()):
            connected_node = node.input(input_index)
            if connected_node:
                debug_print_C(f"   Analizando conexion de entrada: {node.name()} -> {connected_node.name()}")

                if connected_node not in selected_nodes:
                    debug_print_C(f"   {connected_node.name()} descartado: no esta en los nodos seleccionados")
                    continue

                if abs((connected_node.xpos() + connected_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) <= TOLERANCIA_X:
                    debug_print_C(f"        {connected_node.name()} esta en la misma columna")
                    if are_in_same_group(node, connected_node, temp_updated_all_groups):
                        debug_print_C(f"    {node.name()} y {connected_node.name()} ya estan en el mismo grupo, descartando.")
                        continue
                    if connected_node not in new_groups[group_name]:
                        debug_print_C(f"     {connected_node.name()} agregado al grupo {group_name}")
                        new_groups[group_name].append(connected_node)
                        current_x_pos = connected_node.xpos()  # Actualizar current_x_pos al centro del nodo conectado
                        explore_connections(connected_node, group_name, current_x_pos)
                        temp_updated_all_groups[group_name] = new_groups[group_name]
                else:
                    connected_center_x = connected_node.xpos() + connected_node.screenWidth() / 2
                    current_center_x = current_x_pos + node.screenWidth() / 2
                    difference = abs(connected_center_x - current_center_x)
                    debug_print_C(f"        {connected_node.name()} no esta en la misma columna. X de {connected_node.name()}: {connected_node.xpos()} (Centro: {connected_center_x}), comparado con {node.name()} en X: {node.xpos()} (Centro: {current_center_x}). Diferencia: {difference}")
                    new_group_name = f"GR1-{node.name()}-{connected_node.name()}"
                    new_base_x_pos = connected_node.xpos()
                    if connected_node not in new_groups[new_group_name]:
                        debug_print_C(f"   {connected_node.name()} inicia nuevo grupo {new_group_name} con X = {new_base_x_pos}")
                        new_groups[new_group_name].append(connected_node)
                        explore_connections(connected_node, new_group_name, new_base_x_pos)
                        temp_updated_all_groups[new_group_name] = new_groups[new_group_name]

    def are_in_same_group(node1, node2, all_groups):
        debug_print_C(f"    Verificando si {node1.name()} y {node2.name()} estan en el mismo grupo.")
        for group_name, group_nodes in all_groups.items():
            group_node_names = [node.name() for node in group_nodes]
            debug_print_C(f"      Revisando grupo: {group_name} con nodos: {', '.join(group_node_names)}")
            node1_in_group = node1 in group_nodes
            node2_in_group = node2 in group_nodes
            debug_print_C(f"        {node1.name()} esta en el grupo: {node1_in_group}")
            debug_print_C(f"        {node2.name()} esta en el grupo: {node2_in_group}")
            if node1_in_group and node2_in_group:
                debug_print_C(f"        {node1.name()} y {node2.name()} estan en el mismo grupo {group_name}.")
                return True
        debug_print_C(f"    {node1.name()} y {node2.name()} no estan en el mismo grupo.")
        return False

    def add_connected_nodes_recursively(node, group_name, current_x_pos):
        for input_index in range(node.inputs()):
            connected_node = node.input(input_index)
            if connected_node:
                debug_print_C(f"         Analizando recursivamente: {node.name()} -> {connected_node.name()}")
                if connected_node not in new_groups[group_name]:
                    if abs((connected_node.xpos() + connected_node.screenWidth() / 2) - (current_x_pos + node.screenWidth() / 2)) <= TOLERANCIA_X:
                        debug_print_C(f"        {connected_node.name()} esta en la misma columna (recursivo)")
                        debug_print_C(f"       {connected_node.name()} agregado al grupo {group_name} (recursivo)")
                        new_groups[group_name].append(connected_node)
                        current_x_pos = connected_node.xpos()  # Actualizar current_x_pos al centro del nodo conectado
                        add_connected_nodes_recursively(connected_node, group_name, current_x_pos)
                        temp_updated_all_groups[group_name] = new_groups[group_name]
                    else:
                        connected_center_x = connected_node.xpos() + connected_node.screenWidth() / 2
                        current_center_x = current_x_pos + node.screenWidth() / 2
                        difference = abs(connected_center_x - current_center_x)
                        debug_print_C(f"        {connected_node.name()} no esta en la misma columna. X de {connected_node.name()}: {connected_node.xpos()} (Centro: {connected_center_x}), comparado con {node.name()} en X: {node.xpos()} (Centro: {current_center_x}). Diferencia: {difference}")

    def group_exists(group_name, all_groups):
        # Verificacion de longitud minima
        if len(group_name) < 7:
            debug_print_C(f"ERROR: El nombre del grupo '{group_name}' es demasiado corto.")
            return False

        # Eliminar los primeros 4 caracteres del nombre
        remaining_name = group_name[4:]

        # Verificar que el nombre restante contiene solo un '-'
        if remaining_name.count('-') != 1:
            debug_print_C(f"ERROR: El nombre del grupo '{group_name}' contiene un numero incorrecto de guiones '-'.")
            return False

        # Separar el nombre en CONNECTED y MASTER
        connected_name, master_name = remaining_name.split('-')

        debug_print_C(f"            Comparando grupo nuevo en group_exists: {group_name} con CONNECTED: {connected_name} y MASTER: {master_name}")

        # Comprobar si ya existe un grupo con los mismos nodos (sin importar el orden)
        for existing_group_name in all_groups.keys():
            if len(existing_group_name) < 7:
                debug_print_C(f"ERROR: El nombre del grupo existente '{existing_group_name}' es demasiado corto.")
                continue

            existing_remaining_name = existing_group_name[4:]

            if existing_remaining_name.count('-') != 1:
                debug_print_C(f"ERROR: El nombre del grupo existente '{existing_group_name}' contiene un numero incorrecto de guiones '-'.")
                continue

            existing_connected_name, existing_master_name = existing_remaining_name.split('-')

            debug_print_C(f"            Comparando contra grupo existente en group_exists: {existing_group_name} con CONNECTED: {existing_connected_name} y MASTER: {existing_master_name}")

            # Verificar si los nombres de los nodos coinciden, sin importar el orden
            if (connected_name == existing_connected_name and master_name == existing_master_name) or \
               (connected_name == existing_master_name and master_name == existing_connected_name):
                debug_print_C(f"Grupo similar encontrado: {group_name} es similar a {existing_group_name}")
                return True

        return False

    # Recorrer todos los grupos en all_groups
    debug_print_C("  \nVamos a empezar a recorrer todos los grupos:")
    for group_nodes in all_groups.values():
        debug_print_C(f"    Revisando el grupo compuesto por: {[node.name() for node in group_nodes]}")
        for node in group_nodes:
            debug_print_C(f"       Analizando conexiones del nodo: {node.name()}")
            for input_index in range(node.inputs()):
                connected_node = node.input(input_index)
                if connected_node:
                    # Verificar si el connected_node esta en selected_nodes
                    if connected_node not in selected_nodes:
                        debug_print_C(f"         {connected_node.name()} descartado: no esta en los nodos seleccionados")
                        continue
                    else:
                        debug_print_C(f"         {connected_node.name()} esta en los nodos seleccionados")

                    debug_print_C(f"         Conexion encontrada: {node.name()} -> {connected_node.name()}")
                    if not are_in_same_group(node, connected_node, all_groups):
                        debug_print_C(f"         No pertenecen al mismo grupo")

                        group_name = f"GR1-{node.name()}-{connected_node.name()}"
                        if group_exists(group_name, all_groups):
                            debug_print_C(f"         No iniciamos el grupo {group_name} porque ya existe uno similar")
                        else:
                            # Verificar si el nodo CONNECT ya es el nodo CONNECT de otro grupo
                            debug_print_C(f"            Comparando grupo nuevo: {group_name} con CONNECTED: {connected_node.name()} y MASTER: {node.name()}")
                            for existing_group_name in all_groups.keys():
                                existing_connected_master = existing_group_name[4:].split('-')
                                existing_connected_name, existing_master_name = existing_connected_master

                                debug_print_C(f"         Comparando del existente con CONNECTED: {existing_connected_name} y MASTER: {existing_master_name}. Grupo: : {existing_group_name}")
                                debug_print_C(f"         Los de este grupo son:       CONNECTED: {node.name()} y MASTER: {connected_node.name()}")

                                if existing_connected_name == node.name():
                                    debug_print_C(f"         {node.name()} ya es CONNECT de otro grupo  A-  {existing_connected_name}")
                                if existing_master_name == connected_node.name():
                                    debug_print_C(f"         {connected_node.name()} ya es MASTER de otro grupo A- {existing_master_name}")

                            if any(existing_group.startswith(f"GR1-{node.name()}") for existing_group in all_groups.keys()):
                                debug_print_C(f"         {connected_node.name()} ya es CONNECT de otro grupo B")
                                continue
                            if any(existing_group.endswith(f"-{connected_node.name()}") for existing_group in all_groups.keys()):
                                debug_print_C(f"         {node.name()} ya es MASTER de otro grupo B")
                                continue

                            current_x_pos = connected_node.xpos()  # Valor X del nodo conectado
                            debug_print_C(f"         Iniciando grupo {group_name} con base en {connected_node.name()} (X = {current_x_pos})")
                            new_groups[group_name].append(connected_node)
                            explore_connections(connected_node, group_name, current_x_pos)
                            temp_updated_all_groups[group_name] = new_groups[group_name]

                        break  # Solo necesitamos encontrar una conexion valida para crear el grupo

    # Actualizar all_groups con los nuevos GR1 encontrados
    all_groups.update(new_groups)

    debug_print_C("Terminando nuevos GR1\n")

    return new_groups



## Renombrando y organizando grupos

def rename_groups_by_proximity(principal_nodes, all_groups):
    # Renombra y numera a cada grupo segun su proximidad con la columna principal

    # Obtener la posicion X de la columna principal
    main_x_pos = principal_nodes[0].xpos() if principal_nodes else 0

    # Separar grupos a la izquierda y derecha de la columna principal
    left_groups = []
    right_groups = []

    for group_name, nodes in all_groups.items():
        group_x_pos = min(node.xpos() for node in nodes)
        if group_x_pos < main_x_pos:
            left_groups.append((group_name.replace("GR-", ""), nodes, group_x_pos))
        else:
            right_groups.append((group_name.replace("GR-", ""), nodes, group_x_pos))

    # Ordenar grupos por posicion X
    left_groups.sort(key=lambda x: x[2], reverse=True)
    right_groups.sort(key=lambda x: x[2])

    # Renombrar los grupos
    renamed_groups = {}
    current_negative_index = -100
    current_positive_index = 100

    # Renombrar los grupos a la izquierda
    for i, (group_name, nodes, base_x_pos) in enumerate(left_groups):
        if i > 0 and abs(base_x_pos - left_groups[i-1][2]) <= TOLERANCIA_X:
            current_negative_index -= 1
        else:
            current_negative_index -= 100
        new_group_name = f"GR{current_negative_index}_{group_name}"
        renamed_groups[new_group_name] = nodes

    # Renombrar los grupos a la derecha
    for i, (group_name, nodes, base_x_pos) in enumerate(right_groups):
        if i > 0 and abs(base_x_pos - right_groups[i-1][2]) <= TOLERANCIA_X:
            current_positive_index += 1
        else:
            current_positive_index += 100
        new_group_name = f"GR+{current_positive_index}_{group_name}"
        renamed_groups[new_group_name] = nodes

    return renamed_groups

def sort_numerated_groups(numerated_groups, principal_nodes):
    column_groups = defaultdict(list)
    debug_print_D("\n\n_________________________________________________________________________________\n\n")
    debug_print_D("Ordenando los grupos que ya fueron numerados segun su posicion en Y")
    debug_print_D("Tambien eliminamos nodos duplicados en los grupos si existen")

    # Funcion para eliminar duplicados en cada grupo
    def eliminar_duplicados_en_grupos(numerated_groups):
        for group_name, nodes in numerated_groups.items():
            unique_nodes = []
            seen = set()
            for node in nodes:
                if node not in seen:
                    unique_nodes.append(node)
                    seen.add(node)
                else:
                    debug_print_D(f"Eliminando nodo duplicado {node.name()} en el grupo {group_name}")
            numerated_groups[group_name] = unique_nodes

    # Eliminar duplicados antes de proceder
    eliminar_duplicados_en_grupos(numerated_groups)

    # Agrupar los grupos por intervalos de columnas
    for group_name in numerated_groups.keys():
        parts = group_name.split('_')[0]
        num = int(parts.replace('GR', '').replace('+', '').replace('-', ''))
        column_interval = (num // 100) * 100
        column_groups[column_interval].append(group_name)

    def get_master_y_position(group_name):
        prefix, remaining_name, part1, part2, connected_name, master_name = extract_group_name_parts(group_name)

        if prefix is None or remaining_name is None or part1 is None or part2 is None or connected_name is None or master_name is None:
            debug_print_D("ERROR AL SEPARAR NOMBRE DE GRUPO en get_master_y_position!!!")
            debug_print_D(f"Valores obtenidos: prefix={prefix}, remaining_name={remaining_name}, part1={part1}, part2={part2}, connected_name={connected_name}, master_name={master_name}")
            return float('inf')  # En caso de error en el formato, devolver un valor alto para que se ordene al final

        master_node = next((node for node in numerated_groups[group_name] if node.name() == master_name), None)

        if master_node is None:
            debug_print_D(f"Error en get_master_y_position: No se encuentra el nodo MASTER: {master_name} en el grupo: {group_name}")
            return float('inf')  # En caso de que no se encuentre el nodo MASTER, devolver un valor alto para que se ordene al final

        return master_node.ypos()

    sorted_groups = []
    
    # Ordenar las columnas respetando el orden natural y luego por valor Y de nodo MASTER
    all_columns = sorted(column_groups.keys())
    for column in all_columns:
        groups_in_column = column_groups[column]
        # Ordenar los grupos en la columna segun la posicion Y del nodo MASTER
        groups_in_column.sort(key=lambda group_name: -get_master_y_position(group_name))
        debug_print_D(f"  Ordenando columna {column} con grupos:")
        for group in groups_in_column:
            ypos = get_master_y_position(group)
            debug_print_D(f"    {group} con posicion Y = {ypos}")
        sorted_groups.extend(groups_in_column)

    rename_group_names_by_proximity(sorted_groups, principal_nodes, numerated_groups)

    return sorted_groups

def rename_group_names_by_proximity(sorted_groups, principal_nodes, numerated_groups):
    debug_print_I("\n\n_________________________________________________________________________________\n\n")
    debug_print_I("Renombrando los grupos segun su proximidad")

    # Obtener el valor centrado en X de cualquier nodo de principal_nodes
    if not principal_nodes:
        return
    principal_x_center_node = principal_nodes[0]
    principal_x_center = principal_x_center_node.xpos() + principal_x_center_node.screenWidth() / 2
    debug_print_I(f"Valor X de la columna principal tomado del nodo {principal_x_center_node.name()}: {principal_x_center}")

    updated_sorted_groups = []

    for group_name in sorted_groups:
        debug_print_I(f"  Grupo {group_name}")
        
        # Verificar cuantos nodos tiene el grupo
        if len(numerated_groups[group_name]) != 1:
            debug_print_I(f"    Tiene mas de un nodo, no se procesa")
            updated_sorted_groups.append(group_name)
            continue

        # Obtener las partes del nombre del grupo
        prefix, remaining_name, part1, part2, connected_name, master_name = extract_group_name_parts(group_name)

        if prefix is None or remaining_name is None or part1 is None or part2 is None or connected_name is None or master_name is None:
            debug_print_I(f"    ERROR AL SEPARAR NOMBRE DE GRUPO en rename_group_names_by_proximity!!!")
            debug_print_I(f"    Valores obtenidos: prefix={prefix}, remaining_name={remaining_name}, part1={part1}, part2={part2}, connected_name={connected_name}, master_name={master_name}")
            updated_sorted_groups.append(group_name)
            continue

        # Obtener las posiciones centradas en X de connected_name y master_name
        connected_node = nuke.toNode(connected_name)
        master_node = nuke.toNode(master_name)
        if connected_node is None or master_node is None:
            debug_print_I(f"    No se pudo encontrar el nodo {connected_name if connected_node is None else master_name}")
            updated_sorted_groups.append(group_name)
            continue

        connected_x_center = connected_node.xpos() + connected_node.screenWidth() / 2
        master_x_center = master_node.xpos() + master_node.screenWidth() / 2

        debug_print_I(f"    Valor X del nodo connected {connected_name}: {connected_x_center}")
        debug_print_I(f"    Valor X del nodo master {master_name}: {master_x_center}")

        # Comparar las posiciones en X
        if abs(connected_x_center - principal_x_center) > abs(master_x_center - principal_x_center):
            new_group_name = f"{prefix}_{master_name}-{connected_name}"
            debug_print_I(f"    Renombrando grupo {group_name} a {new_group_name}")
            numerated_groups[new_group_name] = numerated_groups.pop(group_name)
            updated_sorted_groups.append(new_group_name)
        else:
            debug_print_I(f"      No se necesita renombrar el grupo {group_name}")
            updated_sorted_groups.append(group_name)

    # Actualizar sorted_groups con los nombres renombrados
    sorted_groups.clear()
    sorted_groups.extend(updated_sorted_groups)

def group_nodes_by_column_interval(numerated_groups):
    grouped_nodes = defaultdict(list)

    for group_name, nodes in numerated_groups.items():
        # Obtener el numero de columna del nombre del grupo
        parts = group_name.split('_')
        if len(parts) > 1:
            group_number = parts[0].replace('GR', '')
            sign = '+' if '+' in group_number else '-'
            group_number = group_number.replace('+', '').replace('-', '')
            if group_number.isdigit():
                column_interval = sign + str((int(group_number) // 100) * 100)
                grouped_nodes[column_interval].extend(nodes)

    return grouped_nodes



## Alinear y organizar nodos

def align_grouped_nodes(numerated_groups):
    grouped_nodes = group_nodes_by_column_interval(numerated_groups)
    
    for interval, nodes_in_interval in grouped_nodes.items():
        # Alinear nodos en el mismo intervalo
        align_nodes_in_column(nodes_in_interval, 'h')

def arrange_nodes(principal_nodes, sorted_numerated_groups, numerated_groups, selected_nodes):
    debug_print_E("\n\n_________________________________________________________________________________")
    debug_print_E("++Arrange:\n")

    # Distribuir verticalmente los nodos de la columna principal
    distribute_nodes_in_column(selected_nodes, principal_nodes, called_from_distribute_Groups=False)

    # Obtener todos los nodos disponibles
    all_nodes = list(set(principal_nodes + [node for nodes in numerated_groups.values() for node in nodes]))

    # Funcion auxiliar para mover nodos en Y
    def move_nodes_in_y(nodes, offset):
        offset = int(offset)  # Convertir offset a entero
        for node in nodes:
            node.setYpos(node.ypos() + offset)
            debug_print_E(f"  Moviendo nodo {node.name()} a nueva posicion Y: {node.ypos()}")

    # Funcion auxiliar para obtener la posicion Y centrada de un nodo
    def get_center_y(node):
        return node.ypos() + node.screenHeight() / 2

    # Procesar cada grupo numerado en el orden proporcionado
    for group_name in sorted_numerated_groups:
        nodes = numerated_groups[group_name]
        debug_print_E(f"\n  Arranging grupo: {group_name}")
        debug_message_B(f"\n  Arranging grupo: {group_name}")

        # Obtener las partes del nombre del grupo
        prefix, remaining_name, part1, part2, connected_name, master_name = extract_group_name_parts(group_name)

        if prefix is None or remaining_name is None or part1 is None or part2 is None or connected_name is None or master_name is None:
            debug_print_E("ERROR AL SEPARAR NOMBRE DE GRUPO en arrange_nodes!!!")
            debug_print_E(f"Valores obtenidos: prefix={prefix}, remaining_name={remaining_name}, part1={part1}, part2={part2}, connected_name={connected_name}, master_name={master_name}")
            continue  # Saltar si hay un error en el formato del nombre del grupo

        debug_print_E(f"    Prefijo: {prefix}, Nombre restante: {remaining_name}")
        debug_print_E(f"    Partes despues de dividir por el primer guion bajo: {part1}, {part2}")
        debug_print_E(f"    Partes despues de dividir por guion medio: {connected_name}, {master_name}")
        debug_print_E(f"  Buscando CONNECTED: {connected_name} y MASTER: {master_name}")

        # Imprimir contenido de all_nodes para depuracion
        debug_print_E(f"  Nodos disponibles en all_nodes: {[node.name() for node in all_nodes]}")
        # Imprimir contenido de nodes para depuracion
        debug_print_E(f"  Nodos en el grupo actual: {[node.name() for node in nodes]}")

        # Buscar el nodo CONNECTED entre todos los nodos disponibles
        connected_node = next((node for node in all_nodes if node.name() == connected_name), None)
        # Buscar el nodo MASTER dentro del grupo
        master_node = next((node for node in nodes if node.name() == master_name), None)

        if connected_node is None or master_node is None:
            debug_print_E(f"Error: CONNECTED o MASTER no encontrados en {group_name}")
            continue  # Saltar si no se encuentran los nodos CONNECTED y MASTER

        connected_center_y = get_center_y(connected_node)
        master_center_y = get_center_y(master_node)

        debug_print_E(f"  CONNECTED node: {connected_node.name()} center Ypos: {connected_center_y}")
        debug_print_E(f"  MASTER node: {master_node.name()} center Ypos: {master_center_y}")

        # Calcular la diferencia en Y entre CONNECTED y MASTER
        y_difference = int(connected_center_y - master_center_y)  # Asegurar que y_difference sea entero
        debug_print_E(f"  Diferencia en Y: {y_difference}")

        # Mover todos los nodos del grupo en base a la diferencia calculada
        move_nodes_in_y(nodes, y_difference)

        # Imprimir el grupo procesado para depuracion
        debug_print_E(f"\n  Grupo procesado: {group_name}")
        for node in nodes:
            debug_print_E(f"  {node.name()}: Nueva posicion Y = {node.ypos()}\n")

def align_connected_and_master(principal_nodes, sorted_numerated_groups, numerated_groups):
    debug_print_E1("\n\n_________________________________________________________________________________")
    debug_print_E1("++Align CONNECTED and MASTER:\n")

    # Obtener todos los nodos disponibles
    all_nodes = list(set(principal_nodes + [node for nodes in numerated_groups.values() for node in nodes]))
    
    # Funcion auxiliar para mover nodos en Y
    def move_nodes_in_y(nodes, offset):
        offset = int(offset)  # Convertir offset a entero
        for node in nodes:
            old_y = node.ypos()
            node.setYpos(node.ypos() + offset)
            debug_print_D(f"    Moviendo nodo {node.name()} de Y: {old_y} a nueva posicion Y: {node.ypos()}")

    # Funcion auxiliar para obtener la posicion Y centrada de un nodo
    def get_center_y(node):
        return node.ypos() + node.screenHeight() / 2

    # Procesar cada grupo numerado en el orden proporcionado
    for group_name in sorted_numerated_groups:
        nodes = numerated_groups[group_name]
        debug_print_E1(f"\n  Procesando grupo: {group_name}")

        # Obtener las partes del nombre del grupo
        prefix, remaining_name, part1, part2, connected_name, master_name = extract_group_name_parts(group_name)

        if prefix is None or remaining_name is None or part1 is None or part2 is None or connected_name is None or master_name is None:
            debug_print_E1("ERROR AL SEPARAR NOMBRE DE GRUPO en align_connected_and_master!!!")
            debug_print_E1(f"Valores obtenidos: prefix={prefix}, remaining_name={remaining_name}, part1={part1}, part2={part2}, connected_name={connected_name}, master_name={master_name}")
            continue  # Saltar si hay un error en el formato del nombre del grupo

        debug_print_E1(f"    Prefijo: {prefix}, Nombre restante: {remaining_name}")
        debug_print_E1(f"    Partes despues de dividir por el primer guion bajo: {part1}, {part2}")
        debug_print_E1(f"    Partes despues de dividir por guion medio: {connected_name}, {master_name}")
        debug_print_E1(f"    Buscando CONNECTED: {connected_name} y MASTER: {master_name}")

        # Buscar el nodo CONNECTED entre todos los nodos disponibles
        connected_node = next((node for node in all_nodes if node.name() == connected_name), None)
        # Buscar el nodo MASTER dentro del grupo
        master_node = next((node for node in nodes if node.name() == master_name), None)
        ############## Me parece que no hace falta busca master en el grupo (porque falla si enrocamos los nombres)
        ############## Asi que lo voy a buscar dentro de todos los nodos
        master_node = next((node for node in all_nodes if node.name() == master_name), None)
        

        
        if connected_node is None or master_node is None:
            debug_print_E1(f"Error: CONNECTED o MASTER no encontrados en {group_name} (align_connected_and_master)")
            debug_print_E1(f"    CONNECTED  {connected_node.name()} encontrado: {connected_node is not None}")
            debug_print_E1(f"    MASTER {master_node.name()} encontrado: {master_node is not None}")
            continue  # Saltar si no se encuentran los nodos CONNECTED y MASTER

        connected_center_y = get_center_y(connected_node)
        master_center_y = get_center_y(master_node)

        debug_print_E1(f"    CONNECTED node: {connected_node.name()} center Ypos: {connected_center_y}")
        debug_print_E1(f"    MASTER node: {master_node.name()} center Ypos: {master_center_y}")

        # Calcular la diferencia en Y entre CONNECTED y MASTER
        if connected_center_y != master_center_y:
            y_difference = int(connected_center_y - master_center_y)  # Asegurar que y_difference sea entero
            debug_print_E1(f"    Diferencia en Y: {y_difference}")

            # Imprimir posiciones antes del ajuste
            debug_print_E1("    Posiciones en Y antes de ajustar:")
            for node in nodes:
                debug_print_E1(f"    {node.name()}: Posicion Y = {node.ypos()}")

            # Mover todos los nodos del grupo en base a la diferencia calculada
            move_nodes_in_y(nodes, y_difference)
            debug_print_E1(f"    Ajustando posicion en Y por {y_difference}")

            # Imprimir el grupo procesado para depuracion
            debug_print_E1(f"\n    Grupo procesado: {group_name}")
            for node in nodes:
                debug_print_E1(f"    {node.name()}: Nueva posicion Y = {node.ypos()}\n")

            # Verificar y mostrar las nuevas posiciones en Y de los nodos
            debug_print_E1("    Nuevas posiciones en Y despues de ajustar:")
            for node in nodes:
                debug_print_E1(f"    {node.name()}: Nueva posicion Y = {node.ypos()}")
        else:
            debug_print_E1(f"    CONNECTED y MASTER ya estan alineados en Y, no es necesario ajustar")
        
def align_nodes_in_column(nodes, direction='v'):
    if direction not in ['h', 'v']:
        print("Direccion no valida")
        return

    if direction == 'v':
        # Encontrar el nodo de referencia (el nodo mas alto)
        reference_node = min(nodes, key=lambda n: n.ypos())
        reference_pos = reference_node.ypos()
        for n in nodes:
            if n != reference_node:
                offset = (reference_node.screenHeight() / 2) - (n.screenHeight() / 2)
                n.setYpos(int(reference_pos + offset))
    elif direction == 'h':
        if len(nodes) > 2:
            # Obtener todas las posiciones X de los nodos
            x_positions = [n.xpos() + n.screenWidth() / 2 for n in nodes]
            # Encontrar el valor de X mas repetido
            most_common_x = max(set(x_positions), key=x_positions.count)
            if x_positions.count(most_common_x) > 1:
                # Si hay mas de un nodo con la misma posicion X, ajustar todos los nodos a esa posicion
                for n in nodes:
                    new_x_pos = int(most_common_x - n.screenWidth() / 2)
                    n.setXpos(new_x_pos)
            else:
                # Si no hay valores repetidos, calcular la posicion promedio del centro en X
                avg_x_center = sum(x_positions) / len(nodes)
                for n in nodes:
                    # Ajustar la posicion X para centrar horizontalmente
                    new_x_pos = int(avg_x_center - n.screenWidth() / 2)
                    n.setXpos(new_x_pos)
        else:
            # Para 2 o menos nodos, calcular la posicion promedio del centro en X
            avg_x_center = sum(n.xpos() + n.screenWidth() / 2 for n in nodes) / len(nodes)
            for n in nodes:
                # Ajustar la posicion X para centrar horizontalmente
                new_x_pos = int(avg_x_center - n.screenWidth() / 2)
                n.setXpos(new_x_pos)

def distribute_nodes_in_column(selected_nodes, nodes, called_from_distribute_Groups=False, numerated_groups=None, sorted_numerated_groups=None, recursion_depth=0):
    """
    La funcion distribute_nodes_in_column utiliza las conexiones de los nodos para identificar el 
    primer y ultimo nodo conectados de la siguiente manera:

    Identificacion del Primer Nodo Conectado:

    Se recorre la lista de nodos ordenados por su posicion en Y.

    Para cada nodo, se verifica si no tiene ninguna conexion de entrada con los nodos en la lista (es decir, 
    que sus entradas no estan en la lista de todos los nodos).

    El primer nodo que cumple esta condicion se identifica como el primer nodo conectado.

    Si no se encuentra ningun nodo que cumpla esta condicion, se selecciona el primer nodo en la lista como 
    el primer nodo conectado por defecto.

    Identificacion del Ultimo Nodo Conectado:

    Se recorre la lista de nodos en orden inverso (de abajo hacia arriba).

    Para cada nodo, se verifica si no tiene ninguna conexion de salida con los nodos en la lista (es decir, 
    que sus salidas no estan en la lista de todos los nodos).

    El primer nodo que cumple esta condicion se identifica como el ultimo nodo conectado.

    Si no se encuentra ningun nodo que cumpla esta condicion, se selecciona el ultimo nodo en la lista como 
    el ultimo nodo conectado por defecto.

    Posicion en Y para el Primer y Ultimo Nodo Conectado:
    Primer Nodo Conectado: Se utiliza la posicion en Y del primer nodo conectado (first_node[2]) y su altura (first_node[1]).
    Ultimo Nodo Conectado: Se utiliza la posicion en Y del ultimo nodo conectado (last_node[2]) y su altura (last_node[1]).
    """
    # Ordenar nodos por posicion y
    nodes.sort(key=lambda node: node.ypos())

    # Obtener la altura de cada nodo y sus posiciones y
    nodes_info = [(node, node.screenHeight(), node.ypos()) for node in nodes]

    if len(nodes_info) < 2:
        return  # No hay suficientes nodos para distribuir

    # Funcion auxiliar para encontrar el primer nodo conectado
    def find_first_connected(nodes_info, all_nodes):
        for node, height, ypos in nodes_info:
            if not any(node.input(i) in all_nodes for i in range(node.inputs())):
                debug_print_G(f"{node.name()} es el primer nodo porque no tiene conexiones de entrada o sus conexiones no estan en el grupo.")
                return node, height, ypos
        return nodes_info[0]  # Si no se encuentra, devolver el primero por defecto

    # Funcion auxiliar para encontrar el ultimo nodo conectado
    def find_last_connected(nodes_info, all_nodes):
        for node, height, ypos in reversed(nodes_info):
            if not any(dep in all_nodes for dep in node.dependent()):
                debug_print_G(f"{node.name()} es el ultimo nodo porque no tiene conexiones de salida o sus conexiones no estan en el grupo.")
                return node, height, ypos
        return nodes_info[-1]  # Si no se encuentra, devolver el ultimo por defecto

    # Obtener una lista de todos los nodos
    all_nodes = [node_info[0] for node_info in nodes_info]

    # Encontrar el primer y ultimo nodo conectados
    first_node = find_first_connected(nodes_info, all_nodes)
    last_node = find_last_connected(nodes_info, all_nodes)

    # Reorganizar los nodos en el orden correcto basado en las conexiones
    def sort_nodes_by_connections(first_node, nodes_info):
        sorted_nodes = [first_node]
        current_node = first_node[0]
        while len(sorted_nodes) < len(nodes_info):
            for node, height, ypos in nodes_info:
                if current_node in [node.input(i) for i in range(node.inputs())]:
                    sorted_nodes.append((node, height, ypos))
                    current_node = node
                    break
        return sorted_nodes

    sorted_nodes_info = sort_nodes_by_connections(first_node, nodes_info)

    # Funcion para distribuir los nodos verticalmente
    def distribute_nodes(sorted_nodes_info, first_node, last_node, free_space, selected_nodes):
        current_y = first_node[2] + first_node[1]  # Inicia desde la base del primer nodo
        new_y_positions = []  # Guardar las posiciones Y despues de la distribucion

        for i, (node, height, ypos) in enumerate(sorted_nodes_info):
            if node == first_node[0] or node == last_node[0]:
                new_y_positions.append((node, ypos))  # Mantener la posicion del primer y ultimo nodo
                continue  # No mover el primer y ultimo nodo
            current_y += free_space / (len(nodes_info) - 1)
            new_y_positions.append((node, int(current_y)))  # Guardar posicion distribuida
            node.setYpos(int(current_y))
            current_y += height
        
        return new_y_positions

    # Imprimir la lista de nodos con sus valores X e Y antes de ser distribuidos
    debug_print_G("\n\n_________________________________________________________________________________")
    debug_print_G("++Distribuyendo:\n")
    debug_print_G("Lista de nodos antes de la distribucion:")
    for node, height, ypos in sorted_nodes_info:
        debug_print_G(f"{node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {ypos}")

    # Imprimir el orden de conexion de los nodos
    debug_print_G("\nOrden de conexion de los nodos:")
    for node, _, ypos in sorted_nodes_info:
        inputs = [input_node.name() for input_node in (node.input(i) for i in range(node.inputs())) if input_node]
        outputs = [output_node.name() for output_node in node.dependent()]
        debug_print_G(f"{node.name()} - Posicion Y: {ypos} - Conexiones de entrada: {inputs} - Conexiones de salida: {outputs}")

    # Calcular el espacio libre total entre el primer y ultimo nodo
    total_height = last_node[2] + last_node[1] - first_node[2]  # Y del ultimo nodo + altura del ultimo nodo - Y del primer nodo
    height_of_nodes = sum(node_info[1] for node_info in nodes_info)  # Altura total de todos los nodos
    free_space = total_height - height_of_nodes  # Espacio libre total

    # Imprimir detalles sobre las alturas
    debug_print_G(f"\nAltura total disponible (del primero al ultimo nodo): {total_height}")
    debug_print_G(f"Altura total de los nodos: {height_of_nodes}")
    debug_print_G(f"Espacio libre: {free_space}")

    # Distribuir los nodos verticalmente sin compensacion
    original_y_positions = [(node, ypos) for node, height, ypos in sorted_nodes_info]
    normal_y_positions = distribute_nodes(sorted_nodes_info, first_node, last_node, free_space, selected_nodes)

    # Imprimir las posiciones originales y las nuevas posiciones sin compensacion
    debug_print_G("\nPosiciones originales y nuevas despues de la distribucion normal:")
    for (node, original_y), (_, normal_y) in zip(original_y_positions, normal_y_positions):
        debug_print_G(f"{node.name()}: Posicion Y original = {original_y}, Nueva posicion Y = {normal_y}")

    # Si se llama desde distribute_Groups, aplicar logica adicional a los nodos distribuidos
    if called_from_distribute_Groups:
        for (node, original_y), (_, normal_y) in zip(original_y_positions, normal_y_positions):
            if node == first_node[0] or node == last_node[0]:
                continue  # Saltar el primer y ultimo nodo

            # Verificar si el nodo se movio hacia arriba o hacia abajo
            if normal_y < original_y:
                is_first_node = True
            else:
                is_first_node = False

            # Llamar a align_parent_to_first_or_last con is_first_node
            align_parent_to_first_or_last(node, numerated_groups, sorted_numerated_groups, is_first_node, selected_nodes=selected_nodes)

    # Si la altura total de los nodos excede la altura disponible, aplicar la compensacion
    SPACING_Y = 6
    if height_of_nodes + (SPACING_Y * (len(nodes_info) - 1)) > total_height:
        debug_message_D(f"\n  Vamos a compensar: {first_node[0].name()}-{last_node[0].name()}")
        extra_height_needed = height_of_nodes + (SPACING_Y * (len(nodes_info) - 1)) - total_height  # Espacio extra necesario
        debug_print_G(f"La altura total de los nodos excede la altura disponible.")
        debug_print_G(f"Espacio extra necesario: {extra_height_needed}")
        
        # Ajustar la posicion del primer y ultimo nodo
        adjustment = extra_height_needed / 2
        first_node_new_y = first_node[2] - adjustment
        first_node[0].setYpos(int(first_node_new_y))

        # Llamar a la funcion nueva para alinear connected y master del primer nodo del grupo si es necesario
        if called_from_distribute_Groups:
            align_parent_to_first_or_last(first_node[0], numerated_groups, sorted_numerated_groups, True, selected_nodes=selected_nodes)

        last_node_new_y = last_node[2] + adjustment
        last_node[0].setYpos(int(last_node_new_y))

        # Llamar a la funcion nueva para alinear connected y master del ultimo nodo del grupo si es necesario
        if called_from_distribute_Groups:
            align_parent_to_first_or_last(last_node[0], numerated_groups, sorted_numerated_groups, False, selected_nodes=selected_nodes)

        # Actualizar las posiciones en sorted_nodes_info despues de mover el primer y ultimo nodo
        for i, (node, height, ypos) in enumerate(sorted_nodes_info):
            if node == first_node[0]:
                sorted_nodes_info[i] = (node, height, first_node_new_y)
            elif node == last_node[0]:
                sorted_nodes_info[i] = (node, height, last_node_new_y)

        # Imprimir los valores actualizados antes de la distribucion compensada
        debug_print_G("\nValores actualizados antes de la distribucion compensada:")
        for node, height, ypos in sorted_nodes_info:
            debug_print_G(f"{node.name()}: Altura = {height}, Posicion Y actualizada = {ypos}")

        # Calcular el incremento ajustado para la compensacion
        free_space = last_node_new_y + last_node[1] - first_node_new_y - height_of_nodes
        increment = free_space / (len(nodes_info) - 1)

        # Distribuir los nodos nuevamente con los valores actualizados
        current_y = first_node_new_y + first_node[1]  # Inicia desde la base del primer nodo compensado
        compensated_y_positions = []

        for i, (node, height, ypos) in enumerate(sorted_nodes_info):
            if node == first_node[0] or node == last_node[0]:
                compensated_y_positions.append((node, int(ypos)))  # Guardar la posicion ajustada del primer y ultimo nodo
                continue  # Saltar el primer y ultimo nodo ya ajustados
            current_y += increment
            compensated_y_positions.append((node, int(current_y)))  # Guardar posicion compensada
            node.setYpos(int(current_y))
            current_y += height

        # Imprimir los valores actualizados despues de la distribucion compensada
        debug_print_G("\nValores actualizados despues de la distribucion compensada:")
        for node, compensated_y in compensated_y_positions:
            debug_print_G(f"{node.name()}: Nueva posicion Y compensada = {compensated_y}")

        # Imprimir las posiciones originales, distribucion normal y distribucion compensada
        debug_print_G("\nPosiciones originales, distribucion normal y distribucion compensada:")
        for (node, original_y), (_, normal_y), (_, compensated_y) in zip(original_y_positions, normal_y_positions, compensated_y_positions):
            debug_print_G(f"{node.name()}: Posicion Y original = {original_y}, Distribucion normal Y = {normal_y}, Distribucion compensada Y = {compensated_y}")
    else:
        debug_print_G("No se necesita compensacion para la distribucion.")

def find_parent_connected_nodes_vertically(node, direction):

    if node.Class() == 'Root' or node.Class() == 'BackdropNode':
        return []

    nodes_list = [(node, node.ypos())]  # Incluir el nodo inicial
    current_node = node

    # Mensaje de depuracion para el nodo inicial
    debug_print_F1(f"Inicio de la busqueda desde el nodo: {current_node.name()} en la direccion: {'arriba' if direction == 't' else 'abajo'}")

    while current_node:
        # Calcula el centro del nodo actual
        current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
        current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

        # Lista para mantener los nodos conectados en la direccion especificada
        search_nodes = [current_node.input(i) for i in range(current_node.inputs()) if current_node.input(i) and current_node.input(i).Class() != 'BackdropNode']
        search_nodes += [n for n in current_node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS) if n.Class() != 'BackdropNode']
        search_nodes = list(set(search_nodes))  # Elimina duplicados y None

        connected_node = None
        for n in search_nodes:
            if n.Class() == 'Root' or n.Class() == 'BackdropNode':
                continue

            # Calcula el centro del nodo conectado
            node_center_x = n.xpos() + (n.screenWidth() / 2)
            node_center_y = n.ypos() + (n.screenHeight() / 2)

            # Verifica la direccion y si el nodo conectado esta dentro de la tolerancia y en la direccion correcta
            if direction == 't' and abs(node_center_x - current_node_center_x) <= TOLERANCIA_X and node_center_y < current_node_center_y:
                connected_node = n
            elif direction == 'b' and abs(node_center_x - current_node_center_x) <= TOLERANCIA_X and node_center_y > current_node_center_y:
                connected_node = n

        if connected_node:
            nodes_list.append((connected_node, connected_node.ypos()))
            debug_print_F1(f"Nodo encontrado: {connected_node.name()} en la posicion Y: {connected_node.ypos()}")
            current_node = connected_node
        else:
            debug_print_F1("No se encontraron mas nodos conectados en la direccion especificada.")
            break

    return nodes_list

def sort_parent_overlapping_nodes(parent_column_nodes_list, is_first_node, selected_nodes, called_from_distribute_Groups, numerated_groups, sorted_numerated_groups, recursion_depth=0):
    SPACING_Y = 15
    MAX_RECURSION_DEPTH = 3  # Limitar la recursion a un maximo de 3 niveles

    if recursion_depth > MAX_RECURSION_DEPTH:
        debug_print_F1(f"Recursion depth {recursion_depth} exceeded the limit, returning to avoid infinite loop.")
        return

    # Limitar la lista de nodos a solo los nodos seleccionados
    parent_column_nodes_list = [(node, ypos) for node, ypos in parent_column_nodes_list if node in selected_nodes]

    debug_message_A("Click en OK para hacer el sort_parent_overlapping_nodes")

    # Imprimir los nombres de todos los nodos en la lista junto con sus posiciones Y de la lista y actuales
    debug_print_F1("  Lista de nodos y sus posiciones Y:")
    for node, ypos in parent_column_nodes_list:
        debug_print_F1(f"    Nodo: {node.name()}, Posicion Y en la lista: {ypos}, Posicion Y actual: {node.ypos()}")

    for i in range(len(parent_column_nodes_list) - 1):
        node1, ypos1 = parent_column_nodes_list[i]
        node2, ypos2 = parent_column_nodes_list[i + 1]

        height1 = node1.screenHeight()
        height2 = node2.screenHeight()

        node1_top = node1.ypos()
        node1_bottom = node1.ypos() + height1
        node2_top = node2.ypos()
        node2_bottom = node2.ypos() + height2

        if is_first_node:
            # Comparar node1_top con node2_bottom
            if node1_top - SPACING_Y < node2_bottom:
                new_ypos2 = node1_top - height2 - SPACING_Y
                node2.setYpos(new_ypos2)
                debug_print_F1(f"    Superposicion detectada: {node1.name()} y {node2.name()}. Moviendo {node2.name()} a {new_ypos2}")
            else:
                debug_print_F1(f"    No hay superposicion entre {node1.name()} y {node2.name()}")
        else:
            # Comparar node1_bottom con node2_top
            if node1_bottom + SPACING_Y > node2_top:
                new_ypos2 = node1_bottom + SPACING_Y
                node2.setYpos(new_ypos2)
                debug_print_F1(f"    Superposicion detectada: {node1.name()} y {node2.name()}. Moviendo {node2.name()} a {new_ypos2}")
            else:
                debug_print_F1(f"    No hay superposicion entre {node1.name()} y {node2.name()}")

    # Llamar a distribute_nodes_in_column para redistribuir los nodos
    nodes = [node for node, ypos in parent_column_nodes_list]
    distribute_nodes_in_column(selected_nodes, nodes, called_from_distribute_Groups, numerated_groups, sorted_numerated_groups, recursion_depth + 1)

def align_parent_to_first_or_last(node, numerated_groups, sorted_numerated_groups, is_first_node, selected_nodes):
    node_name = node.name()

    debug_message_E("Click en OK para hacer el align_parent_to_first_or_last")
    
    def get_center_y(node):
        return node.ypos() + node.screenHeight() / 2

    # Obtener la posicion Y centrada del nodo recibido
    centered_new_y_pos = get_center_y(node)

    for group_name in sorted_numerated_groups:
        prefix, remaining_name, part1, part2, connected_name, master_name = extract_group_name_parts(group_name)

        if prefix is None or remaining_name is None or part1 is None or part2 is None or connected_name is None or master_name is None:
            debug_print_F("ERROR AL SEPARAR NOMBRE DE GRUPO en align_parent_to_first_or_last!!!")
            debug_print_F(f"Valores obtenidos: prefix={prefix}, remaining_name={remaining_name}, part1={part1}, part2={part2}, connected_name={connected_name}, master_name={master_name}")
            continue

        debug_print_F(f"Comparando grupo {group_name} con CONNECTED: {connected_name} y MASTER: {master_name}")

        if node_name == connected_name:
            debug_print_F(f"{node_name} es CONNECTED del grupo {group_name}")
            master_node = nuke.toNode(master_name)
            if master_node:
                # Crear una lista de nodos conectados hacia arriba o hacia abajo
                direction = 't' if is_first_node else 'b'
                parent_column_nodes_list = find_parent_connected_nodes_vertically(master_node, direction)

                # Obtener la nueva posicion centrada en Y para el nodo master
                master_node.setYpos(int(centered_new_y_pos - master_node.screenHeight() / 2))
                debug_print_F(f"Moviendo MASTER {master_name} a nueva posicion Y centrada: {master_node.ypos()}")
                
                # Llamar a sort_parent_overlapping_nodes con la lista de nodos y sus posiciones Y
                sort_parent_overlapping_nodes(parent_column_nodes_list, is_first_node, selected_nodes, called_from_distribute_Groups=True, numerated_groups=numerated_groups, sorted_numerated_groups=sorted_numerated_groups)                
                
        elif node_name == master_name:
            debug_print_F(f"{node_name} es MASTER del grupo {group_name}")
            connected_node = nuke.toNode(connected_name)
            if connected_node:
                # Crear una lista de nodos conectados hacia arriba o hacia abajo
                direction = 't' if is_first_node else 'b'
                parent_column_nodes_list = find_parent_connected_nodes_vertically(connected_node, direction)
            
                # Obtener la nueva posicion centrada en Y para el nodo connected
                connected_node.setYpos(int(centered_new_y_pos - connected_node.screenHeight() / 2))
                debug_print_F(f"Moviendo CONNECTED {connected_name} a nueva posicion Y centrada: {connected_node.ypos()}")

                # Llamar a sort_parent_overlapping_nodes con la lista de nodos y sus posiciones Y
                sort_parent_overlapping_nodes(parent_column_nodes_list, is_first_node, selected_nodes, called_from_distribute_Groups=True, numerated_groups=numerated_groups, sorted_numerated_groups=sorted_numerated_groups)
                
        else:
            debug_print_F(f"{node_name} no es CONNECTED ni MASTER del grupo {group_name}")

def sort_columns_overlapping_nodes(principalGroup, columnGroups, selected_nodes, numerated_groups, sorted_numerated_groups, original_positions):
    
    # Llamar a la nueva funcion unoverlap_nodes
    unoverlap_nodes(principalGroup, columnGroups, selected_nodes, numerated_groups, sorted_numerated_groups, original_positions)


    # Almacenar las posiciones actuales de los nodos antes de cualquier movimiento
    current_position_map = {}

    for group_pos, nodes in columnGroups.items():
        if group_pos == principalGroup:
            continue

        # Obtener las posiciones actuales y originales de los nodos en esta columna
        current_positions = sorted(nodes, key=lambda n: n.ypos())
        original_column_nodes = sorted([node for node in original_positions.keys() if node in nodes], key=lambda n: original_positions[n][1])

        debug_print_J(f"\n\n  Comparando posiciones en columna en X = {group_pos}:")
        debug_print_J(f"  {'Pos.':<5}{'Original (Nodo, Y)':<40}{'Actual (Nodo, Y)'}")
        for index, (original_node, current_node) in enumerate(zip(original_column_nodes, current_positions)):
            original_y = original_positions[original_node][1]
            current_y = current_node.ypos()
            debug_print_J(f"  {index + 1:<5}{original_node.name():<30} Y={original_y:<10}{current_node.name():<30} Y={current_y}")
            current_position_map[current_node] = current_y  # Guardar la posicion actual impresa

        # Reorganizar los nodos si estan fuera de orden
        for i in range(len(original_column_nodes)):
            original_node = original_column_nodes[i]
            current_node = current_positions[i]

            if current_node != original_node:
                # Obtener la posicion objetivo basada en la lista impresa
                target_node = original_column_nodes[i]
                target_ypos = current_position_map[target_node]  # Usar la posicion de la lista impresa

                debug_print_J(f"\n    + Posicion actual {i + 1}: Nodo {current_node.name()}, Y={current_position_map[current_node]}.")
                debug_print_J(f"         Originalmente estaba en posicion {original_column_nodes.index(current_node) + 1}. Donde ahora esta el nodo {target_node.name()} con Y={target_ypos}")
                debug_print_J(f"         Pasando a posicion original, Y={target_ypos}.")
                debug_print_J(f"         Buscando nodos conectados a {current_node.name()} en otras columnas:")

                # Mover el nodo a la posicion correcta
                current_node.setYpos(target_ypos)

                # Ajustar los nodos conectados solo del nodo movido
                align_parent_to_moved_node(current_node, numerated_groups, sorted_numerated_groups, selected_nodes)

            else:
                debug_print_J(f"\n    + Posicion {i + 1}: Nodo {current_node.name()}, Y={current_position_map[current_node]} esta en la posicion correcta.")



def align_parent_to_moved_node(moved_node, numerated_groups, sorted_numerated_groups, selected_nodes):
    """
    Ajusta la posicion de un nodo conectado si esta en una columna diferente a la del nodo movido.
    """

    def get_center_y(moved_node):
        return int(moved_node.ypos() + moved_node.screenHeight() / 2)

    def adjust_for_overlap(parent_node, nodes_in_column):
        SPACING_Y = 10
        debug_print_J(f"                Revisando superposicion para el nodo {parent_node.name()} en columna diferente.")
        for other_node in nodes_in_column:
            if other_node == parent_node:
                continue

            parent_node_top = parent_node.ypos()
            parent_node_bottom = parent_node.ypos() + parent_node.screenHeight()
            other_node_top = other_node.ypos()
            other_node_bottom = other_node.ypos() + other_node.screenHeight()

            debug_print_J(f"                    Comparando con {other_node.name()}:")
            debug_print_J(f"                        - parent_node_top = {parent_node_top}, parent_node_bottom = {parent_node_bottom}")
            debug_print_J(f"                        - other_node_top = {other_node_top}, other_node_bottom = {other_node_bottom}")

            # Si el nodo se superpone con el nodo anterior, mover hacia abajo
            if parent_node_top < other_node_bottom + SPACING_Y and parent_node_top > other_node_top:
                new_ypos = other_node_bottom + SPACING_Y
                parent_node.setYpos(new_ypos)
                debug_print_J(f"                    Mover {parent_node.name()} hacia abajo para evitar superposicion con {other_node.name()}: nueva posicion Y = {new_ypos}")
            # Si el nodo se superpone con el nodo siguiente, mover hacia arriba
            elif parent_node_bottom > other_node_top - SPACING_Y and parent_node_bottom < other_node_bottom:
                new_ypos = other_node_top - parent_node.screenHeight() - SPACING_Y
                parent_node.setYpos(new_ypos)
                debug_print_J(f"                    Mover {parent_node.name()} hacia arriba para evitar superposicion con {other_node.name()}: nueva posicion Y = {new_ypos}")

    def restore_original_order(parent_node, nodes_in_column, original_positions):
        debug_print_J(f"\n               Verificando si {parent_node.name()} ha cambiado de posicion en su columna.")
        current_order = sorted(nodes_in_column, key=lambda n: n.ypos())
        original_order = sorted(nodes_in_column, key=lambda n: original_positions[n][1])

        debug_print_J(f"                 Orden original: {[moved_node.name() for moved_node in original_order]}")
        debug_print_J(f"                 Orden actual: {[moved_node.name() for moved_node in current_order]}")

        if current_order != original_order:
            debug_print_J(f"    {parent_node.name()} ha cambiado de posicion. Restaurando el orden original.")
            for i in range(len(current_order)):
                if current_order[i] == parent_node:
                    continue
                original_ypos = original_positions[original_order[i]][1]
                current_order[i].setYpos(original_ypos)
                debug_print_J(f"                 Moviendo {current_order[i].name()} a su posicion original Y = {original_ypos}")
        else:
            debug_print_J(f"                 {parent_node.name()} no ha cambiado de posicion. No es necesario ajustar otros nodos.")

    # Obtener la posicion Y centrada del nodo recibido (moved_node)
    centered_y_pos_moved_node = get_center_y(moved_node)
    debug_print_J(f"             Posicion moved node {moved_node.name()} Y {moved_node.ypos()}")
    debug_print_J(f"             Posicion moved node {moved_node.name()} Y {centered_y_pos_moved_node} (centrada)")

    # Encontrar nodos conectados al nodo que se ha movido en otras columnas
    connected_nodes = [n for n in moved_node.dependent() if n in selected_nodes and abs(n.xpos() - moved_node.xpos()) >= 10]
    debug_print_J(f"             Nodos conectados a {moved_node.name()} en otras columnas: {[n.name() for n in connected_nodes]}")

        
    if connected_nodes:
        for connected_node in connected_nodes:
            # Obtener todos los nodos en la columna del nodo conectado
            connected_column_nodes = [n for n in selected_nodes if abs(n.xpos() - connected_node.xpos()) < 10]
            connected_column_nodes.sort(key=lambda n: n.ypos())
            #debug_print_J(f"             ++connected_column_nodes {connected_column_nodes.name}")

            
            debug_print_J(f"             Posicion parent connected {connected_node.name()} Y {connected_node.ypos()}")
            debug_print_J(f"             Moviendo parent connected {connected_node.name()} a Y {centered_y_pos_moved_node}")
            debug_message_F("Moviendo parent connected {connected_node.name()} a Y {centered_y_pos_moved_node}")
            
            # Alinear el connected_node (parent_node) a el moved_node de manera centrada
            connected_node.setYpos(int(centered_y_pos_moved_node - connected_node.screenHeight() / 2))

            # Chequear superposiciones del parent node dentro de su propia columna
            adjust_for_overlap(connected_node, connected_column_nodes)

            # Chequear que no se haya cambiado el orden de los nodos de la columna parent y restaurarlos si es necesario
            restore_original_order(connected_node, connected_column_nodes, {n: (n.xpos(), n.ypos()) for n in connected_column_nodes})
    else:
        debug_print_J(f"             No se encontraron nodos conectados en otras columnas para {moved_node.name()}.")

    debug_print_J(f"         Finalizado el ajuste para {moved_node.name()}\n")

def unoverlap_nodes(principalGroup, columnGroups, selected_nodes, numerated_groups, sorted_numerated_groups, original_positions):
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        debug_print_J(f"\n\n  Iteracion {iteration}:")

        no_overlap_detected = True

        for group_pos, nodes in columnGroups.items():
            if group_pos == principalGroup:
                continue

            # Obtener las posiciones actuales de los nodos en esta columna
            current_positions = sorted(nodes, key=lambda n: n.ypos())

            # Imprimir la lista inicial de nodos con sus techos, bases y espacios
            debug_print_J("\n\n  Lista de nodos en la columna en X = " + str(group_pos) + ":")
            debug_print_J(f"  {'Nodo':<25}{'Techo (Y)':<15}{'Base (Y)':<15}{'Espacio (Y)':<15}")
            
            initial_positions = []
            for i, node in enumerate(current_positions):
                node_top = node.ypos()
                node_bottom = node.ypos() + node.screenHeight()
                if i < len(current_positions) - 1:
                    next_node_top = current_positions[i + 1].ypos()
                    space = next_node_top - node_bottom
                else:
                    space = "N/A"  # El ultimo nodo no tiene un nodo siguiente para calcular espacio

                debug_print_J(f"  {node.name():<25}{node_top:<15}{node_bottom:<15}{space:<15}")
                initial_positions.append((node, node_top, node_bottom, space))
            
            # Chequear superposiciones y ajustar nodos
            for i, (node, node_top, node_bottom, space) in enumerate(initial_positions):
                if space != "N/A" and space < 0:
                    no_overlap_detected = False  # Indica que se detecto una superposicion
                    # Se detecto una superposicion
                    debug_print_J(f"  Superposicion detectada entre {node.name()} y {current_positions[i + 1].name()}")
                    debug_message_F(f"Superposicion detectada entre {node.name()} y {current_positions[i + 1].name()}")

                    next_node = current_positions[i + 1]
                    next_node_top = initial_positions[i + 1][1]
                    next_node_bottom = next_node_top + next_node.screenHeight()

                    # Determinar el espacio libre arriba y abajo
                    if i > 0:
                        prev_node_bottom = initial_positions[i - 1][2]  # La base del nodo anterior
                        space_up = node_top - prev_node_bottom
                    else:
                        space_up = float('inf')  # No hay nodo anterior, espacio libre arriba es infinito

                    space_down = initial_positions[i + 2][1] - next_node_bottom if i + 2 < len(initial_positions) else float('inf')

                    # Decidir si mover hacia arriba o hacia abajo
                    if space_up > space_down:
                        debug_print_J(f"  Moviendo {node.name()} hacia arriba para evitar superposicion")
                        debug_message_F(f"Moviendo {node.name()} hacia arriba para evitar superposicion")
                        new_ypos = node_top - next_node.screenHeight() - 10  # Ajusta 10 unidades arriba
                        node.setYpos(int(new_ypos))
                        align_parent_to_moved_node(node, numerated_groups, sorted_numerated_groups, selected_nodes)
                    else:
                        debug_print_J(f"  Moviendo {next_node.name()} hacia abajo para evitar superposicion")
                        debug_message_F(f"Moviendo {next_node.name()} hacia abajo para evitar superposicion")
                        new_ypos = next_node_bottom + 10  # Ajusta 10 unidades abajo
                        next_node.setYpos(int(new_ypos))
                        align_parent_to_moved_node(next_node, numerated_groups, sorted_numerated_groups, selected_nodes)

            # Imprimir la lista final de nodos con sus nuevas posiciones
            debug_print_J("\n\n  Lista final de nodos en la columna en X = " + str(group_pos) + " despues de ajustes:")
            debug_print_J(f"  {'Nodo':<25}{'Techo (Y)':<15}{'Base (Y)':<15}{'Espacio (Y)':<15}")

            for i, node in enumerate(current_positions):
                node_top = node.ypos()
                node_bottom = node.ypos() + node.screenHeight()
                if i < len(current_positions) - 1:
                    next_node_top = current_positions[i + 1].ypos()
                    space = next_node_top - node_bottom
                    if space < 0:
                        no_overlap_detected = False  # Si sigue habiendo superposicion
                else:
                    space = "N/A"  # El ultimo nodo no tiene un nodo siguiente para calcular espacio

                debug_print_J(f"  {node.name():<25}{node_top:<15}{node_bottom:<15}{space:<15}")

        # Si no se detecto ninguna superposicion, salir del bucle
        if no_overlap_detected:
            debug_print_J("\nNo se detectaron mas superposiciones. Terminando el proceso.")
            break
    else:
        debug_print_J("\nSe alcanzo el numero maximo de iteraciones. Algunas superposiciones podrian persistir.")





def main():
    # Obtener nodos seleccionados
    selected_nodes = nuke.selectedNodes()

    # Iniciar el undo
    undo = nuke.Undo()
    undo.begin("Arrange Nodes")

    # Crear una lista con todos los nodos seleccionados que no sean backdrops ni viewers
    regular_nodes = [node for node in selected_nodes if node.Class() not in ["BackdropNode", "Viewer"]]

    # Encontrar las columnas, la columna principal y su grupo, y obtener las posiciones originales
    columnGroups, principal_nodes, principalGroup, original_positions = find_main_column(regular_nodes)
    
    if principal_nodes is None:
        undo.end()  # Cierra el grupo de Undo
        return  # Termina la ejecucion del metodo si no hay una columna principal

    # Imprimir el resultado de la lista de la columna principal
    debug_print_R("\n\n_________________________________________________________________________________\n")
    debug_print_R("Nodos en la columna principal:")
    for node in principal_nodes:
        debug_print_R(f"   {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")

    # Encontrar grupos basados en conexiones
    connection_groups = find_GR1(principal_nodes, selected_nodes)
    all_groups = connection_groups.copy()

    # Imprimir los resultados de los grupos basados en conexiones
    debug_print_R("\n\n_________\n")
    debug_print_R("\nGrupos basados en conexiones con la columna principal:")
    for group_name, nodes in connection_groups.items():
        debug_print_R(f"  {group_name}:")
        for node in nodes:
            debug_print_R(f"    {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")

    debug_print_R("\n\n_________________________________________________________________________________\n")
    
    # Bucle para encontrar y procesar nodos restantes hasta un maximo de 3 iteraciones
    max_iterations = 3
    for iteration in range(max_iterations):
        debug_print_R(f"\n\nBucando grupos GR2. Esta es la vez numero {iteration + 1}:\n")

        # Encontrar y procesar nodos GR2
        remaining_GR2_groups = find_remaining_GR2(principal_nodes, selected_nodes, all_groups)
        all_groups.update(remaining_GR2_groups)

        # Imprimir los resultados de los grupos GR2
        debug_print_R("\n_________\n\n")
        debug_print_R("Grupos GR2 creados:")
        for group_name, nodes in remaining_GR2_groups.items():
            debug_print_R(f"  {group_name} compuesto por estos nodos:")
            for node in nodes:
                debug_print_R(f"    {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")

        # Encontrar nuevos GR1 a partir de los GR2
        remaining_gr1_groups = find_remaining_GR1(principal_nodes, selected_nodes, all_groups)
        all_groups.update(remaining_gr1_groups)

        # Imprimir los resultados de los nuevos GR1
        debug_print_R("\n_________\n\n")
        debug_print_R("Nuevos GR1 encontrados:")
        for group_name, nodes in remaining_gr1_groups.items():
            debug_print_R(f"{group_name}:")
            for node in nodes:
                debug_print_R(f"  {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")

        # Comprobar si hay nodos restantes sin grupo
        remaining_nodes = [node for node in selected_nodes if node not in principal_nodes and not any(node in nodes for nodes in all_groups.values())]
        if not remaining_nodes:
            break  # Salir del bucle si no hay nodos restantes

        # Actualizar grupos para la siguiente iteracion
        connection_groups.update(remaining_GR2_groups)
        connection_groups.update(remaining_gr1_groups)

    # Renombrar los grupos eliminando "1" y "2" antes de la impresion final
    final_groups = {group_name.strip().replace("GR1-", "GR-").replace("GR2-", "GR-"): nodes for group_name, nodes in all_groups.items()}


    # Imprimir todos los grupos encontrados antes de la distribucion
    debug_print_R("\n\n_________________________________________________________________________________\n\n")
    debug_print_R("Todos los grupos encontrados (GR):")
    for group_name, nodes in final_groups.items():
        debug_print_R(f"  {group_name}:")
        for node in nodes:
            debug_print_R(f"    {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")

    # Numerar los grupos segun su ubicacion en columnas
    numerated_groups = rename_groups_by_proximity(principal_nodes, final_groups)

    # Ordenar los grupos numerados y eliminar cualquier nodo duplicado
    sorted_numerated_groups = sort_numerated_groups(numerated_groups, principal_nodes)

    # Imprimir todos los grupos numerados en orden
    debug_print_R("\n\n_________________________________________________________________________________\n")
    debug_print_R("Todos los grupos numerados y ordenados por Y (GR):")
    for group_name in sorted_numerated_groups:
        nodes = numerated_groups[group_name]
        debug_print_R(f"{group_name}:")
        for node in nodes:
            debug_print_R(f"  {node.name()}: Posicion X = {node.xpos() + node.screenWidth() / 2}, Posicion Y = {node.ypos()}")


    # Alinear nodos de la columna principal
    align_nodes_in_column(principal_nodes, 'h')

    # Llamar a la nueva funcion para alinear a todos los grupos
    align_grouped_nodes(numerated_groups)

    
    # Llamar a arrange nodes
    debug_message_C("Click en OK para hacer el arrange")
    arrange_nodes(principal_nodes, sorted_numerated_groups, numerated_groups, selected_nodes)
    

    # Alinear los nodos conectados entre si en caso de que no hayan quedado bien (si sucede, se mueven en Y los grupos)
    debug_message_C("Click en OK para hacer el align connected")
    align_connected_and_master(principal_nodes, sorted_numerated_groups, numerated_groups)    
    

    # Distribuir todos los grupos de uno a uno
    debug_message_C("Click en OK para hacer el distribute_Groups")
    distribute_Groups(sorted_numerated_groups, numerated_groups, selected_nodes)
    
    # Alinear los nodos conectados entre si en caso de que no hayan quedado bien (si sucede, se mueven en Y los grupos)
    debug_message_C("Click en OK para hacer el align connected DE NUEVO")
    align_connected_and_master(principal_nodes, sorted_numerated_groups, numerated_groups)      

    # Llamada a la nueva funcion antes de cerrar el undo
    debug_message_F("Click en OK para hacer el sort_columns_overlapping_nodes")
    sort_columns_overlapping_nodes(principalGroup, columnGroups, selected_nodes, numerated_groups, sorted_numerated_groups, original_positions)


    # Terminar el undo
    undo.end()




