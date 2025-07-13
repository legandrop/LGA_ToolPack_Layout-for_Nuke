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
import gc
import weakref
from collections import OrderedDict


# Importar iconos de la carpeta icons
def _get_icon(name):
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# ===== GESTIÓN DE MEMORIA SOLO PARA MÓDULOS PROBLEMÁTICOS =====
# Configuración para evitar errores de "bad allocation" SOLO en módulos problemáticos
MAX_CACHED_MODULES = 3  # Reducir cache para evitar problemas de memoria
ENABLE_AUTO_CLEANUP = True  # Activar limpieza automática
ENABLE_MEMORY_MONITORING = True  # Activar monitoreo de memoria


class MemoryManager:
    """Gestor de memoria para evitar bad allocation errors SOLO en módulos problemáticos"""

    def __init__(self):
        self.module_cache = OrderedDict()
        self.weak_refs = {}
        self.problematic_modules = {
            "LGA_StickyNote",
            "LGA_NodeLabel",
            "LGA_backdrop",
        }  # SOLO estos módulos causan conflictos

    def cleanup_old_modules(self):
        """Limpia módulos antiguos del cache"""
        if not ENABLE_AUTO_CLEANUP:
            return

        while len(self.module_cache) > MAX_CACHED_MODULES:
            oldest_key = next(iter(self.module_cache))
            removed_module = self.module_cache.pop(oldest_key)
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Limpiando módulo del cache: {oldest_key}")
            del removed_module

        # Forzar garbage collection solo si es necesario
        if len(self.module_cache) > MAX_CACHED_MODULES - 1:
            gc.collect()

    def register_module(self, module_name, module_obj):
        """Registra un módulo en el cache con gestión de memoria"""
        if module_obj is None:
            return

        # Limpiar módulos antiguos primero
        self.cleanup_old_modules()

        # Agregar el nuevo módulo
        self.module_cache[module_name] = module_obj

        # Crear weak reference para monitoreo
        if ENABLE_MEMORY_MONITORING:
            self.weak_refs[module_name] = weakref.ref(module_obj)
            print(
                f"[MEMORY] Módulo registrado: {module_name} (Cache: {len(self.module_cache)}/{MAX_CACHED_MODULES})"
            )

    def get_module(self, module_name):
        """Obtiene un módulo del cache"""
        cached_module = self.module_cache.get(module_name)
        if cached_module is not None and ENABLE_MEMORY_MONITORING:
            print(f"[MEMORY] Usando módulo desde cache: {module_name}")
        return cached_module

    def clear_problematic_modules(self):
        """Limpia solo los módulos problemáticos"""
        if ENABLE_MEMORY_MONITORING:
            print("[MEMORY] Limpiando solo módulos problemáticos...")

        for module_name in list(self.module_cache.keys()):
            if module_name in self.problematic_modules:
                removed_module = self.module_cache.pop(module_name)
                if ENABLE_MEMORY_MONITORING:
                    print(f"[MEMORY] Limpiando módulo problemático: {module_name}")
                del removed_module

        # Limpiar weak references
        for module_name in self.problematic_modules:
            if module_name in self.weak_refs:
                del self.weak_refs[module_name]

        gc.collect()

    def clear_all(self):
        """Limpia todo el cache de memoria"""
        if ENABLE_MEMORY_MONITORING:
            print(
                f"[MEMORY] Limpiando todo el cache ({len(self.module_cache)} módulos)"
            )
        self.module_cache.clear()
        self.weak_refs.clear()
        gc.collect()


# Instancia global del gestor de memoria
memory_manager = MemoryManager()


