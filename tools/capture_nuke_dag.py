"""
______________________________________________________________

  capture_nuke_dag v1.02 | 2026 | Lega

  Captura el DAG actual de Nuke via MCP broker y genera:
  - JSON estructurado (nodos + conexiones)
  - PNG visual aproximado al Node Graph real
  - SVG opcional
______________________________________________________________

ChangeLog:
- v1.00 (2026-07-04): version inicial con captura MCP, JSON y render PNG/SVG.
- v1.01 (2026-07-04): corrige render de conexiones, quita inputs desconectados y captura solo DAG top-level.
- v1.02 (2026-07-05): mejora fidelidad visual (colores reales, flechas de flujo y dots).
"""

from __future__ import annotations

import argparse
import json
import math
import queue
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow no esta instalado. Instala con: pip install pillow"
    ) from exc


DEFAULT_BROKER_COMMAND = [
    "powershell",
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    r"C:\Portable\LGA_NukeMCP\scripts\mcp\start_kleer_broker.ps1",
]

DEFAULT_PROTOCOL_VERSION = "2025-03-26"
DEFAULT_PORT_HOST = "127.0.0.1"
DEFAULT_PORT = 54321
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_JSON_PATH = DEFAULT_OUTPUT_DIR / "dag_snapshot.json"
DEFAULT_PNG_PATH = DEFAULT_OUTPUT_DIR / "dag_snapshot.png"
DEFAULT_SVG_PATH = DEFAULT_OUTPUT_DIR / "dag_snapshot.svg"

NODE_BASE_COLORS = {
    "Blur": (206, 144, 88),
    "Grade": (114, 164, 244),
    "Roto": (129, 212, 123),
    "RotoPaint": (129, 212, 123),
    "RotoPaint2": (129, 212, 123),
    "Dot": (238, 224, 73),
    "Viewer": (57, 57, 57),
    "BackdropNode": (72, 72, 72),
    "Merge": (123, 178, 248),
    "Merge2": (123, 178, 248),
    "Transform": (140, 180, 235),
    "Read": (108, 160, 108),
    "Write": (174, 98, 98),
}

DEFAULT_NODE_COLOR = (125, 125, 125)
DOT_NODE_COLOR = (220, 220, 220)
GRAPH_BG_COLOR = (52, 53, 57)
EDGE_FLOW_COLOR = (24, 24, 24)
EDGE_MASK_COLOR = (239, 219, 64)
NODE_BORDER_COLOR = (14, 14, 14)

CAPTURE_DAG_CODE = r"""
import nuke

def _safe_knob_value(node, knob_name, default=None):
    knob = node.knob(knob_name)
    if knob is None:
        return default
    try:
        return knob.value()
    except Exception:
        return default

def _safe_input_label(node, index):
    for attr in ("inputLabel", "input_label"):
        fn = getattr(node, attr, None)
        if not callable(fn):
            continue
        try:
            value = fn(index)
        except Exception:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""

def _safe_default_node_color(node_class, _cache={}):
    if node_class in _cache:
        return _cache[node_class]
    try:
        value = int(nuke.defaultNodeColor(node_class))
    except Exception:
        value = 0
    _cache[node_class] = value
    return value

nodes = []

for node in nuke.allNodes(recurseGroups=False):
    if node.Class() == "Root":
        continue

    inputs = []
    for i in range(node.inputs()):
        src = node.input(i)
        inputs.append(
            {
                "input_index": int(i),
                "source_node": src.name() if src is not None else None,
                "input_label": _safe_input_label(node, i),
            }
        )

    tile_color = _safe_knob_value(node, "tile_color", 0)
    label_raw = _safe_knob_value(node, "label", "") or ""

    item = {
        "name": node.name(),
        "class": node.Class(),
        "xpos": int(node.xpos()),
        "ypos": int(node.ypos()),
        "screenWidth": int(node.screenWidth()) if hasattr(node, "screenWidth") else None,
        "screenHeight": int(node.screenHeight()) if hasattr(node, "screenHeight") else None,
        "tile_color": int(tile_color or 0),
        "default_color": int(_safe_default_node_color(node.Class()) or 0),
        "selected": bool(_safe_knob_value(node, "selected", False)),
        "label": str(label_raw),
        "label_eval": str(label_raw),
        "channels": _safe_knob_value(node, "channels", ""),
        "size": _safe_knob_value(node, "size", None),
        "output": _safe_knob_value(node, "output", ""),
        "inputs": inputs,
    }
    nodes.append(item)

nodes.sort(key=lambda n: (n["ypos"], n["xpos"], n["name"]))
result = {"ok": True, "node_count": len(nodes), "nodes": nodes}
"""


