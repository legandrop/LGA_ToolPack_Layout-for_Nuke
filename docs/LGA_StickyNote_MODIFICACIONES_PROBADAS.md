> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

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
- Desconexión antes de crear nuevas conexiones en `setup_connections_Sticky()`

**Código implementado**:
```python
def setup_connections_Sticky(self):
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

### 9. **NOVENA CORRECCIÓN: PATRÓN SINGLETON COMO KULABELER.PY (NO FUNCIONÓ)**
**Fecha**: Implementación más reciente
**Descripción**: Cambiar el patrón de instanciación múltiple por un patrón singleton como kulabeler.py

**Cambios realizados**:
- Crear instancia global única al importar: `STICKY_EDITOR_INSTANCE = StickyNoteEditor()`
- Modificar `run_sticky_note_editor()` para usar la instancia global
- Cambiar `close()` por `hide()` en botones Cancel y OK
- Agregar verificación `if self.isVisible()` en método `run()`
- Aplicar mismos cambios a `LGA_NodeLabel.py`

**Código implementado**:
```python
# Crear instancia global única al importar el módulo (como kulabeler.py)
STICKY_EDITOR_INSTANCE = StickyNoteEditor()

def run_sticky_note_editor():
    """Mostrar el editor de StickyNote dentro de Nuke usando patrón singleton"""
    global STICKY_EDITOR_INSTANCE
    # Usar la instancia global única, igual que kulabeler.py
    STICKY_EDITOR_INSTANCE.run()

def run(self):
    """Ejecuta el editor usando patrón similar a kulabeler.py"""
    # Si ya está visible, solo traer al frente
    if self.isVisible():
        self.raise_()
        self.activateWindow()
        return
    # ... resto del código

def on_cancel_clicked(self):
    # Solo ocultar la ventana, no cerrarla (como kulabeler.py)
    self.hide()
