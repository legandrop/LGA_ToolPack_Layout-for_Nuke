"""
______________________________________________________________

  LGA_arrangeNodes v2.0 | 2026 | Lega

  Align and distribute multiple columns based on connections
______________________________________________________________

Notes:
- This is a full rewrite based on the validated graph layout core.
- Works on selected nodes only.
- Uses node centers and screen sizes (heights) for distribution.
"""

import nuke
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
import os
import time

# -------------------------
# Config
# -------------------------
TOLERANCE_X = 55  # pixels for column grouping
MIN_GAP = 10      # pixels minimum gap between node boxes
# Compresión mínima permitida cuando no hay espacio (en px).
MIN_GAP_FLOOR = 3
# Fixed gap between the bottom edge of the upper branch and
# the top edge of the lower branch when resolving overlaps.
OVERLAP_NODE_GAP = 30

# -------------------------
# Logging config
# -------------------------
DEBUG = True
DEBUG_CONSOLE = True
DEBUG_LOG = True

script_start_time = None
debug_log_listener = None
debug_logger = None


class RelativeTimeFormatter(logging.Formatter):
    """Formatter that includes relative time since script start."""
    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="arrangeNodes"):
    """Configure logging to write ONLY to file (no console)."""
    global debug_log_listener

    log_filename = f"debugPy_{script_name}.log"
    log_file_path = os.path.join(
        os.path.dirname(__file__), "..", "logs", log_filename
    )

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as exc:
            print(f"Warning: could not clear log: {exc}")

    logger_name = f"{script_name.lower()}_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = RelativeTimeFormatter("[%(relative_time)s] %(message)s")
    file_handler.setFormatter(formatter)

    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass

    debug_log_listener = QueueListener(
        log_queue, file_handler, respect_handler_level=True
    )
    debug_log_listener.daemon = True
    debug_log_listener.start()

    return logger


def _init_logging() -> None:
    global debug_logger
    if DEBUG and DEBUG_LOG:
        debug_logger = setup_debug_logging(script_name="arrangeNodes")


def debug_print(*message, level="info"):
    """Logging helper with console/file switches."""
    global script_start_time
    msg = " ".join(str(arg) for arg in message)

    if DEBUG and DEBUG_LOG:
        if debug_logger is None:
            _init_logging()
        if script_start_time is None:
            script_start_time = time.time()
        if level == "debug":
            debug_logger.debug(msg)
        elif level == "warning":
            debug_logger.warning(msg)
        elif level == "error":
            debug_logger.error(msg)
        else:
            debug_logger.info(msg)

    if DEBUG and DEBUG_CONSOLE:
        if script_start_time is None:
            script_start_time = time.time()
        relative_time = time.time() - script_start_time
        timestamped_msg = f"[{relative_time:.3f}s] {msg}"
        print(timestamped_msg)


def cleanup_logging():
    """Stop the logging listener on exit."""
    global debug_log_listener
    if debug_log_listener:
        try:
            debug_print("Deteniendo listener de logging...")
            debug_log_listener.stop()
            debug_print("Listener detenido")
        except Exception as exc:
            debug_print(f"Error en cleanup: {exc}", level="error")


try:
    import atexit
    atexit.register(cleanup_logging)
except Exception:
    pass

# Classes to ignore
IGNORED_CLASSES = {"BackdropNode", "Viewer"}

# Classes that commonly use a mask as last input
MASK_LAST_CLASSES = {
    "Grade",
    "Blur",
    "ColorCorrect",
    "Multiply",
    "Merge",
    "Merge2",
    "Copy",
}

# -------------------------
# Core data structures
# -------------------------
@dataclass
class NodeModel:
    name: str
    column: str
    order: int
    klass: str = ""
    height: float = 20.0
    x: float = 0.0
    y: float = 0.0
    ref: Optional[object] = None
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
    nodes: Dict[str, NodeModel] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    principal_column: Optional[str] = None
    column_positions: Dict[str, float] = field(default_factory=dict)
    auto_columns: bool = True
    tolerance_x: float = TOLERANCE_X

    def add_node(self, node: NodeModel) -> None:
        self.nodes[node.name] = node
        if node.column not in self.column_positions:
            self.column_positions[node.column] = node.x

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def columns(self) -> Dict[str, List[NodeModel]]:
        cols: Dict[str, List[NodeModel]] = {}
        for node in self.nodes.values():
            cols.setdefault(node.column, []).append(node)
        for col in cols:
            cols[col].sort(key=lambda n: n.order)
        return cols


