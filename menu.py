"""
__________________________________________

  LGA Layout ToolPack v2.5 | Lega
__________________________________________

"""

import nuke
import nukescripts
import importlib
import sys
import os


# Importar iconos de la carpeta icons
def _get_icon(name):
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# ===== ENCAPSULACIÓN COMPLETA CON NAMESPACES SEPARADOS =====
# Para evitar conflictos entre scripts que tienen funciones con nombres idénticos,
# implementamos encapsulación completa donde cada módulo se carga en su propio
# namespace aislado usando importlib.


class ModuleNamespace:
    """Clase para encapsular módulos en namespaces separados"""

    def __init__(self, module_name, plugin_path=None):
        self.module_name = module_name
        self.plugin_path = plugin_path
        self._module = None
        self._loaded = False

    def _load_module(self):
        """Carga el módulo en un namespace aislado"""
        if self._loaded:
            return self._module

        try:
            # Agregar path si es necesario
            if self.plugin_path:
                if self.plugin_path not in sys.path:
                    sys.path.insert(0, self.plugin_path)
                    nuke.pluginAddPath(self.plugin_path)

            # Recargar el módulo si ya existe para evitar conflictos
            if self.module_name in sys.modules:
                self._module = importlib.reload(sys.modules[self.module_name])
            else:
                self._module = importlib.import_module(self.module_name)

            self._loaded = True
            print(
                f"[NAMESPACE] Módulo '{self.module_name}' cargado en namespace aislado"
            )
            return self._module

        except Exception as e:
            print(f"[NAMESPACE ERROR] Error cargando módulo '{self.module_name}': {e}")
            return None

    def get_function(self, function_name):
        """Obtiene una función del módulo encapsulado"""
        module = self._load_module()
        if module and hasattr(module, function_name):
            return getattr(module, function_name)
        else:
            print(
                f"[NAMESPACE ERROR] Función '{function_name}' no encontrada en módulo '{self.module_name}'"
            )
            return None

    def call_function(self, function_name, *args, **kwargs):
        """Llama a una función del módulo encapsulado"""
        func = self.get_function(function_name)
        if func:
            return func(*args, **kwargs)
        return None


# ===== INSTANCIAS DE NAMESPACES PARA CADA MÓDULO =====
# Cada módulo problemático tendrá su propio namespace aislado

# Módulos básicos
dots_ns = ModuleNamespace("Dots")
dots_after_ns = ModuleNamespace("LGA_dotsAfter")
script_checker_ns = ModuleNamespace("LGA_scriptChecker")

# Módulos problemáticos que causan conflictos
sticky_note_ns = ModuleNamespace("LGA_StickyNote")
node_label_ns = ModuleNamespace("LGA_NodeLabel")

# Backdrop modules con paths específicos
backdrop_path = os.path.join(os.path.dirname(__file__), "LGA_backdrop")
lga_backdrop_ns = ModuleNamespace("LGA_backdrop", backdrop_path)
lga_backdrop_replacer_ns = ModuleNamespace("LGA_backdropReplacer")

oz_backdrop_path = os.path.join(os.path.dirname(__file__), "oz_backdrop")
oz_backdrop_ns = ModuleNamespace("oz_backdrop", oz_backdrop_path)
oz_backdrop_replacer_ns = ModuleNamespace("LGA_oz_backdropReplacer")

# Otros módulos
select_nodes_ns = ModuleNamespace("LGA_selectNodes")
align_nodes_ns = ModuleNamespace("LGA_alignNodes_Backdrops")
distribute_nodes_ns = ModuleNamespace("LGA_distributeNodes_Backdrops")
arrange_nodes_ns = ModuleNamespace("LGA_arrangeNodes")
scale_widget_ns = ModuleNamespace("scale_widget")

# Módulos de movimiento de nodos
push_nodes_ns = ModuleNamespace("nuke_move_nodes.push_nodes")
pull_nodes_ns = ModuleNamespace("nuke_move_nodes.pull_nodes")

