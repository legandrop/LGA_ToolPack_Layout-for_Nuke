"""
LGA_BD_config.py - Sistema de configuración para LGA_backdrop
Maneja guardado y carga de valores por defecto para backdrop properties
"""

import os
import sys
import configparser
import platform
from typing import Optional, Dict, Any

# Variable global para controlar el debug
DEBUG = False

# Constantes de configuración
CONFIG_SECTION = "BackdropDefaults"
CONFIG_FILE_NAME = "backdrop_defaults.ini"

# Claves de configuración
CONFIG_FONT_SIZE_KEY = "font_size"
CONFIG_FONT_NAME_KEY = "font_name"
CONFIG_BOLD_KEY = "bold"
CONFIG_ITALIC_KEY = "italic"
CONFIG_ALIGN_KEY = "align"
CONFIG_MARGIN_KEY = "margin"
CONFIG_APPEARANCE_KEY = "appearance"
CONFIG_BORDER_WIDTH_KEY = "border_width"

# Valores por defecto
DEFAULT_FONT_SIZE = 50
DEFAULT_FONT_NAME = "Verdana"
DEFAULT_BOLD = False
DEFAULT_ITALIC = False
DEFAULT_ALIGN = "left"
DEFAULT_MARGIN = 50
DEFAULT_APPEARANCE = "Fill"
DEFAULT_BORDER_WIDTH = 1.0


def debug_print(*message):
    """Función para debug prints controlados"""
    if DEBUG:
        print(*message)


def get_config_directory():
    """
    Obtiene el directorio de configuración específico para backdrop defaults.
    Sigue el mismo patrón que LGA_ToolPack_settings.py
    """
    # Determinar el directorio base según el OS
    if platform.system() == "Windows":
        base_dir = os.path.join(os.environ.get("APPDATA", ""), "LGA")
    elif platform.system() == "Darwin":  # macOS
        base_dir = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support", "LGA"
        )
    else:  # Linux y otros
        base_dir = os.path.join(os.path.expanduser("~"), ".config", "LGA")

    # Subdirectorio específico para ToolPack Layout
    config_dir = os.path.join(base_dir, "ToolPack_Layout")

    # Crear directorio si no existe
    try:
        os.makedirs(config_dir, exist_ok=True)
        debug_print(f"Config directory: {config_dir}")
    except Exception as e:
        debug_print(f"Error creating config directory: {e}")
        return None

    return config_dir


def get_config_path():
    """
    Obtiene la ruta completa al archivo de configuración
    """
    config_dir = get_config_directory()
    if not config_dir:
        return None

    config_path = os.path.join(config_dir, CONFIG_FILE_NAME)
    debug_print(f"Config file path: {config_path}")
    return config_path


def ensure_config_exists():
    """
    Asegura que el archivo de configuración existe con valores por defecto
    """
    config_path = get_config_path()
    if not config_path:
        debug_print("Cannot create config - invalid path")
        return False

    if os.path.exists(config_path):
        debug_print(f"Config file already exists: {config_path}")
        return True

    # Crear archivo con valores por defecto
    config = configparser.ConfigParser()
    config.add_section(CONFIG_SECTION)

    config.set(CONFIG_SECTION, CONFIG_FONT_SIZE_KEY, str(DEFAULT_FONT_SIZE))
    config.set(CONFIG_SECTION, CONFIG_FONT_NAME_KEY, DEFAULT_FONT_NAME)
    config.set(CONFIG_SECTION, CONFIG_BOLD_KEY, str(DEFAULT_BOLD))
    config.set(CONFIG_SECTION, CONFIG_ITALIC_KEY, str(DEFAULT_ITALIC))
    config.set(CONFIG_SECTION, CONFIG_ALIGN_KEY, DEFAULT_ALIGN)
    config.set(CONFIG_SECTION, CONFIG_MARGIN_KEY, str(DEFAULT_MARGIN))
    config.set(CONFIG_SECTION, CONFIG_APPEARANCE_KEY, DEFAULT_APPEARANCE)
    config.set(CONFIG_SECTION, CONFIG_BORDER_WIDTH_KEY, str(DEFAULT_BORDER_WIDTH))

    try:
        with open(config_path, "w") as configfile:
            config.write(configfile)
        debug_print(f"Created config file with defaults: {config_path}")
        return True
    except Exception as e:
        debug_print(f"Error creating config file: {e}")
        return False


