# Plan de migración Nuke 15 → Nuke 16 (PySide2 → PySide6)

## Estrategia
- Usar una capa de compatibilidad de imports (helper propio o `qtpy`) con fallback PySide6 → PySide2.
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
- [ ] `scale_widget.py`
- [ ] `distributeNodes.py`
- [ ] `dag.py`
- [ ] `LGA_zoom.py`
- [ ] `LGA_selectNodes.py.panel`
- [ ] `LGA_scriptChecker.py`
- [ ] `LGA_middleClick.py`
- [ ] `Km_NodeGraphEN/PysideImport.py`
- [ ] `Km_NodeGraphEN/Km_NodeGraph_Easy_Navigate.py`

## Pasos sugeridos
1) Crear helper `qt_compat.py` (o usar `qtpy`) que exporte `QtWidgets`, `QtGui`, `QtCore`, `QAction`, `QGuiApplication`, `PYSIDE_VER`.
2) Cambiar imports en todos los scripts de la lista para usar el helper.
3) Reemplazar `QDesktopWidget` por `QGuiApplication.primaryScreen().geometry()/availableGeometry()`.
4) Sustituir `QtOpenGL.QGLWidget` en `scale_widget.py`; si no se usa GL real, eliminar dependencia y usar DAG como QWidget.
5) Asegurar `QAction` se importe desde `QtGui` en PySide6.
6) Si aparece audio con `QSound`, migrar a `QMediaPlayer + QAudioOutput`.
7) Probar manualmente en Nuke 15 y 16 apertura de paneles, backdrops, zoom middle-click, selectNodes, Km NodeGraph, captura/render de DAG.

## Cambios aplicados hasta ahora
- `qt_compat.py` agregado: fallback PySide6 → PySide2.
- `LGA_StickyNote.py` actualizado a v1.92: usa `qt_compat`, tooltips ahora se cierran al cerrar/OK/Cancel, debug apagado por defecto, auto-run comentado.
- `LGA_NodeLabel.py` actualizado a v0.83: usa `qt_compat`, tooltips con parent y cierre garantizado en OK/Cancel/cierre de ventana, namespace/version bumped.
- `LGA_StickyNote_Utils.py` actualizado a v1.01: usa `qt_compat` para PySide6/2 (sin fallback legacy).
- `LGA_backdrop.py` actualizado a v0.81: usa `qt_compat`, tooltips con parent/cierre asegurado en OK/Cancel/closeEvent, `QDesktopWidget` reemplazado por `QGuiApplication.primaryScreen().availableGeometry()`, namespace/version bumped.
- `LGA_BD_knobs.py` actualizado a imports `qt_compat`.
- `LGA_BD_fit.py` actualizado a imports `qt_compat` (QFont/QFontMetrics).
- `LGA_BD_callbacks.py` ajusta callback inline para probar PySide6 y luego PySide2 en QFont/QFontMetrics.

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

