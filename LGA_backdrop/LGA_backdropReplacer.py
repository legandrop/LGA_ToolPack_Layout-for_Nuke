"""
___________________________________________________________________________________________

  LGA_backdropReplacer v1.0 | Lega
  Replace the selected backdrop with an LGA_backdrop
  or all backdrops if none are selected, and calling LGA_backdropZorder in the end
___________________________________________________________________________________________

"""

import nuke
import nukescripts
import os
import sys

# Variable global para activar o desactivar los debug_prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


# Obtener la ruta del directorio donde se encuentra el script actual
script_dir = os.path.dirname(__file__)

# Importar modulos del LGA_backdrop
import LGA_backdrop
import LGA_BD_knobs
import LGA_BD_callbacks
import LGA_BD_fit
import LGA_BD_config


def strip_html_tags(text):
    """Elimina etiquetas HTML del texto"""
    import re

    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def create_lga_backdrop_silent(
    user_text="",
    xpos=0,
    ypos=0,
    bdwidth=200,
    bdheight=200,
    note_font_size=42,
    tile_color=10,
    z_order=0,
    appearance="Fill",
    border_width=1.0,
):
    """
    Crea un LGA_backdrop sin mostrar el dialogo de entrada de texto.
    Esta funcion replica la logica de autoBackdrop() pero sin interaccion del usuario.
    """
    debug_print(f"Creating LGA_backdrop with text: '{user_text}'")

    # Cargar valores por defecto desde configuracion
    try:
        backdrop_defaults = LGA_BD_config.get_backdrop_defaults()
        default_font_name = backdrop_defaults["font_name"]
        default_bold = backdrop_defaults["bold"]
        default_italic = backdrop_defaults["italic"]
        default_align = backdrop_defaults["align"]
        margin_value = backdrop_defaults["margin"]
        debug_print(f"Loaded backdrop defaults: {backdrop_defaults}")
    except Exception as e:
        debug_print(f"Error loading backdrop defaults, using hardcoded values: {e}")
        # Usar valores hardcoded como fallback
        default_font_name = "Verdana"
        default_bold = False
        default_italic = False
        default_align = "left"
        margin_value = 50

    # Construir el valor de font con bold/italic
    font_value = default_font_name
    if default_bold:
        font_value += " Bold"
    if default_italic:
        font_value += " Italic"

    # Aplicar alignment al texto del label
    formatted_user_text = user_text
    if default_align == "center":
        formatted_user_text = '<div align="center">' + user_text + "</div>"
    elif default_align == "right":
        formatted_user_text = '<div align="right">' + user_text + "</div>"

    # Crear el backdrop
    n = nuke.nodes.BackdropNode(
        xpos=xpos,
        bdwidth=bdwidth,
        ypos=ypos,
        bdheight=bdheight,
        tile_color=tile_color,
        note_font_size=note_font_size,
        note_font=font_value,
        z_order=z_order,
        label=formatted_user_text,
        appearance=appearance,
        border_width=border_width,
    )

    # Agregar todos los knobs personalizados (pasar el alignment por defecto)
    LGA_BD_knobs.add_all_knobs(n, formatted_user_text, default_align)

    # Sincronizar el slider zorder con el valor del z_order nativo despues de crear los knobs
    if "zorder" in n.knobs():
        current_z_order = n["z_order"].getValue()
        n["zorder"].setValue(current_z_order)
        debug_print(f"Sincronizado slider zorder con z_order nativo: {current_z_order}")

    # Sincronizar el margin slider con el valor por defecto cargado
    if "margin_slider" in n.knobs():
        n["margin_slider"].setValue(margin_value)
        debug_print(f"Sincronizado margin slider con valor por defecto: {margin_value}")

    # Sincronizar el font size slider con el valor por defecto cargado
    if "lga_note_font_size" in n.knobs():
        n["lga_note_font_size"].setValue(note_font_size)
        debug_print(
            f"Sincronizado font size slider con valor por defecto: {note_font_size}"
        )

    # Configurar callbacks
    LGA_BD_callbacks.setup_callbacks(n)

    debug_print(f"LGA_backdrop created successfully: {n.name()}")
    return n