# -------------------------
# Layout core (ported from layout_core.py)
# -------------------------

def _column_order(graph: Graph) -> Dict[str, int]:
    ordered = sorted(graph.column_positions.items(), key=lambda kv: kv[1])
    return {col: idx for idx, (col, _x) in enumerate(ordered)}


def _subgroup_height(subgroup: List[NodeModel]) -> float:
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
    groups: List[Tuple[float, List[NodeModel]]] = []
    for node in sorted(nodes, key=lambda n: n.original_x if n.original_x is not None else n.x):
        x = node.original_x if node.original_x is not None else node.x
        placed = False
        for i, (gx, gnodes) in enumerate(groups):
            if abs(x - gx) <= graph.tolerance_x:
                gnodes.append(node)
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


def _choose_anchor(graph: Graph, edge: Edge) -> Tuple[NodeModel, NodeModel]:
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


def _column_subgroups(graph: Graph, column: str) -> List[List[NodeModel]]:
    nodes = [n for n in graph.nodes.values() if n.column == column]
    if not nodes:
        return []
    adj = _flow_adjacency(graph, column)
    visited: Set[str] = set()
    subgroups: List[List[NodeModel]] = []
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


def _baseline_distribute_subgroup(subgroup: List[NodeModel], min_gap: float) -> None:
    if not subgroup:
        return
    top = max((n.original_y if n.original_y is not None else n.y) + n.height / 2 for n in subgroup)
    bottom = min((n.original_y if n.original_y is not None else n.y) - n.height / 2 for n in subgroup)
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


def _shift_subgroup(subgroup: List[NodeModel], delta: float) -> None:
    for node in subgroup:
        node.y += delta


def _subgroup_bounds(subgroup: List[NodeModel]) -> Tuple[float, float]:
    tops = [n.y + n.height / 2 for n in subgroup]
    bottoms = [n.y - n.height / 2 for n in subgroup]
    return max(tops), min(bottoms)


def _format_subgroup(subgroup: List[NodeModel]) -> str:
    if not subgroup:
        return "[]"
    if len(subgroup) == 1:
        return subgroup[0].name
    return f"{subgroup[0].name}..{subgroup[-1].name}"


def _log_column_overview(graph: Graph) -> None:
    cols = graph.columns()
    debug_print(f"Columnas detectadas: {len(cols)} | principal={graph.principal_column}")
    for col, nodes in cols.items():
        if not nodes:
            continue
        top_name = nodes[0].name
        bottom_name = nodes[-1].name
        debug_print(f"Columna {col}: {len(nodes)} nodos, top={top_name}, bottom={bottom_name}")


def _find_anchor_for_node(graph: Graph, node: NodeModel, potential_cols: Set[str]) -> Optional[NodeModel]:
    candidates: List[Tuple[int, NodeModel]] = []
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
        fallback: List[Tuple[int, NodeModel]] = []
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
) -> Optional[Tuple[float, str]]:
    if not next_cols:
        return None
    next_nodes = {n.name for n in graph.nodes.values() if n.column in next_cols}
    pot_nodes = [n for n in graph.nodes.values() if n.column in potential_cols and n.y >= anchor_y]
    pot_nodes.sort(key=lambda n: n.y, reverse=True)

    for node in pot_nodes:
        for edge in graph.edges:
            if edge.src == node.name and edge.dst in next_nodes:
                return node.y, edge.dst
            if edge.dst == node.name and edge.src in next_nodes:
                return node.y, edge.src
    return None


