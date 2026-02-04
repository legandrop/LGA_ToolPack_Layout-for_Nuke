"""
Convert graph JSON to Graphviz DOT.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from graph_io import load_graph_json
from graphviz_export import to_dot


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python graph_to_dot.py <input.json> <output.dot>")
        raise SystemExit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    graph = load_graph_json(in_path)
    dot = to_dot(graph, title=Path(in_path).stem)
    Path(out_path).write_text(dot, encoding="utf-8")


if __name__ == "__main__":
    main()