def replace_with_lga_backdrop():
    """
    Reemplaza los backdrops seleccionados (o todos si ninguno esta seleccionado)
    con LGA_backdrops manteniendo todas las propiedades originales.
    """
    selected_backdrops = [
        n for n in nuke.selectedNodes() if n.Class() == "BackdropNode"
    ]

    if selected_backdrops:
        # Si hay backdrops seleccionados, reemplaza solo esos
        nodes_to_replace = selected_backdrops
        debug_print(
            f"Reemplazando {len(selected_backdrops)} backdrop(s) seleccionado(s)"
        )
    else:
        # Si no hay backdrops seleccionados, reemplaza todos
        nodes_to_replace = [n for n in nuke.allNodes() if n.Class() == "BackdropNode"]
        debug_print(
            f"Reemplazando todos los backdrops del proyecto: {len(nodes_to_replace)}"
        )

    if not nodes_to_replace:
        nuke.message("No hay backdrops para reemplazar.")
        return

    replaced_count = 0

    for node in nodes_to_replace:
        try:
            # Guardar las propiedades del backdrop existente
            label = node["label"].getValue()
            note_font_size = int(node["note_font_size"].getValue())
            tile_color = int(node["tile_color"].getValue())
            xpos = int(node.xpos())
            ypos = int(node.ypos())
            bdwidth = int(node["bdwidth"].getValue())
            bdheight = int(node["bdheight"].getValue())

            # Obtener z_order (puede venir de diferentes knobs)
            if "zorder" in node.knobs():
                z_order = int(node["zorder"].getValue())
            elif "z_order" in node.knobs():
                z_order = int(node["z_order"].getValue())
            else:
                z_order = 0

            # Obtener appearance y border_width
            appearance = "Fill"
            border_width = 1.0

            if "appearance" in node.knobs():
                appearance = node["appearance"].value()
            elif "oz_appearance" in node.knobs():
                appearance = node["oz_appearance"].value()

            if "border_width" in node.knobs():
                border_width = float(node["border_width"].value())
            elif "oz_border_width" in node.knobs():
                border_width = float(node["oz_border_width"].value())

            # Guardar el nombre del nodo antes de eliminarlo
            node_name = node.name()

            debug_print(f"Procesando backdrop: {node_name}")
            debug_print(f"- Label: '{label}'")
            debug_print(f"- Font size: {note_font_size}")
            debug_print(f"- Position: ({xpos}, {ypos})")
            debug_print(f"- Size: {bdwidth}x{bdheight}")
            debug_print(f"- Z-order: {z_order}")
            debug_print(f"- Appearance: {appearance}")
            debug_print(f"- Border width: {border_width}")

            # Limpiar etiquetas HTML del label para obtener texto plano
            stripped_label = strip_html_tags(label)

            # Deseleccionar todos los nodos
            for n in nuke.allNodes():
                n.setSelected(False)

            # Crear un nuevo LGA_backdrop con las propiedades guardadas
            new_bd = create_lga_backdrop_silent(
                user_text=stripped_label,
                xpos=xpos,
                ypos=ypos,
                bdwidth=bdwidth,
                bdheight=bdheight,
                note_font_size=note_font_size,
                tile_color=tile_color,
                z_order=z_order,
                appearance=appearance,
                border_width=border_width,
            )

            # Eliminar el backdrop original
            nuke.delete(node)
            replaced_count += 1

            debug_print(
                f"Backdrop reemplazado exitosamente: {node_name} -> {new_bd.name()}"
            )

        except Exception as e:
            # Guardar el nombre del nodo antes de usarlo en caso de error
            try:
                node_name = node.name()
            except:
                node_name = "Unknown"
            debug_print(f"[ERROR] Error al reemplazar backdrop {node_name}: {e}")
            continue

    # Mostrar resultado solo en consola (sin ventana popup)
    if replaced_count > 0:
        debug_print(
            f"Se reemplazaron {replaced_count} backdrop(s) con LGA_backdrop exitosamente."
        )
    else:
        debug_print("No se pudo reemplazar ningun backdrop.")

    # Importar y ejecutar LGA_backdropZorder despues de reemplazar los backdrops
    try:
        import LGA_backdropZorder

        LGA_backdropZorder.order_all_backdrops()
        debug_print("LGA_backdropZorder ejecutado exitosamente")
    except Exception as e:
        debug_print(f"Error al ejecutar LGA_backdropZorder.py: {e}")


if __name__ == "__main__":
    replace_with_lga_backdrop()
