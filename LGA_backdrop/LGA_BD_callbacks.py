"""
LGA_BD_callbacks.py - Callbacks para LGA_backdrop
"""

import nuke
import LGA_BD_knobs

# Variable global para activar o desactivar los prints
DEBUG = False


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
DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

node = nuke.thisNode()
knob = nuke.thisKnob()

debug_print(f"[CALLBACK DEBUG] Knob changed: {knob.name()} = {knob.value()}")

if knob.name() == 'zorder':
    # Sincronizar el slider zorder con z_order (asegurar que sea entero)
    value = int(round(knob.value()))
    node['z_order'].setValue(value)
    # Asegurar que el slider también muestre el valor entero
    knob.setValue(value)
elif knob.name() == 'z_order':
    # Sincronizar z_order con el slider zorder (asegurar que sea entero)
    if 'zorder' in node.knobs():
        value = int(round(knob.value()))
        node['zorder'].setValue(value)

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
    debug_print(f"[DEBUG] Ejecutando autofit automático completo...")
    
    try:
        # Usar la misma lógica que la función fit_to_selected_nodes pero SIN cambiar Z-order
        this = node
        padding = this["margin_slider"].getValue()

        if this.isSelected:
            this.setSelected(False)
        
        selNodes = nuke.selectedNodes()
        debug_print(f"[DEBUG] Nodos inicialmente seleccionados: {len(selNodes)}")

        # Si no hay nodos seleccionados, buscar nodos dentro del backdrop
        if not selNodes:
            debug_print(f"[DEBUG] No hay nodos seleccionados, buscando nodos dentro del backdrop")
            
            # Buscar nodos dentro del backdrop (función inline copiada de fit_to_selected_nodes)
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
                # No hacer nada si no hay nodos
                pass
            else:
                debug_print(f"[DEBUG] Encontrados {len(selNodes)} nodos dentro del backdrop para autofit")

        # Continuar con el cálculo de autofit completo solo si hay nodos
        if selNodes:
            # Obtener el texto y tamaño de fuente del backdrop actual (IGUAL QUE LA FUNCIÓN PRO)
            user_text = this["label"].getValue()
            note_font_size = this["note_font_size"].getValue()
            
            # Calcular los límites básicos para el nodo de fondo
            bdX = min([node_calc.xpos() for node_calc in selNodes])
            bdY = min([node_calc.ypos() for node_calc in selNodes])
            bdW = max([node_calc.xpos() + node_calc.screenWidth() for node_calc in selNodes]) - bdX
            bdH = max([node_calc.ypos() + node_calc.screenHeight() for node_calc in selNodes]) - bdY

            debug_print(f"[DEBUG] Límites calculados básicos: X={bdX}, Y={bdY}, W={bdW}, H={bdH}")
            
            # ===== AQUÍ VIENE LA LÓGICA COMPLETA DE TEXTO (copiada de fit_to_selected_nodes) =====
            
            # Función para eliminar tags HTML
            import re
            def strip_html_tags_inline(text):
                clean_text = re.sub(r"<.*?>", "", text)
                return clean_text
            
            # Función para calcular extra top
            def calculate_extra_top_inline(text, font_size):
                line_count = text.count("\\n") + 2
                text_height = font_size * line_count
                return text_height
            
            # Función para calcular mínimo horizontal
            def calculate_min_horizontal_inline(text, font_size):
                text = strip_html_tags_inline(text)
                debug_print(f"[DEBUG INLINE] Texto utilizado para el cálculo: {text}")
                
                # Calcular el ajuste del tamaño de la fuente
                adjustment = 0.2 * font_size - 1.5
                adjusted_font_size = font_size - adjustment
                
                # Crear una fuente con la familia Verdana y el tamaño ajustado
                from PySide2.QtGui import QFontMetrics, QFont
                font = QFont("Verdana")
                font.setPointSize(adjusted_font_size)
                metrics = QFontMetrics(font)
                
                lines = text.split("\\n")
                max_width = max(metrics.horizontalAdvance(line) for line in lines)
                min_horizontal = max_width
                
                debug_print(f"[DEBUG INLINE] Línea más larga tiene {max_width} píxeles de ancho.")
                debug_print(f"[DEBUG INLINE] Ancho mínimo calculado: {min_horizontal}")
                return min_horizontal
            
            # Calcular el tamaño adicional necesario para el texto
            extra_top = calculate_extra_top_inline(user_text, note_font_size)
            debug_print(f"[DEBUG] extra_top fit: {extra_top}")
            
            # Calcular el ancho mínimo necesario para el texto
            min_horizontal = calculate_min_horizontal_inline(user_text, note_font_size)
            debug_print(f"[DEBUG] min_horizontal nuevo: {min_horizontal}")
            
            # Expandir los límites para dejar un pequeño borde (IGUAL QUE LA FUNCIÓN PRO)
            if padding < extra_top:
                top = -extra_top
            else:
                top = -padding
            
            debug_print(f"[DEBUG] top nuevo fit: {top}")
            bottom = padding
            debug_print(f"[DEBUG] bottom nuevo fit: {bottom}")
            
            # Ajustar los valores de left y right para asegurar el mínimo horizontal
            left = -1 * padding
            debug_print(f"[DEBUG] left nuevo: {left}")
            additional_width = max(0, min_horizontal - bdW)
            left_adjustment = additional_width / 2
            right_adjustment = additional_width / 2
            
            right = padding + right_adjustment
            debug_print(f"[DEBUG] right nuevo: {right}")
            left -= left_adjustment
            debug_print(f"[DEBUG] left ajustado: {left}")
            
            bdX += left
            bdY += top
            bdW += right - left
            bdH += bottom - top
            
            # ===== APLICAR LOS NUEVOS VALORES (SIN TOCAR Z-ORDER) =====
            this["xpos"].setValue(bdX)
            this["bdwidth"].setValue(bdW)
            this["ypos"].setValue(bdY)
            this["bdheight"].setValue(bdH)
            
            debug_print(f"[DEBUG] Autofit COMPLETO aplicado: X={bdX}, Y={bdY}, W={bdW}, H={bdH}")
            debug_print(f"[DEBUG] Z-order NO modificado (preservado)")
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

        # NUEVA FUNCIONALIDAD: Asegurar que los sliders no tengan animación
        debug_print(
            f"[DEBUG] Aplicando NO_ANIMATION a sliders para node: {node.name()}"
        )
        fix_animation_flags(node)

        # FORZAR NO_ANIMATION al border_width nativo específicamente
        if "border_width" in node.knobs():
            border_width_knob = node["border_width"]
            if hasattr(border_width_knob, "setFlag"):
                border_width_knob.setFlag(nuke.NO_ANIMATION)
                debug_print(
                    f"[DEBUG] FORCED NO_ANIMATION to native border_width for existing backdrop: {node.name()}"
                )

    debug_print(f"[DEBUG] add_knobs_to_existing_backdrops completed")


