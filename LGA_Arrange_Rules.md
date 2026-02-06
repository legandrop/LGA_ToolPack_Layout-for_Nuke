# LGA Arrange Nodes — Rules Log

Last updated: 2026-02-06

## Goal
Define the **arrange behavior** (rules and priorities) that will be implemented in Nuke.

## Status (2026-02-06)
- `LGA_arrangeNodes.py` rewritten as **v2.0**, using the validated graph layout core and a Nuke adapter.
- Logging system (Docu_Logging_System) integrated into `LGA_arrangeNodes.py` with key decision logs.

## Rules / Discoveries (confirmed)
1. **Vertical order is preserved** within each column (original order never changes).
   - Nuke adapter **inverts Y** for layout so “higher” matches the core (larger Y).
2. **Connection alignment rule:** if a node is connected across columns, it must share the same Y as the connected node.
   - **Anchor direction:** by default **the input aligns to the node it feeds** (dst is anchor, src follows).  
   - **Principal guard:** if one side is in the principal column, the **principal node is always the anchor**.
3. **Priority for conflicting connections:** alignment is enforced **from principal outward**; farther columns must adapt and **do not restrict** inner columns.  
   - Implementation detail: alignment runs in **multiple passes** so dependencies (outer ↔ inner) settle.
   - **Fallback:** if a column has no anchor toward the principal, it aligns **to its source** even if that source is farther out.
4. **Baseline distribution:** nodes are distributed vertically as equidistant as possible based on the current column/subgroup height.  
   - **Principal column is redistributed every iteration** with **top/bottom fixed**.
5. **Overlap resolution priority:**
   - First, push the **secondary** column subgroup down to clear overlaps.
   - **Principal top/bottom never move**; if needed, **redistribute within bounds** (no expansion).
   - **New (v08 case):** enforce a **fixed edge gap** between adjacent subgroups in a column:
     - **upper bottom edge** vs **lower top edge**  
     - target: `gap = OVERLAP_EDGE_GAP`  
     - `delta = OVERLAP_EDGE_GAP - (upper_bottom_edge - lower_top_edge)`  
     - shift the **upper** subgroup by `delta` (can be up or down).  
     If the upper subgroup is anchored to principal, apply the same `delta` to its anchor and
     redistribute the principal within fixed bounds.
6. **No overlaps are acceptable** (avoid at all cost).
7. **X‑alignment per column:** align to the most common X (if repeated), otherwise average.
8. **Node heights matter:** distribution is based on **bounding boxes** (center ± height/2).
9. **Dot size matters:** dots can be smaller/larger depending on settings and must be respected.
10. **Subgroup alignment (single anchor):** in non‑principal columns, a connected subgroup is shifted **as a whole** to match **one anchor** (closest to principal).  
    - This **preserves equidistant spacing** inside the subgroup.
    - **No segmentation** inside a subgroup; only **between subgroups**.
11. **Top constraint:** unconnected nodes must not rise above the top of the principal column.
12. **Principal inference (when missing):** choose the column with **max subgroup height** as principal.
13. **Flow adjacency inside a column:** any non‑mask connection (including A/B) keeps nodes in the same subgroup.
14. **Single-column selection:** the principal column is distributed like any other (no special skip).
15. **Anchors in principal are not fixed:** external columns re‑align to the principal after its redistribution.

## Decisions from User (2026-02-06)
1. Apply column discovery + principal selection (done in core via `auto_columns`).
2. Subgroup behavior: **apply single‑anchor shift**. Clarified rule: the subgroup follows one anchor; internal spacing is preserved.
3. Potential/next columns logic: **removed for arrange** (outer columns must not restrict inner).
4. SubSubgroupOld handling: **apply**.
5. Top constraint for unconnected nodes: **apply**.
6. Connectivity‑order distribution: **pending** (needs decision).
7. Recursive conflict propagation: **pending** (only partially handled so far).
8. X alignment heuristic (most common X first): **apply**.
9. Nuke‑specific filtering (Backdrop/Viewer): **apply in Nuke** implementation.
10. Logging: **apply** (debugPy_arrangeNodes.log, key decisions only).
11. Principal top/bottom fixed; redistribute within bounds: **apply**.
12. Do not fix anchors in principal: **apply**.

## Pending / Open
- **Connection‑order based distribution (NU):** decide whether to derive ordering from connectivity instead of vertical order when conflicts exist.
- **Recursive conflict propagation:** confirm if we must propagate overlap fixes to parent columns beyond principal.
