import nuke
from PySide2 import QtCore, QtGui, QtWidgets, QtOpenGL
import re
from collections import namedtuple

DAG_TITLE = "Node Graph"
DAG_OBJECT_NAME = "DAG"

Direction = namedtuple("Direction", "axis, descending, center")
AXIS_X = 0
AXIS_Y = 1
RIGHT = Direction(axis=AXIS_X, descending=False, center=False)
LEFT = Direction(axis=AXIS_X, descending=True, center=False)
DOWN = Direction(axis=AXIS_Y, descending=False, center=False)
UP = Direction(axis=AXIS_Y, descending=True, center=False)
CENTER_X = Direction(axis=AXIS_X, descending=False, center=True)
CENTER_Y = Direction(axis=AXIS_Y, descending=False, center=True)


class NodeWrapper(object):
    """Wraps a nuke node with its bounds, and exposes all the methods from QRectF to be used on the node"""

    def __init__(self, node):
        """
        Args:
            node (nuke.Node): Node to wrap
        """
        self.bounds = get_node_bounds(node)
        self.node = node
        self.is_backdrop = node.Class() == "BackdropNode"
        self._nodes_and_margins = None  # For backdrops only

    def __getattr__(self, item):
        try:
            attr = getattr(self.bounds, item)
        except AttributeError:
            return getattr(self.node, item)
        if callable(attr):
            return self._wrapped(attr)
        return attr

    def _wrapped(self, func):
        def wrapper(*args, **kwargs):
            before_size = self.bounds.size()
            result = func(*args, **kwargs)
            self._commit_move()
            if self.bounds.size() != before_size:
                self._commit_resize()
            return result

        return wrapper

    def _commit_move(self):
        new_pos = self.bounds.topLeft().toPoint()
        self.node.setXYpos(new_pos.x(), new_pos.y())

    def _commit_resize(self):
        if not self.is_backdrop:
            raise NotImplementedError(
                "Tried to resize a node other than a backdrop, which is not supported. You may get unexpected results."
            )
        self._commit_move()
        self.node["bdwidth"].setValue(int(self.bounds.width()))
        self.node["bdheight"].setValue(int(self.bounds.height()))

    def normalize(self):
        self.bounds = self.bounds.normalized()
        self._commit_move()
        self._commit_resize()

    def move_center(self, value, axis):
        """Extra method to allow moving a node center based on a single axis

        Args:
            value (int): New center position
            axis (int): Axis index, 0 for X, 1 for Y
        """
        current_center = list(self.center().toTuple())
        t = current_center[:]
        current_center[axis] = value
        self.moveCenter(QtCore.QPoint(*current_center))

    def store_margins(self):
        if not self.is_backdrop:
            raise NotImplementedError(
                "Tried to calculate margins on a non-backdrop node"
            )
        nodes = self.node.getNodes()
        nodes_bounds = get_nodes_bounds(nodes)
        margins = calculate_bounds_adjustment(nodes_bounds, self)
        self._nodes_and_margins = {"nodes": nodes, "margins": margins}

    def restore_margins(self):
        if not self.is_backdrop:
            raise NotImplementedError("Tried to set margins on a non-backdrop node")
        if not self._nodes_and_margins:
            raise RuntimeError("No margins were saved for this backdrop, can't restore")
        nodes_bounds = get_nodes_bounds(self._nodes_and_margins["nodes"])
        nodes_bounds.adjust(*self._nodes_and_margins["margins"])
        self.setCoords(*nodes_bounds.getCoords())

    def place_around_nodes(self, nodes, padding=50):
        if not self.is_backdrop:
            raise NotImplementedError("Can only place backdrops around nodes")
        if not nodes:
            return
        label_height = get_label_size(self.node).height()
        nodes_bounds = get_nodes_bounds(nodes)
        nodes_bounds.adjust(-padding, -(padding + label_height), padding, padding)
        self.setCoords(*nodes_bounds.getCoords())


