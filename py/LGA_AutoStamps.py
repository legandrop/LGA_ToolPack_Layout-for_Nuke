"""
__________________________________________________________

  LGA_AutoStamps v0.03 | Lega
  Encuentra conexiones "sucias" entre nodos y las reemplaza
  automaticamente por Stamps (Anchor + Wired) de Adrian Pueyo.

  v0.01:
    - Conexiones largas directas (padre -> hijo) mas alla de un
      threshold de distancia: se reemplazan por Anchor + Wired.

  v0.02:
    - Distribuciones por Dots: cuando un nodo reparte su salida a
      traves de un arbol de Dots hacia varios destinos, se borran
      los Dots y se crea 1 Anchor en el origen + 1 Wired por destino.

  v0.03:
    - Hidden inputs: nodos con 'hide_input' (conexion oculta a un
      origen lejano).
        * Si es un Dot: se borra y se reemplaza por un Wired.
        * Si es otro nodo: no se toca, solo se le alimenta un Wired.
        * Naming: si el nodo oculto tiene 'label', Anchor y Wired
          toman ese label; si no, el nombre derivado del origen.
        * Reuse: un solo Anchor por nodo origen (1 padre, N hijos).
__________________________________________________________

"""

import os
import sys
import nuke

# ----------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------

# Distancia (en pixeles del Node Graph) a partir de la cual una conexion
# directa se considera "larga" y se reemplaza por Stamps. Medida entre los
# centros del nodo padre y el nodo hijo.
DISTANCE_THRESHOLD = 250

# Cantidad minima de destinos finales para colapsar un arbol de Dots.
# (En el ejemplo del usuario son 3; con 2 ya conviene limpiar.)
MIN_DESTINATIONS = 3

# Separacion vertical entre el padre y el Anchor que se crea debajo.
ANCHOR_GAP_Y = 40

# Separacion vertical entre el Wired y el hijo que tiene debajo.
WIRED_GAP_Y = 40

# Clases de nodos que NO participan (ni como origen ni como destino).
SKIP_CLASSES = ["Viewer", "BackdropNode", "Root"]

# Variable global para activar o desactivar los prints
DEBUG = True


def debug_print(message):
    if DEBUG:
        print(message)


# ----------------------------------------------------------------------
# IMPORT DE STAMPS (Adrian Pueyo)
# ----------------------------------------------------------------------
# El modulo stamps suele estar ya importado en la sesion de Nuke (se carga
# al inicio desde CollectedTools_LGA). Por las dudas agregamos su path.

def _import_stamps():
    try:
        import stamps  # ya cargado en la sesion
        return stamps
    except ImportError:
        pass

    stamps_path = os.path.join(
        os.path.expanduser("~"), ".nuke", "CollectedTools_LGA", "stamps"
    )
    if os.path.isdir(stamps_path) and stamps_path not in sys.path:
        sys.path.insert(0, stamps_path)
    try:
        import stamps
        return stamps
    except ImportError:
        nuke.message(
            "LGA_AutoStamps: no se pudo importar el modulo 'stamps'.\n"
            "Verifica que la tool Stamps de Adrian Pueyo este instalada."
        )
        return None


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------

def node_center(n):
    """Centro (x, y) del nodo en coordenadas del Node Graph."""
    cx = n.xpos() + n.screenWidth() / 2.0
    cy = n.ypos() + n.screenHeight() / 2.0
    return cx, cy


