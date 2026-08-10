"""Push nodes up or down to make space in the DAG."""

# Import third-party modules
import nuke

# Import local modules
from nuke_move_nodes import utils


def _create_pivot():
    """Create a NoOp node in the DAG at the last clicked position.\

    Returns:
        nuke.Node: NoOp node.

    """
    return nuke.createNode("NoOp")


def _get_nodes_bounding_box(pivot_nodes):
    """Get the bounding box of given nodes.

    Args:
        pivot_nodes (:obj:`list` of :obj:`nuke.Node`): Nodes to get the
            bounding box of.

    Returns:
        :obj:`tuple` of :obj:`int`: The left, top, right and bottom edge
            containing given nodes.

    """
    # Of selected nodes, find the pivot node
    pivot_node_left = utils.find_leftest(pivot_nodes)
    pivot_node_top = utils.find_highest(pivot_nodes)
    pivot_node_right = utils.find_rightest(pivot_nodes)
    pivot_node_bottom = utils.find_lowest(pivot_nodes)

    pivot_nodes = (
        pivot_node_left,
        pivot_node_top,
        pivot_node_right,
        pivot_node_bottom,
    )

    # Get pivot bounding box.
    pivot_box = [0, 0, 0, 0]

    center_functions = (
        utils.get_center_x,
        utils.get_center_y,
        utils.get_center_x,
        utils.get_center_y,
    )

    for index, pivot_node in enumerate(pivot_nodes):
        if pivot_node_left.Class() == "BackdropNode":
            pivot_box[index] = utils.get_node_bounds(pivot_node)[index]
        else:
            pivot_box[index] = center_functions[index](pivot_node)
    return pivot_box


