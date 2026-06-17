"""
__________________________________________________________

  LGA_AutoStamps v0.01 | Lega
  Encuentra conexiones largas entre nodos y las reemplaza
  automaticamente por Stamps (Anchor + Wired) de Adrian Pueyo.

  v0.01 (simple):
    - Recorre todas las conexiones del script.
    - Mide la distancia entre el nodo origen (padre) y destino (hijo).
    - Si la distancia supera DISTANCE_THRESHOLD:
        * Crea un Anchor Stamp justo debajo del padre.
        * Crea un Wired Stamp justo arriba del hijo.
        * Reconecta: padre -> Anchor ... Wired -> hijo.
__________________________________________________________

"""

import os
import sys
import nuke

# ----------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------

# Distancia (en pixeles del Node Graph) a partir de la cual una conexion
# se considera "larga" y se reemplaza por Stamps. Medida entre los centros
# del nodo padre y el nodo hijo.
DISTANCE_THRESHOLD = 250

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
# HELPERS DE GEOMETRIA
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


# ----------------------------------------------------------------------
# LOGICA PRINCIPAL
# ----------------------------------------------------------------------

def find_long_connections(threshold):
    """
    Devuelve una lista de tuplas (origen, destino, input_index, distancia)
    para cada conexion cuyo largo supere el threshold.
    origen = nodo padre (la fuente).
    destino = nodo hijo (el que tiene al padre como input).
    """
    pairs = []
    for node in nuke.allNodes():
        if node.Class() in SKIP_CLASSES:
            continue
        for i in range(node.inputs()):
            src = node.input(i)
            if src is None:
                continue
            if src.Class() in SKIP_CLASSES:
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


def replace_connection_with_stamps(stamps, src, dst, input_index):
    """
    Reemplaza la conexion directa src -> dst por:
        src -> Anchor (debajo de src)  ...  Wired (arriba de dst) -> dst
    """
    deselect_all()

    # --- Anchor (padre) ---
    src.setSelected(True)
    title = derive_title(stamps, src)
    node_type = stamps.nodeType(stamps.realInput(src))

    anchor = stamps.anchor(
        title=title, tags=node_type, input_node=src, node_type=node_type
    )
    # anchor() NO setea el input internamente: lo conectamos explicitamente.
    anchor.setInput(0, src)

    # Posicionar el Anchor centrado y justo debajo del padre.
    ax = int(src.xpos() + src.screenWidth() / 2 - anchor.screenWidth() / 2)
    ay = int(src.ypos() + src.screenHeight() + ANCHOR_GAP_Y)
    anchor.setXYpos(ax, ay)
    debug_print("Anchor '{0}' creado en ({1},{2})".format(anchor.name(), ax, ay))

    # --- Wired (hijo) ---
    wired = stamps.wired(anchor)  # ya conecta su input 0 al anchor (hidden)

    # Posicionar el Wired centrado y justo arriba del hijo.
    wx = int(dst.xpos() + dst.screenWidth() / 2 - wired.screenWidth() / 2)
    wy = int(dst.ypos() - wired.screenHeight() - WIRED_GAP_Y)
    wired.setXYpos(wx, wy)
    debug_print("Wired '{0}' creado en ({1},{2})".format(wired.name(), wx, wy))

    # --- Reconectar el hijo al Wired (esto desconecta del padre) ---
    dst.setInput(input_index, wired)
    debug_print(
        "Reconectado: {0}.input({1}) -> {2}".format(
            dst.name(), input_index, wired.name()
        )
    )

    deselect_all()


def main():
    stamps = _import_stamps()
    if stamps is None:
        return

    pairs = find_long_connections(DISTANCE_THRESHOLD)

    if not pairs:
        debug_print("No se encontraron conexiones mas largas que {0}.".format(DISTANCE_THRESHOLD))
        nuke.message(
            "LGA_AutoStamps: no se encontraron conexiones mas largas que {0} px.".format(
                DISTANCE_THRESHOLD
            )
        )
        return

    nuke.Undo().begin("LGA_AutoStamps")
    try:
        for src, dst, input_index, dist in pairs:
            replace_connection_with_stamps(stamps, src, dst, input_index)
    finally:
        nuke.Undo().end()

    debug_print("LGA_AutoStamps: {0} conexion/es reemplazada/s.".format(len(pairs)))


if __name__ == "__main__":
    main()