# Easy Navigate modules
km_nodegraph_path = os.path.join(os.path.dirname(__file__), "Km_NodeGraphEN")
easy_navigate_ns = ModuleNamespace("Km_NodeGraph_Easy_Navigate", km_nodegraph_path)
model_ns = ModuleNamespace("model", km_nodegraph_path)

# Zoom module
zoom_ns = ModuleNamespace("LGA_zoom")

# ===== FUNCIONES WRAPPER ENCAPSULADAS =====
# Estas funciones usan los namespaces para evitar conflictos


def _run_dots():
    """Ejecuta Dots con namespace encapsulado"""
    return dots_ns.call_function("Dots")


def _run_dots_after_left():
    """Ejecuta dotsAfter left con namespace encapsulado"""
    return dots_after_ns.call_function("dotsAfter", direction="l")


def _run_dots_after_left_plus():
    """Ejecuta dotsAfter left+ con namespace encapsulado"""
    return dots_after_ns.call_function("dotsAfter", direction="ll")


def _run_dots_after_right():
    """Ejecuta dotsAfter right con namespace encapsulado"""
    return dots_after_ns.call_function("dotsAfter", direction="r")


def _run_dots_after_right_plus():
    """Ejecuta dotsAfter right+ con namespace encapsulado"""
    return dots_after_ns.call_function("dotsAfter", direction="rr")


def _run_script_checker():
    """Ejecuta scriptChecker con namespace encapsulado"""
    return script_checker_ns.call_function("main")


def _run_sticky_note():
    """Ejecuta StickyNote con namespace encapsulado"""
    return sticky_note_ns.call_function("run_sticky_note_editor")


def _run_lga_backdrop():
    """Ejecuta LGA_backdrop con namespace encapsulado"""
    return lga_backdrop_ns.call_function("autoBackdrop")


def _run_lga_backdrop_replacer():
    """Ejecuta LGA_backdropReplacer con namespace encapsulado"""
    return lga_backdrop_replacer_ns.call_function("replace_with_lga_backdrop")


def _run_oz_backdrop():
    """Ejecuta oz_backdrop con namespace encapsulado"""
    return oz_backdrop_ns.call_function("autoBackdrop")


def _run_oz_backdrop_replacer():
    """Ejecuta oz_backdropReplacer con namespace encapsulado"""
    return oz_backdrop_replacer_ns.call_function("replace_with_oz_backdrop")


def _run_node_label():
    """Ejecuta NodeLabel con namespace encapsulado"""
    return node_label_ns.call_function("run_node_label_editor")


def _run_select_nodes_left():
    """Ejecuta selectNodes left con namespace encapsulado"""
    return select_nodes_ns.call_function("selectNodes", "l")


def _run_select_nodes_right():
    """Ejecuta selectNodes right con namespace encapsulado"""
    return select_nodes_ns.call_function("selectNodes", "r")


def _run_select_nodes_top():
    """Ejecuta selectNodes top con namespace encapsulado"""
    return select_nodes_ns.call_function("selectNodes", "t")


def _run_select_nodes_bottom():
    """Ejecuta selectNodes bottom con namespace encapsulado"""
    return select_nodes_ns.call_function("selectNodes", "b")


def _run_select_connected_nodes_left():
    """Ejecuta selectConnectedNodes left con namespace encapsulado"""
    return select_nodes_ns.call_function("selectConnectedNodes", "l")


def _run_select_connected_nodes_right():
    """Ejecuta selectConnectedNodes right con namespace encapsulado"""
    return select_nodes_ns.call_function("selectConnectedNodes", "r")


def _run_select_connected_nodes_top():
    """Ejecuta selectConnectedNodes top con namespace encapsulado"""
    return select_nodes_ns.call_function("selectConnectedNodes", "t")


def _run_select_connected_nodes_bottom():
    """Ejecuta selectConnectedNodes bottom con namespace encapsulado"""
    return select_nodes_ns.call_function("selectConnectedNodes", "b")


def _run_select_all_nodes_left():
    """Ejecuta selectAllNodes left con namespace encapsulado"""
    return select_nodes_ns.call_function("selectAllNodes", "l")


def _run_select_all_nodes_right():
    """Ejecuta selectAllNodes right con namespace encapsulado"""
    return select_nodes_ns.call_function("selectAllNodes", "r")