def get_backdrop_defaults():
    """
    Carga los valores por defecto del backdrop desde el archivo de configuración

    Returns:
        Dict con las configuraciones: font_size, font_name, bold, italic, align, margin
    """
    # Valores por defecto como fallback
    defaults = {
        "font_size": DEFAULT_FONT_SIZE,
        "font_name": DEFAULT_FONT_NAME,
        "bold": DEFAULT_BOLD,
        "italic": DEFAULT_ITALIC,
        "align": DEFAULT_ALIGN,
        "margin": DEFAULT_MARGIN,
        "appearance": DEFAULT_APPEARANCE,
        "border_width": DEFAULT_BORDER_WIDTH,
    }

    config_path = get_config_path()
    if not config_path or not os.path.exists(config_path):
        debug_print("Config file not found, using hardcoded defaults")
        return defaults

    config = configparser.ConfigParser()
    try:
        config.read(config_path)

        if not config.has_section(CONFIG_SECTION):
            debug_print(f"Section {CONFIG_SECTION} not found, using defaults")
            return defaults

        # Leer valores del archivo, con fallback a defaults
        font_size = config.getint(
            CONFIG_SECTION, CONFIG_FONT_SIZE_KEY, fallback=DEFAULT_FONT_SIZE
        )
        font_name = config.get(
            CONFIG_SECTION, CONFIG_FONT_NAME_KEY, fallback=DEFAULT_FONT_NAME
        )
        bold = config.getboolean(CONFIG_SECTION, CONFIG_BOLD_KEY, fallback=DEFAULT_BOLD)
        italic = config.getboolean(
            CONFIG_SECTION, CONFIG_ITALIC_KEY, fallback=DEFAULT_ITALIC
        )
        align = config.get(CONFIG_SECTION, CONFIG_ALIGN_KEY, fallback=DEFAULT_ALIGN)
        margin = config.getint(
            CONFIG_SECTION, CONFIG_MARGIN_KEY, fallback=DEFAULT_MARGIN
        )
        appearance = config.get(
            CONFIG_SECTION, CONFIG_APPEARANCE_KEY, fallback=DEFAULT_APPEARANCE
        )
        border_width = config.getfloat(
            CONFIG_SECTION, CONFIG_BORDER_WIDTH_KEY, fallback=DEFAULT_BORDER_WIDTH
        )

        loaded_defaults = {
            "font_size": font_size,
            "font_name": font_name,
            "bold": bold,
            "italic": italic,
            "align": align,
            "margin": margin,
            "appearance": appearance,
            "border_width": border_width,
        }

        debug_print(f"Loaded backdrop defaults: {loaded_defaults}")
        return loaded_defaults

    except Exception as e:
        debug_print(f"Error reading config file: {e}")
        return defaults


