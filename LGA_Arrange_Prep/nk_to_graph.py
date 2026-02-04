"""
Convert .nk file to layout_core.Graph JSON.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from typing import Dict, List

from layout_core import Graph, Node, Edge
from nk_parser import parse_nk, NkNode
from graph_io import save_graph_json


CLASS_BASE_HEIGHTS = {
    "Merge": 0.8,
    "Merge2": 0.8,
    "Blur": 0.6,
    "Roto": 0.6,
    "Copy": 0.6,
}


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

    for nk_node in nk_graph.nodes:
        x = nk_node.x * scale
        y = -nk_node.y * scale  # invert Y so up is positive
        height = _estimate_height(nk_node)
        node = Node(
            name=nk_node.name,
            klass=nk_node.klass,
            column="C0",
            order=0,
            x=x,
            y=y,
            height=height,
        )
        graph.add_node(node)

    for edge in nk_graph.edges:
        graph.add_edge(Edge(edge.src, edge.dst, kind=edge.kind, align=edge.align))

    _group_columns(list(graph.nodes.values()), tolerance_x=tolerance_x)

    if return_meta:
        meta = {
            "source_nk": nk_path,
            "root_name": nk_graph.root_name,
            "scale": scale,
            "tolerance_x": tolerance_x,
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
