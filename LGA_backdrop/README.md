# LGA_backdrop v2.0

## Descripción

LGA_backdrop es una implementación personalizada de autoBackdrop para Nuke, con knobs personalizados y funcionalidades avanzadas basadas en oz_backdrop pero con arquitectura modular.

## Características

- **Ventana de diálogo personalizada**: Pregunta el nombre del backdrop antes de crearlo
- **Interfaz limpia**: Ventana sin marco con estilo personalizado
- **Controles de teclado**: 
  - `Ctrl+Enter` para confirmar
  - `Escape` para cancelar
- **Posicionamiento inteligente**: Se posiciona cerca del cursor del mouse
- **Manejo de Z-order**: Gestiona correctamente las capas de los backdrops
- **Soporte para nodos vacíos**: Crea un backdrop básico si no hay nodos seleccionados
- **Altura multilínea persistente**: Preserva la altura del campo de texto al guardar/cargar scripts

## Funcionalidades Avanzadas

### Tab "backdrop" 
- **Label**: Link directo al `label` nativo del BackdropNode usando `Link_Knob`
- **Font Size**: Slider numérico (`lga_note_font_size`) sincronizado con `note_font_size` nativo
- **Margin**: Dropdown (`lga_margin`) para alineación del texto (Left/Center/Right) ubicado en la misma línea que Font Size
- **Font**: Link directo al `note_font` nativo del BackdropNode con dropdown de fuentes y controles Bold/Italic integrados (ubicado en línea separada)

### Sección de Colores
- **Widget de Colores Avanzado**: Implementación de botones estilo swatch con sistema de variaciones usando PyCustom_Knob
- **Botón Random con Gradiente**: Primer botón con gradiente multicolor arcoíris que aplica colores RGB completamente aleatorios
- **9 Familias de Colores**: Botones con variaciones cíclicas (Red, Green, Blue, Yellow, Cyan, Magenta, Orange, Purple, Gray)
- **Sistema de Variaciones**: Cada color tiene 5 variaciones que ciclan automáticamente al hacer clic repetido
- **Variables Controlables**: `MIN_LIGHTNESS`, `MAX_LIGHTNESS`, `MIN_SATURATION`, `MAX_SATURATION` para controlar rangos de variación
- **Tracking Inteligente**: Sistema interno que recuerda la última variación aplicada para ciclo correcto
- **Conversión HLS**: Algoritmos internos de conversión RGB↔HLS para generar variaciones precisas de luminancia y saturación
- **Comportamiento Especial Gray**: El gris solo varía en luminancia (de oscuro a claro) manteniendo saturación en 0
- **Persistencia**: Clase registrada globalmente (`nuke.LGA_ColorSwatchWidget`) para preservar funcionalidad al guardar/cargar scripts

### Sección de Resize
- **Margin**: Slider automático para configurar el margen del auto fit (rango 10-200) - ejecuta autofit completo al cambiar (preserva Z-order)
- **Auto Fit**: Botón para redimensionar manualmente abarcando nodos seleccionados o nodos dentro del backdrop (preserva Z-order)

### Sección de Style
- **Style**: Link directo al dropdown nativo `appearance` del BackdropNode (Fill/Border)
- **Border Width**: Link directo al slider nativo `border_width` del BackdropNode (solo activo cuando appearance está en Border)
- **Save Defaults**: Botón con icono `lga_bd_save.png` integrado al final de la línea de Style (movido desde Font)

### Sección de Z-Order (copiada de oz_backdrop)
- **Z Order**: Slider con labels "Back" y "Front" (rango -10 a +10)

### Funcionalidad Save Defaults
- **Save as Default**: Botón con icono `lga_bd_save.png` integrado al final de la línea de Style
- **Posicionamiento**: Ubicado después del slider Border Width en la línea de Style
- **Tooltip**: "Save current properties as default for new backdrops"
- **Funcionalidad**: Guarda font size, font name, bold, italic, align y margin en archivo de configuración
- **Sincronización**: Extrae valores actuales del backdrop incluyendo font size slider y alignment dropdown
- **Widget Compacto**: Tamaño fijo (28x28px) sin spacers para integración perfecta en línea

## Sistema de Configuración de Defaults

### Arquitectura del Sistema
El sistema de configuración sigue el mismo patrón que `LGA_ToolPack_settings.py` para garantizar consistencia:

### Ubicación de Archivos
- **Windows**: `%APPDATA%\LGA\ToolPack_Layout\backdrop_defaults.ini`
- **macOS**: `~/Library/Application Support/LGA/ToolPack_Layout/backdrop_defaults.ini`
- **Linux**: `~/.config/LGA/ToolPack_Layout/backdrop_defaults.ini`