def _run_select_all_nodes_top():
    """Ejecuta selectAllNodes top con namespace encapsulado"""
    return select_nodes_ns.call_function("selectAllNodes", "t")


def _run_select_all_nodes_bottom():
    """Ejecuta selectAllNodes bottom con namespace encapsulado"""
    return select_nodes_ns.call_function("selectAllNodes", "b")


def _run_align_nodes_left():
    """Ejecuta alignNodes left con namespace encapsulado"""
    return align_nodes_ns.call_function("alignNodes", direction="l")


def _run_align_nodes_right():
    """Ejecuta alignNodes right con namespace encapsulado"""
    return align_nodes_ns.call_function("alignNodes", direction="r")


def _run_align_nodes_top():
    """Ejecuta alignNodes top con namespace encapsulado"""
    return align_nodes_ns.call_function("alignNodes", direction="t")


def _run_align_nodes_bottom():
    """Ejecuta alignNodes bottom con namespace encapsulado"""
    return align_nodes_ns.call_function("alignNodes", direction="b")


def _run_distribute_nodes_horizontal():
    """Ejecuta distribute horizontal con namespace encapsulado"""
    return distribute_nodes_ns.call_function("distribute", direction="h")


def _run_distribute_nodes_vertical():
    """Ejecuta distribute vertical con namespace encapsulado"""
    return distribute_nodes_ns.call_function("distribute", direction="v")


def _run_arrange_nodes():
    """Ejecuta arrangeNodes con namespace encapsulado"""
    return arrange_nodes_ns.call_function("main")


def _run_scale_nodes():
    """Ejecuta scale_widget con namespace encapsulado"""
    return scale_widget_ns.call_function("scale_tree")


def _run_push_nodes_up():
    """Ejecuta push nodes up con namespace encapsulado"""
    push_module = push_nodes_ns._load_module()
    if push_module:
        return push_module.push(up=True)


def _run_push_nodes_down():
    """Ejecuta push nodes down con namespace encapsulado"""
    push_module = push_nodes_ns._load_module()
    if push_module:
        return push_module.push(down=True)


def _run_push_nodes_left():
    """Ejecuta push nodes left con namespace encapsulado"""
    push_module = push_nodes_ns._load_module()
    if push_module:
        return push_module.push(left=True)


def _run_push_nodes_right():
    """Ejecuta push nodes right con namespace encapsulado"""
    push_module = push_nodes_ns._load_module()
    if push_module:
        return push_module.push(right=True)


def _run_pull_nodes_up():
    """Ejecuta pull nodes up con namespace encapsulado"""
    pull_module = pull_nodes_ns._load_module()
    if pull_module:
        return pull_module.pull(up=True)


def _run_pull_nodes_down():
    """Ejecuta pull nodes down con namespace encapsulado"""
    pull_module = pull_nodes_ns._load_module()
    if pull_module:
        return pull_module.pull(down=True)


def _run_pull_nodes_left():
    """Ejecuta pull nodes left con namespace encapsulado"""
    pull_module = pull_nodes_ns._load_module()
    if pull_module:
        return pull_module.pull(left=True)


def _run_pull_nodes_right():
    """Ejecuta pull nodes right con namespace encapsulado"""
    pull_module = pull_nodes_ns._load_module()
    if pull_module:
        return pull_module.pull(right=True)


def _run_easy_navigate_show_panel():
    """Ejecuta Easy Navigate show panel con namespace encapsulado"""
    return easy_navigate_ns.call_function("ShowMainWindow")


def _run_easy_navigate_settings():
    """Ejecuta Easy Navigate settings con namespace encapsulado"""
    return easy_navigate_ns.call_function("ShowSettings")


def _run_easy_navigate_edit_bookmarks():
    """Ejecuta Easy Navigate edit bookmarks con namespace encapsulado"""
    return easy_navigate_ns.call_function("ShowEditBookmarksWindow")


def _run_easy_navigate_templates():
    """Ejecuta Easy Navigate templates con namespace encapsulado"""
    return easy_navigate_ns.call_function("ShowTemplatesWindow")


