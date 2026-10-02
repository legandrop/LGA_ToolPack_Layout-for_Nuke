"""
__________________________________________

  LGA Layout ToolPack | Lega
__________________________________________

"""

import nuke
import nukescripts

# Importar iconos de la carpeta icons
import os

# --- Config loader & helpers -------------------------------------------
import importlib


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
PY_DIR = os.path.join(ROOT_DIR, "py")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")


def _read_product_version():
    """Lee la version publicada desde la fuente unica VERSION."""
    version_path = os.path.join(ROOT_DIR, "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as version_file:
            return version_file.read().strip()
    except (OSError, UnicodeError) as error:
        nuke.warning("No se pudo leer VERSION de LGA_ToolPack-Layout: %s" % error)
        return "unknown"


PRODUCT_VERSION = _read_product_version()

# Carga los modulos runtime desde py/
nuke.pluginAddPath(PY_DIR.replace("\\", "/"))


# El estado de las tools lo resuelve LGA_ToolPackLayout_Enabled, que lo lee de
# la carpeta de datos del usuario y no de adentro del pack. Vive en py/ para que
# el panel de Enable Tools use exactamente la misma logica que el menu.
#
# Aca vivia ademas una funcion que reescribia el ini de `.nuke` en CADA arranque
# de Nuke para agregarle las claves nuevas. Se elimino: hacia una escritura sin
# lock (dos Nukes a la vez duplicaban la clave y el ini quedaba invalido, con el
# error silenciado) y ya no hace falta, porque las claves nuevas salen del
# manifiesto del pack y el archivo del usuario solo guarda lo que difiere.
#
# `except Exception` y no `except ImportError`: un SyntaxError o un fallo de
# encoding al importar no son ImportError, se propagarian y Nuke arrancaria sin
# el menu entero, que es exactamente lo que se quiere evitar.
try:
    import LGA_ToolPackLayout_Enabled as _enabled_config
except Exception as _enabled_error:
    # Si el modulo falta, el menu tiene que armarse igual y con todo visible:
    # es preferible mostrar de mas a dejar al usuario sin herramientas.
    nuke.warning("No se pudo cargar LGA_ToolPackLayout_Enabled: %s" % _enabled_error)
    _enabled_config = None
else:
    # Siembra la config del usuario la primera vez, rescatando lo que hubiera
    # configurado antes de que esa ubicacion existiera. Va en su propio try
    # por el mismo motivo: sembrar es una comodidad, no una condicion para
    # que exista el menu.
    try:
        _enabled_config.ensure_user_ini()
    except Exception as _seed_error:
        nuke.warning("No se pudo sembrar la config de LGA Layout ToolPack: %s" % _seed_error)


def load_tool_flags():
    """Estado efectivo de las tools. {} si el modulo de config no cargo."""
    if _enabled_config is None:
        return {}
    return _enabled_config.load_flags()


def is_enabled(key: str) -> bool:
    """Si no está en ninguna capa => True (default)."""
    if _enabled_config is None:
        return True
    return _enabled_config.is_enabled(key)


def add_tool(menu, label, key, module, attr, shortcut=None, icon=None, context=2):
    """Registra una tool si está habilitada y la importa tarde (lazy)."""
    if not is_enabled(key):
        try:
            import nuke

            nuke.warning(f"Tool disabled: {key}")
        except Exception:
            pass
        return

    def _runner():
        m = importlib.import_module(module)
        func = getattr(m, attr)
        return func()

    kwargs = {}
    if shortcut:
        kwargs["shortcut"] = shortcut
    if icon:
        kwargs["icon"] = icon
    if context is not None:
        kwargs["shortcutContext"] = context

    menu.addCommand(label, _runner, **kwargs)


def any_enabled(keys):
    return any(is_enabled(k) for k in keys)


def _export_to_main(**objects):
    """Publica los objetos recibidos en el namespace __main__.

    Nuke evalua los comandos de menu pasados como string dentro de __main__.
    Mientras la implementacion vivia en menu.py eso funcionaba solo, porque Nuke
    ejecuta menu.py en ese mismo namespace. Ahora el codigo vive en este modulo,
    asi que sus imports quedan en el namespace del modulo y los comandos string
    fallarian con NameError si no se publican explicitamente.
    """
    import __main__

    for name, obj in objects.items():
        setattr(__main__, name, obj)


# --- End config helpers ---------------------------------------------------------


def _get_icon(name):
    icons_root = os.path.join(PY_DIR, "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# Crear el menu "TPL"
n = nuke.menu("Nuke").addMenu("TPL", icon=_get_icon("LGA_Node"))


# -----------------------------------------------------------------------------

# Agrega el comando "NODE GRAPH" al menu "LAYOUT TOOLPACK"
n.addCommand("LAYOUT TOOLPACK", lambda: None)


# Define el icono para los items A
icon_LTPA = _get_icon("LTPA")


add_tool(
    n,
    label="  Add Dots Before",
    key="Add_Dots_Before",
    module="Dots",
    attr="Dots",
    shortcut=",",
    icon=icon_LTPA,
    context=2,
)


if is_enabled("Dots_After_System"):
    import LGA_dotsAfter

    _export_to_main(LGA_dotsAfter=LGA_dotsAfter)

    n.addCommand(
        "  Add Dots After - Left",
        'LGA_dotsAfter.dotsAfter(direction="l")',
        "Shift+,",
        shortcutContext=2,
        icon=icon_LTPA,
    )
    n.addCommand(
        "  Add Dots After - Left +",
        'LGA_dotsAfter.dotsAfter(direction="ll")',
        "Ctrl+Shift+,",
        shortcutContext=2,
        icon=icon_LTPA,
    )
    n.addCommand(
        "  Add Dots After - Right",
        'LGA_dotsAfter.dotsAfter(direction="r")',
        "Shift+.",
        shortcutContext=2,
        icon=icon_LTPA,
    )
    n.addCommand(
        "  Add Dots After - Right +",
        'LGA_dotsAfter.dotsAfter(direction="rr")',
        "Ctrl+Shift+.",
        shortcutContext=2,
        icon=icon_LTPA,
    )


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items B
icon_LTPB = _get_icon("LTPB")

add_tool(
    n,
    label="  Script Checker",
    key="Script_Checker",
    module="LGA_scriptChecker",
    attr="main",
    shortcut="Ctrl+Alt+h",
    icon=icon_LTPB,
    context=2,
)


add_tool(
    n,
    label="  Create StickyNote",
    key="StickyNote",
    module="LGA_StickyNote",
    attr="run_sticky_note_editor",
    shortcut="Shift+n",
    icon=icon_LTPB,
    context=2,
)


if is_enabled("LGA_Backdrop_System"):
    # Importar el LGA_backdrop
    nuke.pluginAddPath(os.path.join(PY_DIR, "LGA_backdrop").replace("\\", "/"))
    import LGA_backdrop

    _export_to_main(LGA_backdrop=LGA_backdrop)

    nukescripts.autoBackdrop = LGA_backdrop.autoBackdrop  # type: ignore
    n.addCommand(
        "  Create LGA_Backdrop",
        "LGA_backdrop.autoBackdrop()",
        "Shift+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    # Importar el LGA_backdropReplacer para LGA_backdrop
    import LGA_backdropReplacer

    _export_to_main(LGA_backdropReplacer=LGA_backdropReplacer)

    n.addCommand(
        "  Replace with LGA_Backdrop",
        "LGA_backdropReplacer.replace_with_lga_backdrop()",
        "Ctrl+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    # Toggle Fill/Border para todos los backdrops usando el primero como master
    import LGA_backdropToggleAppearance

    _export_to_main(LGA_backdropToggleAppearance=LGA_backdropToggleAppearance)

    n.addCommand(
        "  Toggle Backdrop Fill | Border",
        "LGA_backdropToggleAppearance.toggle_backdrop_fill_border()",
        "Ctrl+Alt+b",
        icon=icon_LTPB,
    )


add_tool(
    n,
    label="  Label Nodes",
    key="NodeLabel",
    module="LGA_NodeLabel",
    attr="run_node_label_editor",
    shortcut="shift+l",
    icon=icon_LTPB,
    context=2,
)


add_tool(
    n,
    label="  AutoStamps",
    key="AutoStamps",
    module="LGA_AutoStamps",
    attr="main",
    icon=icon_LTPB,
    context=2,
)


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")
icon_LTPCDE = _get_icon("LTPCDE")


if is_enabled("Layout_Panel"):
    add_tool(
        n,
        label="  Layout Panel",
        key="Layout_Panel",
        module="LGA_layoutPanel",
        attr="show_panel",
        shortcut="Alt+5",
        icon=icon_LTPCDE,
        context=2,
    )
    n.addSeparator()


if is_enabled("Select_Nodes"):

    import LGA_selectNodes

    _export_to_main(LGA_selectNodes=LGA_selectNodes)

    n.addCommand(
        "  Select Nodes - Left",
        "LGA_selectNodes.selectNodes('l')",
        "Alt+4",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Nodes - Right",
        "LGA_selectNodes.selectNodes('r')",
        "Alt+6",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Nodes - Top",
        "LGA_selectNodes.selectNodes('t')",
        "Alt+8",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Nodes - Bottom",
        "LGA_selectNodes.selectNodes('b')",
        "Alt+2",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    # n.addCommand("--Select Nodes Panel", "LGA_selectNodes.show_select_nodes_panel()", "Meta+5", shortcutContext=2)
    n.addCommand(
        "  Select Conected Nodes - Left",
        "LGA_selectNodes.selectConnectedNodes('l')",
        "Meta+4",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Conected Nodes - Right",
        "LGA_selectNodes.selectConnectedNodes('r')",
        "Meta+6",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Conected Nodes - Top",
        "LGA_selectNodes.selectConnectedNodes('t')",
        "Meta+8",
        shortcutContext=2,
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select Conected Nodes - Bottom",
        "LGA_selectNodes.selectConnectedNodes('b')",
        "Meta+2",
        shortcutContext=2,
        icon=icon_LTPC,
    )

    n.addCommand(
        "  Select All Nodes - Left",
        "LGA_selectNodes.selectAllNodes('l')",
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select All Nodes - Right",
        "LGA_selectNodes.selectAllNodes('r')",
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select All Nodes - Top",
        "LGA_selectNodes.selectAllNodes('t')",
        icon=icon_LTPC,
    )
    n.addCommand(
        "  Select All Nodes - Bottom",
        "LGA_selectNodes.selectAllNodes('b')",
        icon=icon_LTPC,
    )


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items D
icon_LTPD = _get_icon("LTPD")


if is_enabled("Align_Nodes"):
    import LGA_alignNodes_Backdrops

    _export_to_main(LGA_alignNodes_Backdrops=LGA_alignNodes_Backdrops)

    n.addCommand(
        "  Align Nodes or Bdrps - Left",
        "LGA_alignNodes_Backdrops.alignNodes(direction='l')",
        "Ctrl+4",
        shortcutContext=2,
        icon=icon_LTPD,
    )
    n.addCommand(
        "  Align Nodes or Bdrps - Right",
        "LGA_alignNodes_Backdrops.alignNodes(direction='r')",
        "Ctrl+6",
        shortcutContext=2,
        icon=icon_LTPD,
    )
    n.addCommand(
        "  Align Nodes or Bdrps - Top",
        "LGA_alignNodes_Backdrops.alignNodes(direction='t')",
        "Ctrl+8",
        shortcutContext=2,
        icon=icon_LTPD,
    )
    n.addCommand(
        "  Align Nodes or Bdrps - Bottom",
        "LGA_alignNodes_Backdrops.alignNodes(direction='b')",
        "Ctrl+2",
        shortcutContext=2,
        icon=icon_LTPD,
    )


if is_enabled("Distribute_Nodes"):
    import LGA_distributeNodes_Backdrops

    _export_to_main(LGA_distributeNodes_Backdrops=LGA_distributeNodes_Backdrops)

    n.addCommand(
        "  Dist Nodes or Bdrps - Horizontal",
        "LGA_distributeNodes_Backdrops.distribute(direction='h')",
        "Ctrl+0",
        shortcutContext=2,
        icon=icon_LTPD,
    )
    n.addCommand(
        "  Dist Nodes or Bdrps - Vertical",
        "LGA_distributeNodes_Backdrops.distribute(direction='v')",
        "Ctrl+.",
        shortcutContext=2,
        icon=icon_LTPD,
    )


if is_enabled("Arrange_Nodes"):
    import LGA_arrangeNodes

    _export_to_main(LGA_arrangeNodes=LGA_arrangeNodes)

    n.addCommand(
        "  Arrange Nodes",
        "LGA_arrangeNodes.main()",
        "Ctrl+5",
        shortcutContext=2,
        icon=icon_LTPD,
    )
    import LGA_arrangeNodes_OLD

    _export_to_main(LGA_arrangeNodes_OLD=LGA_arrangeNodes_OLD)

    n.addCommand(
        "  Arrange Nodes (Old)",
        "LGA_arrangeNodes_OLD.main()",
        "Ctrl+Alt+5",
        shortcutContext=2,
        icon=icon_LTPD,
    )

"""
# Importar el LGA_arrangeNodes_NU
import LGA_arrangeNodes_NU
n.addCommand("  Arrange Nodes Beta", "LGA_arrangeNodes_NU.main()", "Meta+5", shortcutContext=2, icon=icon_LTPD)
"""

if is_enabled("Scale_Nodes"):
    import scale_widget

    _export_to_main(scale_widget=scale_widget)

    n.addCommand(
        "  Scale Nodes",
        "scale_widget.scale_tree()",
        "ctrl++",
        shortcutContext=2,
        icon=icon_LTPD,
    )


"""
# Importar el LGA_nodePosition
import LGA_nodePosition
n.addCommand("  Node Position", "LGA_nodePosition.nodePosition()", "Meta+5", shortcutContext=2, icon=icon_LTPD)
"""


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items E
icon_LTPE = _get_icon("LTPE")

if is_enabled("Push_Pull_Nodes"):
    from nuke_move_nodes import push_nodes

    _export_to_main(push_nodes=push_nodes)

    n.addCommand(
        "  Push Nodes - Up",
        "push_nodes.push(up=True)",
        "Ctrl+Alt+8",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Push Nodes - Down",
        "push_nodes.push(down=True)",
        "Ctrl+Alt+2",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Push Nodes - Left",
        "push_nodes.push(left=True)",
        "Ctrl+Alt+4",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Push Nodes - Right",
        "push_nodes.push(right=True)",
        "Ctrl+Alt+6",
        shortcutContext=2,
        icon=icon_LTPE,
    )

    # Importar el Pull nodes
    from nuke_move_nodes import pull_nodes

    _export_to_main(pull_nodes=pull_nodes)

    n.addCommand(
        "  Pull Nodes - Up",
        "pull_nodes.pull(up=True)",
        "Ctrl+Alt+shift+8",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Pull Nodes - Down",
        "pull_nodes.pull(down=True)",
        "Ctrl+Alt+shift+2",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Pull Nodes - Left",
        "pull_nodes.pull(left=True)",
        "Ctrl+Alt+shift+4",
        shortcutContext=2,
        icon=icon_LTPE,
    )
    n.addCommand(
        "  Pull Nodes - Right",
        "pull_nodes.pull(right=True)",
        "Ctrl+Alt+shift+6",
        shortcutContext=2,
        icon=icon_LTPE,
    )


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items F
icon_LTPF = _get_icon("LTPF")


if is_enabled("Easy_Navigate"):
    # Km_NodeGraph
    nuke.pluginAddPath(os.path.join(PY_DIR, "Km_NodeGraphEN").replace("\\", "/"))

    # Importar Easy Navigate
    import Km_NodeGraph_Easy_Navigate
    import model

    _export_to_main(Km_NodeGraph_Easy_Navigate=Km_NodeGraph_Easy_Navigate)

    easy_nav_menu = n.addMenu("  Easy Navigate", icon=icon_LTPF)
    settings = model.Settings().Load()
    n.addCommand(
        "  Easy Navigate/Show Panel",
        "Km_NodeGraph_Easy_Navigate.ShowMainWindow()",
        settings["shortcut"],
        shortcutContext=2,
        icon=icon_LTPF,
    )
    n.addCommand(
        "  Easy Navigate/Settings | Help",
        "Km_NodeGraph_Easy_Navigate.ShowSettings()",
        "",
        icon=icon_LTPF,
    )
    n.addCommand(
        "  Easy Navigate/Edit Bookmarks",
        "Km_NodeGraph_Easy_Navigate.ShowEditBookmarksWindow()",
        "",
        icon=icon_LTPF,
    )
    n.addCommand(
        "  Easy Navigate/Templates",
        "Km_NodeGraph_Easy_Navigate.ShowTemplatesWindow()",
        "",
        icon=icon_LTPF,
    )
    n.addCommand(
        "  Easy Navigate/Survive (Reset Bookmarks)",
        "Km_NodeGraph_Easy_Navigate.Survive()",
        "",
        icon=icon_LTPF,
    )


add_tool(
    n,
    label="  Toggle Zoom",
    key="Toggle_Zoom",
    module="LGA_zoom",
    attr="main",
    shortcut="h",
    icon=icon_LTPF,
    context=2,
)

# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser
import nuke


def _enable_tools_runner():
    import LGA_ToolPackLayout_EnabledPanel

    LGA_ToolPackLayout_EnabledPanel.main()


# A proposito NO pasa por is_enabled(): si el usuario apaga todo, este es el
# unico camino de vuelta. Un panel que se puede desactivar a si mismo deja al
# usuario sin forma de reactivar nada sin editar archivos a mano.
n.addCommand("Enable Tools", _enable_tools_runner)

n.addCommand(
    "Documentation v%s" % PRODUCT_VERSION,
    lambda: webbrowser.open(
        "https://github.com/legandrop/LGA_ToolPack_Layout-for_Nuke"
    ),
)