class MCPError(RuntimeError):
    pass


class MCPStdioClient:
    """Cliente MCP minimo para stdio newline JSON-RPC."""

    def __init__(self, command: list[str], protocol_version: str = DEFAULT_PROTOCOL_VERSION):
        self.command = command
        self.protocol_version = protocol_version
        self.process: subprocess.Popen[str] | None = None
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._next_id = 1
        self._closed = False

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        if self.process is not None:
            return
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self.process.stdin is None or self.process.stdout is None:
            raise MCPError("No se pudo abrir stdio para el proceso MCP.")
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        self.initialize()

    def _reader_loop(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        while True:
            line = self.process.stdout.readline()
            if line == "":
                break
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            self._queue.put(message)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def _send(self, payload: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise MCPError("Cliente MCP no iniciado.")
        if self.process.poll() is not None:
            raise MCPError("El proceso MCP termino inesperadamente.")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def _request(self, method: str, params: dict[str, Any] | None = None, timeout: float = 30.0) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.01, deadline - time.time())
            try:
                message = self._queue.get(timeout=remaining)
            except queue.Empty as exc:
                raise MCPError(f"Timeout esperando respuesta de '{method}'.") from exc
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise MCPError(f"Error MCP en '{method}': {message['error']}")
            result = message.get("result")
            if not isinstance(result, dict):
                return {"value": result}
            return result

        raise MCPError(f"Timeout esperando respuesta de '{method}'.")

    def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def initialize(self) -> None:
        self._request(
            "initialize",
            {
                "protocolVersion": self.protocol_version,
                "capabilities": {},
                "clientInfo": {"name": "capture_nuke_dag", "version": "1.02"},
            },
            timeout=45.0,
        )
        self._notify("notifications/initialized")

    def list_tools(self) -> list[str]:
        result = self._request("tools/list", {}, timeout=30.0)
        tools = result.get("tools", [])
        out: list[str] = []
        if isinstance(tools, list):
            for item in tools:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    out.append(item["name"])
        return out

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None, timeout: float = 60.0) -> dict[str, Any]:
        result = self._request(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
            timeout=timeout,
        )
        # FastMCP suele devolver content + structuredContent + isError.
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            if structured.get("status") == "error":
                raise MCPError(str(structured.get("error", "Error desconocido en tool call")))
            return structured

        content = result.get("content")
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if not isinstance(text, str):
                    continue
                text = text.strip()
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
                if isinstance(parsed, dict) and parsed.get("status") == "error":
                    raise MCPError(str(parsed.get("error", "Error desconocido en tool call")))
                if isinstance(parsed, dict):
                    return parsed
                return {"value": parsed}

        if result.get("isError") is True:
            raise MCPError(f"Tool '{name}' devolvio isError=True")
        return result


@dataclass
class RenderNode:
    name: str
    klass: str
    x: float
    y: float
    w: float
    h: float
    color: tuple[int, int, int]
    selected: bool
    display_lines: list[str]
    tag_text: str = ""


def _format_number(value: Any) -> str:
    if isinstance(value, float):
        if abs(value - int(value)) < 1e-6:
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _decode_tile_color(value: Any) -> tuple[int, int, int] | None:
    if value in (None, 0, "0", ""):
        return None
    try:
        raw = int(value) & 0xFFFFFFFF
    except (TypeError, ValueError):
        return None
    if raw == 0:
        return None
    r = (raw >> 24) & 0xFF
    g = (raw >> 16) & 0xFF
    b = (raw >> 8) & 0xFF
    if r == 0 and g == 0 and b == 0:
        return None
    return (r, g, b)


