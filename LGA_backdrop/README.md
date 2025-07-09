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

### Tab "backdrop" (no "Settings")
- **Label**: Campo de texto estilo Nuke nativo (`Multiline_Eval_String_Knob`) con altura multilínea persistente
- **Font Size**: Campo numérico con slider (rango 10-100)
- **Bold**: Botón toggle para aplicar/quitar estilo bold al texto del backdrop (usa tags HTML `<b></b>` internamente sin mostrarlos en el campo de entrada)
- **Italic**: Botón toggle para aplicar/quitar estilo italic al texto del backdrop (usa tags HTML `<i></i>` internamente sin mostrarlos en el campo de entrada)
- **Margin**: Dropdown para alineación del texto (Left/Center/Right) usando tags HTML `<div align="">` internamente

### Sección de Colores
- **Random Color**: Botón para generar color aleatorio
- **8 Colores básicos**: Red, Green, Blue, Yellow, Cyan, Magenta, Orange, Purple

### Sección de Resize
- **Margin**: Slider para configurar el margen del auto fit (rango 10-200)
- **Auto Fit**: Botón para redimensionar automáticamente abarcando nodos seleccionados

### Sección de Z-Order (copiada de oz_backdrop)
- **Z Order**: Slider con labels "Back" y "Front" (rango -5 a +5)

## Sistema de Preservación de Estado

### Problemas Resueltos
1. **Altura Multilínea**: Los `Multiline_Eval_String_Knob` en Nuke pierden su altura visual después de guardar y recargar scripts
2. **Valores de Knobs**: Font size, margin slider, bold, italic y alignment se resetean al valor por defecto al recargar scripts
3. **Separación de Presentación**: Los tags HTML para bold, italic y alignment no deben aparecer en el campo de entrada del usuario

### Soluciones Implementadas
- **Bandera RESIZABLE**: Se aplica automáticamente a todos los `lga_label` knobs usando `setFlag(0x0008)`
- **Callback onScriptLoad**: Detecta backdrops existentes al cargar scripts y preserva valores existentes
- **Recreación inteligente**: Solo recrea knobs cuando es necesario, preservando valores de font size, margin slider, bold, italic y alignment
- **Separación de capas**: `lga_label` contiene texto limpio, `label` nativo contiene HTML con formato
- **Detección automática**: Al cargar scripts, detecta automáticamente si el texto tiene bold, italic y alignment, configurando los knobs apropiados
- **Callbacks sincronizados**: Maneja cambios aplicando formato HTML completo (bold + italic + alignment) solo al label nativo

### Archivos Clave
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_knobs.py`**:
  - `create_label_knob()`: Aplica bandera RESIZABLE al crear knobs
  - `create_font_bold_section()`: Crea botones toggle para bold e italic con preservación de estado
  - `create_margin_alignment_section()`: Crea dropdown para alignment con preservación de estado
  - `create_resize_section()`: Crea sección de margin con slider y botón auto fit
  - `add_all_knobs()`: Maneja creación y recreación inteligente preservando valores
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_callbacks.py`**:
  - `add_knobs_to_existing_backdrops()`: Callback registrado con `nuke.addOnScriptLoad`
  - `knob_changed_script()`: Maneja sincronización de knobs y aplicación de formato HTML (bold + italic + alignment)
- **`LGA_ToolPack-Layout/LGA_backdrop/LGA_BD_fit.py`**:
  - `fit_to_selected_nodes()`: Redimensiona backdrop usando valor del margin slider

### Agregar Nuevos Knobs
Para añadir nuevos knobs personalizados al tab "backdrop":

1. **Crear función de knob** en `LGA_BD_knobs.py`:
```python
def create_nuevo_knob():
    """Crea el nuevo knob personalizado"""
    knob = nuke.String_Knob("nuevo_knob", "Nuevo Knob")
    # Aplicar flags necesarios
    return knob
```

2. **Añadir a add_all_knobs()** en `LGA_BD_knobs.py`:
```python
# Después de los knobs existentes y antes de los dividers/secciones
nuevo_knob = create_nuevo_knob()
node.addKnob(nuevo_knob)
```

3. **Actualizar lista de eliminación** en la misma función:
```python
custom_knob_names = [
    "lga_label", "lga_note_font_size", "bold_space", "lga_bold_button", "lga_bold_state", "lga_italic_button", "lga_italic_state", "margin_align_label", "lga_margin", "nuevo_knob",  # Añadir aquí
    "divider_1", "random_color", ...
]
```

**⚠️ Importante**: Solo es necesario añadir en `add_all_knobs()`. No se requieren modificaciones adicionales en callbacks.

## Cálculo de Tamaño Inteligente

El backdrop usa las mismas funciones de cálculo que oz_backdrop:
- **calculate_extra_top()**: Calcula altura adicional basada en líneas de texto
- **calculate_min_horizontal()**: Calcula ancho mínimo basado en el texto más largo
- Se ejecuta tanto al crear el backdrop como al usar "Encompass"

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
- ✅ **Z-order management**: Implementada
- ✅ **Knobs personalizados**: Implementados (modulares)
- ✅ **Colores básicos**: Implementados (8 colores + random)
- ✅ **Resize functions**: Implementadas (grow, shrink, encompass)
- ✅ **Font size con slider**: Implementado
- ✅ **Bold toggle button**: Implementado con preservación de estado
- ✅ **Italic toggle button**: Implementado con preservación de estado
- ✅ **Margin alignment**: Implementado en la misma línea que Bold e Italic
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

- `LGA_backdrop.py`: Implementación principal y ventana de diálogo
- `LGA_BD_knobs.py`: Manejo modular de knobs personalizados y sistema de altura multilínea
- `LGA_BD_fit.py`: Funciones de cálculo de tamaño y encompass
- `LGA_BD_callbacks.py`: Callbacks, eventos y preservación de altura multilínea
- `README.md`: Este archivo de documentación

## Notas técnicas

- **Arquitectura modular**: Cada funcionalidad en su propio archivo
- **BackdropNode con knobs**: Tab "backdrop" con funcionalidades avanzadas
- **Preservación automática**: Sistema inteligente de preservación de altura multilínea
- **Cálculo inteligente**: Usa las mismas funciones que oz_backdrop para tamaño
- **PySide2**: Para la ventana de diálogo
- **Compatible**: Con la arquitectura de plugins de Nuke
- **Callbacks**: Sincronización automática entre knobs (ej: zorder ↔ z_order) 