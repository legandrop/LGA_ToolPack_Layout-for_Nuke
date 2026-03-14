"""
Convert .nk directly to Graphviz DOT (via internal graph conversion).
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from nk_to_graph import nk_to_graph
from graphviz_export import to_dot


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python nk_to_dot.py <input.nk> <output.dot> [scale] [tolerance_x]")
        raise SystemExit(1)

    nk_path = sys.argv[1]
    out_path = sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    tolerance_x = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5

    graph = nk_to_graph(nk_path, scale=scale, tolerance_x=tolerance_x)
    dot = to_dot(graph, title=Path(nk_path).stem)
    Path(out_path).write_text(dot, encoding="utf-8")


if __name__ == "__main__":
    main()