def _pick_node_color(node: dict[str, Any]) -> tuple[int, int, int]:
    klass = str(node.get("class", ""))
    if klass == "Dot":
        return DOT_NODE_COLOR
    tile = _decode_tile_color(node.get("tile_color"))
    if tile is not None:
        return tile
    default_color = _decode_tile_color(node.get("default_color"))
    if default_color is not None:
        return default_color
    return NODE_BASE_COLORS.get(klass, DEFAULT_NODE_COLOR)


def _build_display_lines(node: dict[str, Any]) -> list[str]:
    lines = [str(node.get("name", ""))]
    klass = str(node.get("class", ""))
    label_eval = node.get("label_eval")

    if klass == "Blur":
        channels = str(node.get("channels") or "").strip()
        size_value = node.get("size")
        if channels and channels not in {"rgba", "rgb", "all"}:
            lines.append(f"({channels})")
        if size_value not in (None, ""):
            lines.append(_format_number(size_value))
        elif isinstance(label_eval, str) and label_eval.strip():
            lines.extend([chunk for chunk in label_eval.splitlines() if chunk.strip()])
    elif isinstance(label_eval, str) and label_eval.strip():
        lines.extend([chunk for chunk in label_eval.splitlines() if chunk.strip()])

    # Evita lineas excesivas para conservar legibilidad.
    return lines[:3]


def _classify_input_kind(
    node_class: str,
    input_index: int,
    total_inputs: int,
    input_label: str = "",
) -> str:
    label_lower = input_label.strip().lower()
    if "mask" in label_lower:
        return "mask"
    if node_class in {"Merge", "Merge2"}:
        if input_index >= 2:
            return "mask"
        return "flow"
    return "flow"


def _is_dark(color: tuple[int, int, int]) -> bool:
    r, g, b = color
    luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
    return luminance < 100


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("arial.ttf", "segoeui.ttf", "tahoma.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    end: tuple[float, float],
    direction: str,
    color: tuple[int, int, int],
    size: int,
) -> None:
    x, y = end
    s = max(4, size)
    if direction == "down":
        points = [(x, y), (x - s, y - s), (x + s, y - s)]
    elif direction == "up":
        points = [(x, y), (x - s, y + s), (x + s, y + s)]
    elif direction == "left":
        points = [(x, y), (x + s, y - s), (x + s, y + s)]
    elif direction == "right":
        points = [(x, y), (x - s, y - s), (x - s, y + s)]
    else:
        return
    draw.polygon(points, fill=color)


def _segment_direction(start: tuple[float, float], end: tuple[float, float]) -> str:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if abs(dx) > abs(dy):
        return "right" if dx >= 0 else "left"
    return "down" if dy >= 0 else "up"


