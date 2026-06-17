"""
__________________________________________________________

  LGA_AutoStamps v0.90 | Lega
  Encuentra conexiones "sucias" entre nodos y las reemplaza
  automaticamente por Stamps (Anchor + Wired) de Adrian Pueyo.

  v0.10:
    - Conexiones largas directas (padre -> hijo) mas alla de un DISTANCE_THRESHOLD de distancia: se reemplazan por Anchor + Wired.

  v0.20:
    - Distribuciones por Dots: cuando un nodo reparte su salida a traves de un arbol de Dots hacia varios destinos, se borran los Dots y se crea 1 Anchor en el origen + 1 Wired por destino.

  v0.30:
    - Hidden inputs: nodos con 'hide_input' (conexion oculta a un origen lejano).
        * Si es un Dot: se borra y se reemplaza por un Wired.
        * Si es otro nodo: no se toca, solo se le alimenta un Wired.
        * Naming: si el nodo oculto tiene 'label', Anchor y Wired
          toman ese label; si no, el nombre derivado del origen.
        * Reuse: un solo Anchor por nodo origen (1 padre, N hijos).

  v0.40:
    - Confirmacion por grupo: antes de dejar cada Stamp (padre + sus hijos), se crean los Stamps, se hace zoom a ellos y se muestra un cartel con el nombre sugerido (editable) y botones Reemplazar / Cancelar.
        * Cancelar revierte SOLO ese grupo (manual, sin tocar el Undo).
        * Todo corre dentro de un unico nuke.Undo(): un solo Ctrl+Z
          revierte todos los grupos aceptados.

  v0.50:
    - El zoom encuadra el CONTEXTO (el padre del padre = nodo origen, y los hijos de los hijos = nodos destino), no los Stamps solos.
    - ZOOM_OUT_FACTOR: variable para alejar mas el zoom y dar contexto.
    - El cartel es NO bloqueante: el usuario puede navegar el DAG mientras decide (event loop anidado).

  v0.60:
    - Arquitectura two-phase:
        * Fase 1 (preview, con undo DESHABILITADO): crea Stamps, zoom, cartel, junta decisiones y revierte cada grupo.
        * Fase 2 (apply, con un unico nuke.Undo): re-aplica solo los aceptados, sin cartel.
      Asi los grupos cancelados no dejan "basura" en el historial y un solo Ctrl+Z deshace todo sin disparar la avalancha de errores de los callbacks de stamps.

  v0.70:
    - Cartel con estilo LGA_NodeLabel: frameless, fondo translucido, sombra, borde redondeado, barra de titulo arrastrable (drag & drop) y botones estilizados. Aparece centrado en el DAG.

  v0.80:
    - Hold-to-peek: manteniendo apretado el boton "Mantené apretado para ver lo que había" el cartel muestra las conexiones ORIGINALES; al soltarlo vuelve a mostrar los Stamps. Mismo encuadre para comparar A/B. Como la preview corre con undo deshabilitado, el toggle  revierte/reconstruye libremente sin ensuciar el historial.

  v0.90:
    - Ventana inicial de opciones para elegir que pases correr antes del preview.
    - Dialog de confirmacion en ingles con acciones explicitas: Skip, Apply y Apply & Stop.
    - Padding configurable por ventana y sin mensaje final cuando no se aplican cambios.
__________________________________________________________

"""

import os
import sys
import nuke

from LGA_QtAdapter_ToolPack_Layout import QtWidgets, QtGui, QtCore

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
ZOOM_OUT_FACTOR = 1.1

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
    # IMPORTANTE: NO seleccionar el source. Si hay un nodo seleccionado,
    # nuke.createNode hace "splice" e inserta el Anchor entre el source y su
    # primer dependiente, robandole el input a ese dependiente. Eso rompia el
    # cancel (el snapshot guardaba el Anchor como input original, y al borrarlo
    # quedaba la referencia muerta). Creamos el Anchor suelto y conectamos a mano.
    deselect_all()
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


