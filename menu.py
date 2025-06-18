"""
__________________________________________

  LGA Layout ToolPack v2.31 - Lega
__________________________________________

"""

# Importar iconos de la carpeta icons
import os


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


# Importar el Dots
import Dots

n.addCommand("  Add Dots Before", "Dots.Dots()", ",", shortcutContext=2, icon=icon_LTPA)


# Importar el LGA_dotsAfter
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


# Importar el LGA_StickyNote
import LGA_StickyNote

n.addCommand(
    "  Create StickyNote",
    "LGA_StickyNote.run_sticky_note()",
    "Ctrl+Shift+n",
    shortcutContext=2,
    icon=icon_LTPB,
)


# Importar el oz_backdrop
nuke.pluginAddPath("./oz_backdrop")


# Importar y asignar el atajo de teclado para LGA_oz_backdrop
# import LGA_oz_backdrop
# n.addCommand("  Create Oz_Backdrop", "LGA_oz_backdrop.create_oz_backdrop()", "Shift+b", shortcutContext=2, icon=icon_LTPB)
import oz_backdrop

nukescripts.autoBackdrop = oz_backdrop.autoBackdrop
n.addCommand(
    "  Create Oz_Backdrop",
    "oz_backdrop.autoBackdrop()",
    "Shift+b",
    shortcutContext=2,
    icon=icon_LTPB,
)


# Importar el LGA_oz_backdropReplacer
import LGA_oz_backdropReplacer

n.addCommand(
    "  Replace with Oz_Backdrop",
    "LGA_oz_backdropReplacer.replace_with_oz_backdrop()",
    "Ctrl+b",
    shortcutContext=2,
    icon=icon_LTPB,
)


# Importar el ku_labeler (con shortcut shift+n)
import ku_labeler
from ku_labeler import Core_SetLabel

LABELPOPUP = Core_SetLabel()
n.addCommand(
    "  Label Nodes", LABELPOPUP.run, "shift+n", shortcutContext=2, icon=icon_LTPB
)


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")


# Importar el LGA_selectNodes
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
    "  Select All Nodes - Left", "LGA_selectNodes.selectAllNodes('l')", icon=icon_LTPC
)
n.addCommand(
    "  Select All Nodes - Right", "LGA_selectNodes.selectAllNodes('r')", icon=icon_LTPC
)
n.addCommand(
    "  Select All Nodes - Top", "LGA_selectNodes.selectAllNodes('t')", icon=icon_LTPC
)
n.addCommand(
    "  Select All Nodes - Bottom", "LGA_selectNodes.selectAllNodes('b')", icon=icon_LTPC
)


# -----------------------------------------------------------------------------
# Separador
n.addSeparator()


# Define el icono para los items D
icon_LTPD = _get_icon("LTPD")


# Importar el LGA_alignNodes_Backdrops
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


# Importar el LGA_distributeNodes_Backdrops
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


# Importar el LGA_arrangeNodes
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

# Importar Scale Nodes
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

# Importar el Push Nodes
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


# Importar LGA_zoom
import LGA_zoom

n.addCommand("  Toggle Zoom", "LGA_zoom.main()", "h", shortcutContext=2, icon=icon_LTPF)

# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser
import nuke

LTP_script_dir = os.path.dirname(os.path.realpath(__file__))
LTP_pdf_path = os.path.join(LTP_script_dir, "LGA_LayoutToolPack.pdf")

n.addCommand("v2.3", lambda: webbrowser.open("file://" + LTP_pdf_path))
