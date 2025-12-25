# Plan de migración Nuke 15 → Nuke 16 (PySide2 → PySide6)

## Estrategia
- Usar capa de compatibilidad de imports (`qt_compat.py`) con funciones helper avanzadas y fallback PySide6 → PySide2.
- Funciones helper automatizan cambios de API Qt5/Qt6: `horizontal_advance()`, `primary_screen_geometry()`, `set_layout_margin()`.
- Reemplazar APIs Qt5 deprecadas: `QDesktopWidget`, `QtOpenGL.QGLWidget`, `QAction` en `QtWidgets`, enums de `QSizePolicy` en instancias, `QSound`.
- Ajustar accesos a DAG: ya es `QWidget`, no OpenGL; usar `objectName` y `render()`.
- Mantener compatibilidad con Nuke 15 mediante try/except o helper único.

## Checklist de archivos a actualizar
- [x] `LGA_StickyNote.py`
 - [x] `LGA_NodeLabel.py`
- [x] `LGA_StickyNote_Utils.py`
- [x] `LGA_backdrop/LGA_backdrop.py`
 - [x] `LGA_backdrop/LGA_BD_knobs.py`
 - [x] `LGA_backdrop/LGA_BD_fit.py`
 - [x] `LGA_backdrop/LGA_BD_callbacks.py`
- [X] `oz_backdrop/oz_backdrop.py` ** ESTE NO SE HACE
- [X] `oz_backdrop/oz_encompassScript.py` ** ESTE NO SE HACE
 - [x] `scale_widget.py`
- [x] `distributeNodes.py`
- [x] `dag.py`
 - [x] `LGA_zoom.py` (v2.22)
- [x] `LGA_selectNodes.py.panel`
- [x] `LGA_scriptChecker.py`
- [x] `LGA_middleClick.py`
- [x] `Km_NodeGraphEN/PysideImport.py`
- [x] `Km_NodeGraphEN/Km_NodeGraph_Easy_Navigate.py`
 - [x] `scale_widget.py`
- [x] `distributeNodes.py`
- [x] `dag.py`
- [x] `LGA_zoom.py`
- [x] `LGA_selectNodes.py.panel`
- [x] `LGA_scriptChecker.py`
- [x] `LGA_middleClick.py`
- [x] `Km_NodeGraphEN/PysideImport.py`
- [x] `Km_NodeGraphEN/Km_NodeGraph_Easy_Navigate.py`

## Pasos sugeridos
1) `qt_compat.py` incluye funciones helper avanzadas (`horizontal_advance`, `primary_screen_geometry`, `set_layout_margin`) con fallback PySide6 → PySide2.
2) Cambiar imports en todos los scripts para usar `qt_compat` en lugar de imports directos de PySide.
3) Para geometría de pantalla usar `qt_compat.primary_screen_geometry(pos)` (maneja automáticamente QDesktopWidget vs QGuiApplication).
4) Para ancho de texto usar `qt_compat.horizontal_advance(metrics, text)` (compatible Qt5/Qt6 automáticamente).
5) Para márgenes de layout usar `qt_compat.set_layout_margin(layout, margin)` (compatible Qt5/Qt6 automáticamente).
6) Sustituir `QtOpenGL.QGLWidget` en `scale_widget.py`; si no se usa GL real, eliminar dependencia y usar DAG como QWidget.
7) Asegurar `QAction` se importe desde `QtGui` en PySide6 (ya manejado por qt_compat).
8) Si aparece audio con `QSound`, migrar a `QMediaPlayer + QAudioOutput`.
9) Probar manualmente en Nuke 15 y 16 apertura de paneles, backdrops, zoom middle-click, selectNodes, Km NodeGraph, captura/render de DAG.

## Cambios aplicados hasta ahora
- `qt_compat.py` incluye funciones helper avanzadas: `horizontal_advance()`, `primary_screen_geometry()`, `set_layout_margin()` con fallback PySide6 → PySide2.
- `LGA_StickyNote.py` actualizado a v1.92: usa `qt_compat`, tooltips ahora se cierran al cerrar/OK/Cancel, debug apagado por defecto, auto-run comentado.
- `LGA_NodeLabel.py` actualizado a v0.83: usa `qt_compat`, tooltips con parent y cierre garantizado en OK/Cancel/cierre de ventana, namespace/version bumped.
- `LGA_StickyNote_Utils.py` actualizado a v1.01: usa `qt_compat` para PySide6/2 (sin fallback legacy).
- `LGA_backdrop.py` actualizado a v0.81: usa `qt_compat`, tooltips con parent/cierre asegurado en OK/Cancel/closeEvent, `QDesktopWidget` reemplazado por `QGuiApplication.primaryScreen().availableGeometry()`, namespace/version bumped.
- `LGA_BD_knobs.py` actualizado a imports `qt_compat`.
- `LGA_BD_fit.py` actualizado a imports `qt_compat` (QFont/QFontMetrics).
- `LGA_BD_callbacks.py` ajusta callback inline para probar PySide6 y luego PySide2 en QFont/QFontMetrics.
- `scale_widget.py` usa `qt_compat`, DAG QWidget (sin QtOpenGL), reenvío wheel directo al DAG.
- `distributeNodes.py` y `dag.py` usan `qt_compat`.
- `LGA_zoom.py` usa `qt_compat` y alias para mantener la API original.
- `LGA_selectNodes.py.panel` usa `qt_compat`.
- `LGA_scriptChecker.py` usa `qt_compat`.
- `Km_NodeGraphEN/PysideImport.py` usa `qt_compat` y exporta nombres; `Km_NodeGraph_Easy_Navigate.py` usa `qt_compat` y reemplaza `QDesktopWidget` por `QGuiApplication.primaryScreen()`.

### Nota de problema y solución (LGA_backdrop import en Nuke)
- Síntoma: al iniciar Nuke, `ImportError: attempted relative import with no known parent package` y luego crasheo.
- Causa: Nuke carga módulos sin contexto de paquete; imports relativos fallan.
- Solución:
  1) Añadir `LGA_backdrop/__pycache__` limpio y asegurar `LGA_backdrop` en `sys.path`.
  2) Usar imports planos dentro de `LGA_backdrop.py` (`import LGA_BD_knobs`, etc.) y exponer `autoBackdrop` en `__init__.py`.
  3) En `position_window_relative_to_cursor`, reemplazar `availableGeometry(cursor_pos)` por `screenAt(cursor_pos) or primaryScreen()` y `availableGeometry()` sin argumentos (Qt6).

### Notas sobre tooltips persistentes (NodeLabel/StickyNote)
- Problema: tooltips de botones OK/Cancel quedaban flotando tras cerrar/OK/Cancel.
- Solución aplicada:
  - Crear tooltip como `QLabel` con `parent=self`, flags `Qt.Tool | FramelessWindowHint | WindowStaysOnTopHint`, `WA_DeleteOnClose`, `WA_ShowWithoutActivating`.
  - Conectar `destroyed` del diálogo a `hide_custom_tooltip_*`.
  - Llamar a `hide_custom_tooltip_*` en OK/Cancel/closeEvent.
  - En `hide_custom_tooltip_*`, llamar a `close()`, `deleteLater()`, `QToolTip.hideText()` y `QApplication.processEvents(...)` para forzar cierre visual.

## Cómo cargar el ToolPack en Nuke
```python
import nuke
nuke.pluginAddPath("/Users/leg4/.nuke/LGA_ToolPack-Layout")
```

