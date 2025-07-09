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
    for node in nuke.allNodes("BackdropNode"):
        # Asumimos que user_text ya esta guardado en el knob 'label' nativo
        user_text = node["label"].value()
        LGA_BD_knobs.add_all_knobs(node, user_text)


def setup_callbacks(node):
    """
    Configura los callbacks del nodo backdrop
    """
    # Agregar el script de knobChanged
    node["knobChanged"].setValue(knob_changed_script())
