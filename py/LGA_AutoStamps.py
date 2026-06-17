"""
__________________________________________________________

  LGA_AutoStamps v0.05 | Lega
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

  v0.04:
    - Confirmacion por grupo: antes de dejar cada Stamp (padre + sus
      hijos), se crean los Stamps, se hace zoom a ellos y se muestra un
      cartel con el nombre sugerido (editable) y botones Reemplazar /
      Cancelar.
        * Cancelar revierte SOLO ese grupo (manual, sin tocar el Undo).
        * Todo corre dentro de un unico nuke.Undo(): un solo Ctrl+Z
          revierte todos los grupos aceptados.

  v0.05:
    - El zoom encuadra el CONTEXTO (el padre del padre = nodo origen, y
      los hijos de los hijos = nodos destino), no los Stamps solos.
    - ZOOM_OUT_FACTOR: variable para alejar mas el zoom y dar contexto.
    - El cartel es NO bloqueante: el usuario puede navegar el DAG
      mientras decide (event loop anidado).
__________________________________________________________

"""

import os
import sys
import nuke

from LGA_QtAdapter_ToolPack_Layout import QtWidgets, QtCore

# ----------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------

# Distancia (en pixeles del Node Graph) a partir de la cual una conexion
# directa se considera "larga" y se reemplaza por Stamps. Medida entre los
# centros del nodo padre y el nodo hijo.
DISTANCE_THRESHOLD = 250

# Cantidad minima de destinos finales para colapsar un arbol de Dots.
MIN_DESTINATIONS = 3

# Separacion vertical entre el padre y el Anchor que se crea debajo.
ANCHOR_GAP_Y = 40

# Separacion vertical entre el Wired y el hijo que tiene debajo.
WIRED_GAP_Y = 40

# Margen base para el zoom-to-fit (0.9 = deja un 10% de aire alrededor).
ZOOM_MARGIN = 0.9

# Cuanto MAS zoom out hacer para dar contexto al usuario.
#   1.0 = encuadre justo a los nodos (padre del padre + hijos de los hijos).
#   >1.0 = mas alejado / mas contexto alrededor (ej. 1.5 = 50% mas lejos).
ZOOM_OUT_FACTOR = 1.0

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
# HELPERS GENERALES
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


def node_label(n):
    """Devuelve la primera linea del label del nodo, limpia, o ''."""
    k = n.knob("label")
    if not k:
        return ""
    return k.value().split("\n")[0].strip()


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
    # Con los callbacks silenciados, seteamos el estilo a mano (esta conectado).
    try:
        stamps.wiredGetStyle(wired)
    except Exception:
        pass
    debug_print("Wired '{0}' creado en ({1},{2})".format(wired.name(), wx, wy))
    return wired


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


# ----------------------------------------------------------------------
# ZOOM + DIALOGO + TRANSACCION CANCELABLE (v0.04)
# ----------------------------------------------------------------------

def find_dag_widget():
    """Devuelve el widget del Node Graph (DAG) mas grande y visible."""
    try:
        candidates = [
            w for w in QtWidgets.QApplication.allWidgets()
            if w.objectName().startswith("DAG") and w.isVisible() and w.width() > 0
        ]
        if candidates:
            return max(candidates, key=lambda w: w.width() * w.height())
    except Exception:
        pass
    return None


def zoom_to_nodes(nodes, margin=ZOOM_MARGIN):
    """Ajusta zoom y scroll del DAG para que el conjunto de nodos entre lo mas
    grande posible (con un margen)."""
    nodes = [n for n in nodes if n is not None]
    if not nodes:
        return
    minx = min(n.xpos() for n in nodes)
    miny = min(n.ypos() for n in nodes)
    maxx = max(n.xpos() + n.screenWidth() for n in nodes)
    maxy = max(n.ypos() + n.screenHeight() for n in nodes)
    bw = max(maxx - minx, 1)
    bh = max(maxy - miny, 1)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    dag = find_dag_widget()
    if dag is not None:
        scale = min(dag.width() / float(bw), dag.height() / float(bh)) * margin
    else:
        scale = nuke.zoom()
    # Zoom out extra para dar contexto.
    if ZOOM_OUT_FACTOR and ZOOM_OUT_FACTOR > 0:
        scale = scale / float(ZOOM_OUT_FACTOR)
    nuke.zoom(scale, [cx, cy])
    try:
        QtWidgets.QApplication.processEvents()
    except Exception:
        pass