def _align_subgroup_by_subsubgroups(
    graph: Graph,
    subgroup: List[NodeModel],
    potential_cols: Set[str],
    next_cols: Set[str],
    min_gap: float,
) -> Tuple[bool, Set[str], List[Tuple[str, float]]]:
    if not subgroup:
        return False, set(), []

    order = _column_order(graph)
    p_idx = order.get(graph.principal_column, 0) if graph.principal_column else 0

    def dist(col: str) -> int:
        return abs(order.get(col, 0) - p_idx)

    candidates: List[Tuple[int, int, float, NodeModel, NodeModel]] = []
    for node in subgroup:
        anchor = _find_anchor_for_node(graph, node, potential_cols)
        if anchor is None:
            continue
        candidates.append((dist(anchor.column), node.order, abs(anchor.y - node.y), node, anchor))

    if not candidates:
        return False, set(), []

    anchors_by_node: List[Tuple[NodeModel, NodeModel]] = [(c[3], c[4]) for c in candidates]
    unique_anchors = {(n.name, a.name) for n, a in anchors_by_node}
    if len(unique_anchors) > 1:
        index_by_name = {n.name: i for i, n in enumerate(subgroup)}
        anchors_sorted = sorted(anchors_by_node, key=lambda t: index_by_name.get(t[0].name, t[0].order))

        anchor_deltas = {node.name: (anchor.y - node.y) for node, anchor in anchors_sorted}
        for node, anchor in anchors_sorted:
            node.y = anchor.y

        first_node, first_anchor = anchors_sorted[0]
        last_node, last_anchor = anchors_sorted[-1]
        first_idx = index_by_name[first_node.name]
        last_idx = index_by_name[last_node.name]

        delta_first = anchor_deltas.get(first_node.name, 0.0)
        delta_last = anchor_deltas.get(last_node.name, 0.0)
        if first_idx > 0:
            for node in subgroup[:first_idx]:
                node.y += delta_first
        if last_idx < len(subgroup) - 1:
            for node in subgroup[last_idx + 1 :]:
                node.y += delta_last

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
            if gap < 0:
                gap = 0.0

            current_top = top
            for i, node in enumerate(segment):
                if i == 0 or i == len(segment) - 1:
                    current_top -= node.height + gap
                    continue
                node.y = current_top - node.height / 2
                current_top -= node.height + gap

        return True, {anchor.name for _node, anchor in anchors_sorted}, []

    candidates.sort(key=lambda t: (t[0], t[1], t[2]))
    _dist, _order, _delta_abs, aligned_node, anchor = candidates[0]

    # If a node in the subgroup is directly connected to the anchor, align that node.
    connected_nodes: List[NodeModel] = []
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

    # NOTE: We do NOT constrain by next_cols.
    # Alignment is enforced from principal outward; farther columns must adapt.
    return True, {anchor.name}, []


def _distribute_column_with_fixed(nodes: List[NodeModel], fixed: Set[str], min_gap: float) -> None:
    if not nodes:
        return
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


def _principal_nodes(graph: Graph) -> List[NodeModel]:
    if graph.principal_column is None:
        return []
    nodes = [n for n in graph.nodes.values() if n.column == graph.principal_column]
    nodes.sort(key=lambda n: n.order)
    return nodes


def _align_columns_x(graph: Graph) -> None:
    for col, nodes in graph.columns().items():
        if not nodes:
            continue
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
    subgroup_anchor: Dict[str, Dict[int, NodeModel]],
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

        if upper_anchor.y < lower_anchor.y:
            upper_anchor, lower_anchor = lower_anchor, upper_anchor

        debug_print(
            f"Ajuste principal por solapamiento: columna {col}, ancla {lower_anchor.name}, shift={needed:.2f}"
        )
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
        debug_print(
            f"Ajuste principal por conflicto de anclaje: {anchor.name}, shift={needed:.2f}"
        )
        for node in principal:
            if node.order >= anchor.order:
                node.original_y = (node.original_y if node.original_y is not None else node.y) - needed
        adjusted = True

    return adjusted