def fix_animation_flags(node):
    """
    Aplica el flag NO_ANIMATION a todos los sliders que no deben tener animación
    """
    slider_knobs = [
        "margin_slider",
        "zorder",
        "lga_note_font_size",
        "border_width_link",
    ]

    for knob_name in slider_knobs:
        if knob_name in node.knobs():
            knob = node[knob_name]
            if hasattr(knob, "setFlag"):
                knob.setFlag(nuke.NO_ANIMATION)
                debug_print(f"[DEBUG] Applied NO_ANIMATION to {knob_name}")
            else:
                debug_print(
                    f"[DEBUG] Could not apply NO_ANIMATION to {knob_name} - no setFlag method"
                )

    # También aplicar NO_ANIMATION al knob nativo border_width si existe
    if "border_width" in node.knobs():
        border_width_knob = node["border_width"]
        if hasattr(border_width_knob, "setFlag"):
            border_width_knob.setFlag(nuke.NO_ANIMATION)
            debug_print(f"[DEBUG] Applied NO_ANIMATION to native border_width")
        else:
            debug_print(
                f"[DEBUG] Could not apply NO_ANIMATION to native border_width - no setFlag method"
            )


def setup_callbacks(node):
    """
    Configura los callbacks del nodo backdrop
    """
    # Agregar el script de knobChanged
    node["knobChanged"].setValue(knob_changed_script())


# Registrar el callback onScriptLoad
# Esto asegura que los knobs lga_label mantengan su altura multilinea al cargar scripts
nuke.addOnScriptLoad(add_knobs_to_existing_backdrops)
