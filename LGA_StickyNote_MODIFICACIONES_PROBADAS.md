# LGA_StickyNote - Modificaciones Probadas para Solucionar Cuelgues de Nuke

## Problema Identificado
- El script LGA_StickyNote causa cuelgues frecuentes en Nuke
- También hay interferencia con otros scripts como `scale_widget.py`
- Error específico en scale_widget: `AttributeError: __enter__` en context managers

## Modificaciones Probadas (EN ORDEN CRONOLÓGICO)

### 1. **PRIMERA CORRECCIÓN: Sistema de Debouncing (NO FUNCIONÓ)**
**Fecha**: Primera implementación
**Descripción**: Implementamos un sistema de debouncing con QTimer para evitar escritura excesiva
**Cambios realizados**:
- Agregado `DEBOUNCE_DELAY = 150` milisegundos
- Creado `self.update_timer = QtCore.QTimer()`
- Método `_delayed_text_update()` para escritura retrasada
- `self._pending_update` flag para controlar actualizaciones

**Código implementado**:
```python
# Sistema de debouncing para evitar loops de escritura
self.update_timer = QtCore.QTimer()
self.update_timer.setSingleShot(True)
self.update_timer.timeout.connect(self._delayed_text_update)
self._pending_update = False

def on_text_changed(self):
    if not self._pending_update:
        self._pending_update = True
        self.update_timer.start(DEBOUNCE_DELAY)

def _delayed_text_update(self):
    self._pending_update = False
    if self.sticky_node:
        # ... actualizar texto
```

**Resultado**: NO FUNCIONÓ - Seguían los cuelgues

---

### 2. **SEGUNDA CORRECCIÓN: Desconexión Explícita de Señales (NO FUNCIONÓ)**
**Fecha**: Segunda implementación
**Descripción**: Agregamos desconexión explícita de todas las señales para evitar acumulación

**Cambios realizados**:
- Método `_disconnect_all_signals()` mejorado
- Desconexión antes de crear nuevas conexiones en `setup_connections()`

**Código implementado**:
```python
def setup_connections(self):
    # Desconectar conexiones previas para evitar acumulación
    self._disconnect_all_signals()
    
    self.text_edit.textChanged.connect(self.on_text_changed)
    # ... otras conexiones

def _disconnect_all_signals(self):
    try:
        self.text_edit.textChanged.disconnect()
    except:
        pass
    # ... otras desconexiones
```

**Resultado**: NO FUNCIONÓ - Persistían los cuelgues

---

### 3. **TERCERA CORRECCIÓN: Throttling en Callbacks (NO FUNCIONÓ)**
**Fecha**: Tercera implementación
**Descripción**: Aplicamos throttling a los callbacks de font size y margins

**Cambios realizados**:
- Los callbacks de sliders ahora usan el sistema de debouncing
- Evitar llamadas directas a `on_text_changed()`

**Código implementado**:
```python
def on_font_size_changed(self, value):
    if self.sticky_node:
        self.sticky_node["note_font_size"].setValue(value)
        self.font_size_value.setText(str(value))
        # Sin llamada directa a on_text_changed()

def on_margin_changed(self, value):
    if self.sticky_node:
        self.margin_value.setText(str(value))
        # Usar debouncing en lugar de llamada directa
        if not self._pending_update:
            self._pending_update = True
            self.update_timer.start(DEBOUNCE_DELAY)
```

**Resultado**: NO FUNCIONÓ - Continuaron los cuelgues

---

### 4. **CUARTA CORRECCIÓN: Gestión Mejorada de Memoria (NO FUNCIONÓ)**
**Fecha**: Cuarta implementación  
**Descripción**: Mejoramos la limpieza de recursos y gestión de memoria

**Cambios realizados**:
- Método `_cleanup_resources()` más robusto
- Limpieza automática en `closeEvent()`
- Mejor gestión de la función global `run_sticky_note_editor()`

**Código implementado**:
```python
def _cleanup_resources(self):
    try:
        if hasattr(self, "update_timer"):
            self.update_timer.stop()
            self.update_timer.timeout.disconnect()
        self._disconnect_all_signals()
        self.sticky_node = None
        self._pending_update = False
        # ... más limpieza
    except Exception as e:
        print(f"Error durante la limpieza: {e}")

def closeEvent(self, event):
    self._cleanup_resources()
    super().closeEvent(event)

def run_sticky_note_editor():
    global sticky_editor
    if sticky_editor is not None:
        try:
            if hasattr(sticky_editor, "_cleanup_resources"):
                sticky_editor._cleanup_resources()
            sticky_editor.close()
            sticky_editor.deleteLater()
            QtWidgets.QApplication.processEvents()
        except Exception as e:
            print(f"Error limpiando instancia anterior: {e}")
        finally:
            sticky_editor = None
    # ... crear nueva instancia
```

**Resultado**: NO FUNCIONÓ - Los cuelgues persistieron

---

### 5. **QUINTA CORRECCIÓN: Solución de Interferencia con scale_widget.py (PARCIAL)**
**Fecha**: Quinta implementación
**Descripción**: Corregimos el error `AttributeError: __enter__` en scale_widget.py

**Problema identificado**:
```
AttributeError: __enter__ 
File "scale_widget.py", line 327, in __init__
    with self.dag_node:
```

**Cambios realizados**:
- Reemplazamos `with self.dag_node:` por verificaciones de context apropiadas
- Agregamos verificaciones `hasattr(self.dag_node, 'begin')`

**Código implementado**:
```python
# En lugar de: with self.dag_node:
if self.dag_node and hasattr(self.dag_node, 'begin'):
    self.dag_node.begin()
    try:
        self.nodes = nuke.selectedNodes()
    finally:
        self.dag_node.end()
else:
    self.nodes = nuke.selectedNodes()
```

