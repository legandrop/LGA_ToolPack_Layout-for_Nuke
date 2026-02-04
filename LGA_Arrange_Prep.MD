# LGA Arrange — Prep Tooling Log

Last updated: 2026-02-04

## Purpose
All **prep / translation / testing utilities** live here.  
This file documents how to generate graph files from `.nk`, export Graphviz, and validate round‑trips.

## Folder Layout
All prep scripts are under `LGA_Arrange_Prep/`.

Key files:
- `LGA_Arrange_Prep/layout_core.py`  
  Pure‑Python layout logic (no Nuke). Used for graph tests.
- `LGA_Arrange_Prep/graphviz_export.py`  
  Graphviz DOT export.
- `LGA_Arrange_Prep/graph_examples.py`  
  Hand‑built test graphs.
- `LGA_Arrange_Prep/layout_cli.py`  
  Runs examples and prints BEFORE/AFTER DOT.
- `LGA_Arrange_Prep/nk_parser.py`  
  Minimal `.nk` parser (nodes, positions, stack‑based connections).
- `LGA_Arrange_Prep/nk_to_graph.py`  
  `.nk` → graph JSON.
- `LGA_Arrange_Prep/graph_io.py`  
  Graph JSON load/save.
- `LGA_Arrange_Prep/nk_to_dot.py`  
  `.nk` → Graphviz DOT.
- `LGA_Arrange_Prep/graph_to_dot.py`  
  graph JSON → Graphviz DOT.
- `LGA_Arrange_Prep/prep_cli.py`  
  End‑to‑end pipeline: `.nk` → graph JSON + DOTs.
- `LGA_Arrange_Prep/out/`  
  Output folder for generated files.

## Graph JSON Format
Output is a single JSON file:
```json
{
  "meta": { "source_nk": "...", "scale": 0.05, "tolerance_x": 2.5 },
  "nodes": [
    {
      "name": "Grade1",
      "klass": "Grade",
      "column": "C0",
      "order": 0,
      "x": 0.0,
      "y": 10.0,
      "height": 0.5
    }
  ],
  "edges": [
    { "src": "Grade1", "dst": "Blur1", "kind": "flow", "align": false }
  ]
}
```

## Parsing Notes (NK → Graph)
### Connections
- The parser is **stack‑based** (Nuke script semantics).
- Supports: `set var [stack 0]`, `push $var`, `push 0`, `pop`.
- If the `.nk` has **no stack commands**, the parser infers a **linear chain**:
  each node with inputs consumes the previous node on the stack.
- `inputs 1+1` is treated as **mandatory 1 + optional mask 1**.  
  If no extra stack item exists, mask is ignored.

### Position / Scale
- Nuke Y grows **downwards**.  
  We **invert Y** (`y = -nk_y`) so Graphviz grows upwards.
- Default scale = `0.05`.  
  This makes Nuke X/Y values comparable to the test graphs.
- Column grouping uses `tolerance_x = 2.5` (in **scaled units**).

### Height Estimation
`.nk` does not store `screenHeight`, so we approximate:
- Default node height = `0.5` (with **class overrides**):
  - `Blur`, `Roto`, `Copy` → `0.6`
  - `Merge`, `Merge2` → `0.8`
- If label has multiple lines, +`0.15` per extra line.
- Dot height:
  - Default `0.2`.
  - If `size` knob exists, `height = max(0.1, 0.02 * size)`.

This is a **best‑effort approximation**; in Nuke, real height comes from `screenHeight()`.

## Usage
Run end‑to‑end pipeline:
```bash
python3 LGA_Arrange_Prep/prep_cli.py testGraph_v01.nk
```

Outputs:
- `LGA_Arrange_Prep/out/testGraph_v01.graph.json`
- `LGA_Arrange_Prep/out/testGraph_v01.from_nk.dot`
- `LGA_Arrange_Prep/out/testGraph_v01.from_graph.dot`

These DOT files can be pasted into:  
https://dreampuf.github.io/GraphvizOnline

## Latest Run (2026-02-04)
- Command: `python3 LGA_Arrange_Prep/prep_cli.py testGraph_v01.nk`
- Outputs (generated):
  - `LGA_Arrange_Prep/out/testGraph_v01.graph.json`
  - `LGA_Arrange_Prep/out/testGraph_v01.from_nk.dot`
  - `LGA_Arrange_Prep/out/testGraph_v01.from_graph.dot`
- Diff check: DOTs are identical (byte‑for‑byte).

## Next
- Validate that `.nk` connections are correctly recovered in more complex scripts.
- If needed, enhance parsing of optional mask inputs and explicit input knobs.
