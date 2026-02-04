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
        return src, dst

    order = _column_order(graph)
    p_idx = order.get(graph.principal_column, 0)

    def dist(col: str) -> int:
        return abs(order.get(col, 0) - p_idx)

    if dist(src.column) < dist(dst.column):
        return src, dst
    if dist(dst.column) < dist(src.column):
        return dst, src
    return src, dst


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
        gap = min_gap

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
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[0][1]


def _next_connected_y(graph: Graph, potential_cols: Set[str], next_cols: Set[str], anchor_y: float) -> Optional[float]:
    if not next_cols:
        return None
    next_nodes = {n.name for n in graph.nodes.values() if n.column in next_cols}
    pot_nodes = [n for n in graph.nodes.values() if n.column in potential_cols and n.y >= anchor_y]
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
    subgroup: List[NodeModel],
    potential_cols: Set[str],
    next_cols: Set[str],
    min_gap: float,
) -> Tuple[bool, Set[str], List[Tuple[str, float]]]:
    if not subgroup:
        return False, set(), []

    ordered_bt = sorted(subgroup, key=lambda n: n.order, reverse=True)  # bottom to top
    anchors_used: Set[str] = set()
    conflicts: List[Tuple[str, float]] = []

    aligned_indices: List[Tuple[int, NodeModel, NodeModel]] = []
    for i, node in enumerate(ordered_bt):
        anchor = _find_anchor_for_node(graph, node, potential_cols)
        if anchor is None:
            continue
        aligned_indices.append((i, node, anchor))

    if not aligned_indices:
        return False, set(), []

    aligned_indices.sort(key=lambda t: t[0])
    segments: List[Tuple[List[NodeModel], Optional[NodeModel]]] = []

    first_i = aligned_indices[0][0]
    if first_i > 0:
        tail_nodes = ordered_bt[:first_i]
        segments.append((tail_nodes, None))

    for idx, (i, node, anchor) in enumerate(aligned_indices):
        next_i = aligned_indices[idx + 1][0] if idx + 1 < len(aligned_indices) else len(ordered_bt)
        seg_nodes = ordered_bt[i:next_i]
        segments.append((seg_nodes, anchor))
        anchors_used.add(anchor.name)

    for seg_nodes, anchor in segments:
        if anchor is None:
            continue
        aligned_node = seg_nodes[0]
        delta = anchor.y - aligned_node.y
        _shift_subgroup(seg_nodes, delta)

    seg_bounds = []
    for seg_nodes, anchor in segments:
        top, bottom = _subgroup_bounds(seg_nodes)
        seg_bounds.append((seg_nodes, anchor, top, bottom))

    seg_bounds.sort(key=lambda t: t[2], reverse=True)
    for i in range(1, len(seg_bounds)):
        upper_nodes, _upper_anchor, _upper_top, upper_bottom = seg_bounds[i - 1]
        lower_nodes, lower_anchor, lower_top, _lower_bottom = seg_bounds[i]
        gap = upper_bottom - lower_top
        if gap >= min_gap:
            continue
        needed = min_gap - gap
        if lower_anchor is not None:
            conflicts.append((lower_anchor.name, needed))
        else:
            _shift_subgroup(lower_nodes, -needed)
            new_top, new_bottom = _subgroup_bounds(lower_nodes)
            seg_bounds[i] = (lower_nodes, lower_anchor, new_top, new_bottom)

    if next_cols:
        for seg_nodes, seg_anchor, seg_top, _seg_bottom in seg_bounds:
            if seg_anchor is None:
                continue
            next_y = _next_connected_y(graph, potential_cols, next_cols, seg_anchor.y)
            if next_y is None:
                continue
            if seg_top > next_y:
                needed = seg_top - next_y + min_gap
                conflicts.append((seg_anchor.name, needed))

    return True, anchors_used, conflicts


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
        gap = (available - total_heights) / (count - 1)
        if gap < min_gap:
            gap = min_gap

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


def layout(graph: Graph, min_gap: float = MIN_GAP, max_iters: int = 3) -> None:
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

    for _iter in range(max_iters):
        debug_print(f"--- Iteracion {_iter + 1} ---")
        conflicts_all = []
        anchor_conflicts_all = []

        for node in graph.nodes.values():
            node.y = node.original_y
            node.fixed_y = False

        for col in graph.columns().keys():
            if graph.principal_column and col == graph.principal_column:
                continue
            for subgroup in _column_subgroups(graph, col):
                _baseline_distribute_subgroup(subgroup, min_gap=min_gap)

        fixed_subgroups: Dict[str, Set[int]] = {}
        subgroup_lists: Dict[str, List[List[NodeModel]]] = {}
        subgroup_anchor: Dict[str, Dict[int, NodeModel]] = {}
        principal_fixed_nodes: Set[str] = set()

        for col in graph.columns().keys():
            subgroup_lists[col] = _column_subgroups(graph, col)
            subgroup_anchor[col] = {}
            fixed_subgroups[col] = set()

        col_order = _column_order(graph)
        principal_idx = col_order.get(graph.principal_column, 0) if graph.principal_column else 0

        for col, subgroups in subgroup_lists.items():
            if graph.principal_column and col == graph.principal_column:
                continue
            col_idx = col_order.get(col, 0)
            if col_idx >= principal_idx:
                potential_cols = {c for c, i in col_order.items() if principal_idx <= i <= col_idx}
                next_cols = {c for c, i in col_order.items() if i > col_idx}
            else:
                potential_cols = {c for c, i in col_order.items() if col_idx <= i <= principal_idx}
                next_cols = {c for c, i in col_order.items() if i < col_idx}

            for idx, subgroup in enumerate(subgroups):
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
                        for a in anchors:
                            if graph.principal_column and a.column == graph.principal_column:
                                principal_fixed_nodes.add(a.name)

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

        principal_nodes = _principal_nodes(graph)
        if principal_nodes and principal_fixed_nodes:
            _distribute_column_with_fixed(principal_nodes, principal_fixed_nodes, min_gap=min_gap)

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
                if gap >= min_gap:
                    continue
                needed = min_gap - gap
                curr_idx = subgroups.index(curr)
                if curr_idx in fixed_subgroups[col]:
                    conflicts_all.append((col, (i - 1, i, needed)))
                    continue
                _shift_subgroup(curr, -needed)

        adjusted = False
        if anchor_conflicts_all:
            formatted = ", ".join(f"{name} (+{needed:.2f})" for name, needed in anchor_conflicts_all)
            debug_print(f"Conflictos de anclaje detectados: {formatted}")
            adjusted |= _adjust_principal_for_anchor_conflicts(graph, anchor_conflicts_all)
        if conflicts_all:
            formatted = ", ".join(
                f"{col}({upper_idx}->{lower_idx}, +{needed:.2f})"
                for col, (upper_idx, lower_idx, needed) in conflicts_all
            )
            debug_print(f"Conflictos de solapamiento detectados: {formatted}")
            adjusted |= _adjust_principal_for_conflicts(graph, conflicts_all, subgroup_anchor)
        if adjusted:
            debug_print("Principal ajustada por conflictos, re-iterando...")
            continue
        break

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
            y=cy,
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

    # Mark align edges only for cross-column mask/A connections
    for e in graph.edges:
        src = graph.nodes.get(e.src)
        dst = graph.nodes.get(e.dst)
        if not src or not dst:
            continue
        if src.column == dst.column:
            continue
        if e.kind in ("mask", "A"):
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
        new_y = node.y - ref.screenHeight() / 2.0
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