# Group Dags
def get_dag_widgets(visible=True):
    """
    Gets all Qt objects with DAG in the object name

    Args:
        visible (bool): Whether or not to return only visible widgets.

    Returns:
        list[QtWidgets.QWidget]
    """
    dags = []
    all_widgets = QtWidgets.QApplication.instance().allWidgets()
    for widget in all_widgets:
        if DAG_OBJECT_NAME in widget.objectName():
            if not visible or (visible and widget.isVisible()):
                dags.append(widget)
    return dags


def get_current_dag():
    """
    Returns:
        QtWidgets.QWidget: The currently active DAG
    """
    visible_dags = get_dag_widgets(visible=True)
    for dag in visible_dags:
        if dag.hasFocus():
            return dag

    # IF None had focus, and we have at least one, use the first one
    if visible_dags:
        return visible_dags[0]
    return None


def get_dag_node(dag_widget):
    """Get a DAG node for a given dag widget."""
    title = str(dag_widget.windowTitle())
    if DAG_TITLE not in title:
        return None
    if title == DAG_TITLE:
        return nuke.root()
    return nuke.toNode(title.replace(" " + DAG_TITLE, ""))


# Bounds functions
def get_node_bounds(node):
    """
    Return a QRectF corresponding to the node dag bounding box / position

    Note: There is a bug in nuke when a freshly created node is being moved where the width/height
    collapses to 0:

        node = nuke.nodes.Grade()
        node.setXYpos(0, 0)
        print node.screenWidth(), node.screenHeight()
        # Result: 0 0
        # Result should be: 80 20

    We handle this in the code

    :param nuke.Node node: Nuke node to get bounds for
    :rtype: QtCore.QRectF
    """
    if isinstance(node, NodeWrapper):
        return node.bounds
    if node.Class() == "BackdropNode":
        width = node["bdwidth"].value()
        height = node["bdheight"].value()
    else:
        width = node.screenWidth()
        height = node.screenHeight()

    if width == 0:  # Handle a bug as mentioned in docstring
        temp_node = getattr(
            nuke.nodes, node.Class()
        )()  # Make temp node with same class as corrupted node
        try:
            return get_node_bounds(temp_node)
        finally:
            nuke.delete(temp_node)

    return QtCore.QRectF(node.xpos(), node.ypos(), width, height)


def get_nodes_bounds(nodes, center_only=False):
    """
    Get the combined DAG bounding box of all the nodes in the list

    Args:
        nodes (list): List of nuke nodes to get bounds for
        center_only (bool): If True, get the bounding rectangle that encompasses the center points of the nodes

    Returns:
        QtCore.QRectF
    """
    if not nodes:
        raise ValueError("No nodes provided to get_nodes_bounds()")
    all_bounds = [get_node_bounds(n) for n in nodes]
    if center_only:
        poly = QtGui.QPolygon([n.center().toPoint() for n in all_bounds])
        return poly.boundingRect()
    bounds = QtCore.QRectF(
        all_bounds[0]
    )  # Make a new rect so we don't modify the initial one
    for bound in all_bounds[1:]:
        bounds |= bound
    return bounds


def calculate_bounds_adjustment(bounds, target_bounds):
    """Calculate adjust values to apply to 'bounds' in order to match 'target_bounds'

    Args:
        bounds (QtCore.QRectF or NodeWrapper): Original Bounds
        target_bounds (QtCore.QRectF or NodeWrapper): Desired Bounds

    Returns:
        tuple[int, int, int, int]: Bounds adjustments
    """
    bounds_coords = bounds.getCoords()
    target_coords = target_bounds.getCoords()
    return tuple(target_coords[i] - bounds_coords[i] for i in range(4))


