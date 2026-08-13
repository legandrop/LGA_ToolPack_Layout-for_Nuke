"""
LGA_BD_callbacks.py - Callbacks para LGA_backdrop

v1.02 | 2026-08-12
- Agrega un onCreate que normaliza los Link_Knob del backdrop al crearse.
  Al pegar un backdrop viejo, sus links traian el nombre del nodo original
  embebido y Nuke dejaba una dependencia de expresion colgada hacia el.

v1.01 | 2026-07-09
- Reemplaza el knobChanged embebido por nodo por un callback runtime global.
- Limpia callbacks LGA legacy serializados en scripts viejos.
- Debouncea el autofit del margin slider y reutiliza LGA_BD_fit.
"""

import re
from contextlib import contextmanager

import nuke
from LGA_QtAdapter_ToolPack_Layout import QtCore

# Import plano; la ruta se asegura en LGA_backdrop.py.
import LGA_BD_fit as LGA_BD_fit  # type: ignore
import LGA_BD_knobs as LGA_BD_knobs  # type: ignore

DEBUG = False
LEGACY_CALLBACK_MARKERS = (
    "Callback para knobChanged del LGA_backdrop",
    "calculate_min_horizontal_inline",
    "Ejecutando autofit",
)
RUNTIME_KNOBS = {
    "zorder",
    "z_order",
    "lga_note_font_size",
    "margin_slider",
    "lga_margin",
}
LGA_BACKDROP_KNOBS = {
    "label_link",
    "lga_note_font_size",
    "margin_slider",
    "lga_autofit_control",
    "lga_margin",
}
AUTOFIT_DEBOUNCE_MS = 80

_SUPPRESS_CALLBACKS = False
_PROCESSING_NODES = set()
_PENDING_AUTOFIT = {}


def debug_print(*message):
    if DEBUG:
        print("[LGA_backdrop callbacks]", *message)


def knob_changed_script():
    """
    Devuelve un callback vacio para que los .nk sigan siendo portables.
    La funcionalidad viva se registra con nuke.addKnobChanged().
    """
    return ""


@contextmanager
def suppress_callbacks():
    """
    Pausa callbacks runtime mientras se crean o migran knobs de LGA_backdrop.
    """
    global _SUPPRESS_CALLBACKS

    previous = _SUPPRESS_CALLBACKS
    _SUPPRESS_CALLBACKS = True
    try:
        yield
    finally:
        _SUPPRESS_CALLBACKS = previous


def _node_key(node):
    try:
        return node.fullName()
    except Exception:
        return node.name()


def _is_lga_backdrop(node):
    try:
        if node.Class() != "BackdropNode":
            return False
        knobs = node.knobs()
        return any(name in knobs for name in LGA_BACKDROP_KNOBS)
    except Exception:
        return False


def _has_legacy_lga_callback(node):
    try:
        script = node["knobChanged"].value()
    except Exception:
        return False
    return any(marker in script for marker in LEGACY_CALLBACK_MARKERS)


def _set_value_if_changed(knob, value, tolerance=0.0001):
    try:
        current = knob.value()
    except Exception:
        current = knob.getValue()

    if isinstance(current, (int, float)) and isinstance(value, (int, float)):
        if abs(float(current) - float(value)) <= tolerance:
            return
    elif current == value:
        return

    knob.setValue(value)


def normalise_alignment(value):
    if isinstance(value, (int, float)):
        options = ["left", "center", "right"]
        index = int(value)
        if 0 <= index < len(options):
            return options[index]

    value = str(value).lower()
    if value in {"center", "right"}:
        return value
    return "left"


def strip_alignment_tags(text):
    """
    Remueve los tags de alineacion que usa LGA_backdrop y devuelve texto + alignment.
    """
    patterns = (
        ("center", r'^<div align="center">(.*)</div>$'),
        ("right", r'^<div align="right">(.*)</div>$'),
    )
    for alignment, pattern in patterns:
        match = re.match(pattern, text, flags=re.DOTALL)
        if match:
            return match.group(1), alignment
    return text, "left"


def format_label(text, alignment):
    clean_text, _old_alignment = strip_alignment_tags(text)
    if alignment == "center":
        return '<div align="center">' + clean_text + "</div>"
    if alignment == "right":
        return '<div align="right">' + clean_text + "</div>"
    return clean_text


