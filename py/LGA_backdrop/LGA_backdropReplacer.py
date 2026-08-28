"""
___________________________________________________________________________________________

  LGA_backdropReplacer v1.11 | Lega
  Replace the selected backdrop with an LGA_backdrop
  or all backdrops if none are selected, and calling LGA_backdropZorder in the end

  v1.11
  - El aviso de "no hay backdrops" sale por el helper de carteles del
    pack, con fallback a nuke.message si el helper no esta.

  v1.1 | 2026-07-09
  - Preserva label formateado, font, margin, nombre y estilo al actualizar backdrops.
  - Crea nodos sin knobChanged legacy embebido.
  - Suprime callbacks runtime durante la migracion para evitar autofit recursivo.
___________________________________________________________________________________________

"""

import nuke
import nukescripts
import os
import sys

# Carteles con el estilo del pack; si el helper no esta, cae al nuke.message pelado.
try:
    from LGA_UI_MessageBox_ToolPack_Layout import show_info
except ImportError:

    def show_info(parent, title, text):
        nuke.message(text)


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


def detect_alignment_from_label(text):
    """Devuelve texto sin wrapper LGA y alignment detectado."""
    return LGA_BD_callbacks.strip_alignment_tags(text)


def get_knob_value(node, knob_name, default=None):
    """Lee un knob si existe; evita repetir guards en el reemplazo."""
    if knob_name not in node.knobs():
        return default
    try:
        return node[knob_name].value()
    except Exception:
        return node[knob_name].getValue()


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
    note_font=None,
    margin_value=None,
    alignment=None,
    label_is_formatted=False,
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
        default_margin_value = backdrop_defaults["margin"]
        debug_print(f"Loaded backdrop defaults: {backdrop_defaults}")
    except Exception as e:
        debug_print(f"Error loading backdrop defaults, using hardcoded values: {e}")
        # Usar valores hardcoded como fallback
        default_font_name = "Verdana"
        default_bold = False
        default_italic = False
        default_align = "left"
        default_margin_value = 50

    if alignment is None:
        alignment = default_align
    alignment = LGA_BD_callbacks.normalise_alignment(alignment)
    if margin_value is None:
        margin_value = default_margin_value

    # Construir el valor de font con bold/italic
    if note_font:
        font_value = note_font
    else:
        font_value = default_font_name
        if default_bold:
            font_value += " Bold"
        if default_italic:
            font_value += " Italic"

    # Aplicar alignment al texto del label
    if label_is_formatted:
        formatted_user_text = user_text
    else:
        formatted_user_text = LGA_BD_callbacks.format_label(user_text, alignment)

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

    with LGA_BD_callbacks.suppress_callbacks():
        # Agregar todos los knobs personalizados (pasar el alignment por defecto)
        LGA_BD_knobs.add_all_knobs(n, formatted_user_text, alignment)

        # Sincronizar el slider zorder con el valor del z_order nativo despues de crear los knobs
        if "zorder" in n.knobs():
            current_z_order = n["z_order"].getValue()
            n["zorder"].setValue(current_z_order)
            debug_print(f"Sincronizado slider zorder con z_order nativo: {current_z_order}")

        # Sincronizar el margin slider con el valor por defecto cargado
        if "margin_slider" in n.knobs():
            n["margin_slider"].setValue(margin_value)
            debug_print(f"Sincronizado margin slider con valor por defecto: {margin_value}")

        if "lga_margin" in n.knobs():
            n["lga_margin"].setValue(alignment)
            debug_print(f"Sincronizado alignment con valor preservado: {alignment}")

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
        show_info(None, "Backdrop Replacer", "No hay backdrops para reemplazar.")
        return

    replaced_count = 0

    for node in nodes_to_replace:
        try:
            # Guardar las propiedades del backdrop existente
            label = node["label"].getValue()
            clean_label, detected_alignment = detect_alignment_from_label(label)
            note_font_size = int(node["note_font_size"].getValue())
            note_font = get_knob_value(node, "note_font", None)
            margin_value = get_knob_value(node, "margin_slider", None)
            tile_color = int(node["tile_color"].getValue())
            xpos = int(node.xpos())
            ypos = int(node.ypos())
            bdwidth = int(node["bdwidth"].getValue())
            bdheight = int(node["bdheight"].getValue())

            # Obtener z_order (puede venir de diferentes knobs)
            if "z_order" in node.knobs():
                z_order = int(node["z_order"].getValue())
            elif "zorder" in node.knobs():
                z_order = int(node["zorder"].getValue())
            else:
                z_order = 0

            alignment = get_knob_value(node, "lga_margin", detected_alignment)

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
            debug_print(f"- Clean label: '{clean_label}'")
            debug_print(f"- Font size: {note_font_size}")
            debug_print(f"- Font: {note_font}")
            debug_print(f"- Position: ({xpos}, {ypos})")
            debug_print(f"- Size: {bdwidth}x{bdheight}")
            debug_print(f"- Z-order: {z_order}")
            debug_print(f"- Appearance: {appearance}")
            debug_print(f"- Border width: {border_width}")
            debug_print(f"- Alignment: {alignment}")
            debug_print(f"- Margin: {margin_value}")

            # Deseleccionar todos los nodos
            for n in nuke.allNodes():
                n.setSelected(False)

            # Crear un nuevo LGA_backdrop con las propiedades guardadas
            new_bd = create_lga_backdrop_silent(
                user_text=label,
                xpos=xpos,
                ypos=ypos,
                bdwidth=bdwidth,
                bdheight=bdheight,
                note_font_size=note_font_size,
                tile_color=tile_color,
                z_order=z_order,
                appearance=appearance,
                border_width=border_width,
                note_font=note_font,
                margin_value=margin_value,
                alignment=alignment,
                label_is_formatted=True,
            )

            # Eliminar el backdrop original
            nuke.delete(node)
            try:
                new_bd["name"].setValue(node_name)
            except Exception as rename_error:
                debug_print(f"No se pudo restaurar el nombre {node_name}: {rename_error}")
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