# ===== ENCAPSULACIÓN SOLO PARA MÓDULOS PROBLEMÁTICOS =====
class ModuleNamespace:
    """Clase para encapsular SOLO los módulos problemáticos con gestión de memoria"""

    def __init__(self, module_name, plugin_path=None):
        self.module_name = module_name
        self.plugin_path = plugin_path
        self._module = None
        self._loaded = False
        self._loading = False  # Flag para evitar cargas concurrentes

    def _load_module(self):
        """Carga el módulo con gestión de memoria mejorada"""
        if self._loading:
            print(
                f"[MEMORY WARNING] Módulo {self.module_name} ya está cargándose, evitando carga concurrente"
            )
            return None

        # Verificar si está en cache primero
        cached_module = memory_manager.get_module(self.module_name)
        if cached_module is not None:
            self._module = cached_module
            self._loaded = True
            return self._module

        # Si ya está cargado y es válido, devolverlo
        if self._loaded and self._module is not None:
            return self._module

        self._loading = True

        try:
            # Limpiar memoria antes de cargar SOLO si es necesario
            if (
                ENABLE_AUTO_CLEANUP
                and self.module_name in memory_manager.problematic_modules
            ):
                memory_manager.clear_problematic_modules()

            # Agregar path si es necesario
            if self.plugin_path:
                abs_plugin_path = os.path.abspath(self.plugin_path)
                if abs_plugin_path not in sys.path:
                    sys.path.insert(0, abs_plugin_path)
                nuke.pluginAddPath(abs_plugin_path)

            # NUEVO ENFOQUE: No usar reload(), siempre importar fresh
            # Esto evita el error "reload() argument must be a module"
            if self.module_name in sys.modules:
                # En lugar de reload, eliminar del cache de Python y reimportar
                if ENABLE_MEMORY_MONITORING:
                    print(
                        f"[MEMORY] Eliminando módulo de sys.modules: {self.module_name}"
                    )
                del sys.modules[self.module_name]

            # Importar el módulo fresh
            self._module = importlib.import_module(self.module_name)

            # Registrar en el gestor de memoria
            memory_manager.register_module(self.module_name, self._module)

            self._loaded = True
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Módulo '{self.module_name}' cargado exitosamente")

            return self._module

        except Exception as e:
            print(f"[MEMORY ERROR] Error cargando módulo '{self.module_name}': {e}")
            # En caso de error, intentar cargar sin eliminar de sys.modules
            try:
                if self.module_name in sys.modules:
                    self._module = sys.modules[self.module_name]
                    if ENABLE_MEMORY_MONITORING:
                        print(
                            f"[MEMORY] Usando módulo existente de sys.modules: {self.module_name}"
                        )
                    return self._module
            except:
                pass
            return None
        finally:
            self._loading = False

    def get_function(self, function_name):
        """Obtiene una función del módulo con manejo de errores mejorado"""
        try:
            module = self._load_module()
            if module and hasattr(module, function_name):
                return getattr(module, function_name)
            else:
                print(
                    f"[MEMORY ERROR] Función '{function_name}' no encontrada en módulo '{self.module_name}'"
                )
                return None
        except Exception as e:
            print(f"[MEMORY ERROR] Error obteniendo función '{function_name}': {e}")
            return None

    def call_function(self, function_name, *args, **kwargs):
        """Llama a una función con manejo de memoria mejorado"""
        try:
            func = self.get_function(function_name)
            if func:
                result = func(*args, **kwargs)
                return result
            return None
        except Exception as e:
            print(f"[MEMORY ERROR] Error ejecutando función '{function_name}': {e}")
            return None

    def cleanup(self):
        """Limpia el módulo de memoria de forma segura"""
        # Cleanup suave - solo marcar como no cargado
        self._loaded = False
        if ENABLE_MEMORY_MONITORING:
            print(f"[MEMORY] Módulo '{self.module_name}' marcado para recarga")


# ===== INSTANCIAS DE NAMESPACES SOLO PARA MÓDULOS PROBLEMÁTICOS =====
# SOLO los módulos problemáticos que causan conflictos tendrán namespaces encapsulados

# Módulos problemáticos que causan conflictos (con gestión de memoria especial)
sticky_note_ns = ModuleNamespace("LGA_StickyNote")
node_label_ns = ModuleNamespace("LGA_NodeLabel")

# Backdrop modules con paths específicos
backdrop_path = os.path.join(os.path.dirname(__file__), "LGA_backdrop")
lga_backdrop_ns = ModuleNamespace("LGA_backdrop", backdrop_path)
lga_backdrop_replacer_ns = ModuleNamespace("LGA_backdropReplacer")

oz_backdrop_path = os.path.join(os.path.dirname(__file__), "oz_backdrop")
oz_backdrop_ns = ModuleNamespace("oz_backdrop", oz_backdrop_path)
oz_backdrop_replacer_ns = ModuleNamespace("LGA_oz_backdropReplacer")


# ===== FUNCIONES PARA MÓDULOS PROBLEMÁTICOS CON GESTIÓN DE MEMORIA =====
def _run_sticky_note():
    """Ejecuta StickyNote con gestión de memoria especial"""
    print("[MEMORY] Ejecutando StickyNote con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_StickyNote")
    return sticky_note_ns.call_function("run_sticky_note_editor")


