"""
Graph JSON IO helpers for layout_core.Graph.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional
import json

from layout_core import Graph, Node, Edge


def graph_to_dict(graph: Graph, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {"nodes": [], "edges": [], "meta": meta or {}}
    for node in graph.nodes.values():
        data["nodes"].append(
            {
                "name": node.name,
                "klass": node.klass,
                "column": node.column,
                "order": node.order,
                "x": node.x,
                "y": node.y,
                "height": node.height,
            }
        )
    for edge in graph.edges:
        data["edges"].append(asdict(edge))
    return data


def graph_from_dict(data: Dict[str, Any]) -> Graph:
    graph = Graph()
    for n in data.get("nodes", []):
        node = Node(
            name=n["name"],
            klass=n.get("klass", ""),
            column=n.get("column", "C0"),
            order=int(n.get("order", 0)),
            x=float(n.get("x", 0.0)),
            y=float(n.get("y", 0.0)),
            height=float(n.get("height", 0.5)),
        )
        graph.add_node(node)
    for e in data.get("edges", []):
        graph.add_edge(
            Edge(
                src=e["src"],
                dst=e["dst"],
                kind=e.get("kind", "flow"),
                align=bool(e.get("align", False)),
            )
        )
    return graph


def save_graph_json(graph: Graph, path: str, meta: Optional[Dict[str, Any]] = None) -> None:
    data = graph_to_dict(graph, meta=meta)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_graph_json(path: str) -> Graph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return graph_from_dict(data)
