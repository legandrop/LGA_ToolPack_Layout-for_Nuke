"""
__________________________________________________________

  DistributeNodes v1.0 - 2024
  Most of the code was taken from Erwan Leroy's Align script
  Distribute nodes or backdrops horizontally or vertically
_____________________________________________________________________

"""


from collections import defaultdict, namedtuple
import re
from PySide2 import QtCore, QtWidgets, QtGui
import nuke

class NodeWrapper(object):
    """ Wraps a nuke node with its bounds, and exposes all the methods from QRectF to be used on the node """

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
        # Solo mover si la posicion ha cambiado
        if new_pos.x() != self.node.xpos() or new_pos.y() != self.node.ypos():
            self.node.setXYpos(new_pos.x(), new_pos.y())


    def _commit_resize(self):
        if not self.is_backdrop:
            raise NotImplementedError(
                "Tried to resize a node other than a backdrop, which is not supported. You may get unexpected results."
            )
        # Solo cambiar el tamano si es diferente
        new_width = int(self.bounds.width())
        new_height = int(self.bounds.height())
        if new_width != self.node['bdwidth'].value() or new_height != self.node['bdheight'].value():
            self._commit_move()  # Mover primero para asegurar la coherencia de la posicion
            self.node['bdwidth'].setValue(new_width)
            self.node['bdheight'].setValue(new_height)


    def normalize(self):
        self.bounds = self.bounds.normalized()
        self._commit_move()
        self._commit_resize()

    def move_center(self, value, axis):
        """ Extra method to allow moving a node center based on a single axis

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
            raise NotImplementedError("Tried to calculate margins on a non-backdrop node")
        nodes = self.node.getNodes()
        nodes_bounds = get_nodes_bounds(nodes)
        margins = calculate_bounds_adjustment(nodes_bounds, self)
        self._nodes_and_margins = {'nodes': nodes, 'margins': margins}

    def restore_margins(self):
        if not self.is_backdrop:
            raise NotImplementedError("Tried to set margins on a non-backdrop node")
        if not self._nodes_and_margins:
            raise RuntimeError("No margins were saved for this backdrop, can't restore")
        nodes_bounds = get_nodes_bounds(self._nodes_and_margins['nodes'])
        nodes_bounds.adjust(*self._nodes_and_margins['margins'])
        self.setCoords(*nodes_bounds.getCoords())

    def place_around_nodes(self, nodes, padding=50):
        if not self.is_backdrop:
            raise NotImplementedError("Can only place backdrops around nodes")
        if not nodes:
            return
        label_height = get_label_size(self.node).height()
        nodes_bounds = get_nodes_bounds(nodes)
        nodes_bounds.adjust(-padding, -(padding+label_height), padding, padding)
        self.setCoords(*nodes_bounds.getCoords())


def node_center(node):
    """
    A simple function to find a node's center point.
    :param node:
    :return x_pos, y_pos:
    """
    if not isinstance(node, NodeWrapper):
        node = NodeWrapper(node)
    return node.center().toTuple()

def sort_nodes_by_position(nodes, axis=0, reverse=False):
    """
    Sort nodes based by position, using either axis X or Y as primary key, other axis as secondary key.

    Args:
        nodes (list): List of Nuke Nodes
        axis (int): 0 for x, 1 for y
        reverse (bool): whether to reverse order

    Returns:
        list: sorted list
    """
    return sorted(nodes, key=lambda n: (node_center(n)[axis], node_center(n)[1-axis]), reverse=reverse)

def sort_nodes_by_distance(nodes, axis, target):
    """
    Sort nodes based on their distance from the target, on provided axis
    Args:
        nodes (list): List of Nuke Nodes
        axis (int): 0 for x, 1 for y
        target (int): Point from which the distance should be calculated

    Returns:
        list: sorted list
    """
    return sorted(nodes, key=lambda n: abs(node_center(n)[axis] - target))

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
        width = node['bdwidth'].value()
        height = node['bdheight'].value()
    else:
        width = node.screenWidth()
        height = node.screenHeight()

    if width == 0:  # Handle a bug as mentioned in docstring
        temp_node = getattr(nuke.nodes, node.Class())()  # Make temp node with same class as corrupted node
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
    bounds = QtCore.QRectF(all_bounds[0])  # Make a new rect so we don't modify the initial one
    for bound in all_bounds[1:]:
        bounds |= bound
    return bounds

def calculate_bounds_adjustment(bounds, target_bounds):
    """ Calculate adjust values to apply to 'bounds' in order to match 'target_bounds'

    Args:
        bounds (QtCore.QRectF or NodeWrapper): Original Bounds
        target_bounds (QtCore.QRectF or NodeWrapper): Desired Bounds

    Returns:
        tuple[int, int, int, int]: Bounds adjustments
    """
    bounds_coords = bounds.getCoords()
    target_coords = target_bounds.getCoords()
    return tuple(target_coords[i] - bounds_coords[i] for i in range(4))



def distribute_nodes(nodes, axis=0, tolerance=6):
    """
    Equalize the distance between nodes, taking their alignment into account.

    Args:
        nodes (list[nuke.Node]): List of nodes to distribute.
        axis (int): Axis index, 0 for X, 1 for Y
        tolerance (int): Consider nodes less than this distance apart to be in the same row when cataloguing
    """

    undo = nuke.Undo()
    undo.begin("Distribute Nodes")
    # Split backdrops from regular nodes
    backdrops = []
    other_nodes = []
    for node in nodes:
        wrapper = NodeWrapper(node)
        if wrapper.is_backdrop:
            backdrops.append(wrapper)
        else:
            other_nodes.append(wrapper)

    # Catalogue nodes
    rows = defaultdict(list)
    current_row = None
    for node in sort_nodes_by_position(other_nodes, axis=axis):
        pos = node_center(node)[axis]
        # In certain cases some nodes are very slightly offset from one another, and without tolerance it creates
        # multiple rows where it looks like there should be only one.
        # First method of rounding by tolerance failed, so rely on sorted nodes and keeping track of row:
        if current_row is None or abs(pos-current_row) > tolerance:
            rows[pos].append(node)
            current_row = pos
        else:
            rows[current_row].append(node)

    if len(rows) < 2:
        return

    # Store backdrops margins
    for bd in backdrops:
        bd.store_margins()

    positions = sorted(rows.items())
    last_row = positions[-1][0]
    first_row = positions[0][0]
    spacing = (last_row - first_row) // (len(positions) - 1)


    for i, (position, nodes) in enumerate(positions):
        new_pos = first_row + i * spacing
        for node in nodes:
            node.move_center(new_pos, axis)

    # Restore backdrops margins
    for bd in sorted(backdrops, key=lambda bd: bd.node['z_order'].value(), reverse=True):
        bd.restore_margins()

    undo.end()


AXIS_X = 0
AXIS_Y = 1


def distribute_selected_nodes(axis=AXIS_X, tolerance=6):
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        nuke.message("Por favor, selecciona los nodos que deseas distribuir.")
        return
    distribute_nodes(selected_nodes, axis, tolerance)


"""
if __name__ == "__main__":
    # Asegurate de que haya nodos seleccionados para evitar errores
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        nuke.message("Por favor, selecciona los nodos que deseas alinear verticalmente.")
    else:
        # Llama a la funcion distribute_nodes para los nodos seleccionados con alineacion vertical
        distribute_nodes(selected_nodes, axis=AXIS_Y, tolerance=2)

"""