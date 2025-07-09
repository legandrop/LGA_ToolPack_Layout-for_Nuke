"""
LGA_BD_callbacks.py - Callbacks para LGA_backdrop
"""

import nuke
import LGA_BD_knobs

# Variable global para activar o desactivar los prints
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


def knob_changed_script():
    """
    Script que se ejecuta cuando cambia un knob del backdrop
    """
    return """
# Callback para knobChanged del LGA_backdrop
# Variable global para activar o desactivar los prints
DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

node = nuke.thisNode()
knob = nuke.thisKnob()

if knob.name() == 'zorder':
    # Sincronizar el slider zorder con z_order
    node['z_order'].setValue(knob.value())
elif knob.name() == 'z_order':
    # Sincronizar z_order con el slider zorder
    if 'zorder' in node.knobs():
        node['zorder'].setValue(knob.value())

elif knob.name() == 'lga_label':
    # Sincronizar el label personalizado con el knob label nativo del BackdropNode
    # Aplicar bold si el checkbox está activado
    text_value = knob.value()
    debug_print(f"[DEBUG] lga_label changed to: '{text_value}'")
    if 'lga_bold' in node.knobs() and node['lga_bold'].value():
        # Si bold está activado, agregar tags al label nativo pero no al lga_label
        bold_text = '<b>' + text_value + '</b>'
        debug_print(f"[DEBUG] Applying bold to native label: '{bold_text}'")
        node['label'].setValue(bold_text)
    else:
        # Si bold no está activado, usar texto normal
        debug_print(f"[DEBUG] Setting normal text to native label: '{text_value}'")
        node['label'].setValue(text_value)
elif knob.name() == 'lga_note_font_size':
    # Sincronizar el font size personalizado con el knob note_font_size nativo del BackdropNode
    node['note_font_size'].setValue(knob.value())
elif knob.name() == 'lga_bold':
    # Aplicar o quitar estilo bold al texto del label
    current_text = node['lga_label'].value()  # Obtener texto sin tags
    debug_print(f"[DEBUG] lga_bold changed to: {knob.value()}")
    debug_print(f"[DEBUG] Current lga_label text: '{current_text}'")
    if knob.value():
        # Aplicar bold: solo al label nativo, no al lga_label
        bold_text = '<b>' + current_text + '</b>'
        debug_print(f"[DEBUG] Applying bold, setting native label to: '{bold_text}'")
        node['label'].setValue(bold_text)
    else:
        # Quitar bold: usar texto normal
        debug_print(f"[DEBUG] Removing bold, setting native label to: '{current_text}'")
        node['label'].setValue(current_text)
"""


def add_knobs_to_existing_backdrops():
    """
    Asegura que los knobs personalizados se anadan a los BackdropNodes existentes.
    Esta funcion se llama al cargar un script.
    """
    debug_print(f"[DEBUG] add_knobs_to_existing_backdrops called - onScriptLoad")
    backdrop_nodes = nuke.allNodes("BackdropNode")
    debug_print(f"[DEBUG] Found {len(backdrop_nodes)} BackdropNode(s)")

    for node in backdrop_nodes:
        debug_print(f"[DEBUG] Processing node: {node.name()}")
        # Intentar obtener el texto del knob lga_label si existe, de lo contrario, usar el knob label nativo.
        if "lga_label" in node.knobs():
            user_text = node["lga_label"].value()
            debug_print(f"[DEBUG] Using lga_label value: '{user_text}'")
        else:
            user_text = node["label"].value()
            debug_print(f"[DEBUG] Using native label value: '{user_text}'")

            # Obtener el valor actual del font size
        current_font_size = node["note_font_size"].getValue()

        # Detectar si el texto tiene bold
        has_bold = user_text.startswith("<b>") and user_text.endswith("</b>")
        debug_print(f"[DEBUG] Text has bold: {has_bold}")
        if has_bold:
            # Si tiene bold, usar el texto sin los tags para el knob lga_label
            clean_text = user_text[3:-4]  # Remover <b> y </b>
            debug_print(f"[DEBUG] Clean text: '{clean_text}'")
        else:
            clean_text = user_text

        debug_print(f"[DEBUG] Calling add_all_knobs for node: {node.name()}")
        LGA_BD_knobs.add_all_knobs(node, clean_text, current_font_size)
        debug_print(f"[DEBUG] Finished processing node: {node.name()}")

    debug_print(f"[DEBUG] add_knobs_to_existing_backdrops completed")


def setup_callbacks(node):
    """
    Configura los callbacks del nodo backdrop
    """
    # Agregar el script de knobChanged
    node["knobChanged"].setValue(knob_changed_script())


# Registrar el callback onScriptLoad
# Esto asegura que los knobs lga_label mantengan su altura multilinea al cargar scripts
nuke.addOnScriptLoad(add_knobs_to_existing_backdrops)