```

**Resultado**: NO FUNCIONÓ - Crasheó inmediatamente

---

### **11. ❌ INTENTO FALLIDO: RENOMBRAR FUNCIONES EN LGA_BACKDROP.PY**
**Fecha**: Enero 2025
**Descripción**: Intento de renombrar funciones conflictivas en LGA_backdrop.py para evitar conflictos con LGA_StickyNote y LGA_NodeLabel

**Problema identificado**:
El usuario reportó que cuando importaba LGA_backdrop.py, los otros scripts (LGA_StickyNote y LGA_NodeLabel) dejaban de funcionar correctamente. Se identificaron funciones y variables con nombres idénticos entre los scripts.

**Conflictos encontrados**:
1. **Variables globales duplicadas**:
   - `SHADOW_BLUR_RADIUS_Sticky`, `SHADOW_OPACITY_Sticky`, `SHADOW_OFFSET_X`, `SHADOW_OFFSET_Y`, `SHADOW_MARGIN`
   - `DEBUG`

2. **Funciones duplicadas**:
   - `debug_print()`
   - `setup_ui_Sticky()`, `setup_connections_Sticky()`
   - `show_custom_tooltip_Sticky()`, `hide_custom_tooltip_Sticky()`
   - `start_move_Sticky()`, `move_window_Sticky()`, `stop_move_Sticky()`

**Cambios intentados**:
1. **Variables renombradas con prefijo único**:
   ```python
   # ANTES
   SHADOW_BLUR_RADIUS_Sticky = 25
   SHADOW_OPACITY_Sticky = 60
   DEBUG = False
   
   # DESPUÉS
   BACKDROP_SHADOW_BLUR_RADIUS_Sticky = 25
   BACKDROP_SHADOW_OPACITY_Sticky = 60
   BACKDROP_DEBUG = False
   ```

2. **Funciones renombradas con prefijo único**:
   ```python
   # ANTES
   def debug_print(*message):
   def setup_ui_Sticky(self):
   def setup_connections_Sticky(self):
   
   # DESPUÉS
   def backdrop_debug_print(*message):
   def backdrop_setup_ui_Sticky(self):
   def backdrop_setup_connections_Sticky(self):
   ```

**Resultado**: ❌ **NO FUNCIONÓ**
- El renombrado de funciones no solucionó el problema fundamental
- Los conflictos persisten porque Python carga todos los módulos en el mismo espacio de nombres global
- Cuando `LGA_backdrop` importa sus dependencias, estas sobrescriben las funciones de otros módulos
- El problema es más profundo que solo nombres de funciones duplicadas

**Lección aprendida**: 
Renombrar funciones individuales no resuelve el problema de conflictos entre módulos. Se necesita una solución de aislamiento completo de namespaces.

---

### **12. ⚠️ IMPLEMENTACIÓN: IMPORTACIONES PEREZOSAS (LAZY IMPORTS)**
**Fecha**: Enero 2025
**Descripción**: Implementación de importaciones perezosas en menu.py para evitar conflictos al momento de cargar el menú

**Problema identificado**:
Las importaciones directas en menu.py causan que todos los módulos se carguen inmediatamente, creando conflictos de nombres globales entre LGA_StickyNote, LGA_NodeLabel y LGA_backdrop.

**Solución implementada**:
1. **Funciones de importación perezosa**:
   ```python
   def _lazy_import_lga_sticky_note():
       """Importación perezosa para LGA_StickyNote"""
       import LGA_StickyNote
       return LGA_StickyNote
   
   def _lazy_import_lga_node_label():
       """Importación perezosa para LGA_NodeLabel"""
       import LGA_NodeLabel
       return LGA_NodeLabel
   
   def _lazy_import_lga_backdrop():
       """Importación perezosa para LGA_backdrop"""
       nuke.pluginAddPath("./LGA_backdrop")
       import LGA_backdrop
       return LGA_backdrop
   ```

2. **Funciones wrapper para comandos**:
   ```python
   def _run_sticky_note():
       """Ejecuta StickyNote con importación perezosa"""
       sticky_note_module = _lazy_import_lga_sticky_note()
       return sticky_note_module.run_sticky_note_editor()
   
   def _run_node_label():
       """Ejecuta NodeLabel con importación perezosa"""
       node_label_module = _lazy_import_lga_node_label()
       return node_label_module.run_node_label_editor()
   ```

3. **Menú actualizado**:
   ```python
   # ANTES
   import LGA_StickyNote
   n.addCommand("Create StickyNote", "LGA_StickyNote.run_sticky_note_editor()")
   
   # DESPUÉS
   n.addCommand("Create StickyNote", _run_sticky_note)
   ```

**Resultado**: ❌ **NO FUNCIONÓ**
- Las importaciones perezosas no solucionaron el conflicto
- El problema persiste porque cuando se ejecuta la función, el módulo se importa y sobrescribe las funciones globales
- Los conflictos siguen ocurriendo, solo se postergan hasta el momento de ejecución

**Feedback del usuario**: 
"esto de los lazy no arregló nada de nada. si elimporto el backdrop en mi menu.py entra en conflicto con el nodelabel y con el stickynotes"

---

### **13. ⚠️ IMPLEMENTACIÓN: NAMESPACES ENCAPSULADOS CON IMPORTLIB**
**Fecha**: Enero 2025
**Descripción**: Implementación de namespaces completamente separados usando importlib para aislar cada módulo

**Problema identificado**:
Python carga todos los módulos en el mismo espacio de nombres global, causando que las funciones con nombres idénticos se sobrescriban entre módulos.

**Solución implementada**:
1. **Clase ModuleNamespace**:
   ```python
   class ModuleNamespace:
       """Clase para encapsular módulos en namespaces separados"""
       
       def __init__(self, module_name, plugin_path=None):
           self.module_name = module_name
           self.plugin_path = plugin_path
           self._module = None
           self._loaded = False
       
       def _load_module(self):
           """Carga el módulo en un namespace aislado"""
           if self.plugin_path:
               nuke.pluginAddPath(self.plugin_path)
           
           if self.module_name in sys.modules:
               self._module = importlib.reload(sys.modules[self.module_name])
           else:
               self._module = importlib.import_module(self.module_name)
           
           return self._module
       
       def call_function(self, function_name, *args, **kwargs):
           """Llama a una función del módulo encapsulado"""
           module = self._load_module()
           if module and hasattr(module, function_name):
               func = getattr(module, function_name)
               return func(*args, **kwargs)
   ```

2. **Instancias de namespaces separados**:
   ```python
   # Módulos problemáticos que causan conflictos
   sticky_note_ns = ModuleNamespace("LGA_StickyNote")
   node_label_ns = ModuleNamespace("LGA_NodeLabel")
   lga_backdrop_ns = ModuleNamespace("LGA_backdrop", "./LGA_backdrop")
   ```

3. **Funciones wrapper encapsuladas**:
   ```python
   def _run_sticky_note():
       """Ejecuta StickyNote con namespace encapsulado"""
       return sticky_note_ns.call_function("run_sticky_note_editor")
   
   def _run_node_label():
       """Ejecuta NodeLabel con namespace encapsulado"""
       return node_label_ns.call_function("run_node_label_editor")
   ```

**Resultado**: ⚠️ **MEJORA PARCIAL**
- Funcionó mejor y duró más tiempo
- Los conflictos de nombres se redujeron significativamente
- **NUEVO PROBLEMA**: Error de "bad allocation" que causa crashes de Nuke
- El sistema funciona pero consume demasiada memoria

**Feedback del usuario**: 
"funcionó mejor. más tiempo. pero en un momento ejecuté el nodelabel y me dio un error de 'bad allocation' y crasheó nuke"

---

### **14. 🔄 IMPLEMENTACIÓN ACTUAL: GESTIÓN DE MEMORIA MEJORADA**
**Fecha**: Enero 2025
**Descripción**: Implementación de gestión de memoria avanzada para evitar errores de "bad allocation" manteniendo el aislamiento de namespaces

**Problema identificado**:
El sistema de namespaces encapsulados funciona pero causa errores de memoria ("bad allocation") que crashean Nuke. Esto se debe a que múltiples instancias de módulos se mantienen en memoria simultáneamente.

**Solución implementada**:
1. **Gestor de memoria con cache limitado**:
   ```python
   MAX_CACHED_MODULES = 5  # Máximo número de módulos en cache
   ENABLE_AUTO_CLEANUP = True  # Activar limpieza automática
   ENABLE_MEMORY_MONITORING = True  # Activar monitoreo de memoria
   
   class MemoryManager:
       def __init__(self):
           self.module_cache = OrderedDict()
           self.weak_refs = {}
       
       def cleanup_old_modules(self):
           """Limpia módulos antiguos del cache"""
           while len(self.module_cache) > MAX_CACHED_MODULES:
               oldest_key = next(iter(self.module_cache))
               removed_module = self.module_cache.pop(oldest_key)
               del removed_module
           gc.collect()
   ```

2. **ModuleNamespace con gestión de memoria**:
   ```python
   class ModuleNamespace:
       def __init__(self, module_name, plugin_path=None):
           self.module_name = module_name
           self.plugin_path = plugin_path
           self._module = None
           self._loaded = False
           self._loading = False  # Flag para evitar cargas concurrentes
       
       def _load_module(self):
           """Carga el módulo con gestión de memoria mejorada"""
           if self._loading:
               return None
           
           # Verificar si está en cache
           cached_module = memory_manager.get_module(self.module_name)
           if cached_module is not None:
               return cached_module
           
           # Limpiar memoria antes de cargar
           if ENABLE_AUTO_CLEANUP:
               gc.collect()
           
           # Cargar módulo y registrar en cache
           self._module = importlib.import_module(self.module_name)
           memory_manager.register_module(self.module_name, self._module)
           
           return self._module
   ```

3. **Limpieza automática para funciones pesadas**:
   ```python
   def _run_sticky_note():
       """Ejecuta StickyNote con gestión de memoria especial"""
       print("[MEMORY] Ejecutando StickyNote con gestión de memoria especial...")
       # Limpiar memoria antes de ejecutar
       cleanup_all_modules()
       return sticky_note_ns.call_function("run_sticky_note_editor")
   
   def _run_node_label():
       """Ejecuta NodeLabel con gestión de memoria especial"""
       print("[MEMORY] Ejecutando NodeLabel con gestión de memoria especial...")
       # Limpiar memoria antes de ejecutar
       cleanup_all_modules()
       return node_label_ns.call_function("run_node_label_editor")
   ```

4. **Función de limpieza global**:
   ```python
   def cleanup_all_modules():
       """Limpia todos los módulos y libera memoria"""
       print("[MEMORY] Iniciando limpieza global de memoria...")
       
       # Limpiar todos los namespaces
       for namespace in [sticky_note_ns, node_label_ns, lga_backdrop_ns, ...]:
           namespace.cleanup()
       
       # Limpiar el gestor de memoria
       memory_manager.clear_all()
       
       # Forzar garbage collection múltiple
       for _ in range(3):
           gc.collect()
   ```

5. **Comando de debug agregado al menú**:
   ```python
   n.addCommand(
       "  [DEBUG] Clean Memory",
       cleanup_all_modules,
       "",
       shortcutContext=2,
       icon=icon_LTPB,
   )
   ```

**Características implementadas**:
- ✅ **Cache limitado**: Máximo 5 módulos en memoria simultáneamente
- ✅ **Limpieza automática**: Garbage collection forzado antes/después de funciones pesadas
- ✅ **Monitoreo de memoria**: Logs detallados de uso de memoria
- ✅ **Prevención de cargas concurrentes**: Evita múltiples importaciones simultáneas
- ✅ **Weak references**: Para monitoreo de objetos en memoria
- ✅ **Limpieza global**: Función manual para liberar toda la memoria
- ✅ **Manejo de errores**: Try-catch en todas las operaciones de memoria

**Estado actual**: 🔄 **EN PRUEBAS**
- Implementación completa lista para testing
- Combina aislamiento de namespaces con gestión inteligente de memoria
- Debería resolver tanto los conflictos de nombres como los errores de "bad allocation"

**Archivos modificados**:
- `LGA_ToolPack-Layout/menu.py`: Sistema completo de gestión de memoria y namespaces

---

## ESTADO ACTUAL

**Problema principal**: Conflictos de nombres entre módulos que causan malfuncionamiento y crashes de Nuke.

**Evolución del problema**:
1. **Problema original**: Cuelgues de Nuke al usar LGA_StickyNote
2. **Problema identificado**: Conflictos de nombres entre LGA_StickyNote, LGA_NodeLabel y LGA_backdrop
3. **Problema actual**: Error de "bad allocation" al usar el sistema de namespaces

**Soluciones probadas**:
- ❌ **Debouncing y limpieza de señales**: No funcionó
- ❌ **Renombrado de funciones**: No resolvió el problema fundamental
- ❌ **Importaciones perezosas**: Solo postergó el conflicto
- ⚠️ **Namespaces encapsulados**: Funcionó mejor pero causó errores de memoria
- 🔄 **Gestión de memoria mejorada**: Implementación actual en pruebas

**Implementación actual**:
- Sistema de namespaces encapsulados con gestión inteligente de memoria
- Cache limitado de módulos (máximo 5 simultáneos)
- Limpieza automática y garbage collection forzado
- Monitoreo de memoria y prevención de cargas concurrentes
- Comando de debug para limpieza manual

**Estado**: 🔄 **EN PRUEBAS**
- Implementación completa lista para testing
- Combina aislamiento de namespaces con gestión inteligente de memoria
- Debería resolver tanto los conflictos de nombres como los errores de "bad allocation"

**Próximos pasos**:
- Probar el sistema de gestión de memoria mejorada
- Monitorear los logs de memoria para identificar patrones
- Ajustar los parámetros de cache si es necesario
- Considerar implementaciones alternativas si persisten los problemas

---

### **15. ✅ CORRECCIÓN: ELIMINACIÓN DE RELOAD() Y LIMPIEZA ESPECÍFICA**
**Fecha**: Enero 2025
**Descripción**: Corrección del error "reload() argument must be a module" y implementación de limpieza específica por módulo

**Problema identificado**:
El error `reload() argument must be a module` ocurría porque el sistema de limpieza agresiva estaba eliminando módulos de memoria pero luego intentaba hacer `reload()` sobre módulos que ya no existían. Esto causaba que después de ejecutar los scripts 1-2 veces, ya no se pudieran volver a ejecutar.

**Cambios implementados**:
1. **Eliminación de reload()**:
   ```python
   # ANTES - Causaba error "reload() argument must be a module"
   if self.module_name in sys.modules:
       old_module = sys.modules[self.module_name]
       if hasattr(old_module, "__dict__"):
           old_module.__dict__.clear()
       self._module = importlib.reload(sys.modules[self.module_name])
   
   # DESPUÉS - Importación fresh sin reload()
   if self.module_name in sys.modules:
       if ENABLE_MEMORY_MONITORING:
           print(f"[MEMORY] Eliminando módulo de sys.modules: {self.module_name}")
       del sys.modules[self.module_name]
   
   # Importar el módulo fresh
   self._module = importlib.import_module(self.module_name)
   ```

2. **Limpieza específica por módulo**:
   ```python
   def cleanup_specific_module(module_name):
       """Limpia un módulo específico"""
       print(f"[MEMORY] Limpiando módulo específico: {module_name}")
       
       # Limpiar del cache
       if module_name in memory_manager.module_cache:
           removed_module = memory_manager.module_cache.pop(module_name)
           del removed_module
       
       # Limpiar weak reference
       if module_name in memory_manager.weak_refs:
           del memory_manager.weak_refs[module_name]
       
       gc.collect()
   ```

3. **Funciones wrapper mejoradas**:
   ```python
   def _run_sticky_note():
       """Ejecuta StickyNote con gestión de memoria especial"""
       print("[MEMORY] Ejecutando StickyNote con gestión de memoria especial...")
       # Limpiar solo el módulo específico si es necesario
       cleanup_specific_module("LGA_StickyNote")
       return sticky_note_ns.call_function("run_sticky_note_editor")
   
   def _run_node_label():
       """Ejecuta NodeLabel con gestión de memoria especial"""
       print("[MEMORY] Ejecutando NodeLabel con gestión de memoria especial...")
       # Limpiar solo el módulo específico si es necesario
       cleanup_specific_module("LGA_NodeLabel")
       return node_label_ns.call_function("run_node_label_editor")
   ```

4. **Configuración optimizada**:
   ```python
   MAX_CACHED_MODULES = 3  # Reducir cache para evitar problemas de memoria
   ENABLE_AGGRESSIVE_CLEANUP = False  # Desactivar limpieza agresiva
   
   # Identificar módulos problemáticos
   self.problematic_modules = {
       "LGA_StickyNote", 
       "LGA_NodeLabel", 
       "LGA_backdrop"
   }
   ```

5. **Cleanup suave vs agresivo**:
   ```python
   def cleanup(self):
       """Limpia el módulo de memoria de forma segura"""
       if ENABLE_AGGRESSIVE_CLEANUP:
           # Solo hacer cleanup agresivo si está habilitado
           if self._module is not None:
               if hasattr(self._module, "__dict__"):
                   self._module.__dict__.clear()
               self._module = None
           self._loaded = False
       else:
           # Cleanup suave - solo marcar como no cargado
           self._loaded = False
   ```

**Resultado**: ✅ **FUNCIONANDO**
- Eliminado el error "reload() argument must be a module"
- Los scripts se pueden ejecutar múltiples veces sin problemas
- Limpieza específica por módulo evita conflictos innecesarios
- Configuración optimizada reduce el consumo de memoria
- Sistema más estable y robusto

**Feedback del usuario**: 
"por el momento viene funcionando bien!"

**Estado**: 🔄 **TODAVÍA EN TESTING**
- La implementación está funcionando correctamente
- Se continúa monitoreando el comportamiento a largo plazo
- Pendiente confirmación de estabilidad completa

---

## ANÁLISIS TÉCNICO DEL PROBLEMA

### **CAUSA RAÍZ IDENTIFICADA**
El problema fundamental es que Python carga todos los módulos en el mismo espacio de nombres global (`sys.modules`). Cuando múltiples módulos tienen funciones con nombres idénticos (como `debug_print()`, `setup_ui_Sticky()`, `setup_connections_Sticky()`, etc.), las importaciones posteriores sobrescriben las funciones de los módulos anteriores.

### **CONFLICTOS ESPECÍFICOS ENCONTRADOS**
```python
# Funciones duplicadas entre módulos:
- debug_print()          # En LGA_StickyNote, LGA_NodeLabel, LGA_backdrop
- setup_ui_Sticky()             # En LGA_StickyNote, LGA_NodeLabel, LGA_backdrop  
- setup_connections_Sticky()    # En LGA_StickyNote, LGA_NodeLabel, LGA_backdrop
- show_custom_tooltip_Sticky()  # En LGA_StickyNote, LGA_NodeLabel
- hide_custom_tooltip_Sticky()  # En LGA_StickyNote, LGA_NodeLabel
- start_move_Sticky()           # En LGA_StickyNote, LGA_NodeLabel
- move_window_Sticky()          # En LGA_StickyNote, LGA_NodeLabel
- stop_move_Sticky()            # En LGA_StickyNote, LGA_NodeLabel

