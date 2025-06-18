"""Test the util functions."""

# Import built-in modules
import unittest
import time

# Import third-party modules
import nuke
import nukescripts

# Import local modules
from nuke_move_nodes import utils


def clean_up_nodes(nodes_before, nodes_after=None):
    """Delete nodes created during the tests."""
    nodes_after = nodes_after or nuke.allNodes()
    added_nodes = set(nodes_after) - set(nodes_before)

    for node in list(added_nodes):
        nuke.delete(node)


class TestUtils(unittest.TestCase):
    def setUp(self):

        self.nodes_before = nuke.allNodes()

        # Make sure to not add to current selection.
        nukescripts.clear_selection_recursive()

        self.nodes = [
            nuke.createNode("Blur"),
            nuke.createNode("Grade"),
            nuke.createNode("Transform"),
        ]

    def tearDown(self):
        clean_up_nodes(self.nodes_before)

    def test_find_top_node(self):
        """The highest node in the DAG is found."""
        result = utils.find_highest(self.nodes)
        expected = self.nodes[0]
        self.assertEquals(result, expected)

    def test_find_bottom_node(self):
        """The lowest node in the DAG is found."""
        result = utils.find_lowest(self.nodes)
        self.assertEquals(result, self.nodes[-1])


class TestBackdropFunctions(unittest.TestCase):
    def setUp(self):
        """Create test nodes."""
        self.nodes_before = nuke.allNodes()

        # NoOp used as pivot.
        self.node = nuke.nodes.NoOp()
        self.node["label"].setValue("inside backdrop")
        self.node.setXYpos(0, 0)

        # This node's edges overlap with the NoOp but does not surround it.
        self.backdrop_overlapping = nuke.nodes.BackdropNode()
        self.backdrop_overlapping.setName("backdrop_overlapping")
        self.backdrop_overlapping["label"].setValue(
            "overlapping backdrop node"
        )
        self.backdrop_overlapping.setXYpos(300, -100)
        self.backdrop_overlapping["bdwidth"].setValue(300)
        self.backdrop_overlapping["bdheight"].setValue(300)

        # Backdrop node that surrounds the NoOp.
        self.backdrop_surrounding = nuke.nodes.BackdropNode()
        self.backdrop_surrounding.setName("backdrop_surrounding")
        self.backdrop_surrounding["label"].setValue(
            "surrounding backdrop node"
        )
        try:
            self.backdrop_surrounding["z_order"].setValue(1)
        except NameError:
            # No `z_order` knob in Nuke < 10.
            pass
        self.backdrop_surrounding.setXYpos(-100, -100)
        self.backdrop_surrounding["bdwidth"].setValue(300)
        self.backdrop_surrounding["bdheight"].setValue(300)
        self.backdrop_surrounding['tile_color'].setValue(1062683391)

        # Backdrop node that surrounds the NoOp.
        self.backdrop_parent = nuke.nodes.BackdropNode()
        self.backdrop_parent.setName("backdrop_parent")
        self.backdrop_parent["label"].setValue(
            "parent backdrop node"
        )
        self.backdrop_parent.setXYpos(-150, -150)
        self.backdrop_parent["bdwidth"].setValue(400)
        self.backdrop_parent["bdheight"].setValue(400)

        # Backdrop node that does not overlap the NoOp.
        self.backdrop_not_overlapping = nuke.nodes.BackdropNode()
        self.backdrop_not_overlapping.setName("backdrop_not_overlapping")
        self.backdrop_not_overlapping["label"].setValue(
            "not overlapping backdrop node"
        )
        self.backdrop_not_overlapping.setXYpos(300, -500)
        self.backdrop_not_overlapping["bdwidth"].setValue(300)
        self.backdrop_not_overlapping["bdheight"].setValue(300)

        self.backdrops = [
            self.backdrop_surrounding,
            self.backdrop_overlapping,
            self.backdrop_not_overlapping,
        ]

    def tearDown(self):
        """Delete created nodes"""
        clean_up_nodes(self.nodes_before)

    def test_node_is_inside_backdrop(self):
        """The NoOp is inside one of the backdrop nodes."""
        self.assertTrue(
            utils.is_inside_backdrops(
                self.node,
                backdrops=[
                    self.backdrop_surrounding,
                    self.backdrop_overlapping,
                    self.backdrop_not_overlapping,
                ],
            )
        )

    def test_backdrop_is_inside_parent_backdrop(self):
        """The surrounding is inside `backdrop_parent` node."""
        self.assertTrue(
            utils.is_inside_backdrops(
                self.backdrop_surrounding,
                backdrops=[
                    self.backdrop_parent,
                ],
            )
        )

    def test_node_is_outside_backdrop(self):
        """Return false when checking against overlapping nodes."""
        self.assertFalse(
            utils.is_inside_backdrops(
                self.node,
                backdrops=[
                    self.backdrop_overlapping,
                    self.backdrop_not_overlapping,
                ],
            )
        )

    def test_node_is_not_inside_empty_selection(self):
        """Return False if `is_inside_backdrops` is given an empty list."""
        self.assertFalse(utils.is_inside_backdrops(self.node, backdrops=[]))

    def test_get_horizontal_overlapping_backdrop(self):
        """Two BackdropNodes are vertically overlapping with the NoOp."""
        expected = [self.backdrop_overlapping, self.backdrop_surrounding]

        result = utils.get_overlapping_backdrops(
            (self.node.xpos(), self.node.ypos()),
            self.backdrops,
            horizontal=True,
            vertical=False,
        )
        self.assertListEqual(sorted(result), sorted(expected))


def main():
    unittest.main()
