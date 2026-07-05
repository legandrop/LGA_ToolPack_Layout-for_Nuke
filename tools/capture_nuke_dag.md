# capture_nuke_dag.py

Herramienta para capturar el DAG actual de Nuke via MCP broker y generar un snapshot reutilizable para revisar layouts antes/despues de ejecutar scripts como `lga_arrange`.

## Requisitos

- Nuke abierto con el addon MCP activo en `127.0.0.1:54321`.
- Broker MCP de Nuke configurado en `C:\Portable\LGA_NukeMCP`.
- Python disponible desde el entorno donde se ejecuta la repo.

El script usa por defecto este launcher MCP:

```text
C:\Portable\LGA_NukeMCP\scripts\mcp\start_kleer_broker.ps1
```

No se conecta directo a `nukemcp.server`; el flujo esperado es:

```text
capture_nuke_dag.py -> broker MCP -> addon Nuke localhost:54321
```

## Uso basico

Desde la raiz del repo:

```powershell
python tools\capture_nuke_dag.py
```

Salidas por defecto:

```text
tools\output\dag_snapshot.json
tools\output\dag_snapshot.png
tools\output\dag_snapshot.svg
```

## Opciones

```powershell
python tools\capture_nuke_dag.py --output-dir tools\output\before
python tools\capture_nuke_dag.py --json-path tools\output\dag.json --png-path tools\output\dag.png
python tools\capture_nuke_dag.py --no-svg
python tools\capture_nuke_dag.py --scale 1.5 --padding 100
```

Opciones disponibles:

- `--output-dir`: carpeta base de salida. Default: `tools\output`.
- `--json-path`: ruta exacta para el JSON.
- `--png-path`: ruta exacta para el PNG.
- `--svg-path`: ruta exacta para el SVG.
- `--no-svg`: no genera SVG.
- `--scale`: escala visual del render. Default: `1.0`.
- `--padding`: margen alrededor del DAG renderizado. Default: `70`.
- `--broker-command`: comando completo alternativo para lanzar el MCP stdio.
- `--check-host`: host usado para validar el addon. Default: `127.0.0.1`.
- `--check-port`: puerto usado para validar el addon. Default: `54321`.

## Flujo before/after para lga_arrange

1. Capturar el estado inicial:

```powershell
python tools\capture_nuke_dag.py --output-dir tools\output\before
```

2. Ejecutar `lga_arrange` en Nuke.

3. Capturar el estado posterior:

```powershell
python tools\capture_nuke_dag.py --output-dir tools\output\after
```

4. Comparar:

- `tools\output\before\dag_snapshot.json`
- `tools\output\after\dag_snapshot.json`
- `tools\output\before\dag_snapshot.png`
- `tools\output\after\dag_snapshot.png`

El JSON es la fuente precisa para medir cambios de coordenadas, nodos y conexiones. El PNG/SVG sirve para revisar visualmente si el layout conserva proporciones, distancias relativas y conexiones.

## Datos capturados

El JSON incluye:

- informacion del script (`script_info`);
- lista de tools MCP disponibles;
- nodos con `name`, `class`, `xpos`, `ypos`, `screenWidth`, `screenHeight`, `tile_color`, `selected`, labels y knobs visuales relevantes;
- conexiones normalizadas en `edges`;
- conteos `node_count` y `edge_count`.

## Notas

- `execute_python` se ejecuta con `confirm=True` dentro del MCP.
- El render intenta aproximarse al Node Graph real de Nuke, pero la comparacion exacta debe hacerse con el JSON.
- Si Nuke queda ocupado o colgado, el broker puede reportar timeouts aunque el script este bien formado.