class ReplaceDialog(QtWidgets.QDialog):
    """Cartel simple: nombre del nuevo Stamp + Reemplazar / Cancelar."""

    def __init__(self, suggested_name, n_children, parent=None):
        super(ReplaceDialog, self).__init__(parent)
        self.setWindowTitle("LGA AutoStamps")
        # No bloqueante: el usuario puede navegar el DAG mientras esta abierto.
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        layout = QtWidgets.QVBoxLayout(self)

        hijos = "hijo" if n_children == 1 else "hijos"
        info = QtWidgets.QLabel("Nuevo Stamp  ({0} {1}):".format(n_children, hijos))
        layout.addWidget(info)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setText(suggested_name)
        self.name_edit.selectAll()
        self.name_edit.setMinimumWidth(260)
        layout.addWidget(self.name_edit)

        btns = QtWidgets.QHBoxLayout()
        self.cancel_btn = QtWidgets.QPushButton("Cancelar")
        self.replace_btn = QtWidgets.QPushButton("Reemplazar")
        self.replace_btn.setDefault(True)
        btns.addWidget(self.cancel_btn)
        btns.addStretch()
        btns.addWidget(self.replace_btn)
        layout.addLayout(btns)

        self.replace_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_name(self):
        return self.name_edit.text().strip()


def show_replace_dialog(suggested_name, n_children):
    """Muestra el cartel NO bloqueante posicionado en una esquina del DAG.
    Espera la respuesta con un event loop anidado (el DAG sigue navegable).
    Devuelve (accepted, name)."""
    dlg = ReplaceDialog(suggested_name, n_children)
    dlg.adjustSize()
    try:
        dag = find_dag_widget()
        if dag is not None:
            tl = dag.mapToGlobal(QtCore.QPoint(0, 0))
            dlg.move(tl.x() + 30, tl.y() + 30)
    except Exception:
        pass

    # Event loop anidado: bloquea el flujo del script pero NO la UI de Nuke,
    # asi el usuario puede pan/zoom/navegar el DAG mientras decide.
    loop = QtCore.QEventLoop()
    result = {"code": QtWidgets.QDialog.Rejected}

    def _on_finished(code):
        result["code"] = code
        loop.quit()

    dlg.finished.connect(_on_finished)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()
    loop.exec_()

    name = dlg.get_name()
    accepted = result["code"] == QtWidgets.QDialog.Accepted
    dlg.deleteLater()
    return accepted, name


def snapshot_dots(dots, children):
    """Captura lo necesario para recrear un conjunto de Dots y sus conexiones
    (internas entre ellos y de borde hacia source/destinos)."""
    dot_names = set(d.name() for d in dots)
    snaps = []
    for d in dots:
        up = d.input(0)
        up_name = up.name() if (up is not None and up.name() in dot_names) else None
        up_ext = up if (up is not None and up.name() not in dot_names) else None
        downstream_ext = [
            (dep, idx) for (dep, idx) in children.get(d, [])
            if dep.name() not in dot_names
        ]
        snaps.append({
            "name": d.name(),
            "xpos": d.xpos(),
            "ypos": d.ypos(),
            "label": d["label"].value() if d.knob("label") else "",
            "hide_input": bool(d.knob("hide_input") and d["hide_input"].value()),
            "tile_color": d["tile_color"].value() if d.knob("tile_color") else None,
            "up_name": up_name,    # input desde otro Dot del set
            "up_ext": up_ext,      # input desde un nodo externo (source)
            "downstream_ext": downstream_ext,  # destinos externos
        })
    return snaps