def _line_points(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
    return [(int(round(px)), int(round(py))) for px, py in points]


def _node_bounds(nodes: list[RenderNode]) -> tuple[float, float, float, float]:
    min_x = min(node.x for node in nodes)
    min_y = min(node.y for node in nodes)
    max_x = max(node.x + node.w for node in nodes)
    max_y = max(node.y + node.h for node in nodes)
    return min_x, min_y, max_x, max_y


def _to_render_nodes(raw_nodes: list[dict[str, Any]], scale: float, pad: int) -> list[RenderNode]:
    preliminary = []
    for node in raw_nodes:
        x = float(node.get("xpos", 0))
        y = float(node.get("ypos", 0))
        w = float(node.get("screenWidth") or (12 if node.get("class") == "Dot" else 80))
        h = float(node.get("screenHeight") or (12 if node.get("class") == "Dot" else 20))
        preliminary.append((node, x, y, w, h))

    if not preliminary:
        return []

    min_x = min(x for _, x, _, _, _ in preliminary)
    min_y = min(y for _, _, y, _, _ in preliminary)

    render_nodes: list[RenderNode] = []
    for node, x, y, w, h in preliminary:
        render_nodes.append(
            RenderNode(
                name=str(node.get("name", "")),
                klass=str(node.get("class", "")),
                x=(x - min_x) * scale + pad,
                y=(y - min_y) * scale + pad,
                w=max(6.0, w * scale),
                h=max(6.0, h * scale),
                color=_pick_node_color(node),
                selected=bool(node.get("selected", False)),
                display_lines=_build_display_lines(node),
                tag_text=(
                    str(node.get("output") or "").strip()
                    if str(node.get("class", "")) in {"Roto", "RotoPaint", "RotoPaint2"}
                    else ""
                ),
            )
        )
    return render_nodes


def _build_edges(raw_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {str(node.get("name")): node for node in raw_nodes}
    edges: list[dict[str, Any]] = []
    for node in raw_nodes:
        dst_name = str(node.get("name", ""))
        node_class = str(node.get("class", ""))
        inputs = node.get("inputs") or []
        total_inputs = len(inputs)
        if not isinstance(inputs, list):
            continue
        for item in inputs:
            if not isinstance(item, dict):
                continue
            source = item.get("source_node")
            if not source:
                continue
            if str(source) not in by_name:
                continue
            idx_raw = item.get("input_index", 0)
            try:
                input_index = int(idx_raw)
            except (TypeError, ValueError):
                input_index = 0
            input_label = str(item.get("input_label") or "")
            edges.append(
                {
                    "source_node": str(source),
                    "target_node": dst_name,
                    "input_index": input_index,
                    "kind": _classify_input_kind(
                        node_class=node_class,
                        input_index=input_index,
                        total_inputs=total_inputs,
                        input_label=input_label,
                    ),
                }
            )
    return edges


def _draw_connections(
    draw: ImageDraw.ImageDraw,
    raw_nodes: list[dict[str, Any]],
    render_map: dict[str, RenderNode],
    edges: list[dict[str, Any]],
    font_small: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_width: int,
    arrow_size: int,
) -> None:
    by_name = {str(node.get("name")): node for node in raw_nodes}

    for edge in edges:
        src_name = edge["source_node"]
        dst_name = edge["target_node"]
        kind = edge.get("kind", "flow")
        src = render_map.get(src_name)
        dst = render_map.get(dst_name)
        dst_raw = by_name.get(dst_name, {})
        src_raw = by_name.get(src_name, {})
        if src is None or dst is None:
            continue

        src_cx = src.x + (src.w / 2.0)
        src_cy = src.y + (src.h / 2.0)
        dst_cx = dst.x + (dst.w / 2.0)
        dst_cy = dst.y + (dst.h / 2.0)

        if kind == "mask":
            dst_point = (dst.x + dst.w, dst_cy)
            if src_cx >= dst_point[0]:
                src_point = (src.x, src_cy)
            else:
                src_point = (src.x + src.w, src_cy)

            if abs(src_point[1] - dst_point[1]) <= 4:
                points = [src_point, dst_point]
            else:
                mid_x = (src_point[0] + dst_point[0]) / 2.0
                points = [src_point, (mid_x, src_point[1]), (mid_x, dst_point[1]), dst_point]

            draw.line(_line_points(points), fill=EDGE_FLOW_COLOR, width=line_width)
            if len(points) > 1:
                direction = _segment_direction(points[-2], points[-1])
            else:
                direction = "left"
            _draw_arrow(draw, dst_point, direction, EDGE_FLOW_COLOR, size=arrow_size)
            label_y = dst_point[1] - max(9, int(dst.h * 0.5))
            draw.text((dst_point[0] + 6, label_y), "mask", fill=EDGE_MASK_COLOR, font=font_small)
            continue

        # Flujo normal.
        if src_raw.get("class") == "Dot":
            src_point = (src_cx, src_cy)
        else:
            src_point = (src_cx, src.y + src.h)

        if dst_raw.get("class") == "Dot":
            dst_point = (dst_cx, dst_cy)
        else:
            dst_point = (dst_cx, dst.y)

        if abs(src_point[0] - dst_point[0]) <= 2 or abs(src_point[1] - dst_point[1]) <= 2:
            points = [src_point, dst_point]
        elif src_point[1] <= dst_point[1]:
            mid_y = src_point[1] + max(20.0, (dst_point[1] - src_point[1]) * 0.5)
            points = [src_point, (src_point[0], mid_y), (dst_point[0], mid_y), dst_point]
        else:
            points = [src_point, (dst_point[0], src_point[1]), dst_point]

        draw.line(_line_points(points), fill=EDGE_FLOW_COLOR, width=line_width)
        if len(points) > 1:
            direction = _segment_direction(points[-2], points[-1])
        else:
            direction = "down"
        _draw_arrow(draw, dst_point, direction, EDGE_FLOW_COLOR, size=arrow_size)


def _draw_nodes(
    draw: ImageDraw.ImageDraw,
    render_nodes: list[RenderNode],
    font_main: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_small: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    for node in render_nodes:
        x0 = node.x
        y0 = node.y
        x1 = node.x + node.w
        y1 = node.y + node.h

        if node.klass == "Dot":
            draw.ellipse(
                (int(x0), int(y0), int(x1), int(y1)),
                fill=(206, 206, 206),
                outline=NODE_BORDER_COLOR,
                width=1,
            )
            continue

        if node.klass == "Viewer":
            bevel = min(10.0, node.h * 0.6, node.w * 0.15)
            points = [
                (x0 + bevel, y0),
                (x1 - bevel, y0),
                (x1, y0 + node.h / 2.0),
                (x1 - bevel, y1),
                (x0 + bevel, y1),
                (x0, y0 + node.h / 2.0),
            ]
            draw.polygon(_line_points(points), fill=node.color, outline=NODE_BORDER_COLOR)
        else:
            draw.rectangle(
                (int(x0), int(y0), int(x1), int(y1)),
                fill=node.color,
                outline=NODE_BORDER_COLOR,
                width=1,
            )

        # Marquesina lateral similar a los conectores visuales de Nuke.
        side = max(3.0, node.h * 0.16)
        cy = y0 + (node.h / 2.0)
        left_tick = [(x0 - side, cy), (x0, cy - side), (x0, cy + side)]
        right_tick = [(x1 + side, cy), (x1, cy - side), (x1, cy + side)]
        draw.polygon(_line_points(left_tick), fill=NODE_BORDER_COLOR)
        draw.polygon(_line_points(right_tick), fill=NODE_BORDER_COLOR)

        if node.selected:
            draw.rectangle(
                (int(x0 - 2), int(y0 - 2), int(x1 + 2), int(y1 + 2)),
                outline=(255, 219, 79),
                width=1,
            )

        text_color = (246, 246, 246) if _is_dark(node.color) else (18, 18, 18)
        lines = node.display_lines
        if not lines:
            continue

        line_height = max(10, int(node.h / (len(lines) + 1)))
        if line_height <= 11:
            font = font_small
        else:
            font = font_main

        total_text_h = line_height * len(lines)
        start_y = y0 + max(1, (node.h - total_text_h) / 2.0)
        for idx, line in enumerate(lines):
            text_w = draw.textlength(line, font=font)
            tx = x0 + (node.w - text_w) / 2.0
            ty = start_y + (idx * line_height)
            draw.text((tx, ty), line, fill=text_color, font=font)
        if node.tag_text and node.tag_text not in {"rgba", "rgb"}:
            draw.text(
                (x0 + 6, y0 - 14),
                node.tag_text,
                fill=EDGE_MASK_COLOR,
                font=font_small,
            )


def render_png(snapshot: dict[str, Any], output_path: Path, scale: float = 1.0, pad: int = 70) -> None:
    raw_nodes = snapshot.get("nodes", [])
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise RuntimeError("No hay nodos para renderizar en PNG.")

    render_nodes = _to_render_nodes(raw_nodes, scale=scale, pad=pad)
    if not render_nodes:
        raise RuntimeError("No se pudieron preparar nodos para render.")

    min_x, min_y, max_x, max_y = _node_bounds(render_nodes)
    width = int(math.ceil(max_x - min_x + (pad * 2)))
    height = int(math.ceil(max_y - min_y + (pad * 2)))
    width = max(320, width)
    height = max(240, height)

    image = Image.new("RGB", (width, height), GRAPH_BG_COLOR)
    draw = ImageDraw.Draw(image)
    font_main = _load_font(max(12, int(round(11 * scale))))
    font_small = _load_font(max(10, int(round(9 * scale))))
    line_width = max(2, int(round(1.4 * scale)))
    arrow_size = max(5, int(round(3.6 * scale)))

    render_map = {node.name: node for node in render_nodes}
    edges = snapshot.get("edges", [])
    if isinstance(edges, list):
        _draw_connections(
            draw,
            raw_nodes,
            render_map,
            edges,
            font_small=font_small,
            line_width=line_width,
            arrow_size=arrow_size,
        )
    _draw_nodes(draw, render_nodes, font_main=font_main, font_small=font_small)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def render_svg(snapshot: dict[str, Any], output_path: Path, scale: float = 1.0, pad: int = 70) -> None:
    raw_nodes = snapshot.get("nodes", [])
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise RuntimeError("No hay nodos para renderizar en SVG.")

    render_nodes = _to_render_nodes(raw_nodes, scale=scale, pad=pad)
    if not render_nodes:
        raise RuntimeError("No se pudieron preparar nodos para SVG.")

    min_x, min_y, max_x, max_y = _node_bounds(render_nodes)
    width = int(math.ceil(max_x - min_x + (pad * 2)))
    height = int(math.ceil(max_y - min_y + (pad * 2)))
    width = max(320, width)
    height = max(240, height)

    def rgb(color: tuple[int, int, int]) -> str:
        return f"rgb({color[0]},{color[1]},{color[2]})"

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    lines.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{rgb(GRAPH_BG_COLOR)}"/>'
    )

    render_map = {node.name: node for node in render_nodes}
    for edge in snapshot.get("edges", []):
        if not isinstance(edge, dict):
            continue
        src = render_map.get(str(edge.get("source_node")))
        dst = render_map.get(str(edge.get("target_node")))
        if src is None or dst is None:
            continue
        kind = edge.get("kind", "flow")
        src_x = src.x + src.w / 2.0
        src_y = src.y + src.h
        dst_x = dst.x + dst.w / 2.0
        dst_y = dst.y
        color = EDGE_FLOW_COLOR
        if kind == "mask":
            color = EDGE_FLOW_COLOR
            src_x = src.x + src.w
            src_y = src.y + src.h / 2.0
            dst_x = dst.x + dst.w
            dst_y = dst.y + dst.h / 2.0
        lines.append(
            f'<line x1="{src_x:.1f}" y1="{src_y:.1f}" x2="{dst_x:.1f}" y2="{dst_y:.1f}" '
            f'stroke="{rgb(color)}" stroke-width="2"/>'
        )

    for node in render_nodes:
        x0 = node.x
        y0 = node.y
        x1 = node.x + node.w
        y1 = node.y + node.h
        if node.klass == "Dot":
            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0
            half = min(node.w, node.h) / 2.0
            points = f"{cx:.1f},{cy-half:.1f} {cx+half:.1f},{cy:.1f} {cx:.1f},{cy+half:.1f} {cx-half:.1f},{cy:.1f}"
            lines.append(
                f'<polygon points="{points}" fill="{rgb(node.color)}" stroke="{rgb(NODE_BORDER_COLOR)}" stroke-width="1"/>'
            )
        else:
            lines.append(
                f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{node.w:.1f}" height="{node.h:.1f}" '
                f'fill="{rgb(node.color)}" stroke="{rgb(NODE_BORDER_COLOR)}" stroke-width="1"/>'
            )
        text_color = (246, 246, 246) if _is_dark(node.color) else (18, 18, 18)
        if node.display_lines:
            ty = y0 + 12
            for line in node.display_lines[:3]:
                tx = x0 + (node.w / 2.0)
                lines.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{rgb(text_color)}" '
                    f'font-family="Arial, sans-serif" font-size="11">{line}</text>'
                )
                ty += 11

    lines.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _port_is_open(
    host: str,
    port: int,
    timeout: float = 1.5,
    retries: int = 3,
    retry_delay_s: float = 0.2,
) -> bool:
    for attempt in range(max(1, retries)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            if attempt < retries - 1:
                time.sleep(retry_delay_s)
    return False


def capture_snapshot(
    broker_command: list[str],
    check_host: str,
    check_port: int,
) -> dict[str, Any]:
    if not _port_is_open(check_host, check_port):
        print(
            f"[warn] El addon no respondio en {check_host}:{check_port}. "
            "Se intenta continuar via broker MCP activo...",
            file=sys.stderr,
        )

    with MCPStdioClient(broker_command) as client:
        tools = client.list_tools()
        required = {"get_script_info", "execute_python"}
        missing = sorted(required - set(tools))
        if missing:
            raise RuntimeError(
                "El MCP no expuso las tools requeridas: " + ", ".join(missing)
            )

        script_info = client.call_tool("get_script_info", {})
        dag_data = client.call_tool(
            "execute_python",
            {"code": CAPTURE_DAG_CODE, "confirm": True},
            timeout=45.0,
        )
        if dag_data.get("ok") is not True:
            raise RuntimeError(f"execute_python no devolvio ok=True: {dag_data}")

    raw_nodes = dag_data.get("nodes", [])
    if not isinstance(raw_nodes, list):
        raise RuntimeError("La captura de DAG no contiene una lista valida de nodos.")

    edges = _build_edges(raw_nodes)
    snapshot = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture_tool": "capture_nuke_dag.py",
        "broker_command": broker_command,
        "mcp_server": "nuke_kleer (broker)",
        "script_info": script_info,
        "tool_names": sorted(tools),
        "node_count": len(raw_nodes),
        "edge_count": len(edges),
        "nodes": raw_nodes,
        "edges": edges,
    }
    return snapshot


def save_json(snapshot: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    out_dir = Path(args.output_dir).resolve() if args.output_dir else DEFAULT_OUTPUT_DIR
    json_path = Path(args.json_path).resolve() if args.json_path else (out_dir / "dag_snapshot.json")
    png_path = Path(args.png_path).resolve() if args.png_path else (out_dir / "dag_snapshot.png")
    svg_path = Path(args.svg_path).resolve() if args.svg_path else (out_dir / "dag_snapshot.svg")
    return json_path, png_path, svg_path


def _parse_broker_command(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_BROKER_COMMAND)
    return [chunk for chunk in raw.strip().split(" ") if chunk]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Captura DAG de Nuke via MCP broker y renderiza JSON/PNG/SVG."
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Carpeta base de salida (default: tools/output).",
    )
    parser.add_argument("--json-path", default=None, help="Ruta JSON de salida.")
    parser.add_argument("--png-path", default=None, help="Ruta PNG de salida.")
    parser.add_argument("--svg-path", default=None, help="Ruta SVG de salida.")
    parser.add_argument(
        "--no-svg",
        action="store_true",
        help="No generar SVG.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Escala de render (default 1.0).",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=70,
        help="Padding visual alrededor del DAG (default 70).",
    )
    parser.add_argument(
        "--broker-command",
        default=None,
        help="Comando completo para lanzar broker MCP stdio.",
    )
    parser.add_argument(
        "--check-host",
        default=DEFAULT_PORT_HOST,
        help="Host a validar para addon de Nuke (default 127.0.0.1).",
    )
    parser.add_argument(
        "--check-port",
        type=int,
        default=DEFAULT_PORT,
        help="Puerto a validar para addon de Nuke (default 54321).",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    json_path, png_path, svg_path = _resolve_paths(args)
    broker_command = _parse_broker_command(args.broker_command)

    snapshot = capture_snapshot(
        broker_command=broker_command,
        check_host=args.check_host,
        check_port=int(args.check_port),
    )

    save_json(snapshot, json_path)
    render_png(snapshot, png_path, scale=float(args.scale), pad=int(args.padding))
    if not args.no_svg:
        render_svg(snapshot, svg_path, scale=float(args.scale), pad=int(args.padding))

    print(f"[ok] JSON: {json_path}")
    print(f"[ok] PNG:  {png_path}")
    if not args.no_svg:
        print(f"[ok] SVG:  {svg_path}")
    print(f"[ok] Nodos: {snapshot['node_count']} | Conexiones: {snapshot['edge_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