def _run_easy_navigate_survive():
    """Ejecuta Easy Navigate survive con namespace encapsulado"""
    return easy_navigate_ns.call_function("Survive")


def _run_toggle_zoom():
    """Ejecuta toggle zoom con namespace encapsulado"""
    return zoom_ns.call_function("main")


# ===== CONFIGURACIÓN DE BACKDROP CON NAMESPACES =====
def _setup_backdrop_nukescripts():
    """Configura nukescripts.autoBackdrop con namespace encapsulado"""
    if USE_LGA_BACKDROP:
        autoBackdrop_func = lga_backdrop_ns.get_function("autoBackdrop")
        if autoBackdrop_func:
            nukescripts.autoBackdrop = autoBackdrop_func
    else:
        autoBackdrop_func = oz_backdrop_ns.get_function("autoBackdrop")
        if autoBackdrop_func:
            nukescripts.autoBackdrop = autoBackdrop_func


# ===== FUNCIÓN PARA OBTENER SETTINGS DE EASY NAVIGATE =====
def _get_easy_navigate_settings():
    """Obtiene settings de Easy Navigate con namespace encapsulado"""
    model_module = model_ns._load_module()
    if model_module and hasattr(model_module, "Settings"):
        return model_module.Settings().Load()
    return {"shortcut": ""}


# ===== CREACIÓN DEL MENÚ =====

# Crear el menu "TPL"
n = nuke.menu("Nuke").addMenu("TPL", icon=_get_icon("LGA_Node"))

# -----------------------------------------------------------------------------

# Agrega el comando "NODE GRAPH" al menu "LAYOUT TOOLPACK"
n.addCommand("LAYOUT TOOLPACK", lambda: None)

# Define el icono para los items A
icon_LTPA = _get_icon("LTPA")

# Comandos con namespaces encapsulados
n.addCommand("  Add Dots Before", _run_dots, ",", shortcutContext=2, icon=icon_LTPA)

