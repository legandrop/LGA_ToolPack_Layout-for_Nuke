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


def nk_to_graph(
    nk_path: str,
    scale: float = 0.05,
    tolerance_x: float = 2.5,
    return_meta: bool = False,
):
    nk_graph = parse_nk(nk_path)
    graph = Graph()

    name_to_inputs = {}
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

    for edge in nk_graph.edges:
        graph.add_edge(Edge(edge.src, edge.dst, kind=edge.kind, align=edge.align))

    _group_columns(list(graph.nodes.values()), tolerance_x=tolerance_x)

    # Heuristic: if a node has mask inputs but no explicit mask edge,
    # connect the closest node (by Y) from a different column.
    for nk_node in nk_graph.nodes:
        inputs_spec = nk_node.inputs_spec
        if not inputs_spec or "+" not in inputs_spec:
            continue
        mandatory, mask = _parse_inputs_spec(inputs_spec, nk_node.klass)
        if mask <= 0:
            continue
        # Check existing mask edges
        has_mask = any(e.dst == nk_node.name and e.kind == "mask" for e in graph.edges)
        if has_mask:
            continue

        target = graph.nodes.get(nk_node.name)
        if not target:
            continue

        best = None
        best_score = None
        for candidate in graph.nodes.values():
            if candidate.name == target.name:
                continue
            # Must be in a different column (x distance beyond tolerance)
            if abs(candidate.x - target.x) <= tolerance_x:
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

    if return_meta:
        meta = {
            "source_nk": nk_path,
            "root_name": nk_graph.root_name,
            "scale": scale,
            "tolerance_x": tolerance_x,
            "centered_positions": True,
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