def _sync_zorder(node, knob_name):
    if knob_name == "zorder" and "z_order" in node.knobs():
        value = int(round(node["zorder"].value()))
        _set_value_if_changed(node["z_order"], value)
        _set_value_if_changed(node["zorder"], value)
    elif knob_name == "z_order" and "zorder" in node.knobs():
        value = int(round(node["z_order"].value()))
        _set_value_if_changed(node["zorder"], value)


def _sync_font_size(node):
    if "note_font_size" not in node.knobs() or "lga_note_font_size" not in node.knobs():
        return

    value = int(round(node["lga_note_font_size"].value()))
    _set_value_if_changed(node["note_font_size"], value)
    _set_value_if_changed(node["lga_note_font_size"], value)


def _sync_alignment(node):
    if "label" not in node.knobs() or "lga_margin" not in node.knobs():
        return

    alignment = normalise_alignment(node["lga_margin"].value())
    formatted_text = format_label(node["label"].value(), alignment)
    _set_value_if_changed(node["label"], formatted_text)


def _run_autofit(node):
    global _SUPPRESS_CALLBACKS

    previous = _SUPPRESS_CALLBACKS
    _SUPPRESS_CALLBACKS = True
    try:
        LGA_BD_fit.fit_to_selected_nodes(node, show_message=False)
    except Exception as exc:
        debug_print(f"Error en autofit automatico: {exc}")
    finally:
        _SUPPRESS_CALLBACKS = previous


def _run_pending_autofit(key, token):
    pending = _PENDING_AUTOFIT.get(key)
    if not pending or pending[0] != token:
        return

    _PENDING_AUTOFIT.pop(key, None)
    node = pending[1]
    try:
        if _is_lga_backdrop(node):
            _run_autofit(node)
    except (RuntimeError, ReferenceError):
        debug_print("Nodo LGA_backdrop eliminado antes del autofit")


def _schedule_autofit(node):
    key = _node_key(node)
    token = _PENDING_AUTOFIT.get(key, (0, None))[0] + 1
    _PENDING_AUTOFIT[key] = (token, node)

    app = QtCore.QCoreApplication.instance()
    if app is None:
        _run_pending_autofit(key, token)
        return

    QtCore.QTimer.singleShot(
        AUTOFIT_DEBOUNCE_MS,
        lambda: _run_pending_autofit(key, token),
    )


def handle_knob_changed(node=None, knob=None):
    """
    Callback runtime para LGA_backdrop.
    No se guarda dentro del .nk, por lo que el script sigue siendo portable.
    """
    if _SUPPRESS_CALLBACKS:
        return

    try:
        node = node or nuke.thisNode()
        knob = knob or nuke.thisKnob()
        knob_name = knob.name()
    except Exception:
        return

    if knob_name not in RUNTIME_KNOBS or not _is_lga_backdrop(node):
        return

    key = _node_key(node)
    if key in _PROCESSING_NODES:
        return

    _PROCESSING_NODES.add(key)
    try:
        if knob_name in {"zorder", "z_order"}:
            _sync_zorder(node, knob_name)
        elif knob_name == "lga_note_font_size":
            _sync_font_size(node)
        elif knob_name == "lga_margin":
            _sync_alignment(node)
        elif knob_name == "margin_slider":
            _schedule_autofit(node)
    finally:
        _PROCESSING_NODES.discard(key)


def handle_node_created():
    """
    Callback runtime de creacion de BackdropNode.

    Corre tambien al pegar y al cargar un script. Normaliza los Link_Knob
    del pack para que apunten al propio nodo: si el link llega con el nombre
    del nodo original embebido, Nuke registra una dependencia de expresion
    hacia ese nodo y la dibuja como linea punteada en el Node Graph.
    Hacerlo aca, mientras el nodo se esta construyendo, borra esa dependencia
    en el momento; despues del onCreate ya no alcanza con reapuntar el link.
    """
    try:
        node = nuke.thisNode()
    except Exception:
        return

    try:
        with suppress_callbacks():
            LGA_BD_knobs.normalize_link_knobs(node)
    except Exception as exc:
        debug_print(f"Error normalizando links en onCreate: {exc}")


