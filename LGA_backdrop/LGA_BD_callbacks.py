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

debug_print(f"[CALLBACK DEBUG] Knob changed: {knob.name()} = {knob.value()}")

if knob.name() == 'zorder':
    # Sincronizar el slider zorder con z_order
    node['z_order'].setValue(knob.value())
elif knob.name() == 'z_order':
    # Sincronizar z_order con el slider zorder
    if 'zorder' in node.knobs():
        node['zorder'].setValue(knob.value())

elif knob.name() == 'label_link':
    # Manejar cambios en el label
    text_value = knob.value()
    debug_print(f"[DEBUG] label_link changed to: '{text_value}'")

elif knob.name() == 'lga_note_font_size':
    # Sincronizar el font size personalizado con el knob note_font_size nativo del BackdropNode
    node['note_font_size'].setValue(knob.value())

elif knob.name() == 'margin_slider':
    # NUEVA FUNCIONALIDAD: Auto fit automático cuando cambia el margin slider
    debug_print(f"[DEBUG] margin_slider changed to: {knob.value()}")
    debug_print(f"[DEBUG] Ejecutando autofit automático...")
    
    try:
        # Intentar varias formas de importar el módulo
        import sys
        import os
        
        # Agregar la ruta del directorio actual al path
        current_dir = os.path.dirname(node.name())  # Esto no funciona, pero intentamos
        
        # Método más directo: ejecutar el código directamente
        debug_print(f"[DEBUG] Intentando ejecutar fit_to_selected_nodes directamente...")
        
        # Copiar la función directamente aquí para evitar problemas de import
        this = node
        padding = this["margin_slider"].getValue()

        if this.isSelected:
            this.setSelected(False)
        
        selNodes = nuke.selectedNodes()
        debug_print(f"[DEBUG] Nodos inicialmente seleccionados: {len(selNodes)}")

        # Si no hay nodos seleccionados, buscar nodos dentro del backdrop
        if not selNodes:
            debug_print(f"[DEBUG] No hay nodos seleccionados, buscando nodos dentro del backdrop")
            
            # Buscar nodos dentro del backdrop (función inline)
            backdrop_left = this.xpos()
            backdrop_top = this.ypos()
            backdrop_right = backdrop_left + this.screenWidth()
            backdrop_bottom = backdrop_top + this.screenHeight()
            
            nodes_inside = []
            all_nodes = nuke.allNodes()
            
            for node_check in all_nodes:
                if node_check == this or node_check.Class() == 'Root':
                    continue
                    
                node_left = node_check.xpos()
                node_top = node_check.ypos()
                node_right = node_left + node_check.screenWidth()
                node_bottom = node_top + node_check.screenHeight()
                
                if (node_left >= backdrop_left and 
                    node_top >= backdrop_top and 
                    node_right <= backdrop_right and 
                    node_bottom <= backdrop_bottom):
                    
                    nodes_inside.append(node_check)
            
            selNodes = nodes_inside
            
            if not selNodes:
                debug_print(f"[DEBUG] No hay nodos dentro del backdrop para hacer autofit")
                return
            
            debug_print(f"[DEBUG] Encontrados {len(selNodes)} nodos dentro del backdrop para autofit")

        # Continuar con el cálculo de autofit
        if selNodes:
            bdX = min([node_calc.xpos() for node_calc in selNodes])
            bdY = min([node_calc.ypos() for node_calc in selNodes])
            bdW = max([node_calc.xpos() + node_calc.screenWidth() for node_calc in selNodes]) - bdX
            bdH = max([node_calc.ypos() + node_calc.screenHeight() for node_calc in selNodes]) - bdY

            debug_print(f"[DEBUG] Límites calculados: X={bdX}, Y={bdY}, W={bdW}, H={bdH}")
            
            # Aplicar padding y calcular nuevas dimensiones
            bdX_new = bdX - padding
            bdY_new = bdY - padding  
            bdW_new = bdW + (2 * padding)
            bdH_new = bdH + (2 * padding)
            
            # Aplicar los nuevos valores al backdrop
            this["xpos"].setValue(bdX_new)
            this["ypos"].setValue(bdY_new)
            this["bdwidth"].setValue(bdW_new)
            this["bdheight"].setValue(bdH_new)
            
            debug_print(f"[DEBUG] Autofit aplicado: X={bdX_new}, Y={bdY_new}, W={bdW_new}, H={bdH_new}")
        else:
            debug_print(f"[DEBUG] No se encontraron nodos para autofit")
        
    except Exception as e:
        debug_print(f"[DEBUG ERROR] Error en autofit automático: {str(e)}")
        import traceback
        debug_print(f"[DEBUG ERROR] Traceback: {traceback.format_exc()}")

elif knob.name() == 'lga_margin':
    # Sincronizar alignment
    debug_print(f"[DEBUG] lga_margin changed to: '{knob.value()}'")
    
    # Obtener el texto actual del label nativo (limpiar tags previos)
    current_text = node['label'].value()
    debug_print(f"[DEBUG] Current label text: '{current_text}'")
    
    # Limpiar tags de alignment previos
    clean_text = current_text
    if clean_text.startswith('<div align="center">') and clean_text.endswith('</div>'):
        clean_text = clean_text[20:-6]
    elif clean_text.startswith('<div align="right">') and clean_text.endswith('</div>'):
        clean_text = clean_text[19:-6]
    
    # Aplicar nuevo alignment
    formatted_text = clean_text
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

        # Usar el label nativo
        user_text = node["label"].value()
        debug_print(f"[DEBUG] Using native label value: '{user_text}'")

        # Detectar y limpiar formato del texto (solo alignment, no bold/italic)
        clean_text = user_text
        existing_margin_alignment = "left"

        # Detectar y remover div alignment tags
        if clean_text.startswith('<div align="center">') and clean_text.endswith(
            "</div>"
        ):
            clean_text = clean_text[20:-6]  # Remover <div align="center"> y </div>
            existing_margin_alignment = "center"
        elif clean_text.startswith('<div align="right">') and clean_text.endswith(
            "</div>"
        ):
            clean_text = clean_text[19:-6]  # Remover <div align="right"> y </div>
            existing_margin_alignment = "right"

        # Remover tags HTML residuales si existen (de implementaciones anteriores)
        import re

        clean_text = re.sub(r"</?[bi]>", "", clean_text)

        debug_print(f"[DEBUG] Clean text: '{clean_text}'")

        debug_print(f"[DEBUG] Calling add_all_knobs for node: {node.name()}")
        LGA_BD_knobs.add_all_knobs(node, clean_text, existing_margin_alignment)
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
