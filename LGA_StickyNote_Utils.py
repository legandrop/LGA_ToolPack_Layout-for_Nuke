"""
_______________________________________________

  LGA_StickyNote_Utils v1.00 | 2024 | Lega
  Utilidades para el editor de StickyNotes
_______________________________________________

"""

import nuke


class StickyNoteStateManager:
    """Clase para manejar el estado original y las operaciones de los StickyNotes"""

    def __init__(self):
        self.original_state = None
        self.is_new_node = False
        self.sticky_node = None

    def save_original_state(self, sticky_node):
        """Guarda el estado original del sticky note"""
        self.sticky_node = sticky_node

        if sticky_node:
            self.original_state = {
                "label": sticky_node["label"].value(),
                "note_font_size": sticky_node["note_font_size"].value(),
                "note_font_color": sticky_node["note_font_color"].value(),
                "tile_color": sticky_node["tile_color"].value(),
            }
            print(f"Estado original guardado para: {sticky_node.name()}")
        else:
            self.original_state = None

    def set_as_new_node(self, sticky_node):
        """Marca el nodo como nuevo (recién creado)"""
        self.is_new_node = True
        self.sticky_node = sticky_node
        self.original_state = None
        print(f"Nodo marcado como nuevo: {sticky_node.name()}")

    def restore_original_state(self):
        """Restaura el estado original del sticky note"""
        if not self.sticky_node or not self.original_state:
            print("No hay estado original para restaurar")
            return False

        try:
            # Restaurar todos los valores originales
            self.sticky_node["label"].setValue(self.original_state["label"])
            self.sticky_node["note_font_size"].setValue(
                self.original_state["note_font_size"]
            )
            self.sticky_node["note_font_color"].setValue(
                self.original_state["note_font_color"]
            )
            self.sticky_node["tile_color"].setValue(self.original_state["tile_color"])

            print(f"Estado original restaurado para: {self.sticky_node.name()}")
            return True
        except Exception as e:
            print(f"Error al restaurar estado original: {e}")
            return False

    def delete_new_node(self):
        """Elimina el nodo si es nuevo"""
        if self.is_new_node and self.sticky_node:
            try:
                node_name = self.sticky_node.name()
                nuke.delete(self.sticky_node)
                print(f"Nodo nuevo eliminado: {node_name}")
                return True
            except Exception as e:
                print(f"Error al eliminar nodo nuevo: {e}")
                return False
        return False

    def handle_cancel_action(self):
        """Maneja la acción de cancelar"""
        if self.is_new_node:
            # Si es un nodo nuevo, eliminarlo
            return self.delete_new_node()
        else:
            # Si es un nodo existente, restaurar estado original
            return self.restore_original_state()

    def handle_ok_action(self):
        """Maneja la acción de confirmar (mantener cambios)"""
        # No hacer nada especial, solo confirmar que los cambios se mantienen
        if self.sticky_node:
            print(f"Cambios confirmados para: {self.sticky_node.name()}")
            return True
        return False

    def reset(self):
        """Resetea el estado del manager"""
        self.original_state = None
        self.is_new_node = False
        self.sticky_node = None


def extract_clean_text_and_margins(text):
    """
    Extrae el texto limpio y detecta los márgenes X e Y de un texto con formato.

    Args:
        text (str): Texto con formato de StickyNote

    Returns:
        tuple: (texto_limpio, margin_x, margin_y)
    """
    if not text.strip():
        return "", 0, 0

    lines = text.split("\n")

    # Valores por defecto
    margin_x_detected = 0
    margin_y_detected = 0

    # --- Detección de Margin X: buscar primera línea con contenido ---
    for line in lines:
        if line.strip():
            leading = len(line) - len(line.lstrip(" "))
            trailing = len(line) - len(line.rstrip(" "))
            margin_x_detected = min(leading, trailing)
            break

    # --- Detección de Margin Y: líneas vacías al inicio y al final ---
    start_empty = 0
    for line in lines:
        if line.strip() == "":
            start_empty += 1
        else:
            break

    end_empty = 0
    for line in reversed(lines):
        if line.strip() == "":
            end_empty += 1
        else:
            break

    margin_y_detected = min(start_empty, end_empty)

    # --- Extraer solo las líneas de contenido sin margin Y ---
    if margin_y_detected * 2 < len(lines):
        content_lines = lines[margin_y_detected : len(lines) - margin_y_detected]
    else:
        content_lines = []

    # --- Limpiar espacios laterales según margin X detectado ---
    clean_lines = []
    for line in content_lines:
        if margin_x_detected > 0 and len(line) >= 2 * margin_x_detected:
            clean_line = line[margin_x_detected : len(line) - margin_x_detected]
        else:
            # Si no hay margin X o la línea es muy corta, solo strip
            clean_line = line.strip()
        clean_lines.append(clean_line)

    final_clean_text = "\n".join(clean_lines)

    return final_clean_text, margin_x_detected, margin_y_detected


def format_text_with_margins(text, margin_x, margin_y):
    """
    Formatea el texto aplicando los márgenes especificados.

    Args:
        text (str): Texto limpio
        margin_x (int): Margen horizontal (espacios a cada lado)
        margin_y (int): Margen vertical (líneas vacías arriba y abajo)

    Returns:
        str: Texto formateado con márgenes
    """
    if not text:
        return ""

    margin_x_spaces = " " * margin_x

    # Agregar espacios a ambos lados de cada línea (Margin X)
    lines = text.split("\n")
    final_lines = []
    for line in lines:
        final_lines.append(margin_x_spaces + line + margin_x_spaces)

    # Agregar líneas vacías arriba y abajo (Margin Y)
    empty_line = margin_x_spaces + margin_x_spaces  # Línea vacía con margin X
    for _ in range(margin_y):
        final_lines.insert(0, empty_line)  # Agregar arriba
        final_lines.append(empty_line)  # Agregar abajo

    return "\n".join(final_lines)
