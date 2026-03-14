"""
Convert graph JSON to Graphviz DOT.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from graph_io import load_graph_json
import re
from graphviz_export import to_dot


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python graph_to_dot.py <input.json> <output.dot>")
        raise SystemExit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    graph = load_graph_json(in_path)
    raw_title = Path(in_path).stem
    safe_title = re.sub(r"[^A-Za-z0-9_]", "_", raw_title) or "Graph"
    dot = to_dot(graph, title=safe_title)
    Path(out_path).write_text(dot, encoding="utf-8")


if __name__ == "__main__":
    main()
