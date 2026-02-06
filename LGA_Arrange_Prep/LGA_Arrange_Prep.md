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
