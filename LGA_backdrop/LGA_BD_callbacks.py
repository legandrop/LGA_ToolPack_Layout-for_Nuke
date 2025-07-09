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
    # Aplicar solo formato de alignment ya que bold/italic ahora se manejan nativamente
    text_value = knob.value()
    debug_print(f"[DEBUG] lga_label changed to: '{text_value}'")
    
    alignment = "left"
    if 'lga_margin' in node.knobs():
        alignment = node['lga_margin'].value()
    
    # Aplicar solo alignment (sin bold/italic ya que se manejan nativamente)
    formatted_text = text_value
    
    if alignment == "center":
        formatted_text = '<div align="center">' + formatted_text + '</div>'
    elif alignment == "right":
        formatted_text = '<div align="right">' + formatted_text + '</div>'
    
    debug_print(f"[DEBUG] Final formatted text: '{formatted_text}'")
    node['label'].setValue(formatted_text)
elif knob.name() == 'lga_note_font_size':
    # Sincronizar el font size personalizado con el knob note_font_size nativo del BackdropNode
    node['note_font_size'].setValue(knob.value())
elif knob.name() == 'lga_margin':
    # Aplicar alignment al texto del label
    current_text = node['lga_label'].value()  # Obtener texto sin tags
    debug_print(f"[DEBUG] lga_margin changed to: {knob.value()}")
    debug_print(f"[DEBUG] Current lga_label text: '{current_text}'")
    
    # Aplicar solo alignment (sin bold/italic ya que se manejan nativamente)
    formatted_text = current_text
    
    if knob.value() == "center":
        formatted_text = '<div align="center">' + formatted_text + '</div>'
    elif knob.value() == "right":
        formatted_text = '<div align="right">' + formatted_text + '</div>'
    
    debug_print(f"[DEBUG] Final formatted text: '{formatted_text}'")
    node['label'].setValue(formatted_text)

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

        # Detectar y limpiar formato del texto (solo alignment, no bold/italic)
        clean_text = user_text

        # Detectar y remover div alignment tags
        if clean_text.startswith('<div align="center">') and clean_text.endswith(
            "</div>"
        ):
            clean_text = clean_text[20:-6]  # Remover <div align="center"> y </div>
        elif clean_text.startswith('<div align="right">') and clean_text.endswith(
            "</div>"
        ):
            clean_text = clean_text[19:-6]  # Remover <div align="right"> y </div>

        # Remover tags HTML residuales si existen (de implementaciones anteriores)
        import re

        clean_text = re.sub(r"</?[bi]>", "", clean_text)

        debug_print(f"[DEBUG] Clean text: '{clean_text}'")

        debug_print(f"[DEBUG] Calling add_all_knobs for node: {node.name()}")
        LGA_BD_knobs.add_all_knobs(
            node, clean_text, current_font_size
        )  # Ya no pasamos parámetros bold/italic
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
