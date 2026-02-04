"""
Pure-Python layout core for experimenting with Nuke-like column ordering.
Phase 1: no Nuke dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set


@dataclass
class Node:
    name: str
    column: str
    order: int
    height: float = 0.5
    x: float = 0.0
    y: float = 0.0
    fixed_y: bool = False
    original_y: Optional[float] = None
    original_x: Optional[float] = None


@dataclass
class Edge:
    src: str
    dst: str
    kind: str = "flow"
    align: bool = False  # alignment constraint across columns


@dataclass
class Graph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    principal_column: Optional[str] = None
    column_positions: Dict[str, float] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node
        if node.column not in self.column_positions:
            self.column_positions[node.column] = node.x

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def columns(self) -> Dict[str, List[Node]]:
        cols: Dict[str, List[Node]] = {}
        for node in self.nodes.values():
            cols.setdefault(node.column, []).append(node)
        for col in cols:
            cols[col].sort(key=lambda n: n.order)
        return cols


def _column_order(graph: Graph) -> Dict[str, int]:
    ordered = sorted(graph.column_positions.items(), key=lambda kv: kv[1])
    return {col: idx for idx, (col, _x) in enumerate(ordered)}


def _choose_anchor(graph: Graph, edge: Edge) -> Tuple[Node, Node]:
    src = graph.nodes[edge.src]
    dst = graph.nodes[edge.dst]

    if graph.principal_column is None:
        return src, dst

    order = _column_order(graph)
    p_idx = order.get(graph.principal_column, 0)

    def dist(col: str) -> int:
        return abs(order.get(col, 0) - p_idx)

    # Prefer node in principal or closest-to-principal column as anchor
    if dist(src.column) < dist(dst.column):
        return src, dst
    if dist(dst.column) < dist(src.column):
        return dst, src
    # Tie: keep src as anchor
    return src, dst


def _baseline_distribute_column(nodes: List[Node]) -> None:
    if not nodes:
        return
    # Use current positions as boundaries
    top = max(n.y for n in nodes)
    bottom = min(n.y for n in nodes)
    count = len(nodes)
    if count == 1:
        return
    step = (top - bottom) / (count - 1)
    for i, node in enumerate(nodes):
        node.y = top - step * i


def _flow_adjacency(graph: Graph, column: str) -> Dict[str, Set[str]]:
    nodes = [n for n in graph.nodes.values() if n.column == column]
    names = {n.name for n in nodes}
    adj: Dict[str, Set[str]] = {n.name: set() for n in nodes}
    for edge in graph.edges:
        if edge.kind != "flow":
            continue
        if edge.src in names and edge.dst in names:
            adj[edge.src].add(edge.dst)
            adj[edge.dst].add(edge.src)
    return adj


def _column_subgroups(graph: Graph, column: str) -> List[List[Node]]:
    nodes = [n for n in graph.nodes.values() if n.column == column]
    if not nodes:
        return []
    adj = _flow_adjacency(graph, column)
    visited: Set[str] = set()
    subgroups: List[List[Node]] = []
    for node in nodes:
        if node.name in visited:
            continue
        stack = [node.name]
        comp: List[str] = []
        visited.add(node.name)
        while stack:
            current = stack.pop()
            comp.append(current)
            for nb in adj.get(current, set()):
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        comp_nodes = [graph.nodes[name] for name in comp]
        comp_nodes.sort(key=lambda n: n.order)
        subgroups.append(comp_nodes)

    subgroups.sort(key=lambda grp: min(n.order for n in grp))
    return subgroups


def _baseline_distribute_subgroup(subgroup: List[Node], min_gap: float) -> None:
    if not subgroup:
        return
    # Use original positions and heights to define subgroup bounds
    top = max(
        (n.original_y if n.original_y is not None else n.y) + n.height / 2
        for n in subgroup
    )
    bottom = min(
        (n.original_y if n.original_y is not None else n.y) - n.height / 2
        for n in subgroup
    )
    if len(subgroup) == 1:
        subgroup[0].y = (top + bottom) / 2
        return
    available = top - bottom
    total_heights = sum(n.height for n in subgroup)
    gap = (available - total_heights) / (len(subgroup) - 1)
    if gap < min_gap:
        gap = min_gap

    current_top = top
    for node in subgroup:
        node.y = current_top - node.height / 2
        current_top -= node.height + gap


def _shift_subgroup(subgroup: List[Node], delta: float) -> None:
    for node in subgroup:
        node.y += delta


def _subgroup_bounds(subgroup: List[Node]) -> Tuple[float, float]:
    tops = [n.y + n.height / 2 for n in subgroup]
    bottoms = [n.y - n.height / 2 for n in subgroup]
    return max(tops), min(bottoms)


def _distribute_column_with_fixed(nodes: List[Node], fixed: Set[str], min_gap: float) -> None:
    if not nodes:
        return
    # Ensure we always have boundaries
    fixed_indices = [i for i, n in enumerate(nodes) if n.name in fixed]
    if 0 not in fixed_indices:
        fixed_indices.append(0)
    if len(nodes) - 1 not in fixed_indices:
        fixed_indices.append(len(nodes) - 1)
    fixed_indices = sorted(set(fixed_indices))

    for i in range(len(fixed_indices) - 1):
        start = fixed_indices[i]
        end = fixed_indices[i + 1]
        if start == end:
            continue
        top = nodes[start].y + nodes[start].height / 2
        bottom = nodes[end].y - nodes[end].height / 2
        count = end - start + 1
        if count <= 2:
            continue
        segment = nodes[start : end + 1]
        total_heights = sum(n.height for n in segment)
        available = top - bottom
        gap = (available - total_heights) / (count - 1)
        if gap < min_gap:
            gap = min_gap

        current_top = top
        for node in segment:
            if node.name not in fixed:
                node.y = current_top - node.height / 2
            current_top -= node.height + gap


def _principal_nodes(graph: Graph) -> List[Node]:
    if graph.principal_column is None:
        return []
    nodes = [n for n in graph.nodes.values() if n.column == graph.principal_column]
    nodes.sort(key=lambda n: n.order)
    return nodes


def _align_columns_x(graph: Graph) -> None:
    for col, nodes in graph.columns().items():
        if not nodes:
            continue
        # Use average original X as column alignment target
        xs = [n.original_x if n.original_x is not None else n.x for n in nodes]
        target_x = sum(xs) / len(xs)
        for n in nodes:
            n.x = target_x


def _adjust_principal_for_conflicts(
    graph: Graph,
    conflicts: List[Tuple[str, Tuple[int, int, float]]],
    subgroup_anchor: Dict[str, Dict[int, Node]],
) -> bool:
    if graph.principal_column is None:
        return False
    principal = _principal_nodes(graph)
    if not principal:
        return False

    adjusted = False
    for col, (upper_idx, lower_idx, needed) in conflicts:
        anchors = subgroup_anchor.get(col, {})
        upper_anchor = anchors.get(upper_idx)
        lower_anchor = anchors.get(lower_idx)
        if not upper_anchor or not lower_anchor:
            continue

        # Determine which anchor is lower (smaller y)
        if upper_anchor.y < lower_anchor.y:
            upper_anchor, lower_anchor = lower_anchor, upper_anchor

        # Push lower anchor (and everything below it) down
        for node in principal:
            if node.order >= lower_anchor.order:
                node.original_y = (node.original_y if node.original_y is not None else node.y) - needed
        adjusted = True

    return adjusted


def layout(graph: Graph, min_gap: float = 0.2, max_iters: int = 3) -> List[Tuple[str, Tuple[int, int, float]]]:
    """
    Apply baseline distribution, alignment constraints, and resolve overlaps.
    Returns a list of conflicts per column.
    """
    conflicts_all: List[Tuple[str, Tuple[int, int, float]]] = []

    # Initialize original positions once
    for node in graph.nodes.values():
        node.original_y = node.original_y if node.original_y is not None else node.y
        node.original_x = node.original_x if node.original_x is not None else node.x

    for _iter in range(max_iters):
        conflicts_all = []

        # Reset to original positions each iteration
        for node in graph.nodes.values():
            node.y = node.original_y
            node.fixed_y = False

        # Baseline distribution per subgroup (skip principal column)
        for col in graph.columns().keys():
            if graph.principal_column and col == graph.principal_column:
                continue
            for subgroup in _column_subgroups(graph, col):
                _baseline_distribute_subgroup(subgroup, min_gap=min_gap)

        # Apply alignment constraints (shift entire subgroup)
        fixed_subgroups: Dict[str, Set[int]] = {}
        subgroup_map: Dict[str, Dict[str, int]] = {}
        subgroup_lists: Dict[str, List[List[Node]]] = {}
        subgroup_anchor: Dict[str, Dict[int, Node]] = {}
        principal_fixed_nodes: Set[str] = set()

        for col in graph.columns().keys():
            subgroup_lists[col] = _column_subgroups(graph, col)
            subgroup_map[col] = {}
            subgroup_anchor[col] = {}
            for idx, subgroup in enumerate(subgroup_lists[col]):
                for node in subgroup:
                    subgroup_map[col][node.name] = idx
            fixed_subgroups[col] = set()

        for edge in graph.edges:
            if not edge.align:
                continue
            anchor, follower = _choose_anchor(graph, edge)
            col = follower.column
            idx = subgroup_map[col][follower.name]
            subgroup = subgroup_lists[col][idx]
            delta = anchor.y - follower.y
            _shift_subgroup(subgroup, delta)
            fixed_subgroups[col].add(idx)
            subgroup_anchor[col][idx] = anchor
            follower.fixed_y = True
            if graph.principal_column and anchor.column == graph.principal_column:
                principal_fixed_nodes.add(anchor.name)

        # Re-distribute principal column keeping anchor nodes fixed
        principal_nodes = _principal_nodes(graph)
        if principal_nodes and principal_fixed_nodes:
            _distribute_column_with_fixed(principal_nodes, principal_fixed_nodes, min_gap=min_gap)

        # Resolve overlaps between subgroups (top-to-bottom)
        for col, subgroups in subgroup_lists.items():
            if not subgroups:
                continue
            ordered = subgroups
            for i in range(1, len(ordered)):
                prev = ordered[i - 1]
                curr = ordered[i]
                prev_top, prev_bottom = _subgroup_bounds(prev)
                curr_top, curr_bottom = _subgroup_bounds(curr)
                gap = prev_bottom - curr_top
                if gap >= min_gap:
                    continue
                needed = min_gap - gap
                curr_idx = subgroups.index(curr)
                if curr_idx in fixed_subgroups[col]:
                    conflicts_all.append((col, (i - 1, i, needed)))
                    continue
                _shift_subgroup(curr, -needed)

        if conflicts_all:
            adjusted = _adjust_principal_for_conflicts(graph, conflicts_all, subgroup_anchor)
            if adjusted:
                # Re-run after adjusting principal anchors
                continue
        break

    # Align columns in X at the end
    _align_columns_x(graph)

    return conflicts_all