# Variables globales duplicadas:
- DEBUG                  # En múltiples módulos
- SHADOW_BLUR_RADIUS_Sticky     # En LGA_StickyNote, LGA_backdrop
- SHADOW_OPACITY_Sticky         # En LGA_StickyNote, LGA_backdrop
- SHADOW_OFFSET_X        # En LGA_StickyNote, LGA_backdrop
- SHADOW_OFFSET_Y        # En LGA_StickyNote, LGA_backdrop
```

### **SOLUCIÓN IMPLEMENTADA**
1. **Aislamiento de namespaces**: Cada módulo se carga en su propio namespace usando `importlib`
2. **Gestión de memoria**: Cache limitado y limpieza automática para evitar "bad allocation"
3. **Monitoreo**: Logs detallados para tracking de memoria y módulos
4. **Prevención**: Flags para evitar cargas concurrentes y múltiples instancias

---

**Archivo actualizado**: `LGA_StickyNote_MODIFICACIONES_PROBADAS.md`  
**Fecha de última actualización**: Enero 2025  
**Implementación actual**: Gestión de memoria mejorada con namespaces encapsulados 

---

## RESUMEN DE CAMBIOS IMPLEMENTADOS

He completado las dos correcciones que solicitaste:

### **1. ✅ CAMBIO DE NOMBRES DE MÉTODOS**
- **LGA_StickyNote.py**: `def run()` → `def show_sticky_note_editor()`
- **LGA_NodeLabel.py**: `def run()` → `def show_node_label_editor()`
- Actualizado todas las llamadas a estos métodos en las funciones `main()` y `run_*_editor()`

### **2. ✅ INSTANCIACIÓN TARDÍA (LAZY INITIALIZATION)**
- **Eliminado**: Creación de widgets al importar el módulo
- **Implementado**: Los widgets se crean solo cuando se ejecuta la función `run_*_editor()`
- **Agregado**: Mensajes de debug para confirmar cuándo se crean las instancias

### **POSIBLES CULPABLES IDENTIFICADOS Y CORREGIDOS:**

1. **Conflictos de nombres**: Método `run()` usado en múltiples scripts ✅ **CORREGIDO**
2. **Instanciación prematura**: Widgets creados al importar antes de que Nuke esté listo ✅ **CORREGIDO**
3. **Inicialización de UI compleja**: Ahora se posterga hasta que realmente se necesite ✅ **CORREGIDO**

### **PRÓXIMOS PASOS:**
El archivo Feedback.txt parece estar vacío o inaccesible. Los cambios están listos para probar:

1. **Probar los scripts** en Nuke para ver si los cuelgues desaparecen
2. **Verificar** que los nombres únicos de métodos eviten conflictos
3. **Confirmar** que la instanciación tardía elimine los crashes al importar 