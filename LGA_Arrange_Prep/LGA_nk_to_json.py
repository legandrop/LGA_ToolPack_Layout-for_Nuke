"""
Convert .nk file to layout_core.Graph JSON.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from typing import Dict, List

from layout_core import Graph, Node, Edge
from nk_parser import parse_nk, NkNode, _parse_inputs_spec
from graph_io import save_graph_json


CLASS_BASE_HEIGHTS = {
    "Merge": 0.8,
    "Merge2": 0.8,
    "Blur": 0.6,
    "Roto": 0.6,
    "Copy": 0.6,
}

# Approximate Nuke UI sizes (pixels) for center conversion
CLASS_WIDTH_PX = {
    "Dot": 12,
}
CLASS_HEIGHT_PX = {
    "Dot": 12,
    "Blur": 24,
    "Roto": 24,
    "Copy": 24,
    "Merge": 28,
    "Merge2": 28,
}
DEFAULT_WIDTH_PX = 80
DEFAULT_HEIGHT_PX = 20


def _estimate_height(node: NkNode) -> float:
    if node.klass.startswith("Dot"):
        size = node.knobs.get("size")
        if size is not None:
            try:
                val = float(size)
                return max(0.1, 0.02 * val)
            except ValueError:
                pass
        return 0.2

    base = CLASS_BASE_HEIGHTS.get(node.klass, 0.5)
    label = node.label.replace("\\n", "\n") if node.label else ""
    lines = max(1, label.count("\n") + 1) if label else 1
    if lines > 1:
        base += 0.15 * (lines - 1)
    return base


def _group_columns(nodes: List[Node], tolerance_x: float) -> Dict[str, float]:
    groups: List[List[Node]] = []
    centers: List[float] = []

    for node in sorted(nodes, key=lambda n: n.x):
        placed = False
        for i, cx in enumerate(centers):
            if abs(node.x - cx) <= tolerance_x:
                groups[i].append(node)
                centers[i] = sum(n.x for n in groups[i]) / len(groups[i])
                placed = True
                break
        if not placed:
            groups.append([node])
            centers.append(node.x)

    # Assign column names ordered left to right
    ordered = sorted(zip(centers, groups), key=lambda t: t[0])
    for idx, (_cx, grp) in enumerate(ordered):
        col = f"C{idx}"
        for n in grp:
            n.column = col

        # Order top-to-bottom (higher y first)
        grp.sort(key=lambda n: n.y, reverse=True)
        for order_idx, n in enumerate(grp):
            n.order = order_idx

    return {f"C{idx}": cx for idx, (cx, _grp) in enumerate(ordered)}


def _normalize_merge_inputs_by_position(graph: Graph, nk_nodes: Dict[str, NkNode]) -> None:
    """
    Reclassify/complete Merge inputs by spatial position.
    Rules:
      - same-column input => B
      - left-column input => A
      - right-column input (if mask expected) => mask
    If a required input is missing, infer from nearest candidate by Y.
    """
    cols = graph.columns()
    # Column X order
    col_x = {col: sum(n.x for n in nodes) / len(nodes) for col, nodes in cols.items()}
    col_order = {col: idx for idx, (col, _x) in enumerate(sorted(col_x.items(), key=lambda kv: kv[1]))}

    # Build incoming edges map (from original edges)
    incoming: Dict[str, List[Edge]] = {}
    for e in graph.edges:
        incoming.setdefault(e.dst, []).append(e)

    def resolve_dot_source(name: str) -> str:
        cur = name
        visited = set()
        while cur in graph.nodes and graph.nodes[cur].klass.startswith("Dot"):
            if cur in visited:
                break
            visited.add(cur)
            inc = incoming.get(cur, [])
            # follow first non-mask edge if unique
            candidates = [e.src for e in inc if e.kind != "mask"]
            if len(candidates) != 1:
                break
            cur = candidates[0]
        return cur

    def nearest_in_column(col: str, target_y: float) -> Node:
        nodes = cols.get(col, [])
        return min(nodes, key=lambda n: abs(n.y - target_y)) if nodes else None

    merge_names = {n.name for n in graph.nodes.values() if n.klass.startswith("Merge")}
    new_edges: List[Edge] = [e for e in graph.edges if e.dst not in merge_names]

    for node in graph.nodes.values():
        if not node.klass.startswith("Merge"):
            continue
        nk_node = nk_nodes.get(node.name)
        if not nk_node:
            continue
        mandatory, mask = _parse_inputs_spec(nk_node.inputs_spec, nk_node.klass)
        inc = incoming.get(node.name, [])

        # Candidate pools
        same_col = [n for n in graph.nodes.values() if n.column == node.column and n.name != node.name]
        left_candidates = [n for n in graph.nodes.values() if col_order.get(n.column, 0) < col_order.get(node.column, 0)]
        right_candidates = [n for n in graph.nodes.values() if col_order.get(n.column, 0) > col_order.get(node.column, 0)]

        # Prefer candidates above (higher y in graph coords)
        same_above = [n for n in same_col if n.y >= node.y]
        left_above = [n for n in left_candidates if n.y >= node.y]

        # Select A (left, close in Y)
        a_thresh = max(1.5, node.height * 3.0)
        a_candidates = left_above if left_above else left_candidates
        a = None
        if a_candidates:
            cand = min(a_candidates, key=lambda n: abs(n.y - node.y))
            if abs(cand.y - node.y) <= a_thresh:
                a = cand

        # Select B (same column)
        b_candidates = same_above if same_above else same_col
        b = None
        if b_candidates:
            if a is None:
                non_merge = [n for n in b_candidates if not n.klass.startswith("Merge")]
                pool = non_merge if non_merge else b_candidates
            else:
                pool = b_candidates
            b = min(pool, key=lambda n: abs(n.y - node.y))

        # Select mask (right, balance Y + X; prefer nearby dots)
        m = None
        if mask > 0 and right_candidates:
            def mask_score(n: Node) -> float:
                y_dist = abs(n.y - node.y)
                x_dist = abs(n.x - node.x)
                dot_bonus = 0.0 if n.klass.startswith("Dot") else 0.2
                return y_dist + 0.5 * x_dist + dot_bonus

            m = min(right_candidates, key=mask_score)
            if m and m.klass.startswith("Dot"):
                dot_thresh = max(0.6, node.height * 1.5)
                if abs(m.y - node.y) > dot_thresh:
                    non_dots = [n for n in right_candidates if not n.klass.startswith("Dot")]
                    if non_dots:
                        m = min(non_dots, key=mask_score)
                    else:
                        src_name = resolve_dot_source(m.name)
                        if src_name in graph.nodes:
                            m = graph.nodes[src_name]

        # Add inferred edges
        if b:
            new_edges.append(Edge(b.name, node.name, kind="B", align=False))
        if a:
            new_edges.append(Edge(a.name, node.name, kind="A", align=True))
        if m:
            new_edges.append(Edge(m.name, node.name, kind="mask", align=True))

    graph.edges = new_edges


def nk_to_graph(
    nk_path: str,
    scale: float = 0.05,
    tolerance_x: float = 2.5,
    return_meta: bool = False,
    infer_merge_inputs: bool = False,
):
    nk_graph = parse_nk(nk_path)
    graph = Graph()

    name_to_inputs = {}
    nk_nodes_by_name = {n.name: n for n in nk_graph.nodes}
    for nk_node in nk_graph.nodes:
        width_px = CLASS_WIDTH_PX.get(nk_node.klass, DEFAULT_WIDTH_PX)
        height_px = CLASS_HEIGHT_PX.get(nk_node.klass, DEFAULT_HEIGHT_PX)
        center_x = (nk_node.x + width_px / 2) * scale
        center_y = -(nk_node.y + height_px / 2) * scale  # invert Y so up is positive
        height = _estimate_height(nk_node)
        node = Node(
            name=nk_node.name,
            klass=nk_node.klass,
            column="C0",
            order=0,
            x=center_x,
            y=center_y,
            height=height,
        )
        graph.add_node(node)
        name_to_inputs[nk_node.name] = nk_node.inputs_spec

    if nk_graph.explicit_stack_ops:
        for edge in nk_graph.edges:
            graph.add_edge(Edge(edge.src, edge.dst, kind=edge.kind, align=edge.align))

    _group_columns(list(graph.nodes.values()), tolerance_x=tolerance_x)

    # Normalize/infer merge inputs only if explicitly requested
    if infer_merge_inputs:
        _normalize_merge_inputs_by_position(graph, nk_nodes_by_name)

    if not nk_graph.explicit_stack_ops:
        # Rebuild edges from spatial + inputs heuristics
        graph.edges = []

        inputs_map = {n.name: n.inputs_spec for n in nk_graph.nodes}

        # Flow edges per column (respect inputs==0 to break chains)
        for col, nodes in graph.columns().items():
            ordered = sorted(nodes, key=lambda n: n.y, reverse=True)
            prev = None
            for node in ordered:
                inputs_spec = inputs_map.get(node.name)
                mandatory, _mask = _parse_inputs_spec(inputs_spec, node.klass)
                if mandatory == 0:
                    prev = node
                    continue
                if prev is not None:
                    graph.add_edge(Edge(prev.name, node.name, kind="flow", align=False))
                prev = node

        # Helper: column subgroups (split where inputs==0)
        def column_subgroups(nodes):
            groups = []
            current = []
            for n in nodes:
                inputs_spec = inputs_map.get(n.name)
                mandatory, _mask = _parse_inputs_spec(inputs_spec, n.klass)
                if mandatory == 0:
                    if current:
                        groups.append(current)
                    current = [n]
                else:
                    current.append(n)
            if current:
                groups.append(current)
            return groups

        # Precompute columns by X
        cols_sorted = sorted(graph.columns().items(), key=lambda kv: kv[1][0].x)
        col_names = [c for c, _ in cols_sorted]
        col_x = {c: sum(n.x for n in graph.columns()[c]) / len(graph.columns()[c]) for c in col_names}

        # Mask inputs (non-stack heuristics for non-merge nodes too)
        for nk_node in nk_graph.nodes:
            inputs_spec = nk_node.inputs_spec
            mandatory, mask = _parse_inputs_spec(inputs_spec, nk_node.klass)
            if mask <= 0:
                continue
            # If this node is already used as a mask source, skip adding a mask input
            if any(e.kind == "mask" and e.src == nk_node.name for e in graph.edges):
                continue
            # Check existing mask edges
            has_mask = any(e.dst == nk_node.name and e.kind == "mask" for e in graph.edges)
            if has_mask:
                continue
            target = graph.nodes.get(nk_node.name)
            if not target:
                continue
            def has_any_edge(a: str, b: str) -> bool:
                for e in graph.edges:
                    if (e.src == a and e.dst == b) or (e.src == b and e.dst == a):
                        return True
                return False
            best = None
            best_score = None
            for candidate in graph.nodes.values():
                if candidate.name == target.name:
                    continue
                if has_any_edge(candidate.name, target.name):
                    continue
                if candidate.column == target.column:
                    continue
                y_dist = abs(candidate.y - target.y)
                x_dist = abs(candidate.x - target.x)
                penalty = 0.0 if candidate.klass.startswith("Dot") else 1.0
                score = y_dist + 0.1 * x_dist + penalty
                if best_score is None or score < best_score:
                    best = candidate
                    best_score = score
            if best is not None:
                graph.add_edge(Edge(best.name, target.name, kind="mask", align=True))

        # Merge inputs from spatial rules
        _normalize_merge_inputs_by_position(graph, nk_nodes_by_name)

    if return_meta:
        meta = {
            "source_nk": nk_path,
            "root_name": nk_graph.root_name,
            "scale": scale,
            "tolerance_x": tolerance_x,
            "centered_positions": True,
            "used_stack": nk_graph.explicit_stack_ops,
        }
        return graph, meta
    return graph


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python nk_to_graph.py <input.nk> <output.json> [scale] [tolerance_x]")
        raise SystemExit(1)

    nk_path = sys.argv[1]
    out_path = sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    tolerance_x = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5

    graph, meta = nk_to_graph(nk_path, scale=scale, tolerance_x=tolerance_x, return_meta=True)
    save_graph_json(graph, out_path, meta=meta)


if __name__ == "__main__":
    main()
