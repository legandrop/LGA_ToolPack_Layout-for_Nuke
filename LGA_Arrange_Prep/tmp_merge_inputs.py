"""
Temporal: analiza inputs de merges especificos en un .nk.
Uso:
  python tmp_merge_inputs.py testGraph_v03_After.nk
"""

from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

sys.path.append(str(Path(__file__).resolve().parent))

from nk_parser import parse_nk, _parse_inputs_spec


TARGET_MERGES = {"Merge11", "Merge10", "Merge18"}


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python tmp_merge_inputs.py <archivo.nk>")
        raise SystemExit(1)
    nk_path = sys.argv[1]
    graph = parse_nk(nk_path)

    nodes = {n.name: n for n in graph.nodes}
    edges_by_dst: Dict[str, List[Tuple[int, str, str]]] = {}
    for e in graph.edges:
        edges_by_dst.setdefault(e.dst, []).append((e.input_index, e.src, e.kind))

    for name in sorted(TARGET_MERGES):
        node = nodes.get(name)
        if not node:
            print(f"{name}: NO ENCONTRADO")
            continue
        mandatory, mask = _parse_inputs_spec(node.inputs_spec, node.klass)
        total = mandatory + mask
        inputs: List[Optional[Tuple[str, str]]] = [None] * total
        for idx, src, kind in edges_by_dst.get(name, []):
            if 0 <= idx < total:
                inputs[idx] = (src, kind)
        print(f"{name} (inputs {mandatory}+{mask}):")
        for i in range(total):
            if inputs[i] is None:
                print(f"  input {i}: None")
            else:
                src, kind = inputs[i]
                print(f"  input {i}: {src} ({kind})")


if __name__ == "__main__":
    main()
