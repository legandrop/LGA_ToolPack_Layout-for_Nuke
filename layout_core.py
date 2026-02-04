"""
Pure-Python layout core for experimenting with Nuke-like column ordering.
Phase 1: no Nuke dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


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


def _distribute_segment(nodes: List[Node], start_idx: int, end_idx: int, min_gap: float) -> Optional[float]:
    """
    Distribute nodes [start_idx..end_idx] (inclusive) between fixed endpoints.
    Returns required extra space if conflict, else None.
    """
    segment = nodes[start_idx : end_idx + 1]
    if len(segment) <= 1:
        return None

    top = segment[0]
    bottom = segment[-1]
    y_start = top.y
    y_end = bottom.y
    available = y_start - y_end

    heights = [n.height for n in segment]
    total_heights = sum(heights)
    required_available = (total_heights - (heights[0] / 2 + heights[-1] / 2)) + min_gap * (len(segment) - 1)

    if available < required_available:
        return required_available - available

    # Equal gap between bounding boxes
    g = (available - (total_heights - (heights[0] / 2 + heights[-1] / 2))) / (len(segment) - 1)
    if g < min_gap:
        return (min_gap - g) * (len(segment) - 1)

    # Place nodes from top to bottom
    current_y = y_start
    for i in range(1, len(segment)):
        prev = segment[i - 1]
        curr = segment[i]
        current_y -= (prev.height / 2 + g + curr.height / 2)
        if not curr.fixed_y:
            curr.y = current_y
    return None


def _resolve_column_segments(nodes: List[Node], min_gap: float) -> List[Tuple[int, int, float]]:
    """
    Resolve overlaps by distributing nodes between fixed points.
    Returns list of conflicts as (start_idx, end_idx, extra_space_needed).
    """
    conflicts: List[Tuple[int, int, float]] = []
    if not nodes:
        return conflicts

    fixed_indices = [i for i, n in enumerate(nodes) if n.fixed_y]
    # Add boundaries as segment limits
    boundaries = [0] + fixed_indices + [len(nodes) - 1]
    # Deduplicate and sort
    boundaries = sorted(set(boundaries))

    for i in range(len(boundaries) - 1):
        start_idx = boundaries[i]
        end_idx = boundaries[i + 1]
        if start_idx == end_idx:
            continue
        extra = _distribute_segment(nodes, start_idx, end_idx, min_gap)
        if extra is not None:
            conflicts.append((start_idx, end_idx, extra))

    return conflicts


def layout(graph: Graph, min_gap: float = 0.2) -> List[Tuple[str, Tuple[int, int, float]]]:
    """
    Apply baseline distribution, alignment constraints, and resolve overlaps.
    Returns a list of conflicts per column.
    """
    conflicts_all: List[Tuple[str, Tuple[int, int, float]]] = []

    # Baseline distribution per column
    for col_nodes in graph.columns().values():
        _baseline_distribute_column(col_nodes)
        for n in col_nodes:
            n.original_y = n.original_y if n.original_y is not None else n.y

    # Apply alignment constraints
    for edge in graph.edges:
        if not edge.align:
            continue
        anchor, follower = _choose_anchor(graph, edge)
        follower.y = anchor.y
        follower.fixed_y = True

    # Resolve per-column overlaps by segment distribution
    for col, col_nodes in graph.columns().items():
        conflicts = _resolve_column_segments(col_nodes, min_gap=min_gap)
        for conflict in conflicts:
            conflicts_all.append((col, conflict))

    return conflicts_all