def restore_dots(snaps):
    """Recrea los Dots de un snapshot y restaura todas sus conexiones."""
    name_map = {}
    # 1) Recrear todos los Dots (con knobs)
    for s in snaps:
        d = nuke.nodes.Dot()
        d.setXYpos(s["xpos"], s["ypos"])
        if d.knob("label"):
            d["label"].setValue(s["label"])
        if d.knob("hide_input"):
            d["hide_input"].setValue(s["hide_input"])
        if s["tile_color"] is not None and d.knob("tile_color"):
            d["tile_color"].setValue(s["tile_color"])
        name_map[s["name"]] = d
    # 2) Restaurar nombres originales (ya estan libres por el delete)
    for s in snaps:
        try:
            name_map[s["name"]].setName(s["name"])
        except Exception:
            pass
    # 3) Restaurar inputs (internos entre Dots y externos hacia source)
    for s in snaps:
        d = name_map[s["name"]]
        if s["up_name"] is not None:
            d.setInput(0, name_map.get(s["up_name"]))
        elif s["up_ext"] is not None:
            try:
                d.setInput(0, s["up_ext"])
            except Exception:
                pass
    # 4) Restaurar destinos externos hacia los Dots
    for s in snaps:
        d = name_map[s["name"]]
        for (dep, idx) in s["downstream_ext"]:
            try:
                dep.setInput(idx, d)
            except Exception:
                pass


class GroupTx:
    """Transaccion de un grupo (Anchor + sus Wireds). Permite revertir SOLO
    ese grupo manualmente, sin crear un Undo aparte."""

    def __init__(self):
        self.created_nodes = []   # nodos a borrar en revert
        self.input_changes = []   # (node, idx, old_input) -> old debe sobrevivir
        self.knob_changes = []    # (node, knob_name, old_value)
        self.dot_snaps = []       # snapshots de Dots borrados

    def created(self, node):
        self.created_nodes.append(node)

    def change_input(self, node, idx, new_input):
        """Cambia un input cuyo valor previo SOBREVIVE (no es un Dot a borrar)."""
        self.input_changes.append((node, idx, node.input(idx)))
        node.setInput(idx, new_input)

    def change_knob(self, node, knob_name, value):
        self.knob_changes.append((node, knob_name, node[knob_name].value()))
        node[knob_name].setValue(value)

    def snapshot_and_delete_dots(self, dots, children):
        self.dot_snaps.extend(snapshot_dots(dots, children))
        for d in dots:
            try:
                nuke.delete(d)
            except Exception:
                pass

    def revert(self):
        # 1) Borrar nodos creados (desconecta automaticamente sus outputs)
        for n in self.created_nodes:
            try:
                nuke.delete(n)
            except Exception:
                pass
        # 2) Restaurar inputs cuyo valor previo sobrevive
        for (node, idx, old) in reversed(self.input_changes):
            try:
                node.setInput(idx, old)
            except Exception:
                pass
        # 3) Restaurar knobs
        for (node, kn, old) in reversed(self.knob_changes):
            try:
                node[kn].setValue(old)
            except Exception:
                pass
        # 4) Recrear los Dots borrados (esto reconecta los destinos)
        restore_dots(self.dot_snaps)
        debug_print("Grupo cancelado: revertido al estado original.")


def apply_title(anchor, wireds, name):
    """Aplica 'name' como titulo del Anchor y de todos sus Wireds."""
    if not name:
        return
    try:
        anchor["title"].setValue(name)
        if anchor.knob("prev_title"):
            anchor["prev_title"].setValue(name)
    except Exception:
        pass
    for w in wireds:
        try:
            w["title"].setValue(name)
            if w.knob("prev_title"):
                w["prev_title"].setValue(name)
        except Exception:
            pass


