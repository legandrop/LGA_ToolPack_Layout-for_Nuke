"""
______________________________________________________________

  compare_nuke_dag v1.00 | 2026 | Lega

  Comparador automatico before/after para snapshots DAG de Nuke:
  - captura before y after via MCP broker (opcional)
  - compara nodos, posiciones y conexiones
  - genera reporte JSON y comparativa PNG
______________________________________________________________

ChangeLog:
- v1.00 (2026-07-04): version inicial con captura pair + comparacion JSON/PNG.
"""

from __future__ import annotations

import argparse
import json
import math
import shlex
import time
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow no esta instalado. Instala con: pip install pillow"
    ) from exc

from capture_nuke_dag import (
    DEFAULT_BROKER_COMMAND,
    DEFAULT_PORT,
    DEFAULT_PORT_HOST,
    capture_snapshot,
    render_png,
    render_svg,
    save_json,
)


DEFAULT_BEFORE_DIR = Path(__file__).resolve().parent / "output" / "before"
DEFAULT_AFTER_DIR = Path(__file__).resolve().parent / "output" / "after"
DEFAULT_COMPARE_DIR = Path(__file__).resolve().parent / "output" / "compare"


def _parse_command(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_BROKER_COMMAND)
    return shlex.split(raw, posix=False)


def _load_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No existe snapshot: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Snapshot invalido: {path}")
    return data


def _edge_signature(edge: dict[str, Any]) -> tuple[str, str, int, str]:
    src = str(edge.get("source_node", ""))
    dst = str(edge.get("target_node", ""))
    kind = str(edge.get("kind", "flow"))
    idx_raw = edge.get("input_index", 0)
    try:
        idx = int(idx_raw)
    except (TypeError, ValueError):
        idx = 0
    return src, dst, idx, kind


