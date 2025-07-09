"""
LGA_BD_callbacks.py - Callbacks para LGA_backdrop
"""

import nuke
import LGA_BD_knobs


def knob_changed_script():
    """
    Script que se ejecuta cuando cambia un knob del backdrop
    """
    return """
# Callback para knobChanged del LGA_backdrop
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
    node['label'].setValue(knob.value())
elif knob.name() == 'lga_note_font_size':
    # Sincronizar el font size personalizado con el knob note_font_size nativo del BackdropNode
    node['note_font_size'].setValue(knob.value())
"""


def add_knobs_to_existing_backdrops():
    """
    Asegura que los knobs personalizados se anadan a los BackdropNodes existentes.
    Esta funcion se llama al cargar un script.
    """
    print(f"[DEBUG] add_knobs_to_existing_backdrops called - onScriptLoad")
    backdrop_nodes = nuke.allNodes("BackdropNode")
    print(f"[DEBUG] Found {len(backdrop_nodes)} BackdropNode(s)")

    for node in backdrop_nodes:
        print(f"[DEBUG] Processing node: {node.name()}")
        # Intentar obtener el texto del knob lga_label si existe, de lo contrario, usar el knob label nativo.
        if "lga_label" in node.knobs():
            user_text = node["lga_label"].value()
            print(f"[DEBUG] Using lga_label value: '{user_text}'")
        else:
            user_text = node["label"].value()
            print(f"[DEBUG] Using native label value: '{user_text}'")

        # Obtener el valor actual del font size
        current_font_size = node["note_font_size"].getValue()

        print(f"[DEBUG] Calling add_all_knobs for node: {node.name()}")
        LGA_BD_knobs.add_all_knobs(node, user_text, current_font_size)
        print(f"[DEBUG] Finished processing node: {node.name()}")

    print(f"[DEBUG] add_knobs_to_existing_backdrops completed")


def setup_callbacks(node):
    """
    Configura los callbacks del nodo backdrop
    """
    # Agregar el script de knobChanged
    node["knobChanged"].setValue(knob_changed_script())


# Registrar el callback onScriptLoad
# Esto asegura que los knobs lga_label mantengan su altura multilinea al cargar scripts
nuke.addOnScriptLoad(add_knobs_to_existing_backdrops)
