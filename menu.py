"""
__________________________________________

  LGA Layout ToolPack v2.51 | Lega
__________________________________________

"""

import nuke
import nukescripts

# Importar iconos de la carpeta icons
import os

# --- Config loader & helpers -------------------------------------------
import configparser, importlib


def _ini_paths():
    # user-level
    home = os.path.expanduser("~")
    user_ini = os.path.join(home, ".nuke", "_LGA_LayoutToolPack_Enabled.ini")
    # package-level (junto a este archivo)
    pkg_ini = os.path.join(os.path.dirname(__file__), "_LGA_LayoutToolPack_Enabled.ini")
    return user_ini, pkg_ini


_TOOL_FLAGS = None  # cache


def load_tool_flags():
    """Lee el INI (user pisa a package). Si falta o hay error => todo True."""
    global _TOOL_FLAGS
    if _TOOL_FLAGS is not None:
        return _TOOL_FLAGS

    cfg = configparser.ConfigParser()
    cfg.optionxform = str  # respeta mayúsculas en claves
    user_ini, pkg_ini = _ini_paths()

    read_ok = False
    for path in [pkg_ini, user_ini]:
        if os.path.isfile(path):
            try:
                cfg.read(path, encoding="utf-8")
                read_ok = True
            except Exception:
                pass

    flags = {}
    if read_ok and cfg.has_section("Tools"):
        for key, val in cfg.items("Tools"):
            v = str(val).strip().lower()
            flags[key] = v in ("1", "true", "yes", "on")
    else:
        # sin archivo/section => defaults vacíos (=> True por defecto)
        flags = {}

    _TOOL_FLAGS = flags
    return _TOOL_FLAGS


def is_enabled(key: str) -> bool:
    """Si no está en INI => True (default)."""
    flags = load_tool_flags()
    return flags.get(key, True)


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


# --- End config helpers ---------------------------------------------------------


def _get_icon(name):
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
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
    nuke.pluginAddPath("./LGA_backdrop")
    import LGA_backdrop

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

    n.addCommand(
        "  Replace with LGA_Backdrop",
        "LGA_backdropReplacer.replace_with_lga_backdrop()",
        "Ctrl+b",
        shortcutContext=2,
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


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")


if is_enabled("Select_Nodes"):
    import LGA_selectNodes

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

    n.addCommand(
        "  Arrange Nodes",
        "LGA_arrangeNodes.main()",
        "Ctrl+5",
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
    nuke.pluginAddPath("./Km_NodeGraphEN")

    # Importar Easy Navigate
    import Km_NodeGraph_Easy_Navigate
    import model

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

LTP_script_dir = os.path.dirname(os.path.realpath(__file__))
LTP_pdf_path = os.path.join(LTP_script_dir, "LGA_LayoutToolPack.pdf")

n.addCommand("Documentation v2.51", lambda: webbrowser.open("file://" + LTP_pdf_path))