### Configuraciones Guardadas
- **Font Size**: Tamaño de fuente (por defecto: 50)
- **Font Name**: Nombre de la fuente (por defecto: "Verdana")
- **Bold**: Estado del bold (por defecto: False)
- **Italic**: Estado del italic (por defecto: False)
- **Align**: Alineación del texto (por defecto: "left")
- **Margin**: Valor del margin slider (por defecto: 50)

### Comportamiento
- **Al crear backdrop nuevo**: Se cargan automáticamente los valores guardados como defaults
- **Al cargar proyecto existente**: NO se aplican los defaults, se preservan los valores del proyecto
- **Al hacer Save as Default**: Se guardan las configuraciones actuales para futuros backdrops
- **Fallback robusto**: Si no existe configuración, se usan valores hardcoded
- **Sincronización automática**: Font size slider y margin slider se sincronizan con valores por defecto al crear backdrop
- **Detección inteligente**: Convierte índices de dropdown a strings y maneja diferentes tipos de datos

### Módulo LGA_BD_config.py
- **get_backdrop_defaults()**: Carga configuraciones desde archivo INI con fallback robusto
- **save_backdrop_defaults()**: Guarda configuraciones actuales con validación de tipos
- **extract_current_backdrop_settings()**: Extrae configuraciones de un backdrop existente con debug extensivo
- **ensure_config_exists()**: Crea archivo de configuración si no existe
- **Detección de Font**: Maneja correctamente Font_Knob y parsea valores "Arial Bold Italic"
- **Conversión de Alignment**: Convierte índices de dropdown (0, 1, 2) a strings ("left", "center", "right")

## Sistema de Preservación de Estado

### Problemas Resueltos
1. **Duplicación de Link_Knobs**: Los Link_Knobs se duplicaban al guardar y recargar scripts debido a recreación innecesaria
2. **Preservación de Valores**: Font size, margin alignment y Z-order se resetean al recargar scripts
3. **Sincronización**: Los knobs personalizados no se sincronizaban correctamente con los knobs nativos del BackdropNode

### Soluciones Implementadas
- **Link_Knobs Directos**: Uso de `Link_Knob` para vincular directamente a `label` y `note_font` nativos, eliminando duplicación
- **Callback onScriptLoad**: `add_knobs_to_existing_backdrops()` detecta backdrops existentes y solo agrega knobs faltantes
- **Recreación Condicional**: `add_all_knobs()` verifica si los knobs existen antes de crearlos, evitando duplicación
- **Sincronización Bidireccional**: `knob_changed_script()` sincroniza cambios entre knobs personalizados y nativos
- **Preservación de Valores**: Los valores de `lga_note_font_size`, `lga_margin` y `zorder` se preservan al recargar scripts
- **Detección de Alignment**: Detecta automáticamente alignment existente en el `label` y configura el dropdown apropiadamente
- **Persistencia de Widgets**: PyCustom_Knob usa clase registrada globalmente para preservar widgets de colores al guardar/cargar scripts

### Archivos Clave
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_backdrop.py`**:
  - `autoBackdrop()`: Función principal que ahora carga valores por defecto desde configuración al crear nuevos backdrops
  - Sincronización automática de font size slider y margin slider con valores por defecto
  - Construcción correcta de font value con bold/italic y aplicación de alignment HTML
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_config.py`**:
  - `get_backdrop_defaults()`: Carga configuraciones desde archivo INI con fallback robusto
  - `save_backdrop_defaults()`: Guarda configuraciones actuales en archivo INI
  - `extract_current_backdrop_settings()`: Extrae configuraciones actuales de un backdrop node
  - `get_config_directory()`: Maneja rutas multiplataforma siguiendo patrón de LGA_ToolPack_settings
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_knobs.py`**:
  - `create_font_size_knob()`: Crea slider para font size sincronizado con knob nativo
  - `add_all_knobs()`: Maneja creación condicional de knobs, evitando duplicación y preservando valores
  - `add_knobs_to_existing_backdrops()`: Callback onScriptLoad que agrega knobs faltantes a backdrops existentes
  - `ColorSwatchWidget()`: Clase avanzada con sistema de variaciones, tracking interno y algoritmos de conversión HLS
  - `LGA_SaveDefaultsWidget()`: Widget personalizado compacto para botón Save integrado en línea de Style
  - `create_font_section()`: Crea sección de Font con label y dropdown (Save Defaults movido a Style)
  - Widget compacto (28x28px) sin spacers para integración perfecta en línea
  - `_generate_color_variations()`: Genera 5 variaciones por color usando interpolación de luminancia y saturación
  - `_cycle_color_variation()`: Maneja el ciclo inteligente entre variaciones con tracking interno
  - `_apply_random_color()`: Aplica colores RGB completamente aleatorios con reset de tracking
  - `_rgb_to_hls()` y `_hls_to_rgb()`: Funciones de conversión de espacios de color para variaciones precisas
  - `create_lga_color_swatch_buttons()`: Crea PyCustom_Knob con clase registrada globalmente para persistencia
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_callbacks.py`**:
  - `knob_changed_script()`: Sincroniza cambios entre knobs y ejecuta autofit automático inline en cambios de `margin_slider`
  - `fix_animation_flags()`: Aplica el flag NO_ANIMATION a sliders para evitar iconos de animación no deseados
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_fit.py`**:
  - `fit_to_selected_nodes()`: Redimensiona backdrop usando valor del margin slider o nodos internos
  - `find_nodes_inside_backdrop()`: Encuentra eficientemente nodos dentro del backdrop actual
  - `get_nodes_efficiently()`: Método optimizado para obtener nodos usando API nativa de Nuke

### Agregar Nuevos Knobs
Para añadir nuevos knobs personalizados al tab "backdrop":

1. **Agregar verificación condicional** en `add_all_knobs()` dentro de `LGA_BD_knobs.py`:
```python
# Ejemplo: crear nuevo knob solo si no existe
if "nuevo_knob" not in node.knobs():
    nuevo_knob = nuke.String_Knob("nuevo_knob", "Nuevo Knob")
    node.addKnob(nuevo_knob)
    debug_print(f"[DEBUG] Created nuevo_knob")
