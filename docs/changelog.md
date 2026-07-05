v2.59
- Se agrega documentacion de uso en `tools/capture_nuke_dag.md` con requisitos MCP broker, comandos, salidas y flujo before/after para comparar `lga_arrange`.
[ Capture DAG MCP - Documentacion de uso ]

- Se agrega `tools/capture_nuke_dag.py` para capturar el DAG de Nuke via MCP broker (`get_script_info` + `execute_python`) y guardar un snapshot JSON con nodos, atributos visuales e inputs.
- Se agrega render visual reutilizable a PNG/SVG calibrado con geometria de Node Graph para comparar estado before/after de `lga_arrange`.
[ Capture DAG MCP - JSON y PNG ]

v2.58
