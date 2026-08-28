"""
___________________________________________________________________________________________

  LGA_backdropToggleAppearance v1.01 | Lega
  Toggle all backdrops between Fill and Border using the first backdrop as master

  v1.01: Los avisos salen por el helper de carteles del pack (info el de
         "no hay backdrops", warning el de appearance ilegible), con
         fallback a nuke.message si el helper no esta.
  v1.0: Version inicial.
___________________________________________________________________________________________

"""

import nuke

# Carteles con el estilo del pack; si el helper no esta, cae al nuke.message pelado.
try:
    from LGA_UI_MessageBox_ToolPack_Layout import show_info, show_warning
except ImportError:

    def show_info(parent, title, text):
        nuke.message(text)

    def show_warning(parent, title, text):
        nuke.message(text)


DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def _appearance_from_knob(knob):
    try:
        value = knob.value()
    except Exception:
        try:
            value = knob.getValue()
        except Exception:
            return None

    if isinstance(value, (int, float)):
        options = ["Fill", "Border"]
        idx = int(value)
        if 0 <= idx < len(options):
            return options[idx]
        return None

    if value is None:
        return None
    return str(value)


def _set_enum_knob(knob, target):
    try:
        knob.setValue(target)
        return True
    except Exception:
        pass

    try:
        values = knob.values() if hasattr(knob, "values") else None
        if values and target in values:
            knob.setValue(values.index(target))
            return True
    except Exception:
        pass

    return False


def _get_backdrops():
    return [n for n in nuke.allNodes() if n.Class() == "BackdropNode"]


def _get_appearance(node):
    if "appearance" in node.knobs():
        return _appearance_from_knob(node["appearance"])
    if "oz_appearance" in node.knobs():
        return _appearance_from_knob(node["oz_appearance"])
    return None


def _set_appearance(node, target):
    changed = False
    if "appearance" in node.knobs():
        changed = _set_enum_knob(node["appearance"], target) or changed
    if "oz_appearance" in node.knobs():
        changed = _set_enum_knob(node["oz_appearance"], target) or changed
    return changed


def toggle_backdrop_fill_border():
    backdrops = _get_backdrops()
    if not backdrops:
        show_info(None, "Backdrop Appearance", "No hay backdrops para alternar.")
        return

    master_appearance = None
    for node in backdrops:
        master_appearance = _get_appearance(node)
        if master_appearance:
            break

    if not master_appearance:
        show_warning(
            None,
            "Backdrop Appearance",
            "No se pudo leer el appearance del primer backdrop.",
        )
        return

    master_lower = master_appearance.strip().lower()
    if "fill" in master_lower:
        target = "Border"
    elif "border" in master_lower:
        target = "Fill"
    else:
        target = "Fill"

    debug_print(f"Master appearance: {master_appearance} -> target: {target}")

    for node in backdrops:
        _set_appearance(node, target)


if __name__ == "__main__":
    toggle_backdrop_fill_border()