def node_distance(a, b):
    """Distancia euclidea entre los centros de dos nodos."""
    ax, ay = node_center(a)
    bx, by = node_center(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def deselect_all():
    for n in nuke.selectedNodes():
        n.setSelected(False)


def is_stamp(stamps, n):
    """True si el nodo ya es un Anchor o un Wired de Stamps."""
    try:
        return stamps.isAnchor(n) or stamps.isWired(n)
    except Exception:
        return False


def derive_title(stamps, src):
    """Calcula un titulo razonable para el Anchor a partir del nodo origen."""
    title = src.name()
    try:
        real = stamps.realInput(src, stopOnLabel=True, mode="title")
        calc = stamps.getDefaultTitle(real)
        if calc:
            title = str(calc)
    except Exception:
        pass
    # Permitir override desde stamps_config.defaultTitle()
    try:
        custom = stamps.defaultTitle(src)
        if custom:
            title = str(custom)
    except Exception:
        pass
    return title


def create_anchor_below(stamps, source, title=None):
    """Crea un Anchor conectado a 'source' y lo posiciona justo debajo.
    Si 'title' es None, se deriva del nodo origen."""
    deselect_all()
    source.setSelected(True)
    if title is None:
        title = derive_title(stamps, source)
    node_type = stamps.nodeType(stamps.realInput(source))

    anchor = stamps.anchor(
        title=title, tags=node_type, input_node=source, node_type=node_type
    )
    # anchor() NO setea el input internamente: lo conectamos explicitamente.
    anchor.setInput(0, source)

    ax = int(source.xpos() + source.screenWidth() / 2 - anchor.screenWidth() / 2)
    ay = int(source.ypos() + source.screenHeight() + ANCHOR_GAP_Y)
    anchor.setXYpos(ax, ay)
    deselect_all()
    debug_print("Anchor '{0}' creado en ({1},{2})".format(anchor.name(), ax, ay))
    return anchor


def create_wired_above(stamps, anchor, dst):
    """Crea un Wired del 'anchor' y lo posiciona justo arriba de 'dst'."""
    wired = stamps.wired(anchor)  # ya conecta su input 0 al anchor (hidden)
    wx = int(dst.xpos() + dst.screenWidth() / 2 - wired.screenWidth() / 2)
    wy = int(dst.ypos() - wired.screenHeight() - WIRED_GAP_Y)
    wired.setXYpos(wx, wy)
    deselect_all()
    debug_print("Wired '{0}' creado en ({1},{2})".format(wired.name(), wx, wy))
    return wired


# ----------------------------------------------------------------------
# PASE 0: HIDDEN INPUTS (v0.03)
# ----------------------------------------------------------------------

def has_hidden_input(n):
    """True si el nodo tiene el knob hide_input activo y un input(0) real."""
    k = n.knob("hide_input")
    return bool(k and k.value() and n.input(0) is not None)


def node_label(n):
    """Devuelve la primera linea del label del nodo, limpia, o ''."""
    k = n.knob("label")
    if not k:
        return ""
    return k.value().split("\n")[0].strip()


def pickup_title(stamps, pickup, source):
    """Titulo para los Stamps de un hidden input.
    Regla del label: si el nodo oculto tiene label, se usa ese; si no, se
    deriva del nodo origen."""
    label = node_label(pickup)
    if label:
        return label
    return derive_title(stamps, source)


def existing_anchor_for_source(stamps, source):
    """Busca un Anchor ya existente cuyo input(0) sea 'source'. None si no hay."""
    try:
        for a in stamps.allAnchors():
            ai = a.input(0)
            if ai is not None and ai.name() == source.name():
                return a
    except Exception:
        pass
    return None


def get_or_create_anchor(stamps, source, title, registry):
    """Reuse: un solo Anchor por nodo origen. Devuelve el Anchor (lo crea si
    hace falta) usando 'title' solo cuando se crea por primera vez."""
    key = source.name()
    if key in registry:
        return registry[key]
    anchor = existing_anchor_for_source(stamps, source)
    if anchor is None:
        anchor = create_anchor_below(stamps, source, title=title)
    registry[key] = anchor
    return anchor


def find_hidden_inputs(stamps):
    """Devuelve la lista de nodos con hidden input (excluyendo Stamps, que
    tambien usan hide_input por diseno)."""
    pickups = []
    for n in nuke.allNodes():
        if n.Class() in SKIP_CLASSES:
            continue
        if is_stamp(stamps, n):
            continue
        if has_hidden_input(n):
            pickups.append(n)
    return pickups


def replace_hidden_dot(stamps, dot, anchor, children):
    """Borra un Dot con hidden input y lo reemplaza por un Wired (en la misma
    posicion). Los nodos que colgaban del Dot se reconectan al Wired."""
    dot_name = dot.name()  # capturar antes de borrar
    wired = stamps.wired(anchor)
    wx = int(dot.xpos() + dot.screenWidth() / 2 - wired.screenWidth() / 2)
    wy = int(dot.ypos() + dot.screenHeight() / 2 - wired.screenHeight() / 2)
    wired.setXYpos(wx, wy)
    deselect_all()

    for (dep, idx) in children.get(dot, []):
        dep.setInput(idx, wired)
        debug_print(
            "Reconectado: {0}.input({1}) -> {2}".format(dep.name(), idx, wired.name())
        )

    nuke.delete(dot)
    debug_print("Dot oculto '{0}' borrado y reemplazado por Wired.".format(dot_name))


def feed_wired_into_node(stamps, node, anchor):
    """Para un nodo no-Dot con hidden input: NO se borra. Se crea un Wired
    arriba y se conecta a su input(0). Se muestra el input (hide_input=False)
    para que la conexion corta sea visible."""
    wired = create_wired_above(stamps, anchor, node)
    node.setInput(0, wired)
    try:
        node["hide_input"].setValue(False)
    except Exception:
        pass
    debug_print(
        "Nodo '{0}' (hidden input) alimentado por Wired '{1}'.".format(
            node.name(), wired.name()
        )
    )


def process_hidden_inputs(stamps):
    """Releva y procesa todos los hidden inputs. Devuelve la cantidad.
    Reuse de Anchor por nodo origen via 'registry'."""
    children = build_children_map()
    pickups = find_hidden_inputs(stamps)
    registry = {}  # source.name() -> Anchor
    count = 0

    for node in pickups:
        source = node.input(0)
        if source is None:
            continue
        # No tiene sentido anclar a un Stamp o a clases ignoradas.
        if is_stamp(stamps, source) or source.Class() in SKIP_CLASSES:
            continue

        is_dot = node.Class() == "Dot"
        # Nota: un Dot oculto sin nada colgando igual se convierte; es un
        # pickup que el compositor coloco a proposito (preservamos el punto).

        title = pickup_title(stamps, node, source)
        anchor = get_or_create_anchor(stamps, source, title, registry)

        if is_dot:
            replace_hidden_dot(stamps, node, anchor, children)
        else:
            feed_wired_into_node(stamps, node, anchor)
        count += 1

    return count


# ----------------------------------------------------------------------
# PASE 1: DISTRIBUCIONES POR DOTS (v0.02)
# ----------------------------------------------------------------------

def build_children_map():
    """
    Devuelve un dict { nodo : [(downstream, input_index), ...] } a partir de
    todas las conexiones actuales del script.
    """
    children = {}
    for n in nuke.allNodes():
        for i in range(n.inputs()):
            inp = n.input(i)
            if inp is None:
                continue
            children.setdefault(inp, []).append((n, i))
    return children


def collect_dot_tree(source, children):
    """
    Desde 'source', recorre SOLO a traves de Dots y devuelve:
      - dots: lista de Dots que forman el arbol de distribucion.
      - leaves: lista de (destino, input_index) de los nodos reales (no Dot)
                alimentados por algun Dot del arbol.
    Los hijos directos no-Dot de 'source' NO se consideran (no son ruteo).
    Los Dots con hidden input se ignoran: son pickups remotos que maneja
    el pase de hidden inputs, no ruteo visible.
    """
    dots = []
    leaves = []
    seen_dots = set()       # por nombre
    seen_leaves = set()     # por (nombre, idx)

    def is_routing_dot(n):
        if n.Class() != "Dot":
            return False
        k = n.knob("hide_input")
        return not (k and k.value())

    stack = []
    # Arranque: solo seguimos los Dots (de ruteo) colgados del source.
    for (dep, idx) in children.get(source, []):
        if is_routing_dot(dep) and dep.name() not in seen_dots:
            seen_dots.add(dep.name())
            dots.append(dep)
            stack.append(dep)

    while stack:
        cur = stack.pop()
        for (dep, idx) in children.get(cur, []):
            if dep.Class() == "Dot":
                if not is_routing_dot(dep):
                    continue  # pickup oculto: lo ignora este pase
                if dep.name() not in seen_dots:
                    seen_dots.add(dep.name())
                    dots.append(dep)
                    stack.append(dep)
            else:
                key = (dep.name(), idx)
                if key not in seen_leaves:
                    seen_leaves.add(key)
                    leaves.append((dep, idx))

    return dots, leaves


def find_dot_distributions(stamps, children, min_destinations):
    """
    Busca todos los nodos origen que reparten su salida via Dots hacia
    >= min_destinations destinos. Devuelve lista de (source, dots, leaves).
    Los arboles son disjuntos (un Dot tiene un solo input), asi que se
    pueden procesar todos despues de relevarlos.
    """
    results = []
    for node in nuke.allNodes():
        if node.Class() == "Dot":
            continue
        if node.Class() in SKIP_CLASSES:
            continue
        if is_stamp(stamps, node):
            continue
        dots, leaves = collect_dot_tree(node, children)
        if len(leaves) >= min_destinations:
            results.append((node, dots, leaves))
            debug_print(
                "Distribucion por Dots: '{0}' -> {1} destino/s via {2} Dot/s".format(
                    node.name(), len(leaves), len(dots)
                )
            )
    return results


def replace_dot_distribution_with_stamps(stamps, source, dots, leaves):
    """
    Colapsa un arbol de Dots:
      source -> Anchor (debajo)  ...  N Wireds (uno arriba de cada destino).
    Luego borra todos los Dots del arbol.
    """
    anchor = create_anchor_below(stamps, source)

    for (dst, idx) in leaves:
        wired = create_wired_above(stamps, anchor, dst)
        dst.setInput(idx, wired)
        debug_print(
            "Reconectado: {0}.input({1}) -> {2}".format(dst.name(), idx, wired.name())
        )

    for d in dots:
        try:
            nuke.delete(d)
        except Exception:
            pass
    debug_print("Borrados {0} Dot/s del arbol de '{1}'.".format(len(dots), source.name()))


def process_dot_distributions(stamps):
    """Releva y colapsa todas las distribuciones por Dots. Devuelve la cantidad."""
    children = build_children_map()
    trees = find_dot_distributions(stamps, children, MIN_DESTINATIONS)
    for (source, dots, leaves) in trees:
        replace_dot_distribution_with_stamps(stamps, source, dots, leaves)
    return len(trees)


# ----------------------------------------------------------------------
# PASE 2: CONEXIONES LARGAS DIRECTAS (v0.01)
# ----------------------------------------------------------------------

def find_long_connections(stamps, threshold):
    """
    Devuelve [(origen, destino, input_index, distancia), ...] para conexiones
    directas (sin Dots ni Stamps de por medio) cuyo largo supere el threshold.
    """
    pairs = []
    for node in nuke.allNodes():
        if node.Class() in SKIP_CLASSES or node.Class() == "Dot":
            continue
        if is_stamp(stamps, node):
            continue
        for i in range(node.inputs()):
            src = node.input(i)
            if src is None:
                continue
            if src.Class() in SKIP_CLASSES or src.Class() == "Dot":
                continue
            if is_stamp(stamps, src):
                continue
            dist = node_distance(src, node)
            if dist > threshold:
                pairs.append((src, node, i, dist))
                debug_print(
                    "Conexion larga: {0} -> {1} (input {2}) dist={3:.0f}".format(
                        src.name(), node.name(), i, dist
                    )
                )
    return pairs


def replace_connection_with_stamps(stamps, src, dst, input_index):
    """
    Reemplaza la conexion directa src -> dst por:
        src -> Anchor (debajo de src)  ...  Wired (arriba de dst) -> dst
    """
    anchor = create_anchor_below(stamps, src)
    wired = create_wired_above(stamps, anchor, dst)
    dst.setInput(input_index, wired)
    debug_print(
        "Reconectado: {0}.input({1}) -> {2}".format(dst.name(), input_index, wired.name())
    )


def process_long_connections(stamps):
    """Releva y reemplaza todas las conexiones largas directas. Devuelve la cantidad."""
    pairs = find_long_connections(stamps, DISTANCE_THRESHOLD)
    for (src, dst, input_index, dist) in pairs:
        replace_connection_with_stamps(stamps, src, dst, input_index)
    return len(pairs)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    stamps = _import_stamps()
    if stamps is None:
        return

    nuke.Undo().begin("LGA_AutoStamps")
    total = 0
    try:
        # Pase 0: hidden inputs (conexiones ocultas). Va primero para que los
        # otros pases no los pisen (los Wireds nuevos ya son Stamps).
        total += process_hidden_inputs(stamps)
        # Pase 1: distribuciones por Dots (un origen -> muchos destinos).
        total += process_dot_distributions(stamps)
        # Pase 2: conexiones largas directas (sin Dots).
        total += process_long_connections(stamps)
    finally:
        nuke.Undo().end()

    if total == 0:
        debug_print("LGA_AutoStamps: no se encontro nada para reemplazar.")
        nuke.message("LGA_AutoStamps: no se encontro nada para reemplazar.")
        return

    debug_print("LGA_AutoStamps: {0} caso/s reemplazado/s.".format(total))


if __name__ == "__main__":
    main()
