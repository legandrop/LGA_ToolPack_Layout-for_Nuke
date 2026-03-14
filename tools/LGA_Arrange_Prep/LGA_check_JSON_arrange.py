#!/usr/bin/env python3
"""
Check basic arrange rules on a graph JSON:
1) Y alignment for connected nodes in different columns (centered, using heights).
2) No overlap within the same column (using node heights).
Outputs a Spanish report .txt next to the JSON.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Dict, List, Tuple


def load_graph(path: Path) -> Tuple[Dict[str, dict], List[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["name"]: n for n in data.get("nodes", [])}
    edges = data.get("edges", [])
    return nodes, edges


def _center_y(node: dict) -> float:
    return float(node.get("y", 0.0))


def check_alignment(nodes: Dict[str, dict], edges: List[dict], tol: float) -> List[str]:
    errors: List[str] = []
    for e in edges:
        src = nodes.get(e.get("src"))
        dst = nodes.get(e.get("dst"))
        if not src or not dst:
            continue
        if src.get("column") == dst.get("column"):
            continue
        y1 = _center_y(src)
        y2 = _center_y(dst)
        h1 = float(src.get("height", 0.0))
        h2 = float(dst.get("height", 0.0))
        # Consider centered alignment using node sizes:
        # aligned if centers are within half the combined height (overlapping vertical spans).
        max_delta = (h1 + h2) / 2.0 + tol
        if abs(y1 - y2) > max_delta:
            errors.append(
                f'ALIGN_Y: {e.get("src")} ({y1}) -> {e.get("dst")} ({y2}), '
                f'columns {src.get("column")}->{dst.get("column")}, '
                f'h=({h1},{h2})'
            )
    return errors


def check_overlaps(nodes: Dict[str, dict], tol: float) -> List[str]:
    errors: List[str] = []
    by_col: Dict[str, List[dict]] = {}
    for n in nodes.values():
        by_col.setdefault(n.get("column", "C0"), []).append(n)

    for col, col_nodes in by_col.items():
        col_nodes = sorted(col_nodes, key=lambda n: float(n.get("y", 0.0)), reverse=True)
        for i in range(len(col_nodes)):
            n1 = col_nodes[i]
            y1 = _center_y(n1)
            h1 = float(n1.get("height", 0.0))
            for j in range(i + 1, len(col_nodes)):
                n2 = col_nodes[j]
                y2 = _center_y(n2)
                h2 = float(n2.get("height", 0.0))
                min_sep = (h1 + h2) / 2.0 - tol
                if abs(y1 - y2) < min_sep:
                    errors.append(
                        f'OVERLAP: {n1.get("name")} ({y1}, h={h1}) '
                        f'vs {n2.get("name")} ({y2}, h={h2}) in {col}'
                    )
    return errors


def _write_report(path: Path, errors: List[str]) -> Path:
    out_path = path.with_suffix(".arrange_check.txt")
    if errors:
        lines = [f"FALLA: {len(errors)} problemas detectados"]
        lines += [f"- {e}" for e in errors]
    else:
        lines = ["OK: no se detectaron problemas"]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Check JSON arrange rules.")
    ap.add_argument("--", dest="json_path", help="Graph JSON file path")
    ap.add_argument("json_path_pos", nargs="?", help="Graph JSON file path (positional)")
    ap.add_argument("--tol-y", type=float, default=1e-3, help="Y alignment tolerance")
    ap.add_argument("--tol-overlap", type=float, default=1e-6, help="Overlap tolerance")
    args = ap.parse_args()

    json_path = args.json_path or args.json_path_pos
    if not json_path:
        raise SystemExit("Usage: python LGA_check_JSON_arrange.py -- <graph.json>")

    path = Path(json_path)
    nodes, edges = load_graph(path)

    errors: List[str] = []
    errors.extend(check_alignment(nodes, edges, tol=args.tol_y))
    errors.extend(check_overlaps(nodes, tol=args.tol_overlap))

    report_path = _write_report(path, errors)
    if errors:
        print(f"FALLA: {len(errors)} problemas (ver {report_path})")
        raise SystemExit(1)

    print(f"OK: sin problemas (ver {report_path})")


if __name__ == "__main__":
    main()