def get_label_size(node):
    """Calculate the size of a label for a nuke Node

    Args:
        node (nuke.Node):

    Returns:
        QtCore.QSize: Size of the label
    """
    regex = r"^(.+?)( Bold)?( Italic)?$"
    match = re.match(regex, node["note_font"].value())
    font = QtGui.QFont(match.group(1))
    font.setBold(bool(match.group(2)))
    font.setItalic(bool(match.group(3)))
    font.setPixelSize(node["note_font_size"].value())
    metrics = QtGui.QFontMetrics(font)
    return metrics.size(0, node["label"].value())


class ScaleWidget(QtWidgets.QWidget):
    class _VectorWrapper(object):
        def __init__(self, node, bounds, corner=None):
            """
            Store a NodeWrapper and its relative position to the bounds for simplified manipulation.

            :param dag_utils.dag.NodeWrapper node:
            :param QtCore.QRectF bounds: bounds to calculating relative position to
            :param int corner: (Optional)
            """

            def _clamp(v):
                """Clamp vector between 0 and 1"""
                return QtGui.QVector2D(
                    0 if v.x() < 0 else 1 if v.x() > 1 else v.x(),
                    0 if v.y() < 0 else 1 if v.y() > 1 else v.y(),
                )

            self.node_wrapper = node
            self.corner = corner
            self.original_point = self.get_point()
            # Store the corner coordinates relative to the bounds, saves us from calculating it in event loop
            bs = QtGui.QVector2D(
                bounds.size().width(), bounds.size().height()
            )  # bounds size
            vector = (
                QtGui.QVector2D(self.get_point()) - QtGui.QVector2D(bounds.topLeft())
            ) / bs
            self.vector = _clamp(vector)
            self.offset = (vector - self.vector) * bs

        def get_point(self):
            """Return QPoint corresponding to one of the 4 corners or the center of the node"""
            if self.corner is None:
                return self.node_wrapper.center()
            elif self.corner == 0:
                return self.node_wrapper.topLeft()
            elif self.corner == 1:
                return self.node_wrapper.topRight()
            elif self.corner == 2:
                return self.node_wrapper.bottomRight()
            return self.node_wrapper.bottomLeft()

        def move(self, new_point, grid_size=None):
            """Apply the transformation to the node"""
            if grid_size:
                new_point = self._snap_to_grid(new_point, grid_size)
            if self.corner is None:
                self.node_wrapper.moveCenter(new_point)
            elif self.corner == 0:
                self.node_wrapper.setTopLeft(new_point)
            elif self.corner == 1:
                self.node_wrapper.setTopRight(new_point)
            elif self.corner == 2:
                self.node_wrapper.setBottomRight(new_point)
            else:
                self.node_wrapper.setBottomLeft(new_point)
                self.node_wrapper.normalize()  # We've moved all corners, normalize the backdrop

        def _snap_to_grid(self, new_point, grid_size):
            old = QtGui.QVector2D(self.original_point)
            new = QtGui.QVector2D(new_point)
            offset = (new - old) / grid_size
            return (old + QtGui.QVector2D(offset.toPoint()) * grid_size).toPoint()

    handles_cursors = (
        QtCore.Qt.SizeFDiagCursor,
        QtCore.Qt.SizeVerCursor,
        QtCore.Qt.SizeBDiagCursor,
        QtCore.Qt.SizeHorCursor,
    )

    def __init__(self, dag_widget):
        super(ScaleWidget, self).__init__(parent=dag_widget)

        # Group context
        self.dag_node = get_dag_node(
            self.parent()
        )  # 'dag_widget', but it's garbage collected..

        # Make Widget transparent
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Enable mouse tracking so we can get move move events
        self.setMouseTracking(True)

        # Overlay it with the DAG exactly
        dag_rect = dag_widget.geometry()
        dag_rect.moveTopLeft(dag_widget.parentWidget().mapToGlobal(dag_rect.topLeft()))
        self.setGeometry(dag_rect)

        # Attributes
        self.transform = None
        self.grabbed_handle = None

        # Corregir el problema del context manager
        if self.dag_node and hasattr(self.dag_node, "begin"):
            self.dag_node.begin()
            try:
                self.nodes = nuke.selectedNodes()
            finally:
                self.dag_node.end()
        else:
            self.nodes = nuke.selectedNodes()

        self.bounds = get_nodes_bounds(self.nodes, center_only=True)
        visual_bounds = get_nodes_bounds(self.nodes) + (QtCore.QMargins() + 10)
        adjustment = calculate_bounds_adjustment(self.bounds, visual_bounds)
        self.margins = QtCore.QMargins(
            adjustment[0] * -1, adjustment[1] * -1, adjustment[2], adjustment[3]
        )
        self.coordinates = self.store_coordinates()
        self.undo = None

        self.translate_mode = False
        self.move_all = False
        prefs = nuke.toNode("preferences")

        self.snap_to_grid = prefs["SnapToGrid"].value()
        self.grid_size = QtGui.QVector2D(
            max(prefs["GridWidth"].value(), 1), max(prefs["GridHeight"].value(), 1)
        )

    def store_coordinates(self):
        """Get the coordinates of all nodes and store them in a VectorWrapper"""
        all_coords = []

        # Corregir el problema del context manager
        if self.dag_node and hasattr(self.dag_node, "begin"):
            self.dag_node.begin()
            try:
                for node in nuke.allNodes():
                    node_wrapper = NodeWrapper(node)
                    if node_wrapper.is_backdrop:
                        all_coords += [
                            self._VectorWrapper(node_wrapper, self.bounds, corner)
                            for corner in range(4)
                        ]
                    else:
                        all_coords.append(
                            self._VectorWrapper(node_wrapper, self.bounds)
                        )
            finally:
                self.dag_node.end()
        else:
            for node in nuke.allNodes():
                node_wrapper = NodeWrapper(node)
                if node_wrapper.is_backdrop:
                    all_coords += [
                        self._VectorWrapper(node_wrapper, self.bounds, corner)
                        for corner in range(4)
                    ]
                else:
                    all_coords.append(self._VectorWrapper(node_wrapper, self.bounds))
        return all_coords

    def reset_state(self):
        """Re-grab the coordinates of all the nodes"""
        self.grabbed_handle = None
        self.coordinates = self.store_coordinates()

    def paintEvent(self, event):
        """Draw The widget"""
        painter = QtGui.QPainter(self)
        painter.save()

        # Calculate the proper place to draw the stuff
        local_rect = self.geometry()
        local_rect.moveTopLeft(QtCore.QPoint(0, 0))

        # Corregir el problema del context manager
        if self.dag_node and hasattr(self.dag_node, "begin"):
            self.dag_node.begin()
            try:
                scale = nuke.zoom()
                offset = local_rect.center() / scale - QtCore.QPoint(*nuke.center())
            finally:
                self.dag_node.end()
        else:
            scale = nuke.zoom()
            offset = local_rect.center() / scale - QtCore.QPoint(*nuke.center())

        painter.scale(scale, scale)
        painter.translate(offset)
        self.transform = painter.combinedTransform()

        # Draw the bounds rectangle
        black_pen = QtGui.QPen()
        black_pen.setColor(QtGui.QColor("black"))
        black_pen.setWidth(3)
        black_pen.setCosmetic(True)

        painter.setPen(black_pen)
        painter.drawRect(self.bounds.marginsAdded(self.margins))

        # Draw the handles
        yellow_brush = QtGui.QBrush()
        yellow_brush.setColor(QtGui.QColor("white"))
        yellow_brush.setStyle(QtCore.Qt.SolidPattern)

        handle_size = int(16 / scale)
        handle = QtCore.QRectF(0, 0, handle_size, handle_size)
        painter.setBrush(yellow_brush)
        for point in self.get_handles_points():
            handle.moveCenter(point)
            painter.drawRect(handle)

        # Add a text hint for usage
        painter.restore()
        local_rect.setTop(local_rect.bottom() - 70)
        text = "Resize Mode enabled"
        if self.snap_to_grid:
            text += " (Snap to Grid: ON)"
        text += "\nDrag any handle to affect the spacing between your nodes."
        text += "\nCtrl+Drag: affect all nodes, Shift+Drag: Translate, 'S': Toggle Snap to grid, 'Esc': Cancel, "
        text += "Any other key: Confirm and close"
        painter.setPen(black_pen)
        painter.drawText(local_rect, QtCore.Qt.AlignCenter, text)
        painter.setPen(QtGui.QPen(QtGui.QColor("white")))
        painter.drawText(local_rect.translated(1, -1), QtCore.Qt.AlignCenter, text)

    def get_handles_points(self):
        """Return a list of 8 QPoints representing the 8 handles we want to draw"""
        bounds = self.bounds.marginsAdded(self.margins)
        return [
            bounds.topLeft(),
            QtCore.QPoint(bounds.center().x(), bounds.top()),
            bounds.topRight(),
            QtCore.QPoint(bounds.right(), bounds.center().y()),
            bounds.bottomRight(),
            QtCore.QPoint(bounds.center().x(), bounds.bottom()),
            bounds.bottomLeft(),
            QtCore.QPoint(bounds.left(), bounds.center().y()),
        ]

    def get_handle_at_pos(self, pos):
        """Get the handle nearest the provided position"""
        handles = self.get_handles_points()
        nearest = (0, None)  # index, distance
        for i, handle in enumerate(handles):
            transformed = self.transform.map(handle)
            transformed -= pos
            dist = transformed.manhattanLength()
            if nearest[1] is None or dist < nearest[1]:
                nearest = (i, dist)
        return nearest[0]

    def resize_bounds(self, handle, pos):
        """Resize the QRectF representing the bounding box controller based on the clicked handle"""
        if handle is None:
            return
        # As the user interacts with the visual bounds rather than the computed ones, we need to take this into account
        bounds = self.bounds.marginsAdded(self.margins)
        invert_matrix, _invert_success = self.transform.inverted()
        pos = invert_matrix.map(pos)
        attr_prefix = "move" if self.translate_mode else "set"
        if handle == 0:
            getattr(bounds, "{}TopLeft".format(attr_prefix))(pos)
        elif handle == 1:
            getattr(bounds, "{}Top".format(attr_prefix))(pos.y())
        elif handle == 2:
            getattr(bounds, "{}TopRight".format(attr_prefix))(pos)
        elif handle == 3:
            getattr(bounds, "{}Right".format(attr_prefix))(pos.x())
        elif handle == 4:
            getattr(bounds, "{}BottomRight".format(attr_prefix))(pos)
        elif handle == 5:
            getattr(bounds, "{}Bottom".format(attr_prefix))(pos.y())
        elif handle == 6:
            getattr(bounds, "{}BottomLeft".format(attr_prefix))(pos)
        elif handle == 7:
            getattr(bounds, "{}Left".format(attr_prefix))(pos.x())
        self.bounds = bounds.marginsRemoved(self.margins)
        self.repaint()

    def scale_nodes(self, handle, pos, all_nodes=False):
        """Moves either the selected nodes or all the nodes to their relative space to the bounding box controller"""
        if not self.undo:
            # Start undo stack so that the operation can be reverted cleanly
            self.undo = nuke.Undo()
            self.undo.begin("Scale Nodes")

        self.resize_bounds(handle, pos)
        new_size = QtGui.QVector2D(
            self.bounds.size().width(), self.bounds.size().height()
        )
        new_top_left = QtGui.QVector2D(self.bounds.topLeft())

        for coord in self.coordinates:
            if not all_nodes and coord.node_wrapper.node not in self.nodes:
                continue
            new_relative_pos = coord.vector * new_size
            new_pos = new_top_left + new_relative_pos + coord.offset
            coord.move(new_pos.toPoint(), self.grid_size if self.snap_to_grid else None)

    def mouseMoveEvent(self, event):
        """Check which handle is nearest the mouse and set the appropriate cursor"""
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            self.setCursor(QtCore.Qt.SizeAllCursor)
        else:
            handle_index = self.get_handle_at_pos(event.pos())
            self.setCursor(self.handles_cursors[handle_index % 4])

    def eventFilter(self, widget, event):
        """Filter all the events happening while the bounding box controller is shown"""
        if event.type() in [QtCore.QEvent.MouseButtonPress]:
            if not self.geometry().contains(event.globalPos()):
                # Clicked outside the widget
                self.close()
                return False

            if event.button() == QtCore.Qt.LeftButton:
                if widget is self:
                    # Clicked on one of the opaque areas of the widget
                    self.grabbed_handle = self.get_handle_at_pos(event.pos())
                    self.move_all = bool(
                        QtWidgets.QApplication.keyboardModifiers()
                        & QtCore.Qt.ControlModifier
                    )
                    self.translate_mode = bool(
                        QtWidgets.QApplication.keyboardModifiers()
                        & QtCore.Qt.ShiftModifier
                    )
                    return True

                # Left mouse button was clicked, outside the widget.
                if (
                    not QtWidgets.QApplication.keyboardModifiers()
                    and event.buttons() == event.button()
                ):
                    # The mouse press event had no other button pressed at the same time
                    # However, events can happen on other widgets, so check click position
                    if isinstance(widget, QtOpenGL.QGLWidget):
                        self.close()
                    return False

        elif event.type() in [QtCore.QEvent.MouseButtonRelease]:
            if event.button() == QtCore.Qt.LeftButton and widget is self:
                self.reset_state()
                return True

        elif event.type() in [QtCore.QEvent.MouseMove]:
            # Mouse moved, if we had a handle grabbed, resize nodes.
            if self.grabbed_handle is not None:
                self.scale_nodes(
                    self.grabbed_handle, event.pos(), all_nodes=self.move_all
                )
                return True

            # Otherwise, if a button is pressed, we might be moving the dag, so repaint.
            if event.buttons():
                self.repaint()

        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.cancel()
            elif event.key() == QtCore.Qt.Key_S:
                # toggle snap to grid
                self.snap_to_grid = not self.snap_to_grid
                self.repaint()
            # close and accept on any non modifier key
            elif event.key() not in [
                QtCore.Qt.Key_Control,
                QtCore.Qt.Key_Alt,
                QtCore.Qt.Key_Shift,
            ]:
                self.close()

            return True

        # Due to a QT bug, out transparent widget is swallowing wheel events, pass them back to DAG
        # See https://bugreports.qt.io/browse/QTBUG-53418
        elif event.type() == QtCore.QEvent.Wheel and widget is self:
            dag = get_dag_widgets()[0]
            gl_widget = dag.findChild(QtOpenGL.QGLWidget)
            if gl_widget:
                QtWidgets.QApplication.sendEvent(gl_widget, event)
                self.repaint()
                return True

        return False

    def show(self):
        if len(self.nodes) < 2:
            # self.restore_context()
            return
        # self.dag_node.begin()
        super(ScaleWidget, self).show()
        # Install Event filter
        QtWidgets.QApplication.instance().installEventFilter(self)

    def cancel(self):
        if self.undo:
            self.undo.cancel()
            self.undo = None
        self.close()

    def close(self):
        if self.undo:
            self.undo.end()
        QtWidgets.QApplication.instance().removeEventFilter(self)
        super(ScaleWidget, self).close()


def scale_tree():
    """Scale nodes with a bounding widget."""
    this_dag = get_current_dag()
    scale_tree_widget = ScaleWidget(this_dag)
    scale_tree_widget.show()


# scale_tree()