**Resultado**: PARCIAL - Corrigió el error específico de scale_widget pero no los cuelgues de StickyNote

---

### 6. **SEXTA CORRECCIÓN: Variables Globales Únicas (NO FUNCIONÓ)**
**Fecha**: Sexta implementación
**Descripción**: Cambiamos nombres de variables globales para evitar conflictos

**Cambios realizados**:
- `sticky_editor` → `lga_sticky_note_editor_instance`
- Agregado namespace único: `LGA_STICKY_NOTE_NAMESPACE = "LGA_StickyNote_v190"`
- Detección y cierre de widgets conflictivos

**Código implementado**:
```python
# Variables globales con nombres únicos para evitar conflictos
lga_sticky_note_editor_instance = None
LGA_STICKY_NOTE_NAMESPACE = "LGA_StickyNote_v190"

def run_sticky_note_editor():
    global lga_sticky_note_editor_instance
    
    # Verificar widgets conflictivos
    app_instance = QtWidgets.QApplication.instance()
    if app_instance:
        conflicting_widgets = []
        for widget in app_instance.allWidgets():
            widget_name = widget.__class__.__name__
            if widget_name in ['ScaleWidget', 'NodeLabelEditor'] and widget.isVisible():
                conflicting_widgets.append(widget_name)
        
        if conflicting_widgets:
            print(f"Cerrando widgets conflictivos: {conflicting_widgets}")
            # ... cerrar widgets
```

**Resultado**: NO FUNCIONÓ - Siguieron los cuelgues

---

### 7. **SÉPTIMA CORRECCIÓN: Limpieza Mejorada de Señales (NO FUNCIONÓ)**
**Fecha**: Séptima implementación
**Descripción**: Mejoramos la desconexión de señales con verificaciones más robustas

**Cambios realizados**:
- Verificación de `signal.receivers() > 0` antes de desconectar
- Manejo de excepciones `RuntimeError, TypeError, AttributeError`
- Limpieza más segura del timer

**Código implementado**:
```python
def _disconnect_all_signals(self):
    signals_to_disconnect = [
        (self.text_edit, 'textChanged'),
        (self.font_size_slider, 'valueChanged'),
        # ... más señales
    ]
    
    for widget, signal_name in signals_to_disconnect:
        try:
            if hasattr(widget, signal_name):
                signal = getattr(widget, signal_name)
                if signal.receivers() > 0:
                    signal.disconnect()
        except (RuntimeError, TypeError, AttributeError):
            pass

def _cleanup_resources(self):
    try:
        if hasattr(self, "update_timer") and self.update_timer:
            self.update_timer.stop()
            try:
                if self.update_timer.receivers(self.update_timer.timeout) > 0:
                    self.update_timer.timeout.disconnect()
            except (RuntimeError, TypeError):
                pass
        # ... más limpieza
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
```

**Resultado**: NO FUNCIONÓ - Error: "Failed to disconnect signal timeout()"

---

### 8. **OCTAVA CORRECCIÓN: ELIMINACIÓN COMPLETA DEL DEBOUNCING (NO FUNCIONÓ)**
**Fecha**: Implementación más reciente
**Descripción**: Eliminamos completamente el sistema de debouncing y volvimos a escritura inmediata

**Cambios realizados**:
- Comentado/eliminado todo el sistema de `QTimer`
- `on_text_changed()` ahora escribe inmediatamente al label
- Eliminadas todas las referencias a `self._pending_update`
- Eliminado método `_delayed_text_update()`

**Código implementado**:
```python
class StickyNoteEditor(QtWidgets.QDialog):
    def __init__(self):
        # DESHABILITAR COMPLETAMENTE EL SISTEMA DE DEBOUNCING
        # self.update_timer = QtCore.QTimer()
        # self.update_timer.setSingleShot(True)
        # self.update_timer.timeout.connect(self._delayed_text_update)
        # self._pending_update = False

def on_text_changed(self):
    """ESCRITURA INMEDIATA SIN DEBOUNCING"""
    if self.sticky_node:
        current_text = self.text_edit.toPlainText()
        margin_x = self.margin_slider.value()
        margin_y = self.margin_y_slider.value()
        final_text = format_text_with_margins(current_text, margin_x, margin_y)
        self.sticky_node["label"].setValue(final_text)

def on_margin_changed(self, value):
    """ESCRITURA INMEDIATA"""
    if self.sticky_node:
        self.margin_value.setText(str(value))
        self.on_text_changed()  # Llamada directa inmediata

# MÉTODO ELIMINADO
# def _delayed_text_update(self):

def _cleanup_resources(self):
    # YA NO HAY TIMER QUE LIMPIAR
    # if hasattr(self, "update_timer"):
    #     self.update_timer.stop()
```

**Resultado**: NO FUNCIONÓ - Los cuelgues persisten

---

## ESTADO ACTUAL

**Problema**: Todas las modificaciones probadas hasta el momento NO han solucionado los cuelgues de Nuke.

**Hipótesis restantes**:
1. El problema podría estar en `LGA_StickyNote_Utils.py`
2. Podría ser un problema de threading o eventos de Qt
3. Podría haber un loop infinito en alguna otra parte del código
4. Interferencia con otros scripts del sistema
5. Problema con la gestión de nodos de Nuke en tiempo real

**Próximos pasos sugeridos**:
- Revisar `LGA_StickyNote_Utils.py` en detalle
- Implementar logging detallado para identificar dónde ocurre el cuelgue
- Probar una versión mínima del script sin funcionalidades complejas
- Investigar si el problema está en la escritura al nodo o en la interfaz Qt

---

**Archivo creado**: `LGA_StickyNote_MODIFICACIONES_PROBADAS.md`  
**Fecha de última actualización**: Enero 2025 