def add_knobs_to_existing_backdrops():
    """
    Asegura que los knobs personalizados se anadan a los BackdropNodes existentes.
    Esta funcion se llama al cargar un script.
    """
    with suppress_callbacks():
        debug_print("add_knobs_to_existing_backdrops called - onScriptLoad")
        backdrop_nodes = nuke.allNodes("BackdropNode")
        debug_print(f"Found {len(backdrop_nodes)} BackdropNode(s)")

        for node in backdrop_nodes:
            debug_print(f"Processing node: {node.name()}")

            user_text = node["label"].value()
            clean_text, existing_margin_alignment = strip_alignment_tags(user_text)
            clean_text = re.sub(r"</?[bi]>", "", clean_text)

            debug_print(f"Calling add_all_knobs for node: {node.name()}")
            LGA_BD_knobs.add_all_knobs(node, clean_text, existing_margin_alignment)
            setup_callbacks(node, force=False)
            debug_print(f"Finished processing node: {node.name()}")

            debug_print(f"Aplicando NO_ANIMATION a sliders para node: {node.name()}")
            fix_animation_flags(node)

            if "border_width" in node.knobs():
                border_width_knob = node["border_width"]
                if hasattr(border_width_knob, "setFlag"):
                    border_width_knob.setFlag(nuke.NO_ANIMATION)
                    debug_print(
                        f"FORCED NO_ANIMATION to native border_width for existing backdrop: {node.name()}"
                    )

        debug_print("add_knobs_to_existing_backdrops completed")


def fix_animation_flags(node):
    """
    Aplica el flag NO_ANIMATION a todos los sliders que no deben tener animacion.
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
                debug_print(f"Applied NO_ANIMATION to {knob_name}")
            else:
                debug_print(
                    f"Could not apply NO_ANIMATION to {knob_name} - no setFlag method"
                )

    if "border_width" in node.knobs():
        border_width_knob = node["border_width"]
        if hasattr(border_width_knob, "setFlag"):
            border_width_knob.setFlag(nuke.NO_ANIMATION)
            debug_print("Applied NO_ANIMATION to native border_width")
        else:
            debug_print(
                "Could not apply NO_ANIMATION to native border_width - no setFlag method"
            )


def setup_callbacks(node, force=True):
    """
    Configura el callback del nodo para el nuevo modelo runtime.
    """
    if "knobChanged" not in node.knobs():
        return

    if force or _has_legacy_lga_callback(node) or not node["knobChanged"].value():
        node["knobChanged"].setValue(knob_changed_script())


def register_runtime_callbacks():
    """
    Registra callbacks runtime sin serializarlos dentro de cada BackdropNode.
    """
    old_callback = getattr(nuke, "_LGA_BD_RUNTIME_CALLBACK", None)
    if old_callback is not None:
        try:
            nuke.removeKnobChanged(old_callback, nodeClass="BackdropNode")
        except Exception:
            pass

    nuke.addKnobChanged(handle_knob_changed, nodeClass="BackdropNode")
    nuke._LGA_BD_RUNTIME_CALLBACK = handle_knob_changed


def register_create_callback():
    """
    Registra el onCreate runtime sin serializarlo dentro de cada BackdropNode.
    """
    old_callback = getattr(nuke, "_LGA_BD_ONCREATE_CALLBACK", None)
    if old_callback is not None:
        try:
            nuke.removeOnCreate(old_callback, nodeClass="BackdropNode")
        except Exception:
            pass

    nuke.addOnCreate(handle_node_created, nodeClass="BackdropNode")
    nuke._LGA_BD_ONCREATE_CALLBACK = handle_node_created


def register_script_load_callback():
    old_callback = getattr(nuke, "_LGA_BD_ONSCRIPTLOAD_CALLBACK", None)
    if old_callback is not None:
        try:
            nuke.removeOnScriptLoad(old_callback)
        except Exception:
            pass

    nuke.addOnScriptLoad(add_knobs_to_existing_backdrops)
    nuke._LGA_BD_ONSCRIPTLOAD_CALLBACK = add_knobs_to_existing_backdrops


register_runtime_callbacks()
register_create_callback()
register_script_load_callback()