def confirm_group(tx, anchor, wireds, suggested_name, dests=None):
    """Zoom al CONTEXTO (el padre del padre = source, y los hijos de los hijos =
    destinos), muestra el cartel y aplica/revierte segun la respuesta.
    Devuelve True si se acepta, False si se cancela."""
    context = list(wireds) + [anchor]
    try:
        src = anchor.input(0)
        if src is not None:
            context.append(src)
    except Exception:
        pass
    if dests:
        context.extend(dests)
    zoom_to_nodes(context)
    accepted, name = show_replace_dialog(suggested_name, len(wireds))
    if accepted:
        try:
            current = anchor["title"].value()
        except Exception:
            current = ""
        if name and name != current:
            apply_title(anchor, wireds, name)
        return True
    tx.revert()
    return False


# ----------------------------------------------------------------------
# PASE 0: HIDDEN INPUTS (v0.03)
# ----------------------------------------------------------------------

def has_hidden_input(n):
    """True si el nodo tiene el knob hide_input activo y un input(0) real."""
    k = n.knob("hide_input")
    return bool(k and k.value() and n.input(0) is not None)


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


def process_hidden_group(stamps, source, pickups, children):
    """Procesa todos los hidden inputs que apuntan al mismo 'source' como un
    unico grupo (1 Anchor, N Wireds). Devuelve True si se acepta."""
    tx = GroupTx()

    # Titulo: primer label disponible entre los pickups, si no derivado del source.
    title = None
    for p in pickups:
        lbl = node_label(p)
        if lbl:
            title = lbl
            break
    if not title:
        title = derive_title(stamps, source)

    # Reuse: 1 Anchor por origen (reutiliza uno existente si ya lo hay).
    anchor = existing_anchor_for_source(stamps, source)
    if anchor is None:
        anchor = create_anchor_below(stamps, source, title=title)
        tx.created(anchor)

    wireds = []
    dests = []
    for node in pickups:
        if node.Class() == "Dot":
            # Borrar el Dot y reemplazarlo por un Wired en su posicion.
            wired = stamps.wired(anchor)
            wx = int(node.xpos() + node.screenWidth() / 2 - wired.screenWidth() / 2)
            wy = int(node.ypos() + node.screenHeight() / 2 - wired.screenHeight() / 2)
            wired.setXYpos(wx, wy)
            deselect_all()
            try:
                stamps.wiredGetStyle(wired)
            except Exception:
                pass
            tx.created(wired)
            # Reconectar lo que colgaba del Dot al Wired (old = Dot -> snapshot).
            for (dep, idx) in children.get(node, []):
                dep.setInput(idx, wired)
                dests.append(dep)
            tx.snapshot_and_delete_dots([node], children)
            wireds.append(wired)
        else:
            # No-Dot: no se borra; se le alimenta un Wired y se muestra el input.
            wired = create_wired_above(stamps, anchor, node)
            tx.created(wired)
            tx.change_input(node, 0, wired)  # old = source (sobrevive)
            if node.knob("hide_input"):
                tx.change_knob(node, "hide_input", False)
            wireds.append(wired)
            dests.append(node)

    return confirm_group(tx, anchor, wireds, title, dests)


def process_hidden_inputs(stamps):
    """Releva y procesa todos los hidden inputs, agrupados por nodo origen.
    Devuelve la cantidad de grupos aceptados."""
    children = build_children_map()
    pickups = find_hidden_inputs(stamps)

    # Agrupar por origen, preservando el orden de aparicion.
    groups = {}
    order = []
    for node in pickups:
        source = node.input(0)
        if source is None:
            continue
        if is_stamp(stamps, source) or source.Class() in SKIP_CLASSES:
            continue
        key = source.name()
        if key not in groups:
            groups[key] = {"source": source, "pickups": []}
            order.append(key)
        groups[key]["pickups"].append(node)

    debug_print(
        "Pase 0 (hidden inputs): {0} pickup/s -> {1} grupo/s a procesar.".format(
            len(pickups), len(order)
        )
    )
    accepted = 0
    for key in order:
        g = groups[key]
        if process_hidden_group(stamps, g["source"], g["pickups"], children):
            accepted += 1
    return accepted