def save_backdrop_defaults(
    font_size, font_name, bold, italic, align, margin, appearance, border_width
):
    """
    Guarda los valores actuales como nuevos defaults

    Args:
        font_size (int): Tamaño de fuente
        font_name (str): Nombre de la fuente
        bold (bool): Si está en bold
        italic (bool): Si está en italic
        align (str): Alineación (left/center/right)
        margin (int): Valor del margin
        appearance (str): Tipo de appearance (Fill/Border)
        border_width (float): Ancho del borde

    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    config_path = get_config_path()
    if not config_path:
        debug_print("Cannot save config - invalid path")
        return False

    # Asegurar que el directorio existe
    ensure_config_exists()

    config = configparser.ConfigParser()

    # Leer archivo existente si existe
    if os.path.exists(config_path):
        try:
            config.read(config_path)
        except Exception as e:
            debug_print(f"Error reading existing config: {e}")

    # Asegurar que la sección existe
    if not config.has_section(CONFIG_SECTION):
        config.add_section(CONFIG_SECTION)

    # Guardar valores
    try:
        config.set(CONFIG_SECTION, CONFIG_FONT_SIZE_KEY, str(font_size))
        config.set(CONFIG_SECTION, CONFIG_FONT_NAME_KEY, str(font_name))
        config.set(CONFIG_SECTION, CONFIG_BOLD_KEY, str(bold))
        config.set(CONFIG_SECTION, CONFIG_ITALIC_KEY, str(italic))
        config.set(CONFIG_SECTION, CONFIG_ALIGN_KEY, str(align))
        config.set(CONFIG_SECTION, CONFIG_MARGIN_KEY, str(margin))
        config.set(CONFIG_SECTION, CONFIG_APPEARANCE_KEY, str(appearance))
        config.set(CONFIG_SECTION, CONFIG_BORDER_WIDTH_KEY, str(border_width))

        with open(config_path, "w") as configfile:
            config.write(configfile)

        debug_print(f"Backdrop defaults saved successfully to: {config_path}")
        debug_print(
            f"Saved values: font_size={font_size}, font_name={font_name}, bold={bold}, italic={italic}, align={align}, margin={margin}, appearance={appearance}, border_width={border_width}"
        )
        return True

    except Exception as e:
        debug_print(f"Error saving backdrop defaults: {e}")
        return False


def extract_current_backdrop_settings(node):
    """
    Extrae las configuraciones actuales de un backdrop node

    Args:
        node: El backdrop node del cual extraer configuraciones

    Returns:
        Dict con las configuraciones actuales
    """
    try:
        # Font size
        font_size = DEFAULT_FONT_SIZE
        if "lga_note_font_size" in node.knobs():
            font_size = int(node["lga_note_font_size"].getValue())
        elif "note_font_size" in node.knobs():
            font_size = int(node["note_font_size"].getValue())

        # Font name, bold, italic desde note_font
        font_name = DEFAULT_FONT_NAME
        bold = DEFAULT_BOLD
        italic = DEFAULT_ITALIC
        if "note_font" in node.knobs():
            try:
                note_font_knob = node["note_font"]
                debug_print(f"note_font knob type: {type(note_font_knob)}")
                debug_print(f"note_font knob class: {note_font_knob.Class()}")

                # Intentar diferentes métodos para obtener el valor
                if hasattr(note_font_knob, "value"):
                    note_font_value = note_font_knob.value()
                    debug_print(f"note_font.value(): '{note_font_value}'")
                else:
                    note_font_value = note_font_knob.getValue()
                    debug_print(f"note_font.getValue(): '{note_font_value}'")

                # Solo procesar si es string y no numérico
                if (
                    isinstance(note_font_value, str)
                    and not note_font_value.replace(".", "").replace("-", "").isdigit()
                ):
                    font_parts = note_font_value.split()
                    if font_parts:
                        font_name = font_parts[0]
                        bold = "Bold" in font_parts
                        italic = "Italic" in font_parts
                        debug_print(
                            f"Parsed font: name='{font_name}', bold={bold}, italic={italic}"
                        )
                else:
                    debug_print(
                        f"note_font value is not a valid font string: '{note_font_value}'"
                    )

            except Exception as e:
                debug_print(f"Error processing note_font: {e}")
                # Mantener valores por defecto

        # Alignment
        align = DEFAULT_ALIGN
        if "lga_margin" in node.knobs():
            align_value = node["lga_margin"].getValue()
            debug_print(
                f"lga_margin raw value: '{align_value}' (type: {type(align_value)})"
            )
            # El dropdown devuelve un índice, convertir a string
            if isinstance(align_value, (int, float)):
                align_options = ["left", "center", "right"]
                if 0 <= int(align_value) < len(align_options):
                    align = align_options[int(align_value)]
                    debug_print(f"Converted align index {align_value} to '{align}'")
            else:
                align = str(align_value)
                debug_print(f"Using align value as string: '{align}'")

        # Margin
        margin = DEFAULT_MARGIN
        if "margin_slider" in node.knobs():
            margin = int(node["margin_slider"].getValue())

        # Appearance
        appearance = DEFAULT_APPEARANCE
        if "appearance" in node.knobs():
            appearance_value = node["appearance"].getValue()
            debug_print(
                f"appearance raw value: '{appearance_value}' (type: {type(appearance_value)})"
            )
            # El dropdown devuelve un índice, convertir a string
            if isinstance(appearance_value, (int, float)):
                appearance_options = ["Fill", "Border"]
                if 0 <= int(appearance_value) < len(appearance_options):
                    appearance = appearance_options[int(appearance_value)]
                    debug_print(
                        f"Converted appearance index {appearance_value} to '{appearance}'"
                    )
            else:
                appearance = str(appearance_value)
                debug_print(f"Using appearance value as string: '{appearance}'")

        # Border Width
        border_width = DEFAULT_BORDER_WIDTH
        if "border_width" in node.knobs():
            border_width = float(node["border_width"].getValue())

        settings = {
            "font_size": font_size,
            "font_name": font_name,
            "bold": bold,
            "italic": italic,
            "align": align,
            "margin": margin,
            "appearance": appearance,
            "border_width": border_width,
        }

        debug_print(f"Extracted backdrop settings: {settings}")
        return settings

    except Exception as e:
        debug_print(f"Error extracting backdrop settings: {e}")
        # Return defaults en caso de error
        return {
            "font_size": DEFAULT_FONT_SIZE,
            "font_name": DEFAULT_FONT_NAME,
            "bold": DEFAULT_BOLD,
            "italic": DEFAULT_ITALIC,
            "align": DEFAULT_ALIGN,
            "margin": DEFAULT_MARGIN,
            "appearance": DEFAULT_APPEARANCE,
            "border_width": DEFAULT_BORDER_WIDTH,
        }
