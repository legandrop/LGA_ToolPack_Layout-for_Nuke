import nuke

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

def get_backdrops():
    return [n for n in nuke.allNodes() if n.Class() == "BackdropNode"]

def is_overlapping(a, b):
    ax, ay = a['xpos'].value(), a['ypos'].value()
    aw, ah = a['bdwidth'].value(), a['bdheight'].value()
    bx, by = b['xpos'].value(), b['ypos'].value()
    bw, bh = b['bdwidth'].value(), b['bdheight'].value()
    
    overlapping = not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)
    if overlapping:
        debug_print(f"Backdrops superpuestos: {a.name()} y {b.name()}")
    return overlapping

def is_inside(inner, outer):
    ix, iy = inner['xpos'].value(), inner['ypos'].value()
    iw, ih = inner['bdwidth'].value(), inner['bdheight'].value()
    ox, oy = outer['xpos'].value(), outer['ypos'].value()
    ow, oh = outer['bdwidth'].value(), outer['bdheight'].value()
    
    inside = (ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih)
    if inside:
        debug_print(f"{inner.name()} esta dentro de {outer.name()}")
    return inside

def get_area(backdrop):
    area = backdrop['bdwidth'].value() * backdrop['bdheight'].value()
    debug_print(f"Area de {backdrop.name()}: {area}")
    return area

def group_overlapping_backdrops(backdrops):
    groups = []
    for backdrop in backdrops:
        added_to_group = False
        for group in groups:
            if any(is_overlapping(backdrop, b) for b in group):
                group.append(backdrop)
                added_to_group = True
                break
        if not added_to_group:
            groups.append([backdrop])
    return groups

def order_group(group):
    debug_print(f"\nOrdenando grupo de {len(group)} backdrops")
    # Ordenar primero por area, de menor a mayor
    group.sort(key=get_area)
    
    ordered = []
    while group:
        current = group.pop(0)
        insert_index = len(ordered)  # Por defecto, insertar al final
        for i, ordered_backdrop in enumerate(ordered):
            if is_inside(current, ordered_backdrop):
                debug_print(f"{current.name()} esta dentro de {ordered_backdrop.name()}, insertando despues")
                insert_index = i + 1
            elif is_inside(ordered_backdrop, current):
                debug_print(f"{ordered_backdrop.name()} esta dentro de {current.name()}, insertando antes")
                insert_index = i
                break
            elif get_area(current) > get_area(ordered_backdrop):
                debug_print(f"{current.name()} es mas grande que {ordered_backdrop.name()}, insertando antes")
                insert_index = i
                break
        
        ordered.insert(insert_index, current)
        debug_print(f"Insertado {current.name()} en la posicion {insert_index}")
    
    return ordered

def order_all_backdrops():
    backdrops = get_backdrops()
    groups = group_overlapping_backdrops(backdrops)
    
    # Ordenar los grupos de manera determinista, por ejemplo, por el area total del grupo
    groups.sort(key=lambda g: sum(get_area(b) for b in g), reverse=True)
    
    ordered_groups = [order_group(group) for group in groups]
    
    # Asignacion global de z_order
    current_z = 0
    debug_print("\nNuevo orden de backdrops por grupos (de atras hacia adelante):")
    for group_index, group in enumerate(ordered_groups):
        debug_print(f"\nGrupo {group_index + 1}:")
        for i, backdrop in enumerate(group):
            backdrop['z_order'].setValue(current_z)
            debug_print(f"  {i+1}. {backdrop.name()} - Nuevo Z: {current_z}")
            current_z += 1  # Incrementar globalmente
    debug_print("\nSe han ajustado los valores Z de todos los backdrops de manera global.")
    
    return ordered_groups

# Esta parte solo se ejecutara si el script se ejecuta directamente
if __name__ == "__main__":
    ordered_groups = order_all_backdrops()