def _run_node_label():
    """Ejecuta NodeLabel con gestión de memoria especial"""
    print("[MEMORY] Ejecutando NodeLabel con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_NodeLabel")
    return node_label_ns.call_function("run_node_label_editor")


def _run_lga_backdrop():
    """Ejecuta LGA_backdrop con gestión de memoria"""
    print("[MEMORY] Ejecutando LGA_backdrop con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_backdrop")
    return lga_backdrop_ns.call_function("autoBackdrop")


def _run_lga_backdrop_replacer():
    """Ejecuta LGA_backdropReplacer con gestión de memoria"""
    return lga_backdrop_replacer_ns.call_function("replace_with_lga_backdrop")


def _run_oz_backdrop():
    """Ejecuta oz_backdrop con gestión de memoria"""
    return oz_backdrop_ns.call_function("autoBackdrop")


def _run_oz_backdrop_replacer():
    """Ejecuta oz_backdropReplacer con gestión de memoria"""
    return oz_backdrop_replacer_ns.call_function("replace_with_oz_backdrop")


# ===== FUNCIONES DE LIMPIEZA PARA MÓDULOS PROBLEMÁTICOS =====
def cleanup_specific_module(module_name):
    """Limpia un módulo específico"""
    print(f"[MEMORY] Limpiando módulo específico: {module_name}")

    # Limpiar del cache
    if module_name in memory_manager.module_cache:
        removed_module = memory_manager.module_cache.pop(module_name)
        del removed_module

    # Limpiar weak reference
    if module_name in memory_manager.weak_refs:
        del memory_manager.weak_refs[module_name]

    gc.collect()
    print(f"[MEMORY] Módulo {module_name} limpiado")


def cleanup_problematic_modules():
    """Limpia solo los módulos problemáticos"""
    print("[MEMORY] Iniciando limpieza de módulos problemáticos...")

    # Solo limpiar módulos problemáticos, no todos
    memory_manager.clear_problematic_modules()

    # Limpiar solo los namespaces problemáticos
    problematic_namespaces = [sticky_note_ns, node_label_ns, lga_backdrop_ns]

    for namespace in problematic_namespaces:
        try:
            namespace.cleanup()
        except Exception as e:
            print(f"[MEMORY ERROR] Error limpiando namespace: {e}")

    # Forzar garbage collection una sola vez
    gc.collect()

    print("[MEMORY] Limpieza de módulos problemáticos completada")


# ===== CONFIGURACIÓN DE BACKDROP CON GESTIÓN DE MEMORIA =====
def _setup_backdrop_nukescripts():
    """Configura nukescripts.autoBackdrop con gestión de memoria"""
    try:
        if USE_LGA_BACKDROP:
            autoBackdrop_func = lga_backdrop_ns.get_function("autoBackdrop")
            if autoBackdrop_func:
                nukescripts.autoBackdrop = autoBackdrop_func
        else:
            autoBackdrop_func = oz_backdrop_ns.get_function("autoBackdrop")
            if autoBackdrop_func:
                nukescripts.autoBackdrop = autoBackdrop_func
    except Exception as e:
        print(f"[MEMORY ERROR] Error configurando backdrop: {e}")


# ===== IMPORTACIONES NORMALES PARA MÓDULOS QUE FUNCIONAN BIEN =====
# Todos los demás módulos usan importaciones normales como antes

# Módulos básicos - IMPORTACIÓN NORMAL
import Dots
import LGA_dotsAfter
import LGA_scriptChecker

# Módulos de selección - IMPORTACIÓN NORMAL
import LGA_selectNodes

# Módulos de alineación - IMPORTACIÓN NORMAL
import LGA_alignNodes_Backdrops
import LGA_distributeNodes_Backdrops
import LGA_arrangeNodes
import scale_widget

# Módulos de movimiento - IMPORTACIÓN NORMAL
from nuke_move_nodes import push_nodes, pull_nodes

# Easy Navigate modules - IMPORTACIÓN NORMAL
km_nodegraph_path = os.path.join(os.path.dirname(__file__), "Km_NodeGraphEN")
if km_nodegraph_path not in sys.path:
    sys.path.insert(0, km_nodegraph_path)
nuke.pluginAddPath(km_nodegraph_path)

import Km_NodeGraph_Easy_Navigate
import model

