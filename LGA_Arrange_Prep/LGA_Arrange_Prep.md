# LGA Arrange Prep — Estado y Archivos

## Objetivo
Construir una **traducción correcta de `.nk` a JSON** que represente las conexiones reales entre nodos, **igual que Nuke**.  
La meta es que el JSON sea una fuente confiable para:
- generar gráficos (`.dot`),
- validar reglas de alineación,
- y luego traducir la lógica al script final de Nuke.

## Problema actual
La conversión `.nk → JSON` **no está interpretando bien las conexiones**.  
Nuke entiende las conexiones desde el `.nk` y nosotros necesitamos **replicar esa lectura**:
- detectar qué nodo alimenta cada input (A/B/mask/flow),
- y no inferir por posiciones si no hay información real.

## Archivos principales
- `/Users/leg4/.nuke/LGA_ToolPack-Layout/LGA_Arrange_Prep/LGA_nk_to_json.py`  
  Convertidor principal `.nk → JSON`.

- `/Users/leg4/.nuke/LGA_ToolPack-Layout/LGA_Arrange_Prep/nk_parser.py`  
  Parser base del `.nk`.

- `/Users/leg4/.nuke/LGA_ToolPack-Layout/LGA_Arrange_Prep/graph_to_dot.py`  
  Genera `.dot` desde JSON.

## Archivos de prueba
- `/Users/leg4/.nuke/LGA_ToolPack-Layout/testGraph_v03_After.nk`
- `/Users/leg4/.nuke/LGA_ToolPack-Layout/testGraph_v04.nk`

## Salidas actuales
- `/Users/leg4/.nuke/LGA_ToolPack-Layout/LGA_Arrange_Prep/out/testGraph_v04.graph.json`
- `/Users/leg4/.nuke/LGA_ToolPack-Layout/LGA_Arrange_Prep/out/testGraph_v04.graph.dot`

## Qué falta resolver
- **Dónde están las conexiones reales** en `.nk` y cómo extraerlas con precisión.
- Evitar inferencias por posición si el `.nk` no lo indica.
- Lograr que el JSON refleje exactamente los inputs (A/B/mask/flow) como los interpreta Nuke.

## Estado actual (2026-02-06)
La conversión `.nk → JSON` ahora replica la **lógica de Nuke** para conexiones:
- **Las conexiones se derivan solo de la stack** (`set`, `push`, `pop`) y el orden de evaluación del `.nk`.
- Si un nodo **no tiene `inputs` declarado**, Nuke asume **1 input** (principal).  
  Excepción: `Root` siempre es 0.
- Para `Merge/Merge2`: **input 0 = B**, **input 1 = A**, **input 2+ = mask**.
- Clases con puntos (ej. `OFXuk.co...`) se parsean correctamente y no rompen la stack.
- No se usa inferencia espacial para crear conexiones (sin heurísticas).

## Resultado verificado (testGraph_v03_Before)
Se validó que el JSON coincide con Nuke:
- `Merge11` recibe **3 inputs**: `Transform_MatchMove2 (B)`, `Clamp5 (A)`, `Shuffle2 (mask)`.
- `Merge10` recibe **3 inputs**: `Dot4 (B)`, `Clamp3 (A)`, `Merge11 (mask)`.