def _redistribute_principal_with_fixed_bounds(
    graph: Graph,
    principal_fixed_nodes: Set[str],
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
    fixed = set(principal_fixed_nodes)
    fixed.update(anchor_shifts.keys())
    fixed.add(top_node.name)
    fixed.add(bottom_node.name)

    # Reset to original positions before applying shifts
    for n in principal:
        n.y = n.original_y if n.original_y is not None else n.y

    top_y = top_node.y
    bottom_y = bottom_node.y

    # Precompute fixed indices for segment capacity checks
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
                    debug_print(
                        f"WARN ancla {anchor.name} shift cap: needed={shift:.2f} -> "
                        f"{slack:.2f} (segment {anchor.name}..{principal[lower_idx].name})",
                        level="warning",
                    )
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
                    debug_print(
                        f"WARN ancla {anchor.name} shift cap: needed={shift:.2f} -> "
                        f"{-slack:.2f} (segment {principal[upper_idx].name}..{anchor.name})",
                        level="warning",
                    )
                    capped = -slack
            anchor.y = anchor.y - capped

        # Clamp within principal bounds
        if anchor.y > top_y:
            anchor.y = top_y
        if anchor.y < bottom_y:
            anchor.y = bottom_y
        applied = anchor.y - before_y
        if abs(applied) > 1e-6:
            applied_shifts[anchor.name] = applied

    # Capacity check per segment (only warn on failure)
    for i in range(len(fixed_indices) - 1):
        start = fixed_indices[i]
        end = fixed_indices[i + 1]
        if start == end:
            continue
        top = principal[start].y + principal[start].height / 2
        bottom = principal[end].y - principal[end].height / 2
        segment = principal[start : end + 1]
        available = top - bottom
        gap_floor = min(min_gap, MIN_GAP_FLOOR)
        total_heights = sum(n.height for n in segment)
        required_floor = total_heights + gap_floor * (len(segment) - 1)
        if available < required_floor:
            required = total_heights
        else:
            required = required_floor
        if required - available > 0.001:
            debug_print(
                f"WARN tramo {principal[start].name}..{principal[end].name} sin espacio: "
                f"available={available:.2f}, required={required:.2f}",
                level="warning",
            )

    # Redistribute non-fixed nodes between fixed anchors
    _distribute_column_with_fixed(principal, fixed, min_gap=min_gap)

    # Persist new positions as baseline for next iteration
    for n in principal:
        n.original_y = n.y

    return True, applied_shifts


def _propagate_anchor_shifts_to_subgroups(
    graph: Graph,
    subgroup_lists: Dict[str, List[List[NodeModel]]],
    subgroup_anchor_names: Dict[str, Dict[int, Set[str]]],
    applied_shifts: Dict[str, float],
) -> bool:
    """Move anchored subgroups by the same delta applied to their single anchor."""
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


def _final_realign_to_principal(graph: Graph, min_gap: float) -> None:
    """Final pass to align external columns to the principal after redistribution."""
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
    principal: List[NodeModel],
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
    subgroup_lists: Dict[str, List[List[NodeModel]]],
    subgroup_anchor: Dict[str, Dict[int, NodeModel]],
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
            target_node = None
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
                            target_node = node.name
            if target_y is None:
                debug_print(
                    f"Alineacion ancla: {anchor.name} sin nodo conectado en subgrupo {col}[{idx}] (skip)"
                )
                continue
            delta = anchor.y - target_y
            if abs(delta) <= 1e-6:
                debug_print(
                    f"Alineacion ancla: {anchor.name} ya alineada con {target_node} (delta=0)"
                )
                continue
            debug_print(
                f"Alineacion ancla: {anchor.name} -> {target_node} delta={delta:.2f}"
            )
            shifts[anchor.name] = delta
    return shifts


def layout(graph: Graph, min_gap: float = MIN_GAP, max_iters: int = 5) -> None:
    conflicts_all: List[Tuple[str, Tuple[int, int, float]]] = []
    anchor_conflicts_all: List[Tuple[str, float]] = []

    debug_print(f"=== LAYOUT START (min_gap={min_gap}, max_iters={max_iters}) ===")
    debug_print(f"Nodos: {len(graph.nodes)} | Conexiones: {len(graph.edges)}")

    for node in graph.nodes.values():
        node.original_y = node.original_y if node.original_y is not None else node.y
        node.original_x = node.original_x if node.original_x is not None else node.x

    _auto_columns(graph)
    _infer_principal_if_missing(graph)
    _log_column_overview(graph)
    principal_nodes = _principal_nodes(graph)
    if principal_nodes:
        debug_print(
            f"Fila principal detectada: {principal_nodes[0].name} -> {principal_nodes[-1].name} (max subgroup height)"
        )

    only_one_column = len(graph.columns()) <= 1
    if only_one_column:
        debug_print("Solo una columna: se distribuye la principal como cualquier columna")

    principal_fixed_nodes: Set[str] = set()

    for _iter in range(max_iters):
        debug_print(f"--- Iteracion {_iter + 1} ---")
        conflicts_all = []
        anchor_conflicts_all = []

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

        for col in graph.columns().keys():
            if graph.principal_column and col == graph.principal_column and not only_one_column:
                continue
            for subgroup in _column_subgroups(graph, col):
                _baseline_distribute_subgroup(subgroup, min_gap=min_gap)

        fixed_subgroups: Dict[str, Set[int]] = {}
        subgroup_lists: Dict[str, List[List[NodeModel]]] = {}
        subgroup_anchor: Dict[str, Dict[int, NodeModel]] = {}
        subgroup_anchor_names: Dict[str, Dict[int, Set[str]]] = {}

        for col in graph.columns().keys():
            subgroup_lists[col] = _column_subgroups(graph, col)
            subgroup_anchor[col] = {}
            subgroup_anchor_names[col] = {}
            fixed_subgroups[col] = set()

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
                            anchor_list = sorted(
                                anchors,
                                key=lambda a: abs(col_order.get(a.column, 0) - principal_idx),
                            )
                            subgroup_anchor[col][idx] = anchor_list[0]
                            subgroup_anchor_names[col][idx] = set(anchor_names)
                            # No fixed anchors in principal; outer columns adapt to principal
                    after = [n.y for n in subgroup]
                    if any(abs(a - b) > 1e-6 for a, b in zip(after, before)):
                        moved = True
            if not moved:
                break

        # Log subgroup summary per column (non-principal)
        for col, subgroups in subgroup_lists.items():
            if graph.principal_column and col == graph.principal_column:
                continue
            if not subgroups:
                continue
            subgroup_desc = ", ".join(_format_subgroup(sg) for sg in subgroups)
            anchor_desc = ", ".join(
                f"{idx}:{anchor.name}" for idx, anchor in subgroup_anchor[col].items()
            )
            if not anchor_desc:
                anchor_desc = "none"
            debug_print(f"Columna {col} subgrupos: {subgroup_desc} | anchors: {anchor_desc}")

        # Principal already distributed at the start of the iteration

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

        for col, subgroups in subgroup_lists.items():
            if not subgroups:
                continue
            ordered = subgroups
            for i in range(1, len(ordered)):
                prev = ordered[i - 1]
                curr = ordered[i]
                prev_top, prev_bottom = _subgroup_bounds(prev)
                curr_top, _curr_bottom = _subgroup_bounds(curr)
                gap = prev_bottom - curr_top
                delta = OVERLAP_NODE_GAP - gap
                if abs(delta) <= 1e-6:
                    continue
                upper_idx = i - 1
                if upper_idx in fixed_subgroups[col]:
                    conflicts_all.append((col, (upper_idx, i, delta)))
                    continue
                _shift_subgroup(prev, delta)

        adjusted = False
        anchor_shifts: Dict[str, float] = {}
        if anchor_conflicts_all:
            formatted = ", ".join(f"{name} (+{needed:.2f})" for name, needed in anchor_conflicts_all)
            debug_print(f"Conflictos de anclaje detectados: {formatted}")
            for name, needed in anchor_conflicts_all:
                anchor_shifts[name] = max(anchor_shifts.get(name, 0.0), needed)
        if conflicts_all:
            formatted = ", ".join(
                f"{col}({upper_idx}->{lower_idx}, +{needed:.2f})"
                for col, (upper_idx, lower_idx, needed) in conflicts_all
            )
            debug_print(f"Conflictos de solapamiento detectados: {formatted}")
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
        # Si un subgrupo se movio, forzamos al ancla a alinearse con su nodo conectado.
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
                principal_fixed_nodes,
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
            debug_print("Principal redistribuida dentro de top/bottom, re-iterando...")
            continue
        break

    if graph.principal_column:
        _final_realign_to_principal(graph, min_gap=min_gap)
    _align_columns_x(graph)
    debug_print("=== LAYOUT END ===")


# -------------------------
# Nuke adapter
# -------------------------

def _node_center(node) -> Tuple[float, float]:
    return (
        node.xpos() + node.screenWidth() / 2.0,
        node.ypos() + node.screenHeight() / 2.0,
    )


def _classify_input(node, idx: int) -> str:
    klass = node.Class()
    if klass in ("Merge", "Merge2"):
        # Nuke: input 0 = B, input 1 = A, input 2+ = mask
        if idx == 0:
            return "B"
        if idx == 1:
            return "A"
        return "mask"
    if klass == "Copy":
        if node.inputs() > 1 and idx == node.inputs() - 1:
            return "mask"
        if idx == 0:
            return "A"
    if klass in MASK_LAST_CLASSES and node.inputs() > 1 and idx == node.inputs() - 1:
        return "mask"
    return "flow"


def _build_graph_from_nuke(nodes: List[object]) -> Graph:
    graph = Graph(auto_columns=True, tolerance_x=TOLERANCE_X)

    for n in nodes:
        cx, cy = _node_center(n)
        node = NodeModel(
            name=n.name(),
            klass=n.Class(),
            column="C0",
            order=0,
            x=cx,
            y=-cy,
            height=float(n.screenHeight()),
            ref=n,
        )
        graph.add_node(node)

    # Build edges (no align yet)
    selected_set = {n.name() for n in nodes}
    for n in nodes:
        for i in range(n.inputs()):
            inp = n.input(i)
            if inp is None or inp.name() not in selected_set:
                continue
            kind = _classify_input(n, i)
            graph.add_edge(Edge(inp.name(), n.name(), kind=kind, align=False))

    # Assign columns/principal
    _auto_columns(graph)
    _infer_principal_if_missing(graph)
    debug_print(f"Principal detectada (auto-columns): {graph.principal_column}")
    debug_print("Adapter Nuke: usando Y invertida para layout")

    # Mark align edges for any cross-column connection
    for e in graph.edges:
        src = graph.nodes.get(e.src)
        dst = graph.nodes.get(e.dst)
        if not src or not dst:
            continue
        if src.column == dst.column:
            continue
        e.align = True

    align_count = sum(1 for e in graph.edges if e.align)
    debug_print(f"Grafo construido: nodos={len(graph.nodes)}, edges={len(graph.edges)}, align={align_count}")

    return graph


def _apply_graph_to_nuke(graph: Graph) -> None:
    for node in graph.nodes.values():
        if node.ref is None:
            continue
        ref = node.ref
        new_x = node.x - ref.screenWidth() / 2.0
        # Convert back from inverted Y
        new_y = (-node.y) - ref.screenHeight() / 2.0
        ref.setXpos(int(round(new_x)))
        ref.setYpos(int(round(new_y)))


# -------------------------
# Entry point
# -------------------------

def main() -> None:
    _init_logging()
    debug_print("=== Arrange Nodes v2 START ===")
    selected_nodes = nuke.selectedNodes()
    if len(selected_nodes) < 2:
        nuke.message("Select at least 2 nodes to arrange")
        return

    regular_nodes = [n for n in selected_nodes if n.Class() not in IGNORED_CLASSES]
    if len(regular_nodes) < 2:
        nuke.message("Select at least 2 non-backdrop nodes")
        return

    debug_print(f"Seleccionados: {len(selected_nodes)} | regulares: {len(regular_nodes)}")

    undo = nuke.Undo()
    undo.begin("Arrange Nodes v2")
    try:
        graph = _build_graph_from_nuke(regular_nodes)
        layout(graph, min_gap=MIN_GAP)
        _apply_graph_to_nuke(graph)
        debug_print("=== Arrange Nodes v2 END ===")
    finally:
        undo.end()


# If executed as script
if __name__ == "__main__":
    main()
