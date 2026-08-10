"""Test the push_nodes modules.

Notes:
    Only the same node class can be tested because `nuke.Node.screenHeight()`
    and `nuke.Node.screenWidth()` are not evaluated immediately after node
    creation.

    Changes to all nodes in the test script are tested - listing nodes in
    the test data is not optional. For this reason, the previous script is
    closed prior to testing.

    The test operation is undone for easier development of the test script.

"""

# Import built-in modules
import os
import unittest
from operator import methodcaller
from operator import lt as lower
from operator import gt as greater

# Import third-party modules
import nuke
from parameterized.parameterized import parameterized

# Import local modules
from nuke_move_nodes import push_nodes


_TEST_DATA = [
    ('Not pushing in any direction', {
        # No Node should be moved or resized when no direction is specified.
        'push': {},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {},
        'resized': {},
    }),
    ('Push nodes below `dot_pivot_1_center` down', {
        'push': {'down': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            'dot_below_pivot_1': {'down': True},
            'dot_below_right_pivot_1': {'down': True},
            'backdrop_below': {'down': True},
            'dot_inside_backdrop_below': {'down': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdheight': True},
            'surrounding_pivot_2': {'bdheight': True},
            'surrounding_pivot_1': {'bdheight': True},
            'backdrop_sibling': {'bdheight': True},
        },
    }),
    ('Push nodes above `dot_pivot_1_center` up.', {
        'push': {'up': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            'dot_above_pivot_1': {'up': True},
            'backdrop_above': {'up': True},
            'dot_inside_backdrop_above': {'up': True},
            'backdrop_parent_center': {'up': True},
            'surrounding_pivot_2': {'up': True},
            'surrounding_pivot_1': {'up': True},
            'backdrop_sibling': {'up': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdheight': True},
            'surrounding_pivot_2': {'bdheight': True},
            'surrounding_pivot_1': {'bdheight': True},
            'backdrop_sibling': {'bdheight': True},
        },
    }),
    ('Push nodes left of `dot_pivot_1_center` to the left.', {
        'push': {'left': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            'surrounding_pivot_2': {'left': True},
            'backdrop_parent_center': {'left': True},
            'surrounding_pivot_1': {'left': True},
            'backdrop_left': {'left': True},
            'dot_pivot_2_left': {'left': True},
            'dot_below_pivot_2': {'left': True},
            'dot_left_of_pivot_1': {'left': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdwidth': True},
            'surrounding_pivot_1': {'bdwidth': True},
        },
    }),
    ('Push nodes right of `dot_pivot_1_center` to the right.', {
        'push': {'right': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            'backdrop_sibling': {'right': True},
            'backdrop_right': {'right': True},
            'dot_below_right_pivot_1': {'right': True},
            'dot_right_of_pivot_1': {'right': True},
            'dot_right_detached_upper': {'right': True},
            'dot_right_detached_lower': {'right': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdwidth': True},
            'surrounding_pivot_1': {'bdwidth': True},
        },
    }),
    ('Push nodes above and below `dot_pivot_1_center`.', {
        'push': {'down': True, 'up': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            'dot_below_pivot_1': {'down': True},
            'dot_below_right_pivot_1': {'down': True},
            'backdrop_below': {'down': True},
            'dot_inside_backdrop_below': {'down': True},
            'dot_above_pivot_1': {'up': True},
            'backdrop_above': {'up': True},
            'dot_inside_backdrop_above': {'up': True},
            'backdrop_parent_center': {'up': True},
            'surrounding_pivot_2': {'up': True},
            'surrounding_pivot_1': {'up': True},
            'backdrop_sibling': {'up': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdheight': True},
            'surrounding_pivot_2': {'bdheight': True},
            'surrounding_pivot_1': {'bdheight': True},
            'backdrop_sibling': {'bdheight': True},
        },
    }),
    ('Push nodes above, below, left and right of `dot_pivot_1_center`.', {
        'push': {'down': True, 'up': True, 'left': True, 'right': True},
        'pivot_nodes': [
            'dot_pivot_1_center',
        ],
        'moved': {
            # Down
            'dot_below_pivot_1': {'down': True},
            'dot_below_right_pivot_1': {'down': True, 'right': True},
            'backdrop_below': {'down': True},
            'dot_inside_backdrop_below': {'down': True},
            # Up
            'dot_above_pivot_1': {'up': True},
            'backdrop_above': {'up': True},
            'dot_inside_backdrop_above': {'up': True},
            'backdrop_parent_center': {'up': True, 'left': True},
            'surrounding_pivot_2': {'up': True, 'left': True},
            'surrounding_pivot_1': {'up': True, 'left': True},
            'backdrop_sibling': {'up': True, 'right': True},
            # Right
            'backdrop_right': {'right': True},
            'dot_right_of_pivot_1': {'right': True},
            'dot_right_detached_upper': {'right': True},
            'dot_right_detached_lower': {'right': True},
            # Left:
            'backdrop_left': {'left': True},
            'dot_pivot_2_left': {'left': True},
            'dot_below_pivot_2': {'left': True},
            'dot_left_of_pivot_1': {'left': True},
        },
        'resized': {
            'backdrop_parent_center': {'bdheight': True, 'bdwidth': True},
            'surrounding_pivot_1': {'bdheight': True, 'bdwidth': True},
            'surrounding_pivot_2': {'bdheight': True, 'bdwidth': False},
            'backdrop_sibling': {'bdheight': True,  'bdwidth': False},
        },
    }),
    # Use BackdropNode as pivot.
    ('Push nodes below `dot_pivot_1_center` down', {
        'push': {'down': True},
        'pivot_nodes': [
            'backdrop_parent_center',
        ],
        'moved': {
            'backdrop_below': {'down': True},
            'dot_inside_backdrop_below': {'down': True},
        },
        'resized': {},
    }),
    ('Push nodes below `backdrop_below` down', {
        'push': {'down': True},
        'pivot_nodes': [
            'backdrop_below',
        ],
        'moved': {},
        'resized': {},
    }),
]


class TestPushNodes(unittest.TestCase):
    """Test the push nodes implementation."""

    def setUp(self):
        """Open the test Nuke script and record node positions and sizes."""
        nuke.scriptClose()

        test_script = os.path.join(
            os.path.dirname(__file__),
            'data',
            'test_push_nodes.nk')

        nuke.scriptOpen(test_script)
        self.node_positions = {}
        self.backdrop_sizes = {}

        self._record_positions()
        self._record_backdrop_sizes()

    def tearDown(self):
        """Undo the modifications done on the script.

        Undoing the tested operation helps building the test script.

        """
        nuke.undo()
        nuke.root().setModified(False)

    def _record_positions(self):
        """Save the positions of all nodes."""
        for node in nuke.allNodes():
            self.node_positions[node.fullName()] = node.xpos(), node.ypos()

    def _record_backdrop_sizes(self):
        """Save the sizes of all backdrop nodes."""
        for node in nuke.allNodes('BackdropNode'):
            self.backdrop_sizes[node.fullName()] = \
                node['bdwidth'].value(), node['bdheight'].value()

    def _assert_moved(
        self,
        test_name,
        node,
        down=False,
        up=False,
        left=False,
        right=False
    ):
        """Each node moved in the correct direction or stayed unchanged."""
        previous_position = self.node_positions[node.fullName()]
        previous_position_x, previous_position_y = previous_position
        directions = (
            ('down', down, 'ypos', greater, previous_position_y),
            ('up', up, 'ypos', lower, previous_position_y),
            ('left', left, 'xpos', lower, previous_position_x),
            ('right', right, 'xpos', greater, previous_position_x),
        )

        for dir_name, direction, attr, compare, prev_pos in directions:
            self.assertTrue(
                (compare(methodcaller(attr)(node), prev_pos)) == direction,
                '{test}: Node `{node_name}` was {not_}moved {dir_name}. '
                'Previous {attr}: {previous}, new: {new}.'.format(
                    test=test_name,
                    node_name=node.fullName(),
                    not_='not ' * direction,
                    dir_name=dir_name,
                    attr=attr,
                    previous=prev_pos,
                    new=methodcaller(attr)(node),
                )
            )

    def _assert_backdrop_resized(self, node, bdwidth=False, bdheight=False):
        """Assert the correct backdrops were resized."""
        previous_size = self.backdrop_sizes[node.fullName()]
        previous_bdwidth, previous_bdheight = previous_size

        directions = (
            ('bdwidth', bdwidth, previous_bdwidth),
            ('bdheight', bdheight, previous_bdheight),
        )

        for dir_name, direction, previous in directions:
            self.assertTrue(
                (node[dir_name].value() > previous) == direction,
                'BackdropNode {node_name} was {not_}resized. Previous '
                '{dir_name}: {previous}, new: {new}'.format(
                    node_name=node.fullName(),
                    not_='not ' * direction,
                    dir_name=dir_name,
                    previous=previous,
                    new=node[dir_name].value(),
                )
            )

    @parameterized.expand(
        _TEST_DATA
    )
    def test_push_nodes_moved(self, test_name, test_data):
        """Nodes are moved in the specified direction."""
        # Given a selection of pivot_nodes.
        pivot_nodes = [
            nuke.toNode(node_name) for node_name in test_data['pivot_nodes']
        ]

        # When the other nodes are pushed.
        push_nodes.push(pivot_nodes, **test_data['push'])

        # Then nodes may be moved depending on their position.
        for node in nuke.allNodes():
            node_name = node.fullName()
            move = test_data.get('moved', {}).get(node_name, {})
            self._assert_moved(
                test_name,
                node,
                **move
            )

    @parameterized.expand(
        _TEST_DATA
    )
    def test_push_backdrops_resized(self, _test_name, test_data):
        """Backdrop nodes are resized."""
        # Given a selection of pivot_nodes.
        pivot_nodes = [
            nuke.toNode(node_name) for node_name in test_data['pivot_nodes']
        ]
        # When the other nodes are pushed.
        push_nodes.push(pivot_nodes, **test_data['push'])

        # Then Backdrop nodes may be resized depending on their position.
        for backdrop in nuke.allNodes('BackdropNode'):
            node_name = backdrop.fullName()
            self._assert_backdrop_resized(
                backdrop, **test_data.get('resized', {}).get(node_name, {})
            )
