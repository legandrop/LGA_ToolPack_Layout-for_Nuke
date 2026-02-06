"""
Temporal: convierte .nk a JSON (via nk_to_graph) y analiza inputs de merges desde JSON.
Uso:
  python tmp_merge_inputs_from_json.py testGraph_v03_After.nk
  python tmp_merge_inputs_from_json.py LGA_Arrange_Prep/out/testGraph_v03_After.graph.json
"""

from pathlib import Path
import sys
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parent))

from LGA_nk_to_json import nk_to_graph
from graph_io import save_graph_json, load_graph_json


TARGET_MERGES = {"Merge11", "Merge10", "Merge18"}


def _edges_by_dst(graph) -> Dict[str, List[dict]]:
    by_dst: Dict[str, List[dict]] = {}
    for e in graph.edges:
        by_dst.setdefault(e.dst, []).append({"src": e.src, "kind": e.kind})
    return by_dst


def _summarize_inputs(edges: List[dict]) -> Dict[str, List[str]]:
    summary = {"A": [], "B": [], "mask": [], "flow": []}
    for e in edges:
        kind = e["kind"]
        if kind not in summary:
            summary[kind] = []
        summary[kind].append(e["src"])
    return summary


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python tmp_merge_inputs_from_json.py <archivo.nk|archivo.json>")
        raise SystemExit(1)

    in_path = Path(sys.argv[1])
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    if in_path.suffix.lower() == ".nk":
        graph, meta = nk_to_graph(str(in_path), return_meta=True, infer_merge_inputs=False)
        json_path = out_dir / f"{in_path.stem}.graph.json"
        save_graph_json(graph, str(json_path), meta=meta)
        graph = load_graph_json(str(json_path))
    else:
        graph = load_graph_json(str(in_path))

    edges_by_dst = _edges_by_dst(graph)

    for name in sorted(TARGET_MERGES):
        node = graph.nodes.get(name)
        if not node:
            print(f"{name}: NO ENCONTRADO")
            continue
        summary = _summarize_inputs(edges_by_dst.get(name, []))
        print(f"{name}:")
        print(f"  A: {summary.get('A') or 'None'}")
        print(f"  B: {summary.get('B') or 'None'}")
        print(f"  mask: {summary.get('mask') or 'None'}")
        # flow is for non-merge types or unknown cases
        if summary.get('flow'):
            print(f"  flow: {summary.get('flow')}")


if __name__ == "__main__":
    main()
