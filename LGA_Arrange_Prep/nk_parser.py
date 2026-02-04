"""
Minimal .nk parser for extracting nodes, positions, and connections.
Focus: DAG info only (name, class, xpos/ypos, inputs).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


@dataclass
class NkNode:
    name: str
    klass: str
    x: float
    y: float
    inputs_spec: Optional[str] = None
    label: str = ""
    knobs: Dict[str, str] = field(default_factory=dict)


@dataclass
class NkEdge:
    src: str
    dst: str
    input_index: int
    kind: str
    align: bool = False


@dataclass
class NkGraph:
    nodes: List[NkNode] = field(default_factory=list)
    edges: List[NkEdge] = field(default_factory=list)
    root_name: Optional[str] = None


_NODE_START_RE = re.compile(r"^([A-Za-z0-9_]+)\s*\{\s*$")
_SET_STACK_RE = re.compile(r"^set\s+([A-Za-z0-9_]+)\s+\[stack\s+0\]")
_PUSH_RE = re.compile(r"^push\s+(.+)$")


DEFAULT_INPUTS: Dict[str, int] = {
    "Root": 0,
    "Roto": 0,
    "Dot": 1,
    "Grade": 1,
    "Blur": 1,
    "Merge": 2,
    "Merge2": 2,
    "Copy": 2,
}


def _parse_inputs_spec(inputs_spec: Optional[str], klass: str) -> Tuple[int, int]:
    if inputs_spec is None:
        return DEFAULT_INPUTS.get(klass, 1), 0
    spec = inputs_spec.strip()
    if "+" in spec:
        parts = spec.split("+", 1)
        try:
            mandatory = int(parts[0])
        except ValueError:
            mandatory = DEFAULT_INPUTS.get(klass, 1)
        try:
            mask = int(parts[1])
        except ValueError:
            mask = 0
        return mandatory, mask
    try:
        return int(spec), 0
    except ValueError:
        return DEFAULT_INPUTS.get(klass, 1), 0


def _classify_input(klass: str, input_index: int, mandatory: int, mask: int) -> Tuple[str, bool]:
    total = mandatory + mask
    if mask and input_index == total - 1:
        return "mask", True
    if klass.startswith("Merge"):
        if input_index == 0:
            return "A", True
        if input_index == 1:
            return "B", False
    return "flow", False


def _estimate_label_lines(label: str) -> int:
    if not label:
        return 1
    # Normalize escaped newlines
    label = label.replace("\\n", "\n")
    return max(1, label.count("\n") + 1)


def parse_nk(path: str) -> NkGraph:
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    graph = NkGraph()
    stack: List[Optional[str]] = []
    variables: Dict[str, Optional[str]] = {}
    explicit_push = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        m_set = _SET_STACK_RE.match(stripped)
        if m_set:
            var = m_set.group(1)
            variables[var] = stack[-1] if stack else None
            i += 1
            continue

        m_push = _PUSH_RE.match(stripped)
        if m_push:
            token = m_push.group(1).strip()
            if token.startswith("$"):
                val = variables.get(token[1:], None)
            elif token == "0":
                val = None
            else:
                val = token
            stack.append(val)
            explicit_push = True
            i += 1
            continue

        if stripped == "pop":
            if stack:
                stack.pop()
            i += 1
            continue

        m_node = _NODE_START_RE.match(stripped)
        if not m_node:
            i += 1
            continue

        klass = m_node.group(1)
        block_lines = []
        depth = 0
        while i < len(lines):
            l = lines[i]
            block_lines.append(l)
            depth += l.count("{") - l.count("}")
            if depth == 0:
                break
            i += 1

        # Parse knobs
        name = None
        xpos = None
        ypos = None
        inputs_spec = None
        label = ""
        knobs: Dict[str, str] = {}
        for raw in block_lines[1:]:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            m = re.match(r"^([A-Za-z0-9_]+)\s+(.*)$", s)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip()
            knobs[key] = val
            if key == "name":
                name = val
            elif key == "xpos":
                try:
                    xpos = float(val)
                except ValueError:
                    pass
            elif key == "ypos":
                try:
                    ypos = float(val)
                except ValueError:
                    pass
            elif key == "inputs":
                inputs_spec = val
            elif key == "label":
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                label = val

        if klass == "Root":
            if name:
                graph.root_name = name
            i += 1
            continue

        if name is None:
            name = f"{klass}{len(graph.nodes) + 1}"
        if xpos is None:
            xpos = 0.0
        if ypos is None:
            ypos = 0.0

        node = NkNode(
            name=name,
            klass=klass,
            x=xpos,
            y=ypos,
            inputs_spec=inputs_spec,
            label=label,
            knobs=knobs,
        )

        # Build edges based on stack and inputs
        mandatory, mask = _parse_inputs_spec(inputs_spec, klass)
        if mask and not explicit_push:
            mask = 0
        total_inputs = mandatory + mask
        if len(stack) >= total_inputs:
            consume = total_inputs
        else:
            consume = min(len(stack), mandatory)
        inputs: List[Optional[str]] = []
        for _ in range(consume):
            inputs.append(stack.pop())
        inputs.reverse()

        for idx, src in enumerate(inputs):
            if src is None:
                continue
            kind, align = _classify_input(klass, idx, mandatory, mask)
            graph.edges.append(NkEdge(src=src, dst=node.name, input_index=idx, kind=kind, align=align))

        stack.append(node.name)
        explicit_push = False
        graph.nodes.append(node)
        i += 1

    return graph
