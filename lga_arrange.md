# LGA Arrange Nodes — Rules Log

Last updated: 2026-02-04

## Goal
Define the **arrange behavior** (rules and priorities) that will be implemented in Nuke.

## Status (2026-02-04)
- `LGA_arrangeNodes.py` rewritten as **v2.0**, using the validated graph layout core and a Nuke adapter.
- Logging system (Docu_Logging_System) integrated into `LGA_arrangeNodes.py` with key decision logs.

## Rules / Discoveries (confirmed)
1. **Vertical order is preserved** within each column (original order never changes).
   - Nuke adapter **inverts Y** for layout so “higher” matches the core (larger Y).
2. **Connection alignment rule:** if a node is connected across columns, it must share the same Y as the connected node.
3. **Priority for conflicting connections:** the connection to the **principal column** wins; otherwise, the connection to the **closest‑to‑principal column** wins.
4. **Baseline distribution:** nodes are distributed vertically as equidistant as possible based on the current column/subgroup height.
5. **Overlap resolution priority:**
   - First, push the **secondary** column subgroup down to clear overlaps.
   - If there is insufficient space, then adjust the **principal** column.
6. **No overlaps are acceptable** (avoid at all cost).
7. **X‑alignment per column:** align to the most common X (if repeated), otherwise average.
8. **Node heights matter:** distribution is based on **bounding boxes** (center ± height/2).
9. **Dot size matters:** dots can be smaller/larger depending on settings and must be respected.
10. **SubSubgroup segmentation:** in non‑principal columns, each connected node controls **its own segment** (itself + nodes above).
11. **Top constraint:** unconnected nodes must not rise above the top of the principal column.
12. **Principal inference (when missing):** choose the column with **max subgroup height** as principal.
13. **Flow adjacency inside a column:** any non‑mask connection (including A/B) keeps nodes in the same subgroup.

## Decisions from User (2026-02-04)
1. Apply column discovery + principal selection (done in core via `auto_columns`).
2. SubSubgroup behavior: **apply**. Clarified rule: nodes connected to different principal nodes move as separate segments.
3. Potential/next columns logic: **apply**.
4. SubSubgroupOld handling: **apply**.
5. Top constraint for unconnected nodes: **apply**.
6. Connectivity‑order distribution: **pending** (needs decision).
7. Recursive conflict propagation: **pending** (only partially handled so far).
8. X alignment heuristic (most common X first): **apply**.
9. Nuke‑specific filtering (Backdrop/Viewer): **apply in Nuke** implementation.
10. Logging: **apply** (debugPy_arrangeNodes.log, key decisions only).

## Pending / Open
- **Connection‑order based distribution (NU):** decide whether to derive ordering from connectivity instead of vertical order when conflicts exist.
- **Recursive conflict propagation:** confirm if we must propagate overlap fixes to parent columns beyond principal.
