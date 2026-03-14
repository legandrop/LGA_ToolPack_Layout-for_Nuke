"""
Pure-Python layout core for experimenting with Nuke-like column ordering.
Phase 1: no Nuke dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

# Fixed edge gap between upper-branch bottom edge and lower-branch top edge.
# Units match graph coordinates (default min_gap = 0.2).
OVERLAP_EDGE_GAP = 0.2
# Minimum compression gap allowed when there is not enough space.
# Default scale is 0.05 (Nuke px -> graph units), so 3px ~= 0.15.
MIN_GAP_FLOOR = 0.15

@dataclass
class Node:
    name: str
    column: str
    order: int
    klass: str = ""
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
    auto_columns: bool = False
    tolerance_x: float = 0.5

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


def _subgroup_height(subgroup: List[Node]) -> float:
    top = max((n.original_y if n.original_y is not None else n.y) + n.height / 2 for n in subgroup)
    bottom = min((n.original_y if n.original_y is not None else n.y) - n.height / 2 for n in subgroup)
    return top - bottom


def _auto_columns(graph: Graph) -> None:
    if not graph.auto_columns:
        return
    nodes = list(graph.nodes.values())
    if not nodes:
        return

    # Group by X proximity (tolerance_x)
    groups: List[Tuple[float, List[Node]]] = []
    for node in sorted(nodes, key=lambda n: n.original_x if n.original_x is not None else n.x):
        x = node.original_x if node.original_x is not None else node.x
        placed = False
        for i, (gx, gnodes) in enumerate(groups):
            if abs(x - gx) <= graph.tolerance_x:
                gnodes.append(node)
                # update group center
                new_gx = sum((n.original_x if n.original_x is not None else n.x) for n in gnodes) / len(gnodes)
                groups[i] = (new_gx, gnodes)
                placed = True
                break
        if not placed:
            groups.append((x, [node]))

    # Assign column names and positions
    groups.sort(key=lambda g: g[0])
    graph.column_positions.clear()
    for idx, (gx, gnodes) in enumerate(groups):
        col = f"C{idx}"
        graph.column_positions[col] = gx
        for n in gnodes:
            n.column = col

        # Re-assign order by original Y (top to bottom)
        ordered = sorted(
            gnodes,
            key=lambda n: n.original_y if n.original_y is not None else n.y,
            reverse=True,
        )
        for order_idx, n in enumerate(ordered):
            n.order = order_idx

    # Select principal column by max subgroup height
    max_height = None
    principal = None
    for col in graph.columns().keys():
        for subgroup in _column_subgroups(graph, col):
            h = _subgroup_height(subgroup)
            if max_height is None or h > max_height:
                max_height = h
                principal = col
    graph.principal_column = principal


def _infer_principal_if_missing(graph: Graph) -> None:
    if graph.principal_column is not None:
        return
    max_height = None
    principal = None
    for col in graph.columns().keys():
        for subgroup in _column_subgroups(graph, col):
            h = _subgroup_height(subgroup)
            if max_height is None or h > max_height:
                max_height = h
                principal = col
    graph.principal_column = principal


def _choose_anchor(graph: Graph, edge: Edge) -> Tuple[Node, Node]:
    src = graph.nodes[edge.src]
    dst = graph.nodes[edge.dst]

    if graph.principal_column is None:
        # Default: inputs align to the node they feed (dst).
        return dst, src

    # Principal column is always the anchor.
    if src.column == graph.principal_column:
        return src, dst
    if dst.column == graph.principal_column:
        return dst, src

    # Default: inputs align to the node they feed (dst).
    return dst, src


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
        # Treat any non-mask connection inside a column as flow adjacency
        if edge.kind == "mask":
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
        # Preserve original spacing when below min_gap (no forced floor here).
        gap = max(0.0, gap)

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


def _distribute_from_top(nodes: List[Node], top: float, min_gap: float) -> None:
    """
    Place nodes from top to bottom starting at 'top', respecting heights and min_gap.
    Order is preserved by node.order.
    """
    if not nodes:
        return
    ordered = sorted(nodes, key=lambda n: n.order)  # top to bottom
    current_top = top
    for n in ordered:
        n.y = current_top - n.height / 2
        current_top -= n.height + min_gap


def _find_anchor_for_node(
    graph: Graph,
    node: Node,
    potential_cols: Set[str],
) -> Optional[Node]:
    """
    Find an anchor for this node within potential columns based on align edges.
    """
    candidates: List[Tuple[int, Node]] = []
    order = _column_order(graph)
    p_idx = order.get(graph.principal_column, 0) if graph.principal_column else 0

    def dist(col: str) -> int:
        return abs(order.get(col, 0) - p_idx)

    for edge in graph.edges:
        if not edge.align:
            continue
        if node.name not in (edge.src, edge.dst):
            continue
        other_name = edge.dst if edge.src == node.name else edge.src
        other = graph.nodes[other_name]
        if other.column not in potential_cols:
            continue

        anchor, follower = _choose_anchor(graph, edge)
        if follower.name != node.name:
            continue

        candidates.append((dist(anchor.column), anchor))

    if not candidates:
        # Fallback: align to source even if it's in a farther column.
        fallback: List[Tuple[int, Node]] = []
        for edge in graph.edges:
            if not edge.align:
                continue
            if edge.dst == node.name:
                other = graph.nodes.get(edge.src)
                if other is not None:
                    fallback.append((dist(other.column), other))
        if not fallback:
            for edge in graph.edges:
                if not edge.align:
                    continue
                if edge.src == node.name:
                    other = graph.nodes.get(edge.dst)
                    if other is not None:
                        fallback.append((dist(other.column), other))
        if not fallback:
            return None
        fallback.sort(key=lambda t: t[0])
        return fallback[0][1]
    candidates.sort(key=lambda t: t[0])
    return candidates[0][1]


def _next_connected_y(
    graph: Graph,
    potential_cols: Set[str],
    next_cols: Set[str],
    anchor_y: float,
) -> Optional[float]:
    """
    Find the highest (max y) node in potential_cols above the anchor (>= anchor_y)
    that connects to any node in next_cols. Returns that node's y, or None.
    """
    if not next_cols:
        return None
    next_nodes = {n.name for n in graph.nodes.values() if n.column in next_cols}
    pot_nodes = [
        n for n in graph.nodes.values()
        if n.column in potential_cols and n.y >= anchor_y
    ]
    pot_nodes.sort(key=lambda n: n.y, reverse=True)

    for node in pot_nodes:
        for edge in graph.edges:
            if edge.src == node.name and edge.dst in next_nodes:
                return node.y
            if edge.dst == node.name and edge.src in next_nodes:
                return node.y
    return None


def _align_subgroup_by_subsubgroups(
    graph: Graph,
    subgroup: List[Node],
    potential_cols: Set[str],
    next_cols: Set[str],
    min_gap: float,
) -> Tuple[bool, Set[str], List[Tuple[str, float]]]:
    """
    Align the entire subgroup to a single anchor.

    Rule: preserve the subgroup's internal spacing (equidistant distribution)
    and shift the whole subgroup to match its chosen anchor. We only resolve
    collisions between different subgroups; we do not segment a subgroup.
    Returns (aligned?, anchors_used, anchor_conflicts).
    """
    if not subgroup:
        return False, set(), []

    order = _column_order(graph)
    p_idx = order.get(graph.principal_column, 0) if graph.principal_column else 0

    def dist(col: str) -> int:
        return abs(order.get(col, 0) - p_idx)

    candidates: List[Tuple[int, int, float, Node, Node]] = []
    for node in subgroup:
        anchor = _find_anchor_for_node(graph, node, potential_cols)
        if anchor is None:
            continue
        candidates.append((dist(anchor.column), abs(anchor.y - node.y), node.order, node, anchor))

    if not candidates:
        return False, set(), []

    # If multiple anchors exist in the same subgroup, we must align each anchored node
    # to its anchor and redistribute the nodes between those anchors.
    anchors_by_node: List[Tuple[Node, Node]] = [(c[3], c[4]) for c in candidates]
    unique_anchors = {(n.name, a.name) for n, a in anchors_by_node}
    if len(unique_anchors) > 1:
        index_by_name = {n.name: i for i, n in enumerate(subgroup)}
        anchors_sorted = sorted(anchors_by_node, key=lambda t: index_by_name.get(t[0].name, t[0].order))

        # If anchors are sufficiently spaced AND already aligned, treat as single-anchor to preserve spacing.
        conflict = False
        anchor_deltas = {node.name: (anchor.y - node.y) for node, anchor in anchors_sorted}
        align_eps = max(1e-6, min_gap * 0.1)
        any_misaligned = any(abs(delta) > align_eps for delta in anchor_deltas.values())
        for (node_a, anchor_a), (node_b, anchor_b) in zip(anchors_sorted, anchors_sorted[1:]):
            idx_a = index_by_name.get(node_a.name)
            idx_b = index_by_name.get(node_b.name)
            if idx_a is None or idx_b is None:
                continue
            if idx_a > idx_b:
                idx_a, idx_b = idx_b, idx_a
                node_a, node_b = node_b, node_a
                anchor_a, anchor_b = anchor_b, anchor_a
            segment = subgroup[idx_a : idx_b + 1]
            if not segment:
                continue
            required = sum(n.height for n in segment) + min_gap * (len(segment) - 1)
            top = anchor_a.y + node_a.height / 2
            bottom = anchor_b.y - node_b.height / 2
            available = top - bottom
            if available < required:
                conflict = True
                break

        if not conflict and not any_misaligned:
            # Fall back to single-anchor behavior to avoid unnecessary reshaping.
            candidates.sort(key=lambda t: (t[0], t[1], t[2]))
            _dist, _order, _delta_abs, aligned_node, anchor = candidates[0]
            connected_nodes: List[Node] = []
            for node in subgroup:
                for edge in graph.edges:
                    if (
                        (edge.src == node.name and edge.dst == anchor.name)
                        or (edge.dst == node.name and edge.src == anchor.name)
                    ):
                        connected_nodes.append(node)
                        break
            if connected_nodes:
                connected_nodes.sort(key=lambda n: (n.order, abs(anchor.y - n.y)))
                aligned_node = connected_nodes[0]
            delta = anchor.y - aligned_node.y
            _shift_subgroup(subgroup, delta)
            return True, {anchor.name}, []

        # Compute deltas before overriding positions.
        for node, anchor in anchors_sorted:
            node.y = anchor.y

        first_node, first_anchor = anchors_sorted[0]
        last_node, last_anchor = anchors_sorted[-1]
        first_idx = index_by_name[first_node.name]
        last_idx = index_by_name[last_node.name]

        # Shift nodes above/below the outer anchors with the same delta as the closest anchor.
        delta_first = anchor_deltas.get(first_node.name, 0.0)
        delta_last = anchor_deltas.get(last_node.name, 0.0)
        if first_idx > 0:
            for node in subgroup[:first_idx]:
                node.y += delta_first
        if last_idx < len(subgroup) - 1:
            for node in subgroup[last_idx + 1 :]:
                node.y += delta_last

        # Redistribute nodes between consecutive anchors, keeping anchors fixed.
        for (node_a, anchor_a), (node_b, anchor_b) in zip(anchors_sorted, anchors_sorted[1:]):
            idx_a = index_by_name[node_a.name]
            idx_b = index_by_name[node_b.name]
            if idx_a == idx_b:
                continue
            if idx_a > idx_b:
                idx_a, idx_b = idx_b, idx_a
                node_a, node_b = node_b, node_a
                anchor_a, anchor_b = anchor_b, anchor_a

            segment = subgroup[idx_a : idx_b + 1]
            if len(segment) <= 2:
                continue

            top = node_a.y + node_a.height / 2
            bottom = node_b.y - node_b.height / 2
            total_heights = sum(n.height for n in segment)
            available = top - bottom
            gap = (available - total_heights) / (len(segment) - 1)
            # If there is no space, we compress (gap can be < min_gap) to preserve anchors.
            if gap < 0:
                gap = 0.0

            current_top = top
            for i, node in enumerate(segment):
                if i == 0 or i == len(segment) - 1:
                    current_top -= node.height + gap
                    continue
                node.y = current_top - node.height / 2
                current_top -= node.height + gap

        # Detect anchor order conflicts and request principal shifts if needed.
        anchor_conflicts: List[Tuple[str, float]] = []
        for (node_a, anchor_a), (node_b, anchor_b) in zip(anchors_sorted, anchors_sorted[1:]):
            idx_a = index_by_name.get(node_a.name)
            idx_b = index_by_name.get(node_b.name)
            if idx_a is None or idx_b is None:
                continue
            if idx_a > idx_b:
                idx_a, idx_b = idx_b, idx_a
                node_a, node_b = node_b, node_a
                anchor_a, anchor_b = anchor_b, anchor_a
            required = (node_a.height + node_b.height) / 2.0 + min_gap
            actual = anchor_a.y - anchor_b.y
            if actual >= required:
                continue
            needed = required - actual
            if anchor_a.column == graph.principal_column:
                # Move anchor_a up by needed (negative shift)
                anchor_conflicts.append((anchor_a.name, -needed))
            elif anchor_b.column == graph.principal_column:
                # Move anchor_b down by needed (positive shift)
                anchor_conflicts.append((anchor_b.name, needed))

        anchors_used = {anchor.name for _node, anchor in anchors_sorted}
        return True, anchors_used, anchor_conflicts

    # Single-anchor behavior (default): shift whole subgroup to anchor.
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))
    _dist, _order, _delta_abs, aligned_node, anchor = candidates[0]

    # If a node in the subgroup is directly connected to the anchor, align that node.
    connected_nodes: List[Node] = []
    for node in subgroup:
        for edge in graph.edges:
            if (
                (edge.src == node.name and edge.dst == anchor.name)
                or (edge.dst == node.name and edge.src == anchor.name)
            ):
                connected_nodes.append(node)
                break
    if connected_nodes:
        connected_nodes.sort(key=lambda n: (n.order, abs(anchor.y - n.y)))
        aligned_node = connected_nodes[0]

    delta = anchor.y - aligned_node.y
    _shift_subgroup(subgroup, delta)

    anchors_used = {anchor.name}
    conflicts = []

    # NOTE: We do NOT constrain by next_cols.
    # Alignment is enforced from principal outward; farther columns must adapt.

    return True, anchors_used, conflicts


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
        desired = (available - total_heights) / (count - 1)
        gap_floor = min(min_gap, MIN_GAP_FLOOR)
        if desired >= min_gap:
            gap = desired
        elif desired >= gap_floor:
            gap = gap_floor
        else:
            gap = max(0.0, desired)

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
        # Use most common X (rounded) if repeated, else average
        xs = [n.original_x if n.original_x is not None else n.x for n in nodes]
        rounded = [round(x, 3) for x in xs]
        counts = {}
        for x in rounded:
            counts[x] = counts.get(x, 0) + 1
        most_common_x = max(counts, key=counts.get)
        if counts[most_common_x] > 1:
            target_x = most_common_x
        else:
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


def _adjust_principal_for_anchor_conflicts(
    graph: Graph,
    anchor_conflicts: List[Tuple[str, float]],
) -> bool:
    if graph.principal_column is None:
        return False
    principal = _principal_nodes(graph)
    if not principal:
        return False

    anchor_map = {n.name: n for n in principal}
    adjusted = False
    for anchor_name, needed in anchor_conflicts:
        anchor = anchor_map.get(anchor_name)
        if not anchor:
            continue
        for node in principal:
            if node.order >= anchor.order:
                node.original_y = (node.original_y if node.original_y is not None else node.y) - needed
        adjusted = True

    return adjusted


def _redistribute_principal_with_fixed_bounds(
    graph: Graph,
    anchor_shifts: Dict[str, float],
    min_gap: float,
) -> Tuple[bool, Dict[str, float]]:
    """
    Redistribute principal column within fixed top/bottom bounds.
    Anchors can shift up (negative) or down (positive). Shifted anchors are fixed,
    and nodes are redistributed between fixed anchors.
    """
    principal = _principal_nodes(graph)
    if not principal:
        return False, {}

    top_node = principal[0]
    bottom_node = principal[-1]
    fixed = {top_node.name, bottom_node.name}
    fixed.update(anchor_shifts.keys())

    # Reset to original positions before applying shifts
    for n in principal:
        n.y = n.original_y if n.original_y is not None else n.y

    top_y = top_node.y
    bottom_y = bottom_node.y

    fixed_indices = [i for i, n in enumerate(principal) if n.name in fixed]
    fixed_indices = sorted(set(fixed_indices))
    index_by_name = {n.name: i for i, n in enumerate(principal)}

    def _next_fixed_below(idx: int) -> Optional[int]:
        for j in fixed_indices:
            if j > idx:
                return j
        return None

    def _next_fixed_above(idx: int) -> Optional[int]:
        for j in reversed(fixed_indices):
            if j < idx:
                return j
        return None

    applied_shifts: Dict[str, float] = {}
    for anchor_name, shift in anchor_shifts.items():
        if anchor_name in (top_node.name, bottom_node.name):
            continue
        anchor = next((n for n in principal if n.name == anchor_name), None)
        if not anchor:
            continue
        idx = index_by_name.get(anchor.name)
        if idx is None:
            continue

        before_y = anchor.y
        capped = shift
        if shift > 0:
            # Downward shift: cap by space to next fixed below
            lower_idx = _next_fixed_below(idx)
            if lower_idx is not None:
                top = anchor.y + anchor.height / 2
                bottom = principal[lower_idx].y - principal[lower_idx].height / 2
                segment = principal[idx : lower_idx + 1]
                available = top - bottom
                gap_floor = min(min_gap, MIN_GAP_FLOOR)
                total_heights = sum(n.height for n in segment)
                required_floor = total_heights + gap_floor * (len(segment) - 1)
                if available < required_floor:
                    required = total_heights
                else:
                    required = required_floor
                slack = available - required
                if slack < 0:
                    slack = 0.0
                if capped > slack:
                    capped = slack
            anchor.y = anchor.y - capped
        elif shift < 0:
            # Upward shift: cap by space to next fixed above
            upper_idx = _next_fixed_above(idx)
            if upper_idx is not None:
                top = principal[upper_idx].y + principal[upper_idx].height / 2
                bottom = anchor.y - anchor.height / 2
                segment = principal[upper_idx : idx + 1]
                available = top - bottom
                gap_floor = min(min_gap, MIN_GAP_FLOOR)
                total_heights = sum(n.height for n in segment)
                required_floor = total_heights + gap_floor * (len(segment) - 1)
                if available < required_floor:
                    required = total_heights
                else:
                    required = required_floor
                slack = available - required
                if slack < 0:
                    slack = 0.0
                if -capped > slack:
                    capped = -slack
            anchor.y = anchor.y - capped

        if anchor.y > top_y:
            anchor.y = top_y
        if anchor.y < bottom_y:
            anchor.y = bottom_y
        applied = anchor.y - before_y
        if abs(applied) > 1e-6:
            applied_shifts[anchor.name] = applied

    _distribute_column_with_fixed(principal, fixed, min_gap=min_gap)

    for n in principal:
        n.original_y = n.y

    return True, applied_shifts


def _propagate_anchor_shifts_to_subgroups(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[Node]]],
    subgroup_anchor_names: Dict[str, Dict[int, Set[str]]],
    applied_shifts: Dict[str, float],
) -> bool:
    moved = False
    for col, subgroups in subgroup_lists.items():
        if graph.principal_column and col == graph.principal_column:
            continue
        for idx, subgroup in enumerate(subgroups):
            anchor_names = subgroup_anchor_names.get(col, {}).get(idx)
            if not anchor_names or len(anchor_names) != 1:
                continue
            anchor_name = next(iter(anchor_names))
            delta = applied_shifts.get(anchor_name)
            if delta is None or abs(delta) <= 1e-6:
                continue
            _shift_subgroup(subgroup, delta)
            for node in subgroup:
                node.original_y = node.y
            moved = True
    return moved


def _propagate_nonprincipal_anchor_shifts(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[Node]]],
    subgroup_anchor_names: Dict[str, Dict[int, Set[str]]],
    subgroup_anchor_y_at_align: Dict[Tuple[str, int], float],
) -> Set[str]:
    """Move subgroups to follow a single non-principal anchor that moved."""
    moved_cols: Set[str] = set()
    for col, subgroups in subgroup_lists.items():
        if graph.principal_column and col == graph.principal_column:
            continue
        for idx, subgroup in enumerate(subgroups):
            anchor_names = subgroup_anchor_names.get(col, {}).get(idx)
            if not anchor_names or len(anchor_names) != 1:
                continue
            anchor_name = next(iter(anchor_names))
            anchor = graph.nodes.get(anchor_name)
            if not anchor:
                continue
            if graph.principal_column and anchor.column == graph.principal_column:
                continue
            if anchor.column == col:
                continue
            key = (col, idx)
            anchor_y_at_align = subgroup_anchor_y_at_align.get(key)
            if anchor_y_at_align is None:
                continue
            delta = anchor.y - anchor_y_at_align
            if abs(delta) <= 1e-6:
                continue
            _shift_subgroup(subgroup, delta)
            subgroup_anchor_y_at_align[key] = anchor.y
            moved_cols.add(col)
    return moved_cols


def _resolve_overlaps_in_columns(
    subgroup_lists: Dict[str, List[List[Node]]],
    fixed_subgroups: Dict[str, Set[int]],
    conflicts_all: List[Tuple[str, Tuple[int, int, float]]],
    cols: Set[str],
) -> None:
    for col in cols:
        subgroups = subgroup_lists.get(col, [])
        if not subgroups:
            continue
        for i in range(1, len(subgroups)):
            prev = subgroups[i - 1]
            curr = subgroups[i]
            prev_top, prev_bottom = _subgroup_bounds(prev)
            curr_top, _curr_bottom = _subgroup_bounds(curr)
            gap = prev_bottom - curr_top
            delta = OVERLAP_EDGE_GAP - gap
            if abs(delta) <= 1e-6:
                continue
            upper_idx = i - 1
            if upper_idx in fixed_subgroups[col]:
                conflicts_all.append((col, (upper_idx, i, delta)))
                continue
            _shift_subgroup(prev, delta)


def _realign_subgroups_to_anchor_connected(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[Node]]],
    subgroup_anchor_names: Dict[str, Dict[int, Set[str]]],
    subgroup_anchor_y_at_align: Dict[Tuple[str, int], float],
    cols: Set[str],
) -> Set[str]:
    """After propagation, align subgroups to their anchor using the connected node."""
    moved_cols: Set[str] = set()
    for col in cols:
        subgroups = subgroup_lists.get(col, [])
        if not subgroups:
            continue
        for idx, subgroup in enumerate(subgroups):
            anchor_names = subgroup_anchor_names.get(col, {}).get(idx)
            if not anchor_names or len(anchor_names) != 1:
                continue
            anchor_name = next(iter(anchor_names))
            anchor = graph.nodes.get(anchor_name)
            if not anchor:
                continue
            if graph.principal_column and anchor.column == graph.principal_column:
                continue
            if anchor.column == col:
                continue
            target_node = None
            best_dist = None
            for node in subgroup:
                for edge in graph.edges:
                    if not edge.align:
                        continue
                    if (
                        (edge.src == node.name and edge.dst == anchor.name)
                        or (edge.dst == node.name and edge.src == anchor.name)
                    ):
                        dist = abs(anchor.y - node.y)
                        if best_dist is None or dist < best_dist:
                            best_dist = dist
                            target_node = node
            if not target_node:
                continue
            delta = anchor.y - target_node.y
            if abs(delta) <= 1e-6:
                continue
            _shift_subgroup(subgroup, delta)
            subgroup_anchor_y_at_align[(col, idx)] = anchor.y
            moved_cols.add(col)
    return moved_cols


def _subgroup_has_internal_overlap(subgroup: List[Node]) -> bool:
    if len(subgroup) < 2:
        return False
    for i in range(1, len(subgroup)):
        prev = subgroup[i - 1]
        curr = subgroup[i]
        prev_bottom = prev.y - prev.height / 2
        curr_top = curr.y + curr.height / 2
        gap = prev_bottom - curr_top
        if gap < OVERLAP_EDGE_GAP - 1e-6:
            return True
    return False


def _subgroup_follower_nodes(graph: Graph, subgroup: List[Node]) -> Set[str]:
    fixed: Set[str] = set()
    subgroup_names = {n.name for n in subgroup}
    for edge in graph.edges:
        if not edge.align:
            continue
        if edge.src in subgroup_names and edge.dst not in subgroup_names:
            fixed.add(edge.src)
            continue
        if edge.dst in subgroup_names and edge.src not in subgroup_names:
            fixed.add(edge.dst)
    return fixed


def _fix_internal_overlaps_in_subgroups(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[Node]]],
    min_gap: float,
) -> None:
    for col, subgroups in subgroup_lists.items():
        if graph.principal_column and col == graph.principal_column:
            continue
        for subgroup in subgroups:
            if not _subgroup_has_internal_overlap(subgroup):
                continue
            fixed = _subgroup_follower_nodes(graph, subgroup)
            fixed_indices = [i for i, n in enumerate(subgroup) if n.name in fixed]
            if 0 not in fixed_indices:
                fixed_indices.append(0)
            if len(subgroup) - 1 not in fixed_indices:
                fixed_indices.append(len(subgroup) - 1)
            fixed_indices = sorted(set(fixed_indices))
            insufficient = False
            for i in range(len(fixed_indices) - 1):
                start = fixed_indices[i]
                end = fixed_indices[i + 1]
                if start == end:
                    continue
                top = subgroup[start].y + subgroup[start].height / 2
                bottom = subgroup[end].y - subgroup[end].height / 2
                segment = subgroup[start : end + 1]
                total_heights = sum(n.height for n in segment)
                available = top - bottom
                if available + 1e-6 < total_heights:
                    insufficient = True
                    break
            if insufficient:
                continue
            # Redistribute only between fixed anchors to avoid reordering.
            for i in range(len(fixed_indices) - 1):
                start = fixed_indices[i]
                end = fixed_indices[i + 1]
                if start == end:
                    continue
                segment = subgroup[start : end + 1]
                if len(segment) <= 2:
                    continue
                top = subgroup[start].y + subgroup[start].height / 2
                bottom = subgroup[end].y - subgroup[end].height / 2
                total_heights = sum(n.height for n in segment)
                available = top - bottom
                gap = (available - total_heights) / (len(segment) - 1)
                if gap < 0:
                    gap = 0.0
                current_top = top
                for j, node in enumerate(segment):
                    if j == 0 or j == len(segment) - 1:
                        current_top -= node.height + gap
                        continue
                    node.y = current_top - node.height / 2
                    current_top -= node.height + gap


def _final_realign_to_principal(graph: Graph, min_gap: float) -> None:
    col_order = _column_order(graph)
    principal_idx = col_order.get(graph.principal_column, 0) if graph.principal_column else 0
    ordered_cols = [
        c for c in col_order.keys()
        if not (graph.principal_column and c == graph.principal_column)
    ]
    ordered_cols.sort(
        key=lambda c: (abs(col_order.get(c, 0) - principal_idx), col_order.get(c, 0))
    )
    for col in ordered_cols:
        subgroups = _column_subgroups(graph, col)
        col_idx = col_order.get(col, 0)
        if col_idx >= principal_idx:
            potential_cols = {c for c, i in col_order.items() if principal_idx <= i <= col_idx}
            next_cols = {c for c, i in col_order.items() if i > col_idx}
        else:
            potential_cols = {c for c, i in col_order.items() if col_idx <= i <= principal_idx}
            next_cols = {c for c, i in col_order.items() if i < col_idx}
        for subgroup in subgroups:
            _align_subgroup_by_subsubgroups(
                graph,
                subgroup,
                potential_cols,
                next_cols,
                min_gap=min_gap,
            )


def _anchor_shift_slack(
    principal: List[Node],
    fixed_indices: Set[int],
    idx: int,
    direction: str,
    min_gap: float,
) -> float:
    if idx <= 0 or idx >= len(principal) - 1:
        return 0.0
    if direction == "up":
        upper_idx = None
        for j in reversed(sorted(fixed_indices)):
            if j < idx:
                upper_idx = j
                break
        if upper_idx is None:
            return 0.0
        top = principal[upper_idx].y + principal[upper_idx].height / 2
        bottom = principal[idx].y - principal[idx].height / 2
        segment = principal[upper_idx : idx + 1]
    else:
        lower_idx = None
        for j in sorted(fixed_indices):
            if j > idx:
                lower_idx = j
                break
        if lower_idx is None:
            return 0.0
        top = principal[idx].y + principal[idx].height / 2
        bottom = principal[lower_idx].y - principal[lower_idx].height / 2
        segment = principal[idx : lower_idx + 1]

    available = top - bottom
    gap_floor = min(min_gap, MIN_GAP_FLOOR)
    total_heights = sum(n.height for n in segment)
    required_floor = total_heights + gap_floor * (len(segment) - 1)
    if available < required_floor:
        required = total_heights
    else:
        required = required_floor
    slack = available - required
    if slack < 0:
        slack = 0.0
    return slack


def _anchor_alignment_shifts(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[Node]]],
    subgroup_anchor: Dict[str, Dict[int, Node]],
    subgroup_anchor_names: Dict[str, Dict[int, Set[str]]],
) -> Dict[str, float]:
    """
    If a subgroup moved (or was distributed) and its anchor stayed behind,
    return the exact shifts needed to align the anchor to the connected node.
    """
    shifts: Dict[str, float] = {}
    principal = _principal_nodes(graph) if graph.principal_column else []
    principal_index = {n.name: i for i, n in enumerate(principal)}
    for col, subgroups in subgroup_lists.items():
        anchors = subgroup_anchor.get(col, {})
        if not anchors:
            continue
        for idx, subgroup in enumerate(subgroups):
            anchor = anchors.get(idx)
            if not anchor:
                continue
            # Skip moving principal when subgroup has a single anchor in principal.
            if anchor.column == graph.principal_column:
                principal_anchors: Set[str] = set()
                for node in subgroup:
                    for edge in graph.edges:
                        if not edge.align:
                            continue
                        if node.name not in (edge.src, edge.dst):
                            continue
                        other_name = edge.dst if edge.src == node.name else edge.src
                        other = graph.nodes.get(other_name)
                        if other and other.column == graph.principal_column:
                            principal_anchors.add(other.name)
                if len(principal_anchors) == 1:
                    continue
            if anchor.column == graph.principal_column:
                anchor_idx = principal_index.get(anchor.name)
                if anchor_idx is not None and anchor_idx in (0, len(principal) - 1):
                    continue
            target_y = None
            best_dist = None
            for node in subgroup:
                for edge in graph.edges:
                    if (
                        (edge.src == node.name and edge.dst == anchor.name)
                        or (edge.dst == node.name and edge.src == anchor.name)
                    ):
                        dist = abs(anchor.y - node.y)
                        if best_dist is None or dist < best_dist:
                            best_dist = dist
                            target_y = node.y
            if target_y is None:
                continue
            delta = anchor.y - target_y
            if abs(delta) > 1e-6:
                shifts[anchor.name] = delta
    return shifts


def layout(
    graph: Graph,
    min_gap: float = 0.2,
    max_iters: int = 5,
) -> List[Tuple[str, Tuple[int, int, float]]]:
    """
    Apply baseline distribution, alignment constraints, and resolve overlaps.
    Returns a list of conflicts per column.
    """
    conflicts_all: List[Tuple[str, Tuple[int, int, float]]] = []
    anchor_conflicts_all: List[Tuple[str, float]] = []

    # Initialize original positions once
    for node in graph.nodes.values():
        node.original_y = node.original_y if node.original_y is not None else node.y
        node.original_x = node.original_x if node.original_x is not None else node.x

    # Auto-detect columns/principal if enabled
    _auto_columns(graph)
    _infer_principal_if_missing(graph)

    # Mark align only for cross-column edges (override any existing align)
    for edge in graph.edges:
        src = graph.nodes.get(edge.src)
        dst = graph.nodes.get(edge.dst)
        if not src or not dst:
            continue
        edge.align = (src.column != dst.column)

    only_one_column = len(graph.columns()) <= 1

    principal_fixed_nodes: Set[str] = set()
    final_subgroup_anchor_names: Dict[str, Dict[int, Set[str]]] = {}

    for _iter in range(max_iters):
        conflicts_all = []
        anchor_conflicts_all = []

        # Reset to original positions each iteration
        for node in graph.nodes.values():
            node.y = node.original_y
            node.fixed_y = False

        # Distribute principal column every iteration
        principal_nodes = _principal_nodes(graph)
        if principal_nodes:
            if principal_fixed_nodes:
                fixed = set(principal_fixed_nodes)
                fixed.add(principal_nodes[0].name)
                fixed.add(principal_nodes[-1].name)
                _distribute_column_with_fixed(principal_nodes, fixed, min_gap=min_gap)
            else:
                _baseline_distribute_subgroup(principal_nodes, min_gap=min_gap)

        # Baseline distribution per subgroup (skip principal column)
        for col in graph.columns().keys():
            if graph.principal_column and col == graph.principal_column and not only_one_column:
                continue
            for subgroup in _column_subgroups(graph, col):
                _baseline_distribute_subgroup(subgroup, min_gap=min_gap)

        # Apply alignment constraints with sub-subgroup behavior
        fixed_subgroups: Dict[str, Set[int]] = {}
        subgroup_map: Dict[str, Dict[str, int]] = {}
        subgroup_lists: Dict[str, List[List[Node]]] = {}
        subgroup_anchor: Dict[str, Dict[int, Node]] = {}
        subgroup_anchor_names: Dict[str, Dict[int, Set[str]]] = {}
        subgroup_anchor_y_at_align: Dict[Tuple[str, int], float] = {}
        subgroup_anchor_y_at_align: Dict[Tuple[str, int], float] = {}
        # No fixed anchors in principal; outer columns adapt to principal

        for col in graph.columns().keys():
            subgroup_lists[col] = _column_subgroups(graph, col)
            subgroup_map[col] = {}
            subgroup_anchor[col] = {}
            subgroup_anchor_names[col] = {}
            for idx, subgroup in enumerate(subgroup_lists[col]):
                for node in subgroup:
                    subgroup_map[col][node.name] = idx
            fixed_subgroups[col] = set()

        # Pre-compute column order for potential/next columns
        col_order = _column_order(graph)
        principal_idx = col_order.get(graph.principal_column, 0) if graph.principal_column else 0

        # Align columns from principal outward so outer columns follow inner updates.
        ordered_cols = [
            c for c in col_order.keys()
            if not (graph.principal_column and c == graph.principal_column)
        ]
        ordered_cols.sort(
            key=lambda c: (abs(col_order.get(c, 0) - principal_idx), col_order.get(c, 0))
        )

        # Multi-pass alignment so outer/inner dependencies can settle.
        for _pass in range(3):
            moved = False
            for col in ordered_cols:
                subgroups = subgroup_lists.get(col, [])
                col_idx = col_order.get(col, 0)
                if col_idx >= principal_idx:
                    potential_cols = {c for c, i in col_order.items() if principal_idx <= i <= col_idx}
                    next_cols = {c for c, i in col_order.items() if i > col_idx}
                else:
                    potential_cols = {c for c, i in col_order.items() if col_idx <= i <= principal_idx}
                    next_cols = {c for c, i in col_order.items() if i < col_idx}

                for idx, subgroup in enumerate(subgroups):
                    before = [n.y for n in subgroup]
                    aligned, anchor_names, anchor_conflicts = _align_subgroup_by_subsubgroups(
                        graph,
                        subgroup,
                        potential_cols,
                        next_cols,
                        min_gap=min_gap,
                    )
                    if aligned:
                        fixed_subgroups[col].add(idx)
                        if anchor_conflicts:
                            anchor_conflicts_all.extend(anchor_conflicts)
                        if anchor_names:
                            anchors = [graph.nodes[name] for name in anchor_names]
                            # Store one anchor for conflict handling (closest to principal)
                            anchor_list = sorted(
                                anchors,
                                key=lambda a: abs(col_order.get(a.column, 0) - principal_idx),
                            )
                            subgroup_anchor[col][idx] = anchor_list[0]
                            subgroup_anchor_names[col][idx] = set(anchor_names)
                            if len(anchor_names) == 1:
                                subgroup_anchor_y_at_align[(col, idx)] = subgroup_anchor[col][idx].y
                            else:
                                subgroup_anchor_y_at_align.pop((col, idx), None)
                            if len(anchor_names) == 1:
                                subgroup_anchor_y_at_align[(col, idx)] = subgroup_anchor[col][idx].y
                            else:
                                subgroup_anchor_y_at_align.pop((col, idx), None)
                    after = [n.y for n in subgroup]
                    if any(abs(a - b) > 1e-6 for a, b in zip(after, before)):
                        moved = True
            if not moved:
                break
        # Principal already distributed at the start of the iteration
        final_subgroup_anchor_names = {
            col: {idx: set(names) for idx, names in anchors.items()}
            for col, anchors in subgroup_anchor_names.items()
        }

        # Clamp anchored subgroups to principal vertical bounds (no hardcode: any anchor in principal)
        if graph.principal_column:
            principal_nodes = _principal_nodes(graph)
            if principal_nodes:
                principal_top = max(n.y + n.height / 2 for n in principal_nodes)
                principal_bottom = min(n.y - n.height / 2 for n in principal_nodes)
                principal_orig_top = max(
                    (n.original_y if n.original_y is not None else n.y) + n.height / 2
                    for n in principal_nodes
                )
                principal_orig_bottom = min(
                    (n.original_y if n.original_y is not None else n.y) - n.height / 2
                    for n in principal_nodes
                )
                col_orig_bounds: Dict[str, Tuple[float, float]] = {}
                for col_name, col_nodes in graph.columns().items():
                    if not col_nodes:
                        continue
                    top = max(
                        (n.original_y if n.original_y is not None else n.y) + n.height / 2
                        for n in col_nodes
                    )
                    bottom = min(
                        (n.original_y if n.original_y is not None else n.y) - n.height / 2
                        for n in col_nodes
                    )
                    col_orig_bounds[col_name] = (top, bottom)
                for col, subgroups in subgroup_lists.items():
                    if col == graph.principal_column:
                        continue
                    col_orig_top, col_orig_bottom = col_orig_bounds.get(
                        col, (principal_orig_top, principal_orig_bottom)
                    )
                    allowed_top = principal_top + (col_orig_top - principal_orig_top)
                    allowed_bottom = principal_bottom + (col_orig_bottom - principal_orig_bottom)
                    # Never allow a column to go above/below its original extremes.
                    if allowed_top > col_orig_top:
                        allowed_top = col_orig_top
                    if allowed_bottom < col_orig_bottom:
                        allowed_bottom = col_orig_bottom
                    for idx, subgroup in enumerate(subgroups):
                        anchor = subgroup_anchor.get(col, {}).get(idx)
                        if not anchor or anchor.column != graph.principal_column:
                            continue
                        top, bottom = _subgroup_bounds(subgroup)
                        delta = 0.0
                        if top > allowed_top:
                            delta -= (top - allowed_top)
                        if bottom < allowed_bottom:
                            delta += (allowed_bottom - bottom)
                        if abs(delta) > 1e-6:
                            _shift_subgroup(subgroup, delta)

        # Enforce top constraint for unconnected subgroups
        if graph.principal_column:
            principal_top = max(n.y + n.height / 2 for n in _principal_nodes(graph))
            for col, subgroups in subgroup_lists.items():
                if col == graph.principal_column:
                    continue
                for idx, subgroup in enumerate(subgroups):
                    if idx in fixed_subgroups[col]:
                        continue
                    top, _bottom = _subgroup_bounds(subgroup)
                    if top > principal_top:
                        shift = (top - principal_top) + min_gap
                        _shift_subgroup(subgroup, -shift)

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
                # Enforce fixed edge gap between upper-bottom and lower-top.
                delta = OVERLAP_EDGE_GAP - gap
                if abs(delta) <= 1e-6:
                    continue
                upper_idx = i - 1
                if upper_idx in fixed_subgroups[col]:
                    conflicts_all.append((col, (upper_idx, i, delta)))
                    continue
                _shift_subgroup(prev, delta)

        # Propagate shifts from non-principal anchors to dependent subgroups
        propagated_cols = _propagate_nonprincipal_anchor_shifts(
            graph,
            subgroup_lists,
            subgroup_anchor_names,
            subgroup_anchor_y_at_align,
        )
        if propagated_cols:
            realigned_cols = _realign_subgroups_to_anchor_connected(
                graph,
                subgroup_lists,
                subgroup_anchor_names,
                subgroup_anchor_y_at_align,
                propagated_cols,
            )
            cols_to_fix = set(propagated_cols)
            cols_to_fix.update(realigned_cols)
            if cols_to_fix:
                _resolve_overlaps_in_columns(
                    subgroup_lists,
                    fixed_subgroups,
                    conflicts_all,
                    cols_to_fix,
                )

        # Final pass inside iteration: fix internal overlaps within subgroups.
        _fix_internal_overlaps_in_subgroups(graph, subgroup_lists, min_gap=min_gap)

        # Propagate shifts from non-principal anchors to dependent subgroups
        propagated_cols = _propagate_nonprincipal_anchor_shifts(
            graph,
            subgroup_lists,
            subgroup_anchor_names,
            subgroup_anchor_y_at_align,
        )
        if propagated_cols:
            _resolve_overlaps_in_columns(
                subgroup_lists,
                fixed_subgroups,
                conflicts_all,
                propagated_cols,
            )

        adjusted = False
        anchor_shifts: Dict[str, float] = {}
        if anchor_conflicts_all:
            def _apply_shift(name: str, shift: float) -> None:
                current = anchor_shifts.get(name)
                if current is None:
                    anchor_shifts[name] = shift
                else:
                    if shift < 0:
                        anchor_shifts[name] = min(current, shift) if current < 0 else shift
                    elif shift > 0:
                        anchor_shifts[name] = max(current, shift) if current > 0 else shift
            for name, needed in anchor_conflicts_all:
                _apply_shift(name, needed)
        if conflicts_all:
            principal = _principal_nodes(graph)
            index_by_name = {n.name: i for i, n in enumerate(principal)}
            fixed_indices: Set[int] = {0, len(principal) - 1} if principal else set()
            for name in anchor_shifts.keys():
                idx = index_by_name.get(name)
                if idx is not None:
                    fixed_indices.add(idx)

            def _apply_shift(name: str, shift: float) -> None:
                current = anchor_shifts.get(name)
                if current is None:
                    anchor_shifts[name] = shift
                else:
                    if shift < 0:
                        anchor_shifts[name] = min(current, shift) if current < 0 else shift
                    elif shift > 0:
                        anchor_shifts[name] = max(current, shift) if current > 0 else shift

            for col, (upper_idx, lower_idx, delta) in conflicts_all:
                anchors = subgroup_anchor.get(col, {})
                upper_anchor = anchors.get(upper_idx)
                lower_anchor = anchors.get(lower_idx)
                if not upper_anchor and not lower_anchor:
                    continue

                # Cap delta by available slack on anchors (allows smaller gap if no space).
                delta_eff = delta
                if principal and (upper_anchor or lower_anchor):
                    if delta > 0:
                        cap = 0.0
                        if upper_anchor:
                            idx = index_by_name.get(upper_anchor.name)
                            if idx is not None:
                                cap += _anchor_shift_slack(
                                    principal, fixed_indices, idx, "up", min_gap
                                )
                        if lower_anchor:
                            idx = index_by_name.get(lower_anchor.name)
                            if idx is not None:
                                cap += _anchor_shift_slack(
                                    principal, fixed_indices, idx, "down", min_gap
                                )
                        if cap <= 0:
                            continue
                        if cap < delta_eff:
                            delta_eff = cap
                    elif delta < 0:
                        cap = 0.0
                        if upper_anchor:
                            idx = index_by_name.get(upper_anchor.name)
                            if idx is not None:
                                cap += _anchor_shift_slack(
                                    principal, fixed_indices, idx, "down", min_gap
                                )
                        if lower_anchor:
                            idx = index_by_name.get(lower_anchor.name)
                            if idx is not None:
                                cap += _anchor_shift_slack(
                                    principal, fixed_indices, idx, "up", min_gap
                                )
                        if cap <= 0:
                            continue
                        if cap < -delta_eff:
                            delta_eff = -cap

                if delta > 0:
                    remaining = delta_eff
                    if upper_anchor:
                        idx = index_by_name.get(upper_anchor.name)
                        if idx is not None:
                            slack_up = _anchor_shift_slack(
                                principal, fixed_indices, idx, "up", min_gap
                            )
                            move_up = min(remaining, slack_up)
                            if move_up > 0:
                                _apply_shift(upper_anchor.name, -move_up)
                                fixed_indices.add(idx)
                                remaining -= move_up
                    if remaining > 0 and lower_anchor:
                        idx = index_by_name.get(lower_anchor.name)
                        if idx is not None:
                            slack_down = _anchor_shift_slack(
                                principal, fixed_indices, idx, "down", min_gap
                            )
                            move_down = min(remaining, slack_down)
                            if move_down > 0:
                                _apply_shift(lower_anchor.name, move_down)
                                fixed_indices.add(idx)
                                remaining -= move_down
                elif delta < 0:
                    remaining = -delta_eff
                    if upper_anchor:
                        idx = index_by_name.get(upper_anchor.name)
                        if idx is not None:
                            slack_down = _anchor_shift_slack(
                                principal, fixed_indices, idx, "down", min_gap
                            )
                            move_down = min(remaining, slack_down)
                            if move_down > 0:
                                _apply_shift(upper_anchor.name, move_down)
                                fixed_indices.add(idx)
                                remaining -= move_down
                        if remaining > 0 and lower_anchor:
                            idx = index_by_name.get(lower_anchor.name)
                            if idx is not None:
                                slack_up = _anchor_shift_slack(
                                    principal, fixed_indices, idx, "up", min_gap
                                )
                                move_up = min(remaining, slack_up)
                                if move_up > 0:
                                    _apply_shift(lower_anchor.name, -move_up)
                                    fixed_indices.add(idx)
                                    remaining -= move_up
        # If a subgroup moved, force its anchor to align with the connected node.
        anchor_align_shifts = _anchor_alignment_shifts(
            graph,
            subgroup_lists,
            subgroup_anchor,
            subgroup_anchor_names,
        )
        if graph.principal_column:
            principal = _principal_nodes(graph)
            index_by_name = {n.name: i for i, n in enumerate(principal)}
            fixed_indices: Set[int] = {0, len(principal) - 1} if principal else set()
            for name in anchor_shifts.keys():
                idx = index_by_name.get(name)
                if idx is not None:
                    fixed_indices.add(idx)

            def _apply_shift(name: str, shift: float) -> None:
                current = anchor_shifts.get(name)
                if current is None:
                    anchor_shifts[name] = shift
                else:
                    if shift < 0:
                        anchor_shifts[name] = min(current, shift) if current < 0 else shift
                    elif shift > 0:
                        anchor_shifts[name] = max(current, shift) if current > 0 else shift

            for name, delta in anchor_align_shifts.items():
                idx = index_by_name.get(name)
                if idx is None:
                    continue
                if delta > 0:
                    slack = _anchor_shift_slack(principal, fixed_indices, idx, "down", min_gap)
                    if slack <= 0:
                        continue
                    delta = min(delta, slack)
                elif delta < 0:
                    slack = _anchor_shift_slack(principal, fixed_indices, idx, "up", min_gap)
                    if slack <= 0:
                        continue
                    delta = max(delta, -slack)
                else:
                    continue
                if abs(delta) <= 1e-6:
                    continue
                _apply_shift(name, delta)
        if anchor_shifts:
            adjusted, applied_shifts = _redistribute_principal_with_fixed_bounds(
                graph,
                anchor_shifts,
                min_gap=min_gap,
            )
            if adjusted:
                principal_fixed_nodes = set(anchor_shifts.keys())
                if applied_shifts:
                    _propagate_anchor_shifts_to_subgroups(
                        graph,
                        subgroup_lists,
                        subgroup_anchor_names,
                        applied_shifts,
                    )
                else:
                    break
        if adjusted:
            continue
        break

    if graph.principal_column:
        _final_realign_to_principal(graph, min_gap=min_gap)
        if final_subgroup_anchor_names:
            subgroup_lists = {col: _column_subgroups(graph, col) for col in graph.columns().keys()}
            empty_fixed = {col: set() for col in subgroup_lists.keys()}
            cols = set(final_subgroup_anchor_names.keys())
            cols.discard(graph.principal_column)
            if cols:
                realigned_cols = _realign_subgroups_to_anchor_connected(
                    graph,
                    subgroup_lists,
                    final_subgroup_anchor_names,
                    {},
                    cols,
                )
                if realigned_cols:
                    _resolve_overlaps_in_columns(
                        subgroup_lists,
                        empty_fixed,
                        conflicts_all,
                        realigned_cols,
                    )
    # Align columns in X at the end
    _align_columns_x(graph)

    return conflicts_all
