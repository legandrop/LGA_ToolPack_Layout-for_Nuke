"""
Apply layout_core to a graph JSON and export DOT.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from graph_io import load_graph_json
import re
from graphviz_export import to_dot
from layout_core import layout


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python LGA_arrangeJSON.py <input.json> <output.dot> [min_gap]")
        raise SystemExit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]
    min_gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2

    graph = load_graph_json(in_path)
    layout(graph, min_gap=min_gap)
    raw_title = Path(in_path).stem + "_after"
    safe_title = re.sub(r"[^A-Za-z0-9_]", "_", raw_title) or "Graph"
    dot = to_dot(graph, title=safe_title)
    Path(out_path).write_text(dot, encoding="utf-8")


if __name__ == "__main__":
    main()