def push(
    pivot_nodes=None,
    down=False,
    up=False,
    left=False,
    right=False,
    offset=(200, 200),
    adjust_to_grid=True,
):
    """Push nodes around selection to create empty space in DAG.

    This function should follow these rules:

    - All selected nodes stay where they are and only nodes in the specified
      direction are moved.
    - If no node is selected, create a node as pivot to get last clicked
      position in DAG.
    - Selected backdrops should not be re-sized.
    - Deselected backdrops surrounding selected nodes should be re-sized.
    - Overlapping backdrops and their content should not be moved if pushing
      in one direction only.
    - Nodes snapped to the grid should stay snapped after being moved.

    Args:
        pivot_nodes (:obj:`list` of :obj:`nuke.Node`): Nodes to pivot from.
            If none provided, selection will be used. If selection is empty a
            pivot node will be created and deleted afterwards.
        down (bool, optional): If True (default: False), push nodes below down.
        up (bool, optional): If True (default: False), push nodes above up.
        left (bool, optional): If True (default: False), push nodes left.
        right (bool, optional): If True (default: False), push nodes right.
        offset (:obj:`tuple` of :obj:`int`, optional): Offset nodes this far.
        adjust_to_grid (bool): Adjust offset to match the grid preferences to
            preserve snapped graphs.

    """

    ####### UNDO FIX part 1 start ########
    nuke.Undo.begin('Push Nodes')  # Iniciar el grupo de deshacer
    original_backdrop_dimensions = {}
    for backdrop in nuke.allNodes("BackdropNode"):
        original_backdrop_dimensions[backdrop] = {
            'x': backdrop.xpos(),
            'y': backdrop.ypos(),
            'width': backdrop['bdwidth'].value(),
            'height': backdrop['bdheight'].value()
        }
     ####### UNDO FIX part 1 end ########   
    
    try:
        horizontal = left or right
        vertical = down or up

        offset_horizontal, offset_vertical = \
            utils.get_closest_grid_offset(offset) if adjust_to_grid else offset

        # The pivot is a box to allow to push in all directions. Nodes inside the
        # box should stay untouched.
        pivot_nodes = pivot_nodes or nuke.selectedNodes()
        # If nothing is selected, create a node that will serve as pivot and will
        #  be deleted at the end.
        delete_pivot = False
        if not pivot_nodes:
            pivot_nodes = [_create_pivot()]
            delete_pivot = True

        pivot_left, pivot_top, pivot_right, pivot_bottom = _get_nodes_bounding_box(
            pivot_nodes
        )

        all_nodes = nuke.allNodes()

        # If no backdrop is selected, the surrounding backdrop will be scaled.
        backdrops_selected = [
            node for node in pivot_nodes if node.Class() == "BackdropNode"
        ]

        # Overlapping backdrops are moved, not resized.
        backdrops_overlapping_horizontal = utils.get_overlapping_backdrops(
            (pivot_left, pivot_top), horizontal=vertical, vertical=False
        )
        backdrops_overlapping_vertical = utils.get_overlapping_backdrops(
            (pivot_right, pivot_bottom), horizontal=False, vertical=horizontal
        )
        # `backdrops_overlapping` includes surrounding backdrops.
        backdrops_overlapping = (
            backdrops_overlapping_horizontal | backdrops_overlapping_vertical
        )

        # The surrounding backdrops are a subset of the overlapping backdrops.
        backdrops_surrounding = utils.get_surrounding_backdrops(
            pivot_nodes, backdrops_overlapping
        )

        for other_node in all_nodes:
            other_node_name = other_node.name()

            if other_node.Class() == "BackdropNode":
                other_node_center = other_node.xpos(), other_node.ypos()
            else:
                other_node_center = utils.get_center(other_node)

            x, y = other_node_center

            # When pushing horizontally preserve the vertical positions inside
            # overlapping backdrops.
            conditions_vertical = (
                vertical,
                other_node not in pivot_nodes,
                # Skip all nodes inside selected backdrops.
                not utils.is_inside_backdrops(other_node, backdrops_selected)
                or other_node in backdrops_surrounding,
                not utils.is_inside_backdrops(
                    other_node, backdrops_overlapping_horizontal
                )
                or utils.is_inside_backdrops(other_node, backdrops_surrounding),
            )
            conditions_horizontal = (
                horizontal,
                other_node not in pivot_nodes,
                # Skip all nodes inside selected backdrops.
                not utils.is_inside_backdrops(other_node, backdrops_selected)
                or other_node in backdrops_surrounding,
                not utils.is_inside_backdrops(
                    other_node, backdrops_overlapping_vertical
                )
                or utils.is_inside_backdrops(other_node, backdrops_surrounding),
            )

            # The condition under which the backdrop is resized must be determined
            # before moving the backdrop, otherwise moved backdrops may not be
            # surrounded by the same node as on their original position.
            # Resize deselected, surrounding and overlapping backdrops if:
            # - the backdrop is surrounding the selection.
            # Or:
            # - the backdrop is inside a backdrops surrounding the selection.
            resize_condition = (
                other_node in backdrops_overlapping,
                other_node not in backdrops_selected,
                utils.is_inside_backdrops(other_node, backdrops_surrounding) \
                or other_node in backdrops_surrounding,
            )

            # Push nodes.
            if all(conditions_vertical):
                if up and y < pivot_top:
                    other_node.setYpos(int(other_node.ypos() - offset_vertical))
                if down and y > pivot_bottom:
                    other_node.setYpos(int(other_node.ypos() + offset_vertical))
            if all(conditions_horizontal):
                if right and x > pivot_right:
                    other_node.setXpos(int(other_node.xpos() + offset_horizontal))
                if left and x < pivot_left:
                    other_node.setXpos(int(other_node.xpos() - offset_horizontal))

            # Resize backdrops.
            if not all(resize_condition):
                continue

            if other_node in backdrops_overlapping_horizontal:
                backrop_growth_vertical = (down + up) * offset_vertical
                other_node["bdheight"].setValue(
                    other_node["bdheight"].value() + backrop_growth_vertical
                )
            if other_node in backdrops_overlapping_vertical:
                backdrop_growth_horizontal = (left + right) * offset_horizontal
                other_node["bdwidth"].setValue(
                    other_node["bdwidth"].value() + backdrop_growth_horizontal
                    )

        # Delete created pivot.
        if delete_pivot:
            # Make sure it's really the pivot.
            if pivot_nodes[0].Class() == "NoOp":
                nuke.delete(pivot_nodes[0])

    ####### UNDO FIX part 2 start ########
    finally:
        nuke.Undo.end()  # Finalizar el grupo de deshacer
    ####### UNDO FIX part 2 end ########