n.addCommand(
    "  Add Dots After - Left",
    _run_dots_after_left,
    "Shift+,",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Left +",
    _run_dots_after_left_plus,
    "Ctrl+Shift+,",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Right",
    _run_dots_after_right,
    "Shift+.",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Right +",
    _run_dots_after_right_plus,
    "Ctrl+Shift+.",
    shortcutContext=2,
    icon=icon_LTPA,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items B
icon_LTPB = _get_icon("LTPB")

n.addCommand(
    "  Script Checker",
    _run_script_checker,
    "Ctrl+Alt+h",
    shortcutContext=2,
    icon=icon_LTPB,
)

n.addCommand(
    "  Create StickyNote",
    _run_sticky_note,
    "Shift+n",
    shortcutContext=2,
    icon=icon_LTPB,
)

# Flag para elegir entre LGA_backdrop o oz_backdrop
USE_LGA_BACKDROP = True  # Cambiar a False para usar oz_backdrop

# Configurar nukescripts.autoBackdrop con namespace encapsulado
_setup_backdrop_nukescripts()

if USE_LGA_BACKDROP:
    n.addCommand(
        "  Create LGA_Backdrop",
        _run_lga_backdrop,
        "Shift+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    n.addCommand(
        "  Replace with LGA_Backdrop",
        _run_lga_backdrop_replacer,
        "Ctrl+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )
else:
    n.addCommand(
        "  Create Oz_Backdrop",
        _run_oz_backdrop,
        "Shift+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    n.addCommand(
        "  Replace with Oz_Backdrop",
        _run_oz_backdrop_replacer,
        "Ctrl+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

n.addCommand(
    "  Label Nodes",
    _run_node_label,
    "shift+l",
    shortcutContext=2,
    icon=icon_LTPB,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")

n.addCommand(
    "  Select Nodes - Left",
    _run_select_nodes_left,
    "Alt+4",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Right",
    _run_select_nodes_right,
    "Alt+6",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Top",
    _run_select_nodes_top,
    "Alt+8",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Bottom",
    _run_select_nodes_bottom,
    "Alt+2",
    shortcutContext=2,
    icon=icon_LTPC,
)

n.addCommand(
    "  Select Conected Nodes - Left",
    _run_select_connected_nodes_left,
    "Meta+4",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Right",
    _run_select_connected_nodes_right,
    "Meta+6",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Top",
    _run_select_connected_nodes_top,
    "Meta+8",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Bottom",
    _run_select_connected_nodes_bottom,
    "Meta+2",
    shortcutContext=2,
    icon=icon_LTPC,
)

n.addCommand("  Select All Nodes - Left", _run_select_all_nodes_left, icon=icon_LTPC)
n.addCommand("  Select All Nodes - Right", _run_select_all_nodes_right, icon=icon_LTPC)
n.addCommand("  Select All Nodes - Top", _run_select_all_nodes_top, icon=icon_LTPC)
n.addCommand(
    "  Select All Nodes - Bottom", _run_select_all_nodes_bottom, icon=icon_LTPC
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items D
icon_LTPD = _get_icon("LTPD")

n.addCommand(
    "  Align Nodes or Bdrps - Left",
    _run_align_nodes_left,
    "Ctrl+4",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Right",
    _run_align_nodes_right,
    "Ctrl+6",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Top",
    _run_align_nodes_top,
    "Ctrl+8",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Bottom",
    _run_align_nodes_bottom,
    "Ctrl+2",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Dist Nodes or Bdrps - Horizontal",
    _run_distribute_nodes_horizontal,
    "Ctrl+0",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Dist Nodes or Bdrps - Vertical",
    _run_distribute_nodes_vertical,
    "Ctrl+.",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Arrange Nodes",
    _run_arrange_nodes,
    "Ctrl+5",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Scale Nodes",
    _run_scale_nodes,
    "ctrl++",
    shortcutContext=2,
    icon=icon_LTPD,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items E
icon_LTPE = _get_icon("LTPE")

n.addCommand(
    "  Push Nodes - Up",
    _run_push_nodes_up,
    "Ctrl+Alt+8",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Down",
    _run_push_nodes_down,
    "Ctrl+Alt+2",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Left",
    _run_push_nodes_left,
    "Ctrl+Alt+4",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Right",
    _run_push_nodes_right,
    "Ctrl+Alt+6",
    shortcutContext=2,
    icon=icon_LTPE,
)

n.addCommand(
    "  Pull Nodes - Up",
    _run_pull_nodes_up,
    "Ctrl+Alt+shift+8",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Down",
    _run_pull_nodes_down,
    "Ctrl+Alt+shift+2",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Left",
    _run_pull_nodes_left,
    "Ctrl+Alt+shift+4",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Right",
    _run_pull_nodes_right,
    "Ctrl+Alt+shift+6",
    shortcutContext=2,
    icon=icon_LTPE,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items F
icon_LTPF = _get_icon("LTPF")

# Easy Navigate con namespaces encapsulados
easy_nav_menu = n.addMenu("  Easy Navigate", icon=icon_LTPF)

# Obtener settings para shortcut
settings = _get_easy_navigate_settings()

n.addCommand(
    "  Easy Navigate/Show Panel",
    _run_easy_navigate_show_panel,
    settings.get("shortcut", ""),
    shortcutContext=2,
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Settings | Help",
    _run_easy_navigate_settings,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Edit Bookmarks",
    _run_easy_navigate_edit_bookmarks,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Templates",
    _run_easy_navigate_templates,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Survive (Reset Bookmarks)",
    _run_easy_navigate_survive,
    "",
    icon=icon_LTPF,
)

n.addCommand("  Toggle Zoom", _run_toggle_zoom, "h", shortcutContext=2, icon=icon_LTPF)

# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser

LTP_script_dir = os.path.dirname(os.path.realpath(__file__))
LTP_pdf_path = os.path.join(LTP_script_dir, "LGA_LayoutToolPack.pdf")

n.addCommand("Documentation v2.5", lambda: webbrowser.open("file://" + LTP_pdf_path))

print("[NAMESPACE] Sistema de namespaces encapsulados inicializado correctamente")
print(
    "[NAMESPACE] Cada módulo está aislado en su propio namespace para evitar conflictos"
)
