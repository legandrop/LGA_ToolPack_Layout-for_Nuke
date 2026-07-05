v2.59
- Se mejora la fidelidad del render en `tools/capture_nuke_dag.py`: colores reales por clase usando `defaultNodeColor`, flechas direccionales visibles en conexiones (incluyendo horizontales) y eliminacion de marcadores intermedios que desplazaban visualmente los dots.
- Se realizan comprobaciones visuales manuales con recortes comparativos contra capturas reales del DAG para validar geometria y orden de flujo.
[ DAG Render - Colores, flechas y dots ]

- Se corrige `tools/capture_nuke_dag.py` para no dibujar inputs desconectados, capturar solo el DAG top-level visible y clasificar mejor conexiones de mask (evitando trazos amarillos incorrectos en conexiones horizontales).
- Se endurece la captura MCP reduciendo riesgo de cuelgue en Nuke (sin evaluar labels en Nuke y timeout mas corto en `execute_python`).
- Se agrega `tools/compare_nuke_dag.py` con comparacion automatica before/after (captura pair, reporte JSON y PNG comparativa).
- Se actualiza `tools/capture_nuke_dag.md` incorporando el flujo del nuevo comparador automatico.
[ DAG Compare - Fix render y comparador ]

- Se agrega documentacion de uso en `tools/capture_nuke_dag.md` con requisitos MCP broker, comandos, salidas y flujo before/after para comparar `lga_arrange`.
[ Capture DAG MCP - Documentacion de uso ]

- Se agrega `tools/capture_nuke_dag.py` para capturar el DAG de Nuke via MCP broker (`get_script_info` + `execute_python`) y guardar un snapshot JSON con nodos, atributos visuales e inputs.
- Se agrega render visual reutilizable a PNG/SVG calibrado con geometria de Node Graph para comparar estado before/after de `lga_arrange`.
[ Capture DAG MCP - JSON y PNG ]

v2.58