# Estilo del cartel (copiado de LGA_NodeLabel para mantener consistencia visual).
DIALOG_SHADOW_BLUR = 25
DIALOG_SHADOW_OPACITY = 60
DIALOG_SHADOW_OFFSET = 3
DIALOG_SHADOW_MARGIN = 25
OPTIONS_DIALOG_PADDING_X = 18
OPTIONS_DIALOG_PADDING_Y = 14
REPLACE_DIALOG_PADDING_X = 18
REPLACE_DIALOG_PADDING_Y = 14

DIALOG_BUTTON_STYLE = """
    QPushButton {
        background-color: #404040;
        border: 1px solid #555555;
        border-radius: 5px;
        color: #CCCCCC;
        font-size: 12px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #505050;
    }
    QPushButton:pressed {
        background-color: #303030;
    }
"""


ACTION_SKIP = "skip"
ACTION_APPLY = "apply"
ACTION_APPLY_AND_STOP = "apply_and_stop"

PASS_HIDDEN_INPUTS = "hidden_inputs"
PASS_DOT_DISTRIBUTIONS = "dot_distributions"
PASS_LONG_CONNECTIONS = "long_connections"


class AutoStampsOptionsDialog(QtWidgets.QDialog):
    """Initial options dialog. Reuses the existing frameless dark style."""

    def __init__(self, parent=None):
        super(AutoStampsOptionsDialog, self).__init__(parent)
        self.drag_position = None

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Window
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setModal(False)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(
            DIALOG_SHADOW_MARGIN, DIALOG_SHADOW_MARGIN,
            DIALOG_SHADOW_MARGIN, DIALOG_SHADOW_MARGIN,
        )
        main_layout.setSpacing(0)

        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1f1f1f;
                border: 1px solid #555555;
                border-radius: 10px;
                color: #CCCCCC;
            }
            """
        )
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(DIALOG_SHADOW_BLUR)
        shadow.setColor(QtGui.QColor(0, 0, 0, DIALOG_SHADOW_OPACITY))
        shadow.setOffset(DIALOG_SHADOW_OFFSET, DIALOG_SHADOW_OFFSET)
        self.main_frame.setGraphicsEffect(shadow)

        frame_layout = QtWidgets.QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.title_bar = QtWidgets.QLabel("Auto Stamps")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(
            """
            QLabel {
                background-color: #1f1f1f;
                color: #cccccc;
                padding-left: 10px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
                font-weight: bold;
            }
            """
        )
        self.title_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.title_bar.mousePressEvent = self.start_move
        self.title_bar.mouseMoveEvent = self.move_window
        self.title_bar.mouseReleaseEvent = self.stop_move
        frame_layout.addWidget(self.title_bar)

        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1f1f1f;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            QCheckBox {
                background: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
            """
        )
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            OPTIONS_DIALOG_PADDING_X, OPTIONS_DIALOG_PADDING_Y,
            OPTIONS_DIALOG_PADDING_X, OPTIONS_DIALOG_PADDING_Y,
        )
        content_layout.setSpacing(8)

        search_label = QtWidgets.QLabel("Search for:")
        search_label.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: #CCCCCC; font-size: 12px; }"
        )
        content_layout.addWidget(search_label)

        self.hidden_inputs_check = QtWidgets.QCheckBox("Search hidden inputs")
        self.hidden_inputs_check.setToolTip(
            "Find nodes with hidden input connections and replace them with stamps."
        )
        self.hidden_inputs_check.setChecked(True)
        content_layout.addWidget(self.hidden_inputs_check)

        self.dot_distributions_check = QtWidgets.QCheckBox("Search dot distributions")
        self.dot_distributions_check.setToolTip(
            "Find Dot trees that distribute one source to multiple destinations."
        )
        self.dot_distributions_check.setChecked(True)
        content_layout.addWidget(self.dot_distributions_check)

        self.long_connections_check = QtWidgets.QCheckBox("Search long connections")
        self.long_connections_check.setToolTip(
            "Find direct connections longer than the distance threshold."
        )
        self.long_connections_check.setChecked(True)
        content_layout.addWidget(self.long_connections_check)

        content_layout.addSpacing(4)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setFixedHeight(30)
        self.cancel_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.setFixedHeight(30)
        self.start_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.start_button)
        content_layout.addLayout(buttons_layout)

        frame_layout.addWidget(content_widget)
        main_layout.addWidget(self.main_frame)
        self.setLayout(main_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.start_button.clicked.connect(self._start)

        self.adjustSize()

    def selected_passes(self):
        passes = set()
        if self.hidden_inputs_check.isChecked():
            passes.add(PASS_HIDDEN_INPUTS)
        if self.dot_distributions_check.isChecked():
            passes.add(PASS_DOT_DISTRIBUTIONS)
        if self.long_connections_check.isChecked():
            passes.add(PASS_LONG_CONNECTIONS)
        return passes

    def _start(self):
        if not self.selected_passes():
            nuke.message("Select at least one search option.")
            return
        self.accept()

    def start_move(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def move_window(self, event):
        if self.drag_position and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def stop_move(self, event):
        self.drag_position = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.reject()
        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self._start()
        else:
            super(AutoStampsOptionsDialog, self).keyPressEvent(event)


class ReplaceDialog(QtWidgets.QDialog):
    """Cartel para nombrar/confirmar un Stamp. Estilo LGA_NodeLabel: frameless,
    fondo translucido, sombra, barra de titulo arrastrable."""

    def __init__(self, suggested_name, n_children, on_peek_start=None,
                 on_peek_end=None, parent=None):
        super(ReplaceDialog, self).__init__(parent)
        self.drag_position = None
        self._on_peek_start = on_peek_start
        self._on_peek_end = on_peek_end
        self._peeking = False

        # Frameless + translucido + siempre on top + no bloqueante.
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Window
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setModal(False)

        # Layout principal con margen para la sombra.
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(
            DIALOG_SHADOW_MARGIN, DIALOG_SHADOW_MARGIN,
            DIALOG_SHADOW_MARGIN, DIALOG_SHADOW_MARGIN,
        )
        main_layout.setSpacing(0)

        # Frame principal con borde redondeado.
        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1f1f1f;
                border: 1px solid #555555;
                border-radius: 10px;
                color: #CCCCCC;
            }
            """
        )
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(DIALOG_SHADOW_BLUR)
        shadow.setColor(QtGui.QColor(0, 0, 0, DIALOG_SHADOW_OPACITY))
        shadow.setOffset(DIALOG_SHADOW_OFFSET, DIALOG_SHADOW_OFFSET)
        self.main_frame.setGraphicsEffect(shadow)

        frame_layout = QtWidgets.QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Barra de titulo arrastrable.
        self.title_bar = QtWidgets.QLabel("New Stamp")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(
            """
            QLabel {
                background-color: #1f1f1f;
                color: #cccccc;
                padding-left: 10px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
                font-weight: bold;
            }
            """
        )
        self.title_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.title_bar.mousePressEvent = self.start_move
        self.title_bar.mouseMoveEvent = self.move_window
        self.title_bar.mouseReleaseEvent = self.stop_move
        frame_layout.addWidget(self.title_bar)

        # Contenido.
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1f1f1f;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            """
        )
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            REPLACE_DIALOG_PADDING_X, REPLACE_DIALOG_PADDING_Y,
            REPLACE_DIALOG_PADDING_X, REPLACE_DIALOG_PADDING_Y,
        )
        content_layout.setSpacing(0)

        if n_children == 1:
            info_text = "This stamp will replace connections to 1 node."
        else:
            info_text = "This stamp will replace connections to {0} nodes.".format(
                n_children
            )
        info = QtWidgets.QLabel(info_text)
        info.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: #CCCCCC; font-size: 12px; }"
        )
        content_layout.addWidget(info)
        content_layout.addSpacing(8)

        name_label = QtWidgets.QLabel("Name:")
        name_label.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: #CCCCCC; font-size: 12px; }"
        )
        content_layout.addWidget(name_label)
        content_layout.addSpacing(4)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setText(suggested_name)
        self.name_edit.setMinimumWidth(280)
        self.name_edit.setFixedHeight(30)
        self.name_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                color: #CCCCCC;
                selection-background-color: #555555;
                selection-color: #FFFFFF;
            }
            """
        )
        content_layout.addWidget(self.name_edit)
        content_layout.addSpacing(10)

        # Botones.
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.skip_button = QtWidgets.QPushButton("Skip")
        self.skip_button.setFixedHeight(30)
        self.skip_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        self.apply_button = QtWidgets.QPushButton("Apply")
        self.apply_button.setFixedHeight(30)
        self.apply_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        self.apply_stop_button = QtWidgets.QPushButton("Apply & Stop")
        self.apply_stop_button.setFixedHeight(30)
        self.apply_stop_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        buttons_layout.addWidget(self.skip_button)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.apply_stop_button)
        content_layout.addLayout(buttons_layout)

        # Boton "mantener apretado" para ver lo que habia (hold-to-peek).
        content_layout.addSpacing(8)
        self.peek_button = QtWidgets.QPushButton(
            "Hold to preview original connections"
        )
        self.peek_button.setFixedHeight(30)
        self.peek_button.setStyleSheet(DIALOG_BUTTON_STYLE)
        content_layout.addWidget(self.peek_button)

        frame_layout.addWidget(content_widget)
        main_layout.addWidget(self.main_frame)
        self.setLayout(main_layout)

        self._action = ACTION_SKIP
        self.skip_button.clicked.connect(self.skip)
        self.apply_button.clicked.connect(self.apply)
        self.apply_stop_button.clicked.connect(self.apply_and_stop)
        self.name_edit.returnPressed.connect(self.apply)
        # pressed = mouse abajo (ver original); released = mouse arriba (ver Stamps).
        self.peek_button.pressed.connect(self._peek_start)
        self.peek_button.released.connect(self._peek_end)

        self.adjustSize()

    def get_name(self):
        return self.name_edit.text().strip()

    def get_action(self):
        return self._action

    def skip(self):
        self._action = ACTION_SKIP
        self.done(QtWidgets.QDialog.Rejected)

    def apply(self):
        self._action = ACTION_APPLY
        self.done(QtWidgets.QDialog.Accepted)

    def apply_and_stop(self):
        self._action = ACTION_APPLY_AND_STOP
        self.done(QtWidgets.QDialog.Accepted)

    # --- Hold to peek (ver original mientras se mantiene apretado el boton) ---
    def _peek_start(self):
        if not self._peeking:
            self._peeking = True
            if self._on_peek_start:
                self._on_peek_start()

    def _peek_end(self):
        if self._peeking:
            self._peeking = False
            if self._on_peek_end:
                self._on_peek_end()

    # --- Arrastre de la ventana por la barra de titulo ---
    def start_move(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def move_window(self, event):
        if self.drag_position and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def stop_move(self, event):
        self.drag_position = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.skip()
        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.apply()
        else:
            super(ReplaceDialog, self).keyPressEvent(event)

    def showEvent(self, event):
        super(ReplaceDialog, self).showEvent(event)
        self.activateWindow()
        self.raise_()
        self.name_edit.setFocus()
        self.name_edit.selectAll()


def center_dialog_on_dag(dlg):
    """Centra el cartel sobre el viewport del DAG (fallback: cursor)."""
    dlg.adjustSize()
    dag = find_dag_widget()
    if dag is not None:
        tl = dag.mapToGlobal(QtCore.QPoint(0, 0))
        cx = tl.x() + dag.width() // 2
        cy = tl.y() + dag.height() // 2
    else:
        cur = QtGui.QCursor.pos()
        cx, cy = cur.x(), cur.y()
    dlg.move(cx - dlg.width() // 2, cy - dlg.height() // 2)


def show_options_dialog():
    """Shows the initial options dialog. Returns a set of enabled passes, or None
    if the user cancels."""
    dlg = AutoStampsOptionsDialog()
    center_dialog_on_dag(dlg)

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

    if result["code"] == QtWidgets.QDialog.Accepted:
        selected = dlg.selected_passes()
    else:
        selected = None
    dlg.deleteLater()
    return selected


def show_replace_dialog(suggested_name, n_children, on_peek_start=None,
                        on_peek_end=None):
    """Muestra el cartel NO bloqueante centrado en el DAG. Espera la respuesta
    con un event loop anidado (el DAG sigue navegable).
    on_peek_start/on_peek_end: callbacks del hold-to-peek (ver original).
    Devuelve (action, name)."""
    dlg = ReplaceDialog(suggested_name, n_children, on_peek_start, on_peek_end)
    center_dialog_on_dag(dlg)

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
    action = dlg.get_action()
    dlg.deleteLater()
    return action, name


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


def group_context(anchor, wireds, dests):
    """Nodos a encuadrar: el padre del padre (source) + los hijos de los hijos
    (destinos), ademas de los Stamps."""
    context = list(wireds) + [anchor]
    try:
        src = anchor.input(0)
        if src is not None:
            context.append(src)
    except Exception:
        pass
    if dests:
        context.extend(dests)
    return context


def preview_group(build_fn):
    """Construye el grupo (build_fn re-detecta y arma), hace zoom UNA vez y
    muestra el cartel con hold-to-peek (mantener tecla = ver lo original).
    La preview SIEMPRE termina revertida (estado original).
    Devuelve (action, name, title)."""
    state = {"tx": None, "anchor": None, "wireds": None, "dests": None, "title": None}

    def to_stamps():
        # Reconstruye los Stamps si ahora se ve el original.
        if state["tx"] is None:
            built = build_fn()
            if built is None:
                return
            (state["tx"], state["anchor"], state["wireds"],
             state["dests"], state["title"]) = built

    def to_original():
        # Revierte al estado original (lo que habia).
        if state["tx"] is not None:
            state["tx"].revert()
            state["tx"] = None

    to_stamps()  # arranca mostrando los Stamps (resultado)
    if state["tx"] is None:
        return ACTION_SKIP, "", ""

    title = state["title"]
    # Zoom UNA sola vez al contexto, para comparar A/B en el mismo encuadre.
    zoom_to_nodes(group_context(state["anchor"], state["wireds"], state["dests"]))

    action, name = show_replace_dialog(
        title, len(state["wireds"]),
        on_peek_start=to_original, on_peek_end=to_stamps,
    )

    to_original()  # la preview no deja nada: el apply re-crea lo aceptado
    return action, name, title


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


def build_hidden_group(stamps, source, pickups, children):
    """Construye los Stamps para todos los hidden inputs que apuntan al mismo
    'source' (1 Anchor, N Wireds). NO muestra cartel ni revierte.
    Devuelve (tx, anchor, wireds, dests, title)."""
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

    return tx, anchor, wireds, dests, title


def hidden_groups(stamps):
    """Releva los hidden inputs agrupados por nodo origen.
    Devuelve (children_map, [(source, pickups), ...]) en orden de aparicion."""
    children = build_children_map()
    pickups = find_hidden_inputs(stamps)

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
        "Pase 0 (hidden inputs): {0} pickup/s -> {1} grupo/s.".format(
            len(pickups), len(order)
        )
    )
    return children, [(groups[k]["source"], groups[k]["pickups"]) for k in order]


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


def build_dot_distribution(stamps, source, dots, leaves, children):
    """Colapsa un arbol de Dots: 1 Anchor + N Wireds, y borra los Dots.
    NO muestra cartel ni revierte. Devuelve (tx, anchor, wireds, dests, title)."""
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
    return tx, anchor, wireds, dests, title


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


def build_long_connection(stamps, src, dst, input_index):
    """Reemplaza una conexion directa larga por Anchor + Wired.
    NO muestra cartel ni revierte. Devuelve (tx, anchor, wireds, dests, title)."""
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

    return tx, anchor, [wired], [dst], title


# ----------------------------------------------------------------------
# KEYS / CLAVES DE GRUPO  (para casar decisiones entre preview y apply)
# ----------------------------------------------------------------------

def key_hidden(source):
    return "H|" + source.name()


def key_dots(source):
    return "D|" + source.name()


def key_long(src, dst, idx):
    return "L|{0}|{1}|{2}".format(src.name(), dst.name(), idx)


# ----------------------------------------------------------------------
# RE-DETECCION POR IDENTIDAD (para el hold-to-peek: tras revertir, los Dots
# se recrean con referencias nuevas, asi que hay que volver a detectarlos)
# ----------------------------------------------------------------------

def redetect_hidden(stamps, source_name):
    """Devuelve (children, source, pickups) para el grupo de hidden inputs de
    'source_name', o None si ya no existe."""
    source = nuke.toNode(source_name)
    if source is None:
        return None
    children = build_children_map()
    pickups = [
        n for n in find_hidden_inputs(stamps)
        if n.input(0) is not None and n.input(0).name() == source_name
    ]
    if not pickups:
        return None
    return children, source, pickups


def redetect_dots(stamps, source_name):
    """Devuelve (children, source, dots, leaves) para el arbol de Dots de
    'source_name', o None si ya no califica."""
    source = nuke.toNode(source_name)
    if source is None:
        return None
    children = build_children_map()
    dots, leaves = collect_dot_tree(source, children)
    if len(leaves) < MIN_DESTINATIONS:
        return None
    return children, source, dots, leaves


# ----------------------------------------------------------------------
# FASE 1: PREVIEW  (con undo deshabilitado) -> junta decisiones
# ----------------------------------------------------------------------

def preview_all(stamps, enabled_passes):
    """Para cada grupo: construye los Stamps (re-detectables para el peek), hace
    zoom, muestra el cartel y registra la decision. preview_group revierte cada
    grupo. No se graba en el historial de undo (el llamador lo deshabilita).
    Devuelve un dict {clave: titulo_elegido} solo para los aceptados."""
    decisions = {}

    def handle(gkey, build_fn):
        action, name, title = preview_group(build_fn)
        if action in (ACTION_APPLY, ACTION_APPLY_AND_STOP):
            decisions[gkey] = name if name else title
        return action == ACTION_APPLY_AND_STOP

    # Pase 0: hidden inputs.
    if PASS_HIDDEN_INPUTS in enabled_passes:
        _, hgroups = hidden_groups(stamps)
        for (source, _pickups) in hgroups:
            sname = source.name()

            def build_fn(sname=sname):
                redet = redetect_hidden(stamps, sname)
                if redet is None:
                    return None
                ch, s, p = redet
                return build_hidden_group(stamps, s, p, ch)

            if handle(key_hidden(source), build_fn):
                return decisions

    # Pase 1: distribuciones por Dots.
    if PASS_DOT_DISTRIBUTIONS in enabled_passes:
        children = build_children_map()
        trees = find_dot_distributions(stamps, children, MIN_DESTINATIONS)
        debug_print(
            "Pase 1 (distribuciones por Dots): {0} arbol/es.".format(len(trees))
        )
        for (source, _dots, _leaves) in trees:
            sname = source.name()

            def build_fn(sname=sname):
                redet = redetect_dots(stamps, sname)
                if redet is None:
                    return None
                ch, s, d, l = redet
                return build_dot_distribution(stamps, s, d, l, ch)

            if handle(key_dots(source), build_fn):
                return decisions

    # Pase 2: conexiones largas directas.
    if PASS_LONG_CONNECTIONS in enabled_passes:
        pairs = find_long_connections(stamps, DISTANCE_THRESHOLD)
        debug_print("Pase 2 (conexiones largas): {0} conexion/es.".format(len(pairs)))
        for (src, dst, input_index, dist) in pairs:
            sname, dname, idx = src.name(), dst.name(), input_index

            def build_fn(sname=sname, dname=dname, idx=idx):
                s = nuke.toNode(sname)
                d = nuke.toNode(dname)
                if s is None or d is None:
                    return None
                return build_long_connection(stamps, s, d, idx)

            if handle(key_long(src, dst, input_index), build_fn):
                return decisions

    return decisions


# ----------------------------------------------------------------------
# FASE 2: APPLY  (con undo habilitado) -> re-aplica solo los aceptados
# ----------------------------------------------------------------------

def apply_all(stamps, accepted, enabled_passes):
    """Re-detecta los grupos (el grafo volvio al original tras el preview) y
    aplica SOLO los que el usuario acepto, sin cartel. Devuelve la cantidad."""
    total = 0

    # Pase 0: hidden inputs.
    if PASS_HIDDEN_INPUTS in enabled_passes:
        children, hgroups = hidden_groups(stamps)
        for (source, pickups) in hgroups:
            gkey = key_hidden(source)
            if gkey in accepted:
                tx, anchor, wireds, dests, title = build_hidden_group(
                    stamps, source, pickups, children
                )
                apply_title(anchor, wireds, accepted[gkey])
                total += 1

    # Pase 1: distribuciones por Dots.
    if PASS_DOT_DISTRIBUTIONS in enabled_passes:
        children = build_children_map()
        trees = find_dot_distributions(stamps, children, MIN_DESTINATIONS)
        for (source, dots, leaves) in trees:
            gkey = key_dots(source)
            if gkey in accepted:
                tx, anchor, wireds, dests, title = build_dot_distribution(
                    stamps, source, dots, leaves, children
                )
                apply_title(anchor, wireds, accepted[gkey])
                total += 1

    # Pase 2: conexiones largas directas.
    if PASS_LONG_CONNECTIONS in enabled_passes:
        pairs = find_long_connections(stamps, DISTANCE_THRESHOLD)
        for (src, dst, input_index, dist) in pairs:
            gkey = key_long(src, dst, input_index)
            if gkey in accepted:
                tx, anchor, wireds, dests, title = build_long_connection(
                    stamps, src, dst, input_index
                )
                apply_title(anchor, wireds, accepted[gkey])
                total += 1

    return total


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    stamps = _import_stamps()
    if stamps is None:
        return

    enabled_passes = show_options_dialog()
    if enabled_passes is None:
        return

    # Silenciar los callbacks de Stamps durante toda la corrida: nosotros
    # manejamos las conexiones/titulos explicitamente.
    prev_lock = getattr(stamps, "Stamps_LockCallbacks", False)
    stamps.Stamps_LockCallbacks = True

    try:
        # FASE 1: preview con undo DESHABILITADO. Todo lo que se crea/revierte
        # aca NO entra al historial de undo (asi los grupos cancelados no dejan
        # "basura" que luego, al hacer Ctrl+Z, dispara la avalancha de errores
        # de los callbacks de stamps al recrear nodos).
        nuke.Undo().disable()
        try:
            decisions = preview_all(stamps, enabled_passes)
        finally:
            nuke.Undo().enable()

        if not decisions:
            debug_print("LGA_AutoStamps: no se aplico ningun reemplazo.")
            return

        # FASE 2: apply con un unico nuke.Undo(). Solo creaciones limpias de los
        # grupos aceptados -> un solo Ctrl+Z deshace todo sin avalancha.
        nuke.Undo().begin("LGA_AutoStamps")
        try:
            total = apply_all(stamps, decisions, enabled_passes)
        finally:
            nuke.Undo().end()
    finally:
        stamps.Stamps_LockCallbacks = prev_lock

    debug_print("LGA_AutoStamps: {0} grupo/s reemplazado/s.".format(total))


if __name__ == "__main__":
    main()
