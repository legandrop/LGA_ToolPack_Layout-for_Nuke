# ChangeLog

## v2.61
- El `install.pdf` se reemplaza por `install_es.pdf` e `install_en.pdf`. La hoja vieja salia de exportar un Google Doc a mano y quedo congelada en el metodo manual: no menciona los instaladores que el ZIP trae desde hace varias versiones, y ademas daba el backup del `init.py` como `init.py.bak`, un nombre que los motores ya no usan: hoy guardan una copia numerada en `~/.nuke/LGA_init_backups/`. Las dos hojas se generan ahora desde una plantilla unica en el repo de release, con la version leida del `VERSION` del repo, asi que el texto comun deja de mantenerse por separado en cada producto. Se documenta tambien que en macOS el instalador va con `bash installer_mac.sh`: los `.sh` pierden el permiso de ejecucion dentro del `.zip` y `./installer_mac.sh` da `Permission denied`. [ Layout - Reemplazar install.pdf por las hojas en castellano e ingles ]

## v2.60
- El instalador dejaba el `init.py` roto en cualquier equipo que tuviera sus `pluginAddPath` adentro de un bloque `if` —por ejemplo para discriminar por version de Nuke— y ademas reportaba exito. Al reordenar los paths se llevaba tambien las lineas indentadas, dejando el bloque sin cuerpo, y Nuke no arrancaba con un `IndentationError`. Ahora solo toca las lineas en columna 0 y respeta las indentadas donde estan. Suma ademas deduplicacion de paths repetidos, preservacion del BOM del archivo original y una validacion del resultado: si el `init.py` quedaria invalido, no lo modifica y aborta la instalacion. [ Layout - Corregir el manejo del init.py del instalador ]

## v2.59
- Se corrigen los comandos de menú que fallaban con `NameError` (`LGA_backdrop`, `LGA_backdropReplacer`, dots after, select/align/distribute/arrange nodes, scale, push/pull y Easy Navigate). Al mover la implementación de `menu.py` a `LGA_ToolPackLayout_menu.py`, los imports pasaron a vivir en el namespace del módulo, pero Nuke evalúa los comandos pasados como string dentro de `__main__`, donde esos nombres ya no existían. Se agrega el helper `_export_to_main()` y se publica ahí cada módulo usado por un comando string. Los comandos registrados como callable (`add_tool`) nunca estuvieron afectados. [ Layout ToolPack - Reparar comandos de menu tras mover la implementacion ]

- El instalador ordena `~/.nuke/init.py` de forma canónica en Windows y macOS: recolecta todos los bloques `pluginAddPath` de LGA, los reordena según el orden oficial (Layout, ToolPack-B, ToolPack, NodePack, OpenInNukeX, Defaults, CollectedTools), elimina duplicados y deja intactos los paths ajenos. Antes cada plataforma resolvía el orden de una manera distinta y macOS simplemente agregaba al final. [ Layout ToolPack - Unificar el orden del init.py ]

- Se agregan instaladores transaccionales para Windows y macOS, con validación del payload, backup de la carpeta previa, actualización idempotente de `init.py` y restauración ante fallos. Los generadores de release incluyen ambos instaladores y aplican exclusiones seguras aunque no exista un `+exclude.lst` local. [ Layout ToolPack - Agregar instaladores multiplataforma ]

- El `menu.py` del pack se convierte en un wrapper mínimo que detecta los flags oficiales de Hiero y Nuke Studio antes de importar la implementación completa desde `LGA_ToolPackLayout_menu.py`. El pack mantiene una instalación simple mediante `pluginAddPath`, pero deja de crear paths, imports o menús dentro de los hosts de timeline. [ Layout ToolPack - Evitar carga en Hiero y Nuke Studio ]

- Se incorpora `VERSION` como fuente única de la versión publicada y el menú obtiene desde allí su label de documentación. Se normaliza el nombre del changelog, se agregan reglas de desarrollo espejadas y se reserva el bump real para el generador manual de `LGA_Release`. [ Layout ToolPack - Unificar reglas, changelog y versión publicada ]

- Se cambia `LGA_backdrop` para no serializar el callback pesado en el `knobChanged` de cada BackdropNode: ahora usa un callback runtime global filtrado por knobs LGA, con debounce para el autofit automatico del `margin_slider`.
- Se actualiza `LGA_backdropReplacer.py` para regenerar backdrops sin callback legacy embebido, preservando label formateado, font, margin, z-order, estilo visual y nombre cuando sea posible.
- Se agrega `docs/LGA_backdrop_callbacks_runtime.md` con notas de portabilidad y migracion de scripts viejos.
[ LGA Backdrop - Callbacks runtime portables ]

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

## v2.58
