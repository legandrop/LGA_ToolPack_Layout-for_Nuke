"""
Graphviz DOT export helpers.
"""

from typing import List
from layout_core import Graph


def _node_style(name: str) -> str:
    if name.startswith("Grade"):
        return 'shape=box, style="rounded,filled", fillcolor="#cbd6ee"'
    if name.startswith("Roto"):
        return 'shape=box, style="rounded,filled", fillcolor="#8fd18f"'
    if name.startswith("Blur"):
        return 'shape=box, style="rounded,filled", fillcolor="#f4a460"'
    if name.startswith("Copy"):
        return 'shape=box, style="rounded,filled", fillcolor="#d95da8"'
    if name.startswith("Dot"):
        return 'shape=circle, style=filled, fillcolor="#bdbdbd", width=0.2, height=0.2, label=""'
    return 'shape=box, style="rounded,filled", fillcolor="#dddddd"'


def to_dot(graph: Graph, title: str = "G") -> str:
    lines: List[str] = []
    lines.append(f'digraph {title} {{')
    lines.append('  graph [layout=neato, splines=ortho, overlap=false];')
    lines.append('  node [fontname="Helvetica", fontsize=10, fixedsize=true, width=1.6, height=0.5];')

    for node in graph.nodes.values():
        style = _node_style(node.name)
        attrs = [style, f'pos="{node.x},{node.y}!"']
        # Only set per-node height for non-dot nodes
        if not node.name.startswith("Dot"):
            attrs.append(f'height="{node.height}"')
            attrs.append('width="1.6"')
        lines.append(f'  {node.name} [{", ".join(attrs)} ];')

    for edge in graph.edges:
        if edge.kind == "mask":
            lines.append(f'  {edge.src} -> {edge.dst} [label="mask", fontsize=9];')
        else:
            lines.append(f'  {edge.src} -> {edge.dst};')

    lines.append('}')
    return "\n".join(lines)