# Zoom module - IMPORTACIÓN NORMAL
import LGA_zoom


# ===== CREACIÓN DEL MENÚ =====

# Crear el menu "TPL"
n = nuke.menu("Nuke").addMenu("TPL", icon=_get_icon("LGA_Node"))

# -----------------------------------------------------------------------------

# Agrega el comando "NODE GRAPH" al menu "LAYOUT TOOLPACK"
n.addCommand("LAYOUT TOOLPACK", lambda: None)

# Define el icono para los items A
icon_LTPA = _get_icon("LTPA")

# Comandos con importaciones normales
n.addCommand("  Add Dots Before", "Dots.Dots()", ",", shortcutContext=2, icon=icon_LTPA)

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

# Script Checker - IMPORTACIÓN NORMAL
n.addCommand(
    "  Script Checker",
    "LGA_scriptChecker.main()",
    "Ctrl+Alt+h",
    shortcutContext=2,
    icon=icon_LTPB,
)

# StickyNote - CON GESTIÓN DE MEMORIA (PROBLEMÁTICO)
n.addCommand(
    "  Create StickyNote",
    _run_sticky_note,
    "Shift+n",
    shortcutContext=2,
    icon=icon_LTPB,
)

# Flag para elegir entre LGA_backdrop o oz_backdrop
USE_LGA_BACKDROP = True  # Cambiar a False para usar oz_backdrop

# Configurar nukescripts.autoBackdrop con gestión de memoria
_setup_backdrop_nukescripts()

# Backdrop - CON GESTIÓN DE MEMORIA (PROBLEMÁTICO)
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

# NodeLabel - CON GESTIÓN DE MEMORIA (PROBLEMÁTICO)
n.addCommand(
    "  Label Nodes",
    _run_node_label,
    "shift+l",
    shortcutContext=2,
    icon=icon_LTPB,
)

# Agregar comando de limpieza de memoria para debug - SOLO MÓDULOS PROBLEMÁTICOS
n.addCommand(
    "  [DEBUG] Clean Memory",
    cleanup_problematic_modules,
    "",
    shortcutContext=2,
    icon=icon_LTPB,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")

# Select Nodes - IMPORTACIÓN NORMAL
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

# Align Nodes - IMPORTACIÓN NORMAL
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

# Distribute Nodes - IMPORTACIÓN NORMAL
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

# Arrange Nodes - IMPORTACIÓN NORMAL
n.addCommand(
    "  Arrange Nodes",
    "LGA_arrangeNodes.main()",
    "Ctrl+5",
    shortcutContext=2,
    icon=icon_LTPD,
)

# Scale Nodes - IMPORTACIÓN NORMAL
n.addCommand(
    "  Scale Nodes",
    "scale_widget.scale_tree()",
    "ctrl++",
    shortcutContext=2,
    icon=icon_LTPD,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items E
icon_LTPE = _get_icon("LTPE")

# Push/Pull Nodes - IMPORTACIÓN NORMAL
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

# Easy Navigate - IMPORTACIÓN NORMAL
easy_nav_menu = n.addMenu("  Easy Navigate", icon=icon_LTPF)

# Obtener settings para shortcut
settings = model.Settings().Load()

n.addCommand(
    "  Easy Navigate/Show Panel",
    "Km_NodeGraph_Easy_Navigate.ShowMainWindow()",
    settings.get("shortcut", ""),
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

# Toggle Zoom - IMPORTACIÓN NORMAL
n.addCommand("  Toggle Zoom", "LGA_zoom.main()", "h", shortcutContext=2, icon=icon_LTPF)

# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser

LTP_script_dir = os.path.dirname(os.path.realpath(__file__))
LTP_pdf_path = os.path.join(LTP_script_dir, "LGA_LayoutToolPack.pdf")

n.addCommand("Documentation v2.5", lambda: webbrowser.open("file://" + LTP_pdf_path))

print(
    "[MEMORY] Sistema de gestión de memoria inicializado SOLO para módulos problemáticos"
)
print("         Módulos problemáticos: LGA_StickyNote, LGA_NodeLabel, LGA_backdrop")
print("         Resto de módulos: Importación normal sin encapsulación")
print(
    f"[MEMORY] Configuración: MAX_CACHED_MODULES={MAX_CACHED_MODULES}, AUTO_CLEANUP={ENABLE_AUTO_CLEANUP}"
)
