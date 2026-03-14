> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA Arrange — Overview de Prep

Última actualización: 2026-02-06

## Propósito
Aquí viven todas las utilidades de **prep / traducción / testing**.  
Este archivo documenta cómo generar archivos de grafo desde `.nk`, exportar Graphviz y validar round‑trips.

## Flujo obligatorio (regla de trabajo)
Para cualquier regla nueva o cambio de lógica:
1. Convertir `.nk → JSON`.
2. Ejecutar **arrange en JSON** y validar con el **check de JSON**.
3. Generar `.dot` y validar visualmente.
4. Recién ahí portar la lógica a `LGA_arrangeNodes.py` (Nuke).

## Estructura de carpeta
Todos los scripts de prep están en `LGA_Arrange_Prep/`.

Archivos clave:
- `LGA_Arrange_Prep/layout_core.py`  
  Lógica de layout pura en Python (sin Nuke). Usada para tests.
- `LGA_Arrange_Prep/graphviz_export.py`  
  Export de Graphviz DOT.
- `LGA_Arrange_Prep/graph_examples.py`  
  Grafos de prueba hechos a mano.
- `LGA_Arrange_Prep/layout_cli.py`  
  Corre ejemplos y muestra BEFORE/AFTER en DOT.
- `LGA_Arrange_Prep/nk_parser.py`  
  Parser mínimo de `.nk` (nodos, posiciones, conexiones por stack).
- `LGA_Arrange_Prep/LGA_nk_to_json.py`  
  `.nk` → JSON (lógica de stack de Nuke).
- `LGA_Arrange_Prep/graph_io.py`  
  Load/Save de JSON de grafo.
- `LGA_Arrange_Prep/nk_to_dot.py`  
  `.nk` → Graphviz DOT.
- `LGA_Arrange_Prep/graph_to_dot.py`  
  JSON → Graphviz DOT.
- `LGA_Arrange_Prep/prep_cli.py`  
  Pipeline end‑to‑end: `.nk` → JSON + DOTs.
- `LGA_Arrange_Prep/LGA_arrangeJSON.py`  
  Aplica layout a un JSON y exporta DOT.
- `LGA_Arrange_Prep/out/`  
  Carpeta de salida.

## Docs
- `LGA_Arrange_Prep/LGA_NK_to_JSON.md`  
  Estado y reglas específicas de la conversión `.nk → JSON`.

## Formato JSON
El output es un único JSON:
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

## Notas de parsing (NK → Graph)
### Conexiones
- El parser es **stack‑based** (semántica de Nuke).
- Soporta: `set var [stack 0]`, `push $var`, `push 0`, `pop`.
- Si el `.nk` **no tiene comandos de stack**, se infiere una **cadena lineal**:
  cada nodo con inputs consume el nodo anterior del stack.
- `inputs 1+1` se trata como **1 obligatorio + 1 máscara opcional**.  
  Si no hay item extra en el stack, se ignora la máscara.
- Si un nodo tiene **mask input** pero no existe link explícito en el stack, se infiere
  una máscara al **nodo más cercano por Y** en **otra columna** (priorizando Dot).
- Para archivos **sin stack directives**, se habilita la inferencia espacial:
  - Flow edges se crean top‑to‑bottom **dentro de cada columna**, cortando en nodos con `inputs 0`.
  - Inputs **A** de Merge se asignan top‑to‑bottom con el **nodo inferior** de cada subgrupo izquierdo.
  - Inputs de máscara se infieren solo si el nodo **no fue usado** como fuente de máscara.

### Posición / Escala
- En Nuke, Y crece **hacia abajo**.  
  Se **invierte Y** (`y = -nk_y`) para que Graphviz crezca hacia arriba.
- Escala por defecto = `0.05`.  
  Esto hace que X/Y de Nuke sean comparables con los tests.
- Agrupamiento de columnas usa `tolerance_x = 2.5` (en unidades escaladas).

### Centrado (crítico)
`.nk` guarda posiciones **top‑left** (`xpos`, `ypos`).  
Se convierten a **centro** usando tamaños UI aproximados:
- box nodes: ancho `80px`, alto `20px`
- dot nodes: ancho/alto `12px`
- blur/roto/copy: alto `24px`
- merge: alto `28px`

Esto hace que los dots queden centrados bajo su columna, como en Nuke.

### Estimación de alturas
`.nk` no guarda `screenHeight`, así que se aproxima:
- Altura default = `0.5` (con **overrides** por clase):
  - `Blur`, `Roto`, `Copy` → `0.6`
  - `Merge`, `Merge2` → `0.8`
- Si el label tiene múltiples líneas, +`0.15` por línea extra.
- Dot height:
  - Default `0.2`.
  - Si existe knob `size`, `height = max(0.1, 0.02 * size)`.

Esto es **best‑effort**; en Nuke la altura real viene de `screenHeight()`.

## Uso
Pipeline end‑to‑end:
```bash
python3 LGA_Arrange_Prep/prep_cli.py testGraph_v01.nk
```

Aplicar layout a un JSON:
```bash
python3 LGA_Arrange_Prep/LGA_arrangeJSON.py \
  LGA_Arrange_Prep/out/testGraph_v02.graph.json \
  LGA_Arrange_Prep/out/testGraph_v02.graph.arranged.dot
```

Outputs:
- `LGA_Arrange_Prep/out/testGraph_v01.graph.json`
- `LGA_Arrange_Prep/out/testGraph_v01.from_nk.dot`
- `LGA_Arrange_Prep/out/testGraph_v01.from_graph.dot`
- `LGA_Arrange_Prep/out/testGraph_v02.graph.arranged.json`

Estos DOT se pueden pegar en:
https://dreampuf.github.io/GraphvizOnline

## Última corrida (2026-02-04)
- Comando: `python3 LGA_Arrange_Prep/prep_cli.py testGraph_v01.nk`
- Outputs:
  - `LGA_Arrange_Prep/out/testGraph_v01.graph.json`
  - `LGA_Arrange_Prep/out/testGraph_v01.from_nk.dot`
  - `LGA_Arrange_Prep/out/testGraph_v01.from_graph.dot`
- Diff: DOTs idénticos (byte‑for‑byte).
- Update: dot ahora queda **centrado bajo Roto** y **mask input inferido**.

## Última corrida (2026-02-04, v02)
- Comando: `python3 LGA_Arrange_Prep/prep_cli.py testGraph_v02.nk`
- Outputs:
  - `LGA_Arrange_Prep/out/testGraph_v02.graph.json`
  - `LGA_Arrange_Prep/out/testGraph_v02.from_nk.dot`
  - `LGA_Arrange_Prep/out/testGraph_v02.from_graph.dot`
- Diff: DOTs idénticos (byte‑for‑byte).

## Chequeo de layout (2026-02-04)
- Update: `layout_core` ahora **infiera columna principal** cuando falta.
- Comando:
  `python3 LGA_Arrange_Prep/LGA_arrangeJSON.py LGA_Arrange_Prep/out/testGraph_v02.graph.json LGA_Arrange_Prep/out/testGraph_v02.graph.arranged.dot`
- Output:
  - `LGA_Arrange_Prep/out/testGraph_v02.graph.arranged.dot`

## Próximo
- Validar que las conexiones `.nk` se recuperen bien en scripts más complejos.
- Si hace falta, mejorar parsing de máscaras opcionales e inputs explícitos.
