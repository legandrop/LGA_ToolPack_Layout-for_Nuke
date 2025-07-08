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

## Funcionalidades Avanzadas

### Tab "backdrop" (no "Settings")
- **Label**: Campo de texto estilo Nuke nativo (2 líneas) en lugar del "Text" problemático
- **Font Size**: Campo numérico con slider (rango 10-100)

### Sección de Colores
- **Random Color**: Botón para generar color aleatorio
- **8 Colores básicos**: Red, Green, Blue, Yellow, Cyan, Magenta, Orange, Purple

### Sección de Resize (copiada de oz_backdrop)
- **Grow**: Botón para agrandar el backdrop 50pt en todas las direcciones
- **Shrink**: Botón para encoger el backdrop 50pt en todas las direcciones  
- **Encompass**: Botón para redimensionar automáticamente abarcando nodos seleccionados
- **Padding**: Campo numérico para el margen del encompass

### Sección de Z-Order (copiada de oz_backdrop)
- **Z Order**: Slider con labels "Back" y "Front" (rango -5 a +5)

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
- ✅ **Label estilo Nuke**: Implementado (2 líneas)

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
- `LGA_knobs.py`: Manejo modular de knobs personalizados
- `LGA_encompass.py`: Funciones de cálculo de tamaño y encompass
- `LGA_callbacks.py`: Callbacks y manejo de eventos
- `README.md`: Este archivo de documentación

## Notas técnicas

- **Arquitectura modular**: Cada funcionalidad en su propio archivo
- **BackdropNode con knobs**: Tab "backdrop" con funcionalidades avanzadas
- **Cálculo inteligente**: Usa las mismas funciones que oz_backdrop para tamaño
- **PySide2**: Para la ventana de diálogo
- **Compatible**: Con la arquitectura de plugins de Nuke
- **Callbacks**: Sincronización automática entre knobs (ej: zorder ↔ z_order) 