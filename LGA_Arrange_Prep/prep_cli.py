"""
Prep pipeline: .nk -> graph.json -> graph.dot, plus direct .nk -> dot.
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from nk_to_graph import nk_to_graph
from graph_io import save_graph_json
from graphviz_export import to_dot


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python prep_cli.py <input.nk> [out_dir]")
        raise SystemExit(1)

    nk_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    base = nk_path.stem
    graph_json = out_dir / f"{base}.graph.json"
    dot_from_nk = out_dir / f"{base}.from_nk.dot"
    dot_from_graph = out_dir / f"{base}.from_graph.dot"

    graph, meta = nk_to_graph(str(nk_path), return_meta=True)
    save_graph_json(graph, str(graph_json), meta=meta)

    # Direct .nk -> dot
    dot_direct = to_dot(graph, title=base)
    write_text(dot_from_nk, dot_direct)

    # Graph JSON -> dot
    # Re-load to validate roundtrip
    from graph_io import load_graph_json

    graph2 = load_graph_json(str(graph_json))
    dot_round = to_dot(graph2, title=base)
    write_text(dot_from_graph, dot_round)

    print(f"Wrote: {graph_json}")
    print(f"Wrote: {dot_from_nk}")
    print(f"Wrote: {dot_from_graph}")


if __name__ == "__main__":
    main()
