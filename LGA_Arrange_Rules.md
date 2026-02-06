# LGA Arrange Nodes — Reglas

Última actualización: 2026-02-06

## Objetivo
Definir el **comportamiento de arrange** (reglas y prioridades) que se implementa en Nuke.

## Estado (2026-02-06)
- `LGA_arrangeNodes.py` reescrito como **v2.0**, usando el core de layout validado y un adapter de Nuke.
- Sistema de logging (Docu_Logging_System) integrado en `LGA_arrangeNodes.py` con logs de decisiones clave.

## Reglas / Descubrimientos (confirmados)
**Flujo de trabajo obligatorio:** toda regla nueva se valida **primero en JSON**.  
Pasos: `.nk → JSON → arrange JSON → check JSON → DOT`.  
Recién después se porta la lógica a `LGA_arrangeNodes.py` (Nuke).

1. **Se preserva el orden vertical** dentro de cada columna (el orden original no cambia). En Nuke se **invierte Y** para layout (más alto = Y mayor).
2. **Regla de alineación de conexiones:** si un nodo está conectado entre columnas, debe compartir la misma Y que su conectado. Dirección del ancla: por defecto el **input se alinea al nodo que alimenta** (dst es ancla, src sigue). Si uno está en la columna principal, **la principal siempre es el ancla**.
3. **Prioridad para conexiones conflictivas:** la alineación se fuerza **desde la principal hacia afuera**. Las columnas más lejanas **se adaptan** y **no restringen** a las internas. La alineación corre en **múltiples pasadas** para que las dependencias se estabilicen. Fallback: si una columna no tiene ancla hacia la principal, se alinea **a su fuente** aunque esté más lejos.
4. **Distribución base:** los nodos se distribuyen verticalmente lo más equidistante posible según la altura del subgrupo/columna. La **columna principal se redistribuye en cada iteración** con top/bottom fijos.
5. **Resolución de solapes:** primero se resuelve el solape entre subgrupos. La **principal no crece**; si hace falta, se redistribuye dentro de sus límites.
6. **Regla v08 de solapes entre subgrupos:** se impone un **gap fijo entre bordes**: borde inferior del subgrupo superior vs borde superior del subgrupo inferior. Fórmula: `delta = OVERLAP_EDGE_GAP - (upper_bottom_edge - lower_top_edge)`. Se mueve el subgrupo superior por `delta` (puede subir o bajar). Si ese subgrupo está anclado a la principal, se aplica el mismo `delta` a su ancla y se redistribuye la principal dentro de sus límites.
7. **Solape con anclas distintas en la principal:** si los dos subgrupos están anclados a **dos nodos distintos** de la principal, se intenta mover el **ancla superior**. Si el movimiento queda **capado**, el **restante** se aplica al **ancla inferior** en el sentido opuesto. Si aún así no alcanza, se **cappea el delta** al máximo posible y se acepta un gap menor. Luego se redistribuye la principal dentro de top/bottom.
8. **Alineación obligatoria del ancla con su subgrupo:** si un subgrupo se movió (por solape o redistribución), su **ancla en la principal debe moverse** para quedar **exactamente alineada** al nodo conectado del subgrupo. Esta alineación se aplica **antes** de redistribuir la principal por tramos.
   - Se registra en logs si el ancla **se mueve**, si ya estaba alineada, o si **no hay nodo conectado** (skip).
9. **Propagación del movimiento del ancla al subgrupo (y viceversa):** cuando un **ancla en la principal se mueve** para resolver solapes, **su subgrupo conectado debe desplazarse como bloque** con el mismo `delta` (reglas 14/15), y el subgrupo **no puede quedarse atrás**. Si el subgrupo se movió primero, el ancla debe acompañar y quedar alineada.
10. **Re‑alineación final post‑redistribución:** si la principal se redistribuye en una iteración, se debe ejecutar **una pasada final de alineación** de columnas externas hacia la principal para garantizar que **anclas y ramas** queden en la misma Y.
11. **Compresión permitida (global):** si no alcanza el espacio con `MIN_GAP`, se permite comprimir **en cualquier distribución** (principal y subgrupos) hasta un **mínimo** (`MIN_GAP_FLOOR`, 3 px). Si ni siquiera así entra, se permite bajar **hasta 0 px** (sin solapar).
12. **No se permiten solapes** (evitar a toda costa).
13. **Alineación X por columna:** se alinea al X más común (si se repite), si no, al promedio.
14. **Alturas importan:** la distribución se calcula con **bounding boxes** (centro ± alto/2).
15. **Tamaño de Dot importa:** puede variar y debe respetarse.
16. **Alineación de subgrupos (una ancla):** en columnas no principales, un subgrupo conectado se mueve **como bloque** hacia **una sola ancla** (la más cercana a la principal). Se conserva el spacing interno; no hay segmentación dentro del subgrupo.
17. **Alineación de subgrupos (múltiples anclas):** si un subgrupo tiene **más de un nodo conectado** a la misma columna, **cada nodo anclado se alinea** a su respectiva ancla.  
   - Los nodos **entre anclas** se redistribuyen **entre esos dos puntos**.  
   - Los nodos **por encima** de la primera ancla y **por debajo** de la última se desplazan con la **ancla más cercana**.  
   - Si no hay espacio suficiente, se **comprime** el spacing interno sin romper las anclas.
18. **Restricción de tope:** nodos no conectados no deben quedar por encima del tope de la principal.
19. **Inferencia de principal:** si falta, se elige la columna con **mayor altura de subgrupo**.
20. **Adyacencia de flujo en columna:** cualquier conexión no‑mask (incluye A/B) mantiene los nodos en el mismo subgrupo.
21. **Selección de una sola columna:** la principal se distribuye como cualquier columna (sin excepción).
22. **Anclas en principal no se fijan:** columnas externas se realinean a la principal tras su redistribución.

## Decisiones del usuario (2026-02-06)
1. Descubrimiento de columnas + selección de principal: **aplicar** (via `auto_columns`).
2. Subgrupo con una sola ancla: **aplicar**.
3. Lógica de columnas potencial/next: **eliminar** (las externas no restringen internas).
4. Top constraint para no conectados: **aplicar**.
5. Heurística de X (más común primero): **aplicar**.
6. Filtrado Nuke (Backdrop/Viewer): **aplicar en Nuke**.
7. Logging: **aplicar** (debugPy_arrangeNodes.log, decisiones clave).
8. Principal top/bottom fijos: **aplicar**.
9. No fijar anclas en principal: **aplicar**.

## Pendiente / Abierto
- **Distribución por conectividad (NU):** decidir si derivar orden por conectividad en lugar de orden vertical.
- **Propagación recursiva de conflictos:** confirmar si debemos propagar ajustes más allá de la principal.