def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_nodes = {str(n.get("name")): n for n in before.get("nodes", []) if isinstance(n, dict)}
    after_nodes = {str(n.get("name")): n for n in after.get("nodes", []) if isinstance(n, dict)}

    before_names = set(before_nodes.keys())
    after_names = set(after_nodes.keys())
    common_names = sorted(before_names & after_names)

    added_nodes = sorted(after_names - before_names)
    removed_nodes = sorted(before_names - after_names)

    moved: list[dict[str, Any]] = []
    unchanged_count = 0
    total_motion = 0.0
    max_motion = 0.0

    for name in common_names:
        b = before_nodes[name]
        a = after_nodes[name]

        bx = float(b.get("xpos", 0.0))
        by = float(b.get("ypos", 0.0))
        ax = float(a.get("xpos", 0.0))
        ay = float(a.get("ypos", 0.0))
        dx = ax - bx
        dy = ay - by
        dist = math.hypot(dx, dy)

        bw = int(b.get("screenWidth") or 0)
        bh = int(b.get("screenHeight") or 0)
        aw = int(a.get("screenWidth") or 0)
        ah = int(a.get("screenHeight") or 0)
        dw = aw - bw
        dh = ah - bh

        if abs(dx) < 0.001 and abs(dy) < 0.001 and dw == 0 and dh == 0:
            unchanged_count += 1
            continue

        moved.append(
            {
                "name": name,
                "class": str(a.get("class") or b.get("class") or ""),
                "before": {"xpos": bx, "ypos": by, "screenWidth": bw, "screenHeight": bh},
                "after": {"xpos": ax, "ypos": ay, "screenWidth": aw, "screenHeight": ah},
                "delta": {"dx": dx, "dy": dy, "distance": dist, "d_width": dw, "d_height": dh},
            }
        )
        total_motion += dist
        if dist > max_motion:
            max_motion = dist

    moved.sort(key=lambda item: item["delta"]["distance"], reverse=True)

    before_edges_raw = [e for e in before.get("edges", []) if isinstance(e, dict)]
    after_edges_raw = [e for e in after.get("edges", []) if isinstance(e, dict)]
    before_edges = {_edge_signature(edge) for edge in before_edges_raw}
    after_edges = {_edge_signature(edge) for edge in after_edges_raw}

    added_edges = sorted(after_edges - before_edges)
    removed_edges = sorted(before_edges - after_edges)

    report = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": {
            "before_script": before.get("script_info", {}),
            "after_script": after.get("script_info", {}),
        },
        "counts": {
            "before_nodes": len(before_nodes),
            "after_nodes": len(after_nodes),
            "before_edges": len(before_edges),
            "after_edges": len(after_edges),
            "common_nodes": len(common_names),
            "added_nodes": len(added_nodes),
            "removed_nodes": len(removed_nodes),
            "moved_nodes": len(moved),
            "unchanged_common_nodes": unchanged_count,
            "added_edges": len(added_edges),
            "removed_edges": len(removed_edges),
        },
        "motion": {
            "total_distance_px": total_motion,
            "max_distance_px": max_motion,
            "avg_distance_px": (total_motion / len(moved)) if moved else 0.0,
        },
        "added_nodes": [
            {
                "name": name,
                "class": str(after_nodes[name].get("class", "")),
                "xpos": float(after_nodes[name].get("xpos", 0.0)),
                "ypos": float(after_nodes[name].get("ypos", 0.0)),
            }
            for name in added_nodes
        ],
        "removed_nodes": [
            {
                "name": name,
                "class": str(before_nodes[name].get("class", "")),
                "xpos": float(before_nodes[name].get("xpos", 0.0)),
                "ypos": float(before_nodes[name].get("ypos", 0.0)),
            }
            for name in removed_nodes
        ],
        "moved_nodes": moved,
        "edge_changes": {
            "added": [
                {"source_node": s, "target_node": t, "input_index": i, "kind": k}
                for (s, t, i, k) in added_edges
            ],
            "removed": [
                {"source_node": s, "target_node": t, "input_index": i, "kind": k}
                for (s, t, i, k) in removed_edges
            ],
        },
    }
    return report


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("arial.ttf", "segoeui.ttf", "tahoma.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_compare_png(
    before_png: Path,
    after_png: Path,
    report: dict[str, Any],
    output_png: Path,
) -> None:
    before_img = Image.open(before_png).convert("RGB")
    after_img = Image.open(after_png).convert("RGB")

    pad = 24
    gap = 24
    header_h = 92
    footer_h = 26
    canvas_w = before_img.width + after_img.width + (pad * 2) + gap
    canvas_h = max(before_img.height, after_img.height) + header_h + footer_h

    canvas = Image.new("RGB", (canvas_w, canvas_h), (44, 45, 49))
    draw = ImageDraw.Draw(canvas)
    font_title = _load_font(16)
    font_text = _load_font(12)

    before_x = pad
    after_x = pad + before_img.width + gap
    images_y = header_h

    canvas.paste(before_img, (before_x, images_y))
    canvas.paste(after_img, (after_x, images_y))

    draw.rectangle(
        [before_x - 1, images_y - 1, before_x + before_img.width + 1, images_y + before_img.height + 1],
        outline=(92, 126, 246),
        width=2,
    )
    draw.rectangle(
        [after_x - 1, images_y - 1, after_x + after_img.width + 1, images_y + after_img.height + 1],
        outline=(221, 146, 80),
        width=2,
    )

    draw.text((before_x, 18), "BEFORE", fill=(150, 184, 255), font=font_title)
    draw.text((after_x, 18), "AFTER", fill=(245, 173, 107), font=font_title)

    counts = report.get("counts", {})
    motion = report.get("motion", {})
    summary = (
        f"nodos movidos: {counts.get('moved_nodes', 0)} | "
        f"nodos agregados: {counts.get('added_nodes', 0)} | "
        f"nodos eliminados: {counts.get('removed_nodes', 0)} | "
        f"edges +/-: {counts.get('added_edges', 0)}/{counts.get('removed_edges', 0)} | "
        f"movimiento total px: {motion.get('total_distance_px', 0):.2f}"
    )
    draw.text((pad, 54), summary, fill=(230, 230, 230), font=font_text)

    _ensure_parent(output_png)
    canvas.save(output_png)


def _default_paths(before_dir: Path, after_dir: Path, compare_dir: Path) -> dict[str, Path]:
    return {
        "before_json": before_dir / "dag_snapshot.json",
        "before_png": before_dir / "dag_snapshot.png",
        "before_svg": before_dir / "dag_snapshot.svg",
        "after_json": after_dir / "dag_snapshot.json",
        "after_png": after_dir / "dag_snapshot.png",
        "after_svg": after_dir / "dag_snapshot.svg",
        "report_json": compare_dir / "dag_compare_report.json",
        "report_png": compare_dir / "dag_compare.png",
    }


