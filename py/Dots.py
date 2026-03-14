import nuke


tolerance_x = 60  # Tolerance value in X
tolerance_y = 10  # Tolerance value in Y
moveSelectedNode = True  # Variable to decide whether to move the selected node
dsize = int(nuke.toNode("preferences")["dot_node_scale"].value() * 12)

# Determine if the comp style is vertical (True) or horizontal (False)
verticalComp = True

# List of important nodes that require different treatment in vertical or horizontal comp styles
VvsH_Nodes = ["Merge", "Dissolve", "Keymix"]


# Global variable to enable or disable prints
DEBUG = {
    "A": False,  # Original
    "B": False,  # Multiple connected nodes
}


def debug_print_A(*message):
    if DEBUG["A"]:
        print(" ".join(str(m) for m in message))


def debug_print_B(*message):
    if DEBUG["B"]:
        print(" ".join(str(m) for m in message))


def Dots():

    undo = nuke.Undo()
    undo.begin("Add Dot Before")

    nodes = nuke.selectedNodes()

    try:
        # Check if there is more than one selected node
        if len(nodes) > 1:
            same_input_node = None
            all_connected_to_same = True

            for selected in nodes:
                # Check all inputs of the selected node
                inputs = [selected.input(i) for i in range(selected.maxInputs())]
                connected_to_same = False

                for A in inputs:
                    if A is not None:
                        if same_input_node is None:
                            same_input_node = A
                        if A == same_input_node:
                            connected_to_same = True
                            break

                if not connected_to_same:
                    same_input_node = None
                    break

            if same_input_node is not None:
                debug_print_A(
                    "All selected nodes have at least one input connected to the same node:",
                    same_input_node["name"].value(),
                )
                # Check if the node they are connected to is a Dot
                if same_input_node.Class() == "Dot":
                    debug_print_B("The node they are connected to is a Dot")
                    dot_node = same_input_node
                else:
                    debug_print_B("The node they are connected to is not a Dot")

                    # Create a new Dot after the node they are connected to
                    dot_node = nuke.nodes.Dot()
                    dot_node.setInput(0, same_input_node)
                    dot_node.setXYpos(
                        same_input_node.xpos()
                        + same_input_node.screenWidth() // 2
                        - dsize // 2,
                        same_input_node.ypos() + same_input_node.screenHeight() + 50,
                    )
                    same_input_node = dot_node

                    # Connect all selected nodes to the new Dot
                    for selected in nodes:
                        selected.setInput(0, dot_node)

                    debug_print_B(
                        "A Dot has been created after the node",
                        same_input_node["name"].value(),
                        "and all selected nodes have been connected to it",
                    )

                # Print the centered X position of the Dot
                dot_x_center = dot_node.xpos() + dot_node.screenWidth() // 2
                debug_print_B("Centered X position of the Dot:", dot_x_center)

                # Arrange nodes by proximity to the Dot
                node_positions = []

                for selected in nodes:
                    node_x_center = selected.xpos() + selected.screenWidth() // 2
                    node_positions.append((selected, node_x_center))

                # Sort nodes by their centered x position
                node_positions.sort(key=lambda x: x[1])

                # Assign numbers based on proximity
                position_labels = {}
                left_positions = []
                right_positions = []

                for node, x_center in node_positions:
                    if abs(x_center - dot_x_center) <= tolerance_x:
                        position_labels[node["name"].value()] = (
                            0  # Consider as in the same column
                        )

                        # Align the node if moveSelectedNode is True
                        if moveSelectedNode:
                            node.setXpos(dot_x_center - node.screenWidth() // 2)
                            debug_print_B(
                                f"\nNode {node['name'].value()} aligned to X position of Dot: {dot_x_center}\n"
                            )

                    elif x_center < dot_x_center:
                        left_positions.append((node, x_center))
                    elif x_center > dot_x_center:
                        right_positions.append((node, x_center))

                # Assign negative numbers to nodes on the left side (closer to the Dot)
                count_left = -1
                for node, _ in reversed(
                    left_positions
                ):  # Reversed to start from the closest to the Dot
                    position_labels[node["name"].value()] = count_left
                    count_left -= 1

                # Assign positive numbers to nodes on the right side (closer to the Dot)
                count_right = 1
                for node, _ in right_positions:
                    position_labels[node["name"].value()] = count_right
                    count_right += 1

                # Print node names, their assigned numbers, and their centered X positions
                for node_name, position in position_labels.items():
                    for node, x_center in node_positions:
                        if node["name"].value() == node_name:
                            debug_print_B(
                                "Node:",
                                node_name,
                                "Relative position to the Dot:",
                                position,
                                "Centered X position:",
                                x_center,
                            )

                debug_print_B("")
                # Process nodes in negative positions first
                current_position = -1
                previous_dot = None

                while current_position in position_labels.values():
                    for node_name, position in position_labels.items():
                        if position == current_position:
                            for node, x_center in node_positions:
                                if node["name"].value() == node_name:
                                    if current_position == -1:
                                        previous_dot = mainDots(
                                            node,
                                            common_node=same_input_node,
                                            previous_dot=None,
                                        )  # Pass the common node and previous_dot as None
                                        debug_print_B(
                                            f"Node {node_name} in position -1 connected to Dot: {previous_dot['name'].value() if previous_dot else 'None'}"
                                        )
                                    else:
                                        # Connect the current node to the Dot of the previous node
                                        node.setInput(0, previous_dot)
                                        previous_dot = mainDots(
                                            node,
                                            common_node=same_input_node,
                                            previous_dot=previous_dot,
                                        )  # Pass the common node and the updated previous_dot
                                        debug_print_B(
                                            f"Node {node_name} in position {current_position} connected to Dot: {previous_dot['name'].value() if previous_dot else 'None'}"
                                        )
                                    previous_node = node  # Save the current node as previous for the next iteration
                                    break
                    current_position -= 1

                # Process nodes in positive positions similarly
                current_position = 1
                previous_dot = dot_node  # Initially connect node 1 to the main Dot

                while current_position in position_labels.values():
                    for node_name, position in position_labels.items():
                        if position == current_position:
                            for node, x_center in node_positions:
                                if node["name"].value() == node_name:
                                    # Connect the current node to the Dot of the previous node
                                    node.setInput(0, previous_dot)
                                    previous_dot = mainDots(
                                        node,
                                        common_node=same_input_node,
                                        previous_dot=previous_dot,
                                    )  # Pass the common node and the updated previous_dot
                                    debug_print_B(
                                        f"Node {node_name} in position {current_position} connected to Dot: {previous_dot['name'].value() if previous_dot else 'None'}"
                                    )
                                    previous_node = node  # Save the current node as previous for the next iteration
                                    break
                    current_position += 1

            else:
                debug_print_B(
                    "Not all selected nodes have inputs connected to the same node. Processing each selected node individually"
                )
                for selected in nodes:
                    mainDots(selected, common_node=None, previous_dot=None)

        # Check if only one node is selected
        elif len(nodes) == 1:
            selected_node = nodes[0]
            connected_node = selected_node.input(0)

            # Check if the node has more than one connected input
            multiple_inputs = any(
                selected_node.input(i) is not None
                for i in range(1, selected_node.maxInputs())
            )

            if connected_node:
                selected_x_center = (
                    selected_node.xpos() + selected_node.screenWidth() // 2
                )
                connected_x_center = (
                    connected_node.xpos() + connected_node.screenWidth() // 2
                )

                if (
                    abs(selected_x_center - connected_x_center) <= tolerance_x
                    and not multiple_inputs
                ):
                    if not moveSelectedNode:
                        debug_print_B(
                            f"The node {selected_node['name'].value()} is in the same column as its connected node {connected_node['name'].value()}, does not have multiple inputs, and moveSelectedNode is False. Nothing will be done."
                        )
                    else:
                        selected_node.setXpos(
                            connected_node.xpos()
                            + connected_node.screenWidth() // 2
                            - selected_node.screenWidth() // 2
                        )
                        debug_print_B(
                            f"The node {selected_node['name'].value()} has been moved to align with the X position of its connected node {connected_node['name'].value()}."
                        )
                else:
                    debug_print_B(
                        f"The node {selected_node['name'].value()} is NOT in the same column as its connected node {connected_node['name'].value()} or has multiple inputs. Executing mainDots()."
                    )
                    mainDots(
                        selected_node, common_node=None, previous_dot=None
                    )  # Pass None if there is no common node and previous_dot as None
            else:
                debug_print_B(
                    f"The node {selected_node['name'].value()} has no connected node. Executing mainDots()."
                )
                mainDots(
                    selected_node, common_node=None, previous_dot=None
                )  # Pass None if there is no common node and previous_dot as None

            return

    except Exception as e:
        nuke.message(f"An error occurred: {e}")

    finally:
        # debug_print_A('\nEnd undo')
        undo.end()  # Place this at the end of your try-except-finally


def mainDots(selected, common_node=None, previous_dot=None):

    # Print the current state of common_node and previous_dot
    common_node_name = common_node["name"].value() if common_node else "None"
    previous_dot_name = previous_dot["name"].value() if previous_dot else "None"
    debug_print_A(f"common_node: {common_node_name}, previous_dot: {previous_dot_name}")

    # Inputs A, B, C
    A = selected.input(0)
    B = selected.input(1)
    C = selected.input(2)

    debug_print_A(f"\nProcessing node: {selected['name'].value()}")
    debug_print_A(
        f"    Inputs found: A={A['name'].value() if A else 'None'}, B={B['name'].value() if B else 'None'}, C={C['name'].value() if C else 'None'}"
    )

    new_dot = None  # Variable to store the newly created Dot

    # If there is a common_node or a previous_dot (meaning that we are connecting every node to the same input), process the input connected to either of them
    if common_node is not None or previous_dot is not None:
        for idx, input_node in enumerate([A, B, C]):
            if input_node == common_node or input_node == previous_dot:
                new_dot = process_input(
                    input_node,
                    selected,
                    idx,
                    tolerance_x,
                    tolerance_y,
                    dsize,
                    moveSelectedNode,
                    force_single_input=True,
                )
                return new_dot  # Return the newly created Dot to use it as previous_dot in future calls

    else:
        # Process each input using the existing logic
        new_dot_A = process_input(
            A, selected, 0, tolerance_x, tolerance_y, dsize, moveSelectedNode
        )
        new_dot_B = process_input(
            B, selected, 1, tolerance_x, tolerance_y, dsize, moveSelectedNode
        )
        new_dot_C = process_input(
            C, selected, 2, tolerance_x, tolerance_y, dsize, moveSelectedNode
        )
        new_dot = new_dot_A or new_dot_B or new_dot_C  # Return the last created Dot

    debug_print_A(f"mainDots completed for node: {selected['name'].value()}")

    return new_dot  # Return the newly created Dot


def process_input(
    input_node,
    selected_node,
    index,
    tolerance_x,
    tolerance_y,
    dsize,
    moveSelectedNode,
    force_single_input=False,
):
    if input_node is not None:

        # Check if the class of the selected node starts with any of the names in the list
        isNodeInVvsH_Nodes = any(
            selected_node.Class().startswith(node) for node in VvsH_Nodes
        )

        if should_create_dot(
            input_node,
            selected_node,
            tolerance_x,
            tolerance_y,
            index,
            isNodeInVvsH_Nodes,
        ):
            dot = nuke.nodes.Dot()
            dot.setInput(0, input_node)
            selected_node.setInput(index, dot)

            # Print the name of the created Dot
            dot_name = dot["name"].value()
            debug_print_A(f"\n        Dot created: {dot_name}")

            # Check if the selected node has only one connected input and the rest are not,
            # or if we are forcing to treat the input as single.
            if (
                selected_node.input(0) is not None
                and selected_node.input(1) is None
                and selected_node.input(2) is None
            ) or force_single_input:
                # Align the Dot in Y with the input node and in X with the selected node
                dot.setXYpos(
                    int(
                        selected_node.xpos()
                        + selected_node.screenWidth() // 2
                        - dsize // 2
                    ),
                    int(
                        input_node.ypos() + input_node.screenHeight() // 2 - dsize // 2
                    ),
                )
                debug_print_A(
                    f"        Dot created and aligned with input node {input_node['name'].value()} in Y and with selected node {selected_node['name'].value()} in X."
                )
            else:
                # Align the Dot in Y and X with the selected node
                dot.setXYpos(
                    int(input_node.xpos() + input_node.screenWidth() // 2 - dsize // 2),
                    int(
                        selected_node.ypos()
                        + selected_node.screenHeight() // 2
                        - dsize // 2
                    ),
                )
                debug_print_A(
                    f"        Dot created and aligned with selected node {selected_node['name'].value()} in both X and Y."
                )

            return dot  # Return the newly created Dot

        else:
            # Move the selected node if it is within tolerance in X
            if moveSelectedNode:
                input_x_center = input_node.xpos() + input_node.screenWidth() // 2
                selected_x_center = (
                    selected_node.xpos() + selected_node.screenWidth() // 2
                )
                distance_x = abs(input_x_center - selected_x_center)
                isInTheSameColumn = distance_x <= tolerance_x
                isInVerticalException = (
                    verticalComp and index == 0 and isNodeInVvsH_Nodes
                )
                isInHorizontalException = (
                    not verticalComp and index == 1 and isNodeInVvsH_Nodes
                )

                if (
                    isInTheSameColumn
                    or isInVerticalException
                    or isInHorizontalException
                ) and distance_x != 0:
                    selected_node.setXpos(
                        input_node.xpos()
                        + input_node.screenWidth() // 2
                        - selected_node.screenWidth() // 2
                    )
                    debug_print_A(
                        f"        Selected node moved to the X position of {input_node['name'].value()}: {selected_node.xpos()} (original: {selected_x_center})"
                    )

    else:
        debug_print_A(f"        Input {index + 1} not connected. No action taken.")

    return None  # No Dot was created, return None


def should_create_dot(
    input_node, selected_node, tolerance_x, tolerance_y, index, isNodeInVvsH_Nodes
):
    if input_node is None:
        return False

    input_x_center = input_node.xpos() + input_node.screenWidth() // 2
    input_y_center = input_node.ypos() + input_node.screenHeight() // 2

    selected_x_center = selected_node.xpos() + selected_node.screenWidth() // 2
    selected_y_center = selected_node.ypos() + selected_node.screenHeight() // 2

    distance_x = abs(input_x_center - selected_x_center)
    distance_y = abs(input_y_center - selected_y_center)

    debug_print_A(
        f"\n        Evaluating input connected to: {input_node['name'].value()} | Distance X: {distance_x} | Distance Y: {distance_y}"
    )

    if distance_x > tolerance_x:
        debug_print_A(
            f"            X of {distance_x} is greater than Tolerance X of {tolerance_x} - A Dot node might be created"
        )
        X_OK = True
    else:
        debug_print_A(
            f"            X of {distance_x} is less than Tolerance X of {tolerance_x} - A Dot node will not be created"
        )
        X_OK = False

    if distance_y > tolerance_y:
        debug_print_A(
            f"            Y of {distance_y} is greater than Tolerance Y of {tolerance_y} - A Dot node might be created"
        )
        Y_OK = True
    else:
        debug_print_A(
            f"            Y of {distance_y} is less than or equal to Tolerance Y of {tolerance_y} - A Dot node will not be created"
        )
        Y_OK = False

    # Check if the selected node and input match the nodes and inputs that create exceptions
    isInVerticalException = verticalComp and index == 0 and isNodeInVvsH_Nodes
    isInHorizontalException = not verticalComp and index == 1 and isNodeInVvsH_Nodes

    if isInVerticalException:
        debug_print_A(
            f"            Verical Comp mode ON, on an important Vertical vs Horizontal Node while processing the input 0 (B input). Lets move the node instead of creating a dot"
        )
        X_OK = False
    elif isInHorizontalException:
        debug_print_A(
            f"            Verical Comp mode OFF, on an important Vertical vs Horizontal Node while processing the input 1 (A input). Lets move the node instead of creating a dot"
        )
        X_OK = False

    if X_OK and Y_OK:
        debug_print_A(
            f"            Distances within tolerance - A Dot will be created at node {input_node['name'].value()}"
        )
        return True

    debug_print_A(f"            No Dot is needed for node {input_node['name'].value()}")
    return False
