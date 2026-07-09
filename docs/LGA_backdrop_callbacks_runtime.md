# LGA_backdrop callbacks runtime

## Objetivo

`LGA_backdrop` ya no guarda el callback pesado dentro del knob `knobChanged` de cada `BackdropNode`. La logica viva se registra al cargar el ToolPack con `nuke.addKnobChanged()` y se filtra para actuar solo sobre backdrops con knobs de LGA.

Esto evita que cada backdrop serialice cientos de lineas de Python dentro del `.nk`, reduce el trabajo que Nuke hace al abrir scripts grandes y mantiene el archivo portable.

## Portabilidad

Un script enviado a una maquina sin `LGA_backdrop` instalado sigue abriendo como backdrops nativos de Nuke. La otra persona conserva label, color, posicion, tamanio, font, z-order, appearance y border width guardados en el nodo.

Lo que no funciona sin el ToolPack son los controles avanzados de LGA, porque esos knobs y el callback runtime dependen del plugin instalado. El nodo no deberia fallar por imports faltantes, porque ya no se guarda un `knobChanged` que importe modulos de LGA dentro del `.nk`.

## Migracion de scripts viejos

Al cargar un script, `LGA_BD_callbacks.add_knobs_to_existing_backdrops()` intenta limpiar callbacks legacy de LGA si detecta marcadores del callback antiguo. Para dejar un script viejo normalizado de forma explicita, ejecutar el reemplazador:

```python
import LGA_backdropReplacer
LGA_backdropReplacer.replace_with_lga_backdrop()
```

El reemplazador crea backdrops nuevos sin callback legacy embebido y preserva las propiedades visuales importantes del nodo original.

## Comportamiento runtime

El callback global sincroniza:

- `zorder` con `z_order`
- `lga_note_font_size` con `note_font_size`
- `lga_margin` con el wrapper de alineacion del `label`
- `margin_slider` con autofit silencioso y debounced

Durante creacion, carga o reemplazo se usa un modo de supresion interno para que los `setValue()` iniciales no disparen autofit recursivo.