```

**⚠️ Importante**: Siempre usar verificación `if "knob_name" not in node.knobs():` para evitar duplicación al recargar scripts.

## Sistema de Variaciones de Colores

### Variables Controlables
El sistema permite ajustar los rangos de variación editando las constantes de clase en `ColorSwatchWidget`:
```python
MIN_LIGHTNESS = 0.3    # Luminancia mínima (0.0 = negro, 1.0 = blanco)
MAX_LIGHTNESS = 0.8    # Luminancia máxima 
MIN_SATURATION = 0.4   # Saturación mínima (0.0 = gris, 1.0 = color puro)
MAX_SATURATION = 1.0   # Saturación máxima
```

### Comportamiento del Sistema
- **Primera vez**: Al hacer clic en un color, se aplica la variación 0 (más oscura/menos saturada)
- **Clicks repetidos**: Cicla automáticamente entre las 5 variaciones (0→1→2→3→4→0...)
- **Cambio de familia**: Al cambiar a otro color, reinicia desde variación 0
- **Random**: El botón random resetea el tracking y genera RGB completamente aleatorio
- **Gray especial**: Solo varía luminancia manteniendo saturación en 0 para efectos monocromáticos

### Tracking Interno
El sistema usa variables internas para mantener estado:
- `_last_applied_color`: Nombre de la última familia de color aplicada
- `_last_applied_index`: Índice de la última variación aplicada (0-4)

## Funcionalidad Autofit Mejorada

### Detección Automática de Nodos
- **Sin selección**: Si no hay nodos seleccionados, la función `fit_to_selected_nodes()` busca automáticamente todos los nodos dentro del backdrop actual
- **Optimización**: Usa `find_nodes_inside_backdrop()` que emplea `nuke.allNodes()` optimizado internamente
- **Debug extensivo**: Sistema de debug prints para monitorear el proceso de búsqueda y cálculo de límites
- **Soporte completo**: Funciona con todos los tipos de nodos incluidos otros backdrops dentro del backdrop principal

### Autofit Automático con Margin Slider
- **Autofit en tiempo real**: El slider de margin ejecuta autofit automáticamente al cambiar su valor
- **Sin necesidad de botón**: No es necesario hacer clic en el botón Auto Fit, el cambio es inmediato
- **Función completa**: Usa la misma lógica que el botón autofit, respetando texto multilínea, font size y cálculos precisos
- **Preservación de Z-order**: El autofit automático NO modifica el Z-order del backdrop (a diferencia del botón)
- **Callback inteligente**: Usa `knob_changed_script()` con función inline completa que incluye cálculo de texto
- **Debug extensivo**: Sistema completo de debug prints para monitorear el funcionamiento del autofit automático

### Métodos de Optimización
- **`nuke.allNodes()`**: Función nativa optimizada que es la forma más eficiente de obtener nodos en Nuke
- **Evita filtros manuales**: No usa iteración manual innecesaria que puede ser lenta en scripts grandes
- **Cálculo preciso de límites**: Verifica que los nodos estén completamente contenidos dentro del backdrop

## Cálculo de Tamaño Inteligente

El backdrop usa las mismas funciones de cálculo que oz_backdrop:
- **calculate_extra_top()**: Calcula altura adicional basada en líneas de texto
- **calculate_min_horizontal()**: Calcula ancho mínimo basado en el texto más largo
- Se ejecuta tanto al crear el backdrop como al usar "Encompass"

## Cálculo Automático de Z-Order

El sistema incluye lógica inteligente para determinar el Z-order al crear nuevos backdrops:

### Reglas de Z-Order
1. **Backdrops seleccionados**: Si hay backdrops seleccionados, el nuevo se coloca inmediatamente detrás del más lejano (Z menor)
2. **Nodos dentro de backdrops**: Si los nodos seleccionados están dentro de backdrops existentes, el nuevo se coloca al frente de ellos (Z mayor)
3. **Backdrops contenidos**: **NUEVO** - Si el nuevo backdrop contendrá otros backdrops completos dentro de sus límites, se le asigna un Z más bajo que el mínimo de los contenidos

### Evaluación de Contención
- Al crear un backdrop, se evalúan todos los backdrops existentes
- Se verifica si alguno está completamente contenido dentro de los límites del nuevo backdrop
- Si se encuentran backdrops contenidos, el nuevo backdrop recibe: `Z = min_contained_z - 1`
- Esto asegura que el backdrop "padre" quede automáticamente detrás de sus "hijos"

### Preservación de Z-Order
- El valor del slider Z-order se preserva al guardar/cargar scripts, igual que otros valores (bold, italic, font size, etc.)
- La sincronización entre el slider `zorder` y el knob nativo `z_order` funciona en ambas direcciones

## Comparación con oz_backdrop

### Ventana de diálogo
✅ **Implementación idéntica**: La ventana de diálogo funciona exactamente igual que en oz_backdrop:
- Mismo estilo visual (#242527 de fondo, #262626 para el texto)
- Misma funcionalidad de teclado (Ctrl+Enter, Escape)
- Mismo posicionamiento relativo al cursor
- Misma altura y ancho de ventana

### Funcionalidades
- ✅ **Creación básica de backdrop**: Implementada
- ✅ **Manejo de texto del usuario**: Implementada  
- ✅ **Cálculo de límites**: Implementada (con funciones de oz_backdrop)
- ✅ **Z-order management**: Implementada con cálculo automático y preservación de valores
- ✅ **Knobs personalizados**: Implementados (modulares)
- ✅ **Sistema de colores avanzado**: Implementado (9 familias de colores con 5 variaciones cada una + random RGB)
- ✅ **Resize functions**: Implementadas (grow, shrink, encompass)
- ✅ **Font size con slider**: Implementado
- ✅ **Bold toggle button**: Implementado con preservación de estado
- ✅ **Italic toggle button**: Implementado con preservación de estado
- ✅ **Margin alignment**: Implementado en la misma línea que Bold e Italic
- ✅ **Z-order automático**: Implementado con evaluación de contención de backdrops
- ✅ **Preservación de Z-order**: Implementado igual que otros valores personalizados
- ✅ **Label estilo Nuke**: Implementado con altura multilínea persistente

## Uso

El backdrop se puede usar de la misma manera que el oz_backdrop:
1. Seleccionar nodos (opcional)
2. Presionar `Shift+b` o usar el menú TPL
3. Escribir el nombre del backdrop
4. Presionar `Ctrl+Enter` para confirmar

## Configuración

Para cambiar entre LGA_backdrop y oz_backdrop, editar el flag en `menu.py`:

```python
# Flag para elegir entre LGA_backdrop o oz_backdrop
USE_LGA_BACKDROP = True  # Cambiar a False para usar oz_backdrop
```

## Archivos

- `LGA_backdrop.py`: Implementación principal, ventana de diálogo, cálculo automático de Z-order y carga de defaults
- `LGA_BD_config.py`: Sistema de configuración para guardar y cargar valores por defecto del backdrop
- `LGA_BD_knobs.py`: Manejo modular de knobs personalizados, sistema de altura multilínea, preservación de valores y widget Save
- `LGA_BD_fit.py`: Funciones de cálculo de tamaño y encompass
- `LGA_BD_callbacks.py`: Callbacks, eventos, preservación de altura multilínea y detección de formato HTML
- `README.md`: Este archivo de documentación

## Notas técnicas

- **Arquitectura modular**: Cada funcionalidad en su propio archivo
- **BackdropNode con knobs**: Tab "backdrop" con funcionalidades avanzadas
- **Preservación automática**: Sistema inteligente de preservación de altura multilínea
- **Cálculo inteligente**: Usa las mismas funciones que oz_backdrop para tamaño
- **PySide2**: Para la ventana de diálogo
- **Compatible**: Con la arquitectura de plugins de Nuke
- **Callbacks**: Sincronización automática entre knobs (ej: zorder ↔ z_order) 