# ----------------------------------------------------------------------
# PASE 1: DISTRIBUCIONES POR DOTS (v0.02)
# ----------------------------------------------------------------------

def collect_dot_tree(source, children):
    """
    Desde 'source', recorre SOLO a traves de Dots de ruteo y devuelve:
      - dots: lista de Dots que forman el arbol de distribucion.
      - leaves: lista de (destino, input_index) de los nodos reales (no Dot)
                alimentados por algun Dot del arbol.
    Los hijos directos no-Dot de 'source' NO se consideran (no son ruteo).
    Los Dots con hidden input se ignoran (los maneja el pase de hidden inputs).
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


def replace_dot_distribution_with_stamps(stamps, source, dots, leaves, children):
    """Colapsa un arbol de Dots: 1 Anchor + N Wireds, y borra los Dots.
    Devuelve True si se acepta."""
    tx = GroupTx()
    anchor = create_anchor_below(stamps, source)
    tx.created(anchor)
    try:
        title = anchor["title"].value()
    except Exception:
        title = source.name()

    wireds = []
    dests = []
    for (dst, idx) in leaves:
        wired = create_wired_above(stamps, anchor, dst)
        tx.created(wired)
        dst.setInput(idx, wired)  # old = un Dot (se borrara) -> snapshot
        wireds.append(wired)
        dests.append(dst)

    tx.snapshot_and_delete_dots(dots, children)
    return confirm_group(tx, anchor, wireds, title, dests)


def process_dot_distributions(stamps):
    """Releva y colapsa todas las distribuciones por Dots. Devuelve cuantas
    se aceptaron."""
    children = build_children_map()
    trees = find_dot_distributions(stamps, children, MIN_DESTINATIONS)
    debug_print("Pase 1 (distribuciones por Dots): {0} arbol/es.".format(len(trees)))
    accepted = 0
    for (source, dots, leaves) in trees:
        if replace_dot_distribution_with_stamps(stamps, source, dots, leaves, children):
            accepted += 1
    return accepted


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
    """Reemplaza una conexion directa larga por Anchor + Wired.
    Devuelve True si se acepta."""
    tx = GroupTx()
    anchor = create_anchor_below(stamps, src)
    tx.created(anchor)
    try:
        title = anchor["title"].value()
    except Exception:
        title = src.name()

    wired = create_wired_above(stamps, anchor, dst)
    tx.created(wired)
    tx.change_input(dst, input_index, wired)  # old = src (sobrevive)

    return confirm_group(tx, anchor, [wired], title, [dst])


def process_long_connections(stamps):
    """Releva y reemplaza todas las conexiones largas directas. Devuelve
    cuantas se aceptaron."""
    pairs = find_long_connections(stamps, DISTANCE_THRESHOLD)
    debug_print("Pase 2 (conexiones largas): {0} conexion/es.".format(len(pairs)))
    accepted = 0
    for (src, dst, input_index, dist) in pairs:
        if replace_connection_with_stamps(stamps, src, dst, input_index):
            accepted += 1
    return accepted


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    stamps = _import_stamps()
    if stamps is None:
        return

    # Silenciar los callbacks de Stamps durante toda la corrida: nosotros
    # manejamos las conexiones/titulos explicitamente. Esto evita que un
    # knobChanged dispare sobre un Wired ya borrado (crash dentro de stamps.py
    # al procesar eventos en el event loop no bloqueante) y tambien los popups
    # "update linked stamps title?" al renombrar.
    prev_lock = getattr(stamps, "Stamps_LockCallbacks", False)
    stamps.Stamps_LockCallbacks = True

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
        stamps.Stamps_LockCallbacks = prev_lock

    if total == 0:
        debug_print("LGA_AutoStamps: no se aplico ningun reemplazo.")
        nuke.message("LGA_AutoStamps: no se aplico ningun reemplazo.")
        return

    debug_print("LGA_AutoStamps: {0} grupo/s reemplazado/s.".format(total))


if __name__ == "__main__":
    main()