def _capture_and_render(
    broker_command: list[str],
    check_host: str,
    check_port: int,
    json_path: Path,
    png_path: Path,
    svg_path: Path,
    scale: float,
    padding: int,
    no_svg: bool,
) -> dict[str, Any]:
    snapshot = capture_snapshot(
        broker_command=broker_command,
        check_host=check_host,
        check_port=check_port,
    )
    save_json(snapshot, json_path)
    render_png(snapshot, png_path, scale=scale, pad=padding)
    if not no_svg:
        render_svg(snapshot, svg_path, scale=scale, pad=padding)
    return snapshot


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara snapshots DAG before/after con captura automatica via MCP."
    )
    parser.add_argument("--use-existing", action="store_true", help="No captura; usa JSON existentes.")
    parser.add_argument("--before-dir", default=str(DEFAULT_BEFORE_DIR), help="Directorio salida before.")
    parser.add_argument("--after-dir", default=str(DEFAULT_AFTER_DIR), help="Directorio salida after.")
    parser.add_argument("--compare-dir", default=str(DEFAULT_COMPARE_DIR), help="Directorio salida reporte.")
    parser.add_argument("--before-json", default=None, help="Ruta JSON before.")
    parser.add_argument("--after-json", default=None, help="Ruta JSON after.")
    parser.add_argument("--before-png", default=None, help="Ruta PNG before.")
    parser.add_argument("--after-png", default=None, help="Ruta PNG after.")
    parser.add_argument("--before-svg", default=None, help="Ruta SVG before.")
    parser.add_argument("--after-svg", default=None, help="Ruta SVG after.")
    parser.add_argument("--report-json", default=None, help="Ruta JSON de reporte.")
    parser.add_argument("--report-png", default=None, help="Ruta PNG comparativa.")
    parser.add_argument("--no-svg", action="store_true", help="No generar SVG de snapshots.")
    parser.add_argument("--no-pause", action="store_true", help="No esperar Enter entre before/after.")
    parser.add_argument("--wait-seconds", type=float, default=0.0, help="Espera fija cuando --no-pause.")
    parser.add_argument("--scale", type=float, default=1.0, help="Escala de render para snapshots.")
    parser.add_argument("--padding", type=int, default=70, help="Padding visual del render.")
    parser.add_argument("--broker-command", default=None, help="Comando completo broker MCP stdio.")
    parser.add_argument("--check-host", default=DEFAULT_PORT_HOST, help="Host addon Nuke.")
    parser.add_argument("--check-port", type=int, default=DEFAULT_PORT, help="Puerto addon Nuke.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    before_dir = Path(args.before_dir).resolve()
    after_dir = Path(args.after_dir).resolve()
    compare_dir = Path(args.compare_dir).resolve()
    defaults = _default_paths(before_dir, after_dir, compare_dir)

    before_json = Path(args.before_json).resolve() if args.before_json else defaults["before_json"]
    before_png = Path(args.before_png).resolve() if args.before_png else defaults["before_png"]
    before_svg = Path(args.before_svg).resolve() if args.before_svg else defaults["before_svg"]
    after_json = Path(args.after_json).resolve() if args.after_json else defaults["after_json"]
    after_png = Path(args.after_png).resolve() if args.after_png else defaults["after_png"]
    after_svg = Path(args.after_svg).resolve() if args.after_svg else defaults["after_svg"]
    report_json = Path(args.report_json).resolve() if args.report_json else defaults["report_json"]
    report_png = Path(args.report_png).resolve() if args.report_png else defaults["report_png"]

    broker_command = _parse_command(args.broker_command)
    no_svg = bool(args.no_svg)
    scale = float(args.scale)
    padding = int(args.padding)

    if args.use_existing:
        before_snapshot = _load_snapshot(before_json)
        after_snapshot = _load_snapshot(after_json)
        if not before_png.exists():
            _ensure_parent(before_png)
            render_png(before_snapshot, before_png, scale=scale, pad=padding)
        if not after_png.exists():
            _ensure_parent(after_png)
            render_png(after_snapshot, after_png, scale=scale, pad=padding)
    else:
        print("[1/4] Capturando BEFORE...")
        before_snapshot = _capture_and_render(
            broker_command=broker_command,
            check_host=args.check_host,
            check_port=int(args.check_port),
            json_path=before_json,
            png_path=before_png,
            svg_path=before_svg,
            scale=scale,
            padding=padding,
            no_svg=no_svg,
        )

        if args.no_pause:
            if args.wait_seconds > 0:
                print(f"[2/4] Esperando {args.wait_seconds:.1f}s antes de capturar AFTER...")
                time.sleep(args.wait_seconds)
            else:
                print("[2/4] --no-pause activo; capturando AFTER inmediatamente...")
        else:
            print("[2/4] Ejecuta lga_arrange en Nuke y presiona Enter para capturar AFTER.")
            input()

        print("[3/4] Capturando AFTER...")
        after_snapshot = _capture_and_render(
            broker_command=broker_command,
            check_host=args.check_host,
            check_port=int(args.check_port),
            json_path=after_json,
            png_path=after_png,
            svg_path=after_svg,
            scale=scale,
            padding=padding,
            no_svg=no_svg,
        )

    print("[4/4] Comparando snapshots...")
    report = compare_snapshots(before_snapshot, after_snapshot)
    save_json(report, report_json)
    render_compare_png(before_png, after_png, report, report_png)

    print(f"[ok] BEFORE JSON: {before_json}")
    print(f"[ok] AFTER JSON:  {after_json}")
    print(f"[ok] REPORTE:     {report_json}")
    print(f"[ok] COMPARATIVA: {report_png}")
    counts = report.get("counts", {})
    print(
        "[ok] Movidos: "
        f"{counts.get('moved_nodes', 0)} | "
        f"Agregados: {counts.get('added_nodes', 0)} | "
        f"Eliminados: {counts.get('removed_nodes', